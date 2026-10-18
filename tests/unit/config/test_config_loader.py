"""Loading the effective configuration per environment (spec CFG-01, CFG-02, CFG-03, CFG-05)."""

from collections.abc import Callable, Iterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

from centinela_trade.config import ConfigError, SecretsConfig, load_config
from centinela_trade.config.loader import ENV_SECRET_VARS

WriteYaml = Callable[[Path, str, dict[str, Any]], None]

NO_SECRETS: dict[str, str] = {}


@pytest.fixture
def live_ready_dir(config_dir: Path) -> Path:
    """The repo config with the strategy chosen in ``live.yaml``, so live can load."""
    live = config_dir / "live.yaml"
    text = live.read_text()
    text = text.replace("name: null", "name: mean_reversion", 1)
    text = text.replace("timeframe: null", "timeframe: 4h", 1)
    live.write_text(text)
    return config_dir


# --- Repository config files ----------------------------------------------------------


@pytest.mark.parametrize("env", ["backtest", "paper"])
def test_cfg_01_repo_config_loads_for_environment(repo_config_dir: Path, env: str) -> None:
    config = load_config(env, config_dir=repo_config_dir, environ=NO_SECRETS)
    assert config.environment == env
    assert config.exchange.symbol == "BTC/USDT"
    assert config.risk.max_drawdown_pct == Decimal(15)


def test_cfg_01_repo_live_config_fails_while_strategy_is_null(repo_config_dir: Path) -> None:
    with pytest.raises(ConfigError, match=r"live requires strategy\.name and strategy\.timeframe"):
        load_config("live", config_dir=repo_config_dir, environ=NO_SECRETS)


def test_cfg_03_repo_live_yaml_matches_the_schema_once_strategy_is_chosen(
    live_ready_dir: Path,
) -> None:
    config = load_config("live", config_dir=live_ready_dir, environ=NO_SECRETS)

    assert config.environment == "live"
    assert config.exchange.account_label == "tradebot001"
    assert config.risk.max_capital_usd == Decimal(100)
    assert config.strategy.name == "mean_reversion"
    assert config.logging.level == "INFO"  # inherited from base.yaml


def test_default_config_dir_is_cwd_config(
    repo_config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(repo_config_dir.parent)
    assert load_config("backtest", environ=NO_SECRETS).environment == "backtest"


# --- Override semantics ---------------------------------------------------------------


def test_environment_override_wins_and_keeps_other_base_values(
    config_dir: Path, write_yaml: WriteYaml
) -> None:
    override: dict[str, Any] = {
        "environment": "paper",
        "risk": {"risk_per_trade_pct": 0.5},
        "logging": {"level": "DEBUG"},
    }
    write_yaml(config_dir, "paper.yaml", override)

    config = load_config("paper", config_dir=config_dir, environ=NO_SECRETS)

    assert config.risk.risk_per_trade_pct == Decimal("0.5")
    assert config.risk.max_position_pct == Decimal(25)  # untouched base value
    assert config.logging.level == "DEBUG"
    assert config.logging.log_dir == "logs"


def test_override_can_set_a_value_back_to_null(config_dir: Path, write_yaml: WriteYaml) -> None:
    base = yaml.safe_load((config_dir / "base.yaml").read_text())
    base["exchange"]["account_label"] = "base-label"
    write_yaml(config_dir, "base.yaml", base)
    write_yaml(
        config_dir,
        "backtest.yaml",
        {"environment": "backtest", "exchange": {"account_label": None}},
    )

    config = load_config("backtest", config_dir=config_dir, environ=NO_SECRETS)

    assert config.exchange.account_label is None


def test_cfg_02_out_of_range_override_is_rejected_with_field_path(
    config_dir: Path, write_yaml: WriteYaml
) -> None:
    write_yaml(config_dir, "paper.yaml", {"environment": "paper", "risk": {"max_drawdown_pct": 30}})
    with pytest.raises(ConfigError, match=r"(?s)'paper'.*risk\.max_drawdown_pct.*less than or"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


def test_cfg_01_missing_field_is_rejected_with_field_path(
    config_dir: Path, write_yaml: WriteYaml
) -> None:
    base = yaml.safe_load((config_dir / "base.yaml").read_text())
    del base["risk"]["max_orders_per_hour"]
    write_yaml(config_dir, "base.yaml", base)
    with pytest.raises(ConfigError, match=r"risk\.max_orders_per_hour\n\s+Field required"):
        load_config("backtest", config_dir=config_dir, environ=NO_SECRETS)


# --- Environment declaration ----------------------------------------------------------


def test_unknown_environment_is_rejected(repo_config_dir: Path) -> None:
    with pytest.raises(ConfigError, match="unknown environment 'production'"):
        load_config("production", config_dir=repo_config_dir, environ=NO_SECRETS)


@pytest.mark.parametrize("declared", [None, "live", "backtest"])
def test_override_must_declare_its_own_environment(
    config_dir: Path, write_yaml: WriteYaml, declared: str | None
) -> None:
    data: dict[str, Any] = {} if declared is None else {"environment": declared}
    data["logging"] = {"level": "INFO"}
    write_yaml(config_dir, "paper.yaml", data)
    with pytest.raises(ConfigError, match=r"must declare 'environment: paper'"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


# --- File and YAML errors -------------------------------------------------------------


@pytest.mark.parametrize("missing", ["base.yaml", "paper.yaml"])
def test_missing_file_is_rejected(config_dir: Path, missing: str) -> None:
    (config_dir / missing).unlink()
    with pytest.raises(ConfigError, match=rf"config file not found: .*{missing}"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


def test_malformed_yaml_is_rejected(config_dir: Path) -> None:
    (config_dir / "paper.yaml").write_text("environment: paper\nrisk: [unclosed\n")
    with pytest.raises(ConfigError, match="invalid YAML"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


@pytest.mark.parametrize("content", ["", "- a\n- b\n", "just a string\n"])
def test_non_mapping_yaml_is_rejected(config_dir: Path, content: str) -> None:
    (config_dir / "paper.yaml").write_text(content)
    with pytest.raises(ConfigError, match="must contain a mapping"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


def test_duplicate_yaml_key_is_rejected(config_dir: Path) -> None:
    (config_dir / "paper.yaml").write_text(
        "environment: paper\nrisk:\n  max_drawdown_pct: 15\n  max_drawdown_pct: 25\n"
    )
    with pytest.raises(ConfigError, match="duplicate key 'max_drawdown_pct'"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


def test_yaml_is_parsed_safely(config_dir: Path) -> None:
    (config_dir / "paper.yaml").write_text(
        "environment: paper\nx: !!python/object/apply:os.system ['true']\n"
    )
    with pytest.raises(ConfigError, match="invalid YAML"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


# --- Secrets: only from environment variables -----------------------------------------


@pytest.mark.parametrize(
    ("file", "content", "dotted"),
    [
        ("base.yaml", "secrets:\n  telegram_bot_token: x\n", "secrets"),
        ("paper.yaml", "environment: paper\nexchange:\n  api_key: x\n", "exchange.api_key"),
        ("paper.yaml", "environment: paper\nexchange:\n  apiSecret: x\n", "exchange.apiSecret"),
        ("paper.yaml", "environment: paper\nTELEGRAM_BOT_TOKEN: x\n", "TELEGRAM_BOT_TOKEN"),
    ],
)
def test_secret_keys_in_yaml_are_rejected(
    config_dir: Path, file: str, content: str, dotted: str
) -> None:
    (config_dir / file).write_text(content)
    with pytest.raises(ConfigError, match=rf"key '{dotted}' looks like a secret"):
        load_config("paper", config_dir=config_dir, environ=NO_SECRETS)


# --- CFG-05: each environment reads only the variables of its list --------------------

TESTNET_VARS = {"BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET"}
DEMO_VARS = {"BINANCE_DEMO_API_KEY", "BINANCE_DEMO_API_SECRET"}
LIVE_VARS = {"BINANCE_LIVE_API_KEY", "BINANCE_LIVE_API_SECRET"}
TELEGRAM_VARS = {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}
# Fake values: the variable name in lower case.
ALL_VARS = {var: var.lower() for var in TESTNET_VARS | DEMO_VARS | LIVE_VARS | TELEGRAM_VARS}


class RecordingEnviron(Mapping[str, str]):
    """An environment that records every variable read and forbids enumerating it."""

    def __init__(self, data: Mapping[str, str]) -> None:
        self._data = dict(data)
        self.read: set[str] = set()

    def __getitem__(self, key: str) -> str:
        self.read.add(key)
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("load_config must not enumerate the environment (CFG-05)")

    def __len__(self) -> int:
        raise AssertionError("load_config must not enumerate the environment (CFG-05)")


def _loaded(secrets: SecretsConfig) -> dict[str, str]:
    """Secrets that were filled, as ``{ENV_VAR_NAME: value}``."""
    return {
        field.upper(): value.get_secret_value() for field, value in secrets if value is not None
    }


def _dir_for(env: str, repo_config_dir: Path, live_ready_dir: Path) -> Path:
    return live_ready_dir if env == "live" else repo_config_dir


def test_cfg_05_backtest_reads_no_variable_even_if_all_are_set(repo_config_dir: Path) -> None:
    environ = RecordingEnviron(ALL_VARS)
    secrets = load_config("backtest", config_dir=repo_config_dir, environ=environ).secrets
    assert environ.read == set()
    assert _loaded(secrets) == {}


def test_cfg_05_paper_reads_only_demo_and_telegram(repo_config_dir: Path) -> None:
    environ = RecordingEnviron(ALL_VARS)
    secrets = load_config("paper", config_dir=repo_config_dir, environ=environ).secrets
    assert environ.read == DEMO_VARS | TELEGRAM_VARS
    assert _loaded(secrets) == {var: ALL_VARS[var] for var in DEMO_VARS | TELEGRAM_VARS}


def test_cfg_05_live_reads_only_live_and_telegram(live_ready_dir: Path) -> None:
    environ = RecordingEnviron(ALL_VARS)
    secrets = load_config("live", config_dir=live_ready_dir, environ=environ).secrets
    assert environ.read == LIVE_VARS | TELEGRAM_VARS
    assert _loaded(secrets) == {var: ALL_VARS[var] for var in LIVE_VARS | TELEGRAM_VARS}


@pytest.mark.parametrize("env", ["backtest", "paper", "live"])
def test_cfg_05_testnet_variables_are_never_read(
    repo_config_dir: Path, live_ready_dir: Path, env: str
) -> None:
    environ = RecordingEnviron(ALL_VARS)
    load_config(env, config_dir=_dir_for(env, repo_config_dir, live_ready_dir), environ=environ)
    assert environ.read.isdisjoint(TESTNET_VARS)


@pytest.mark.parametrize(
    ("env", "allowed"),
    [
        ("backtest", set()),
        ("paper", DEMO_VARS | TELEGRAM_VARS),
        ("live", LIVE_VARS | TELEGRAM_VARS),
    ],
)
def test_cfg_05_process_environment_is_filtered_the_same_way(
    repo_config_dir: Path,
    live_ready_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    env: str,
    allowed: set[str],
) -> None:
    for var, value in ALL_VARS.items():
        monkeypatch.setenv(var, value)
    config_dir = _dir_for(env, repo_config_dir, live_ready_dir)
    secrets = load_config(env, config_dir=config_dir).secrets
    assert _loaded(secrets) == {var: ALL_VARS[var] for var in allowed}


def test_cfg_05_dry_run_reads_nothing_with_an_empty_environ(repo_config_dir: Path) -> None:
    # Dry-run uses the paper config with no credentials: public endpoints only.
    secrets = load_config("paper", config_dir=repo_config_dir, environ=NO_SECRETS).secrets
    assert _loaded(secrets) == {}


def test_cfg_05_empty_variables_count_as_unset(repo_config_dir: Path) -> None:
    environ = {"BINANCE_DEMO_API_KEY": "", "TELEGRAM_CHAT_ID": "fake-chat"}
    secrets = load_config("paper", config_dir=repo_config_dir, environ=environ).secrets
    assert _loaded(secrets) == {"TELEGRAM_CHAT_ID": "fake-chat"}


def test_cfg_05_allowlists_match_the_secrets_model() -> None:
    listed = {var for variables in ENV_SECRET_VARS.values() for var in variables}
    assert {var.lower() for var in listed} == set(SecretsConfig.model_fields)
    assert listed.isdisjoint(TESTNET_VARS)


def test_cfg_05_paper_variables_are_declared_in_env_example(repo_config_dir: Path) -> None:
    lines = (repo_config_dir.parent / ".env.example").read_text().splitlines()
    declared = {line.split("=", 1)[0] for line in lines if line and not line.startswith("#")}
    assert set(ENV_SECRET_VARS["paper"]) <= declared


def test_validation_errors_do_not_leak_secrets(repo_config_dir: Path) -> None:
    environ = {"BINANCE_LIVE_API_SECRET": "fake-secret-value"}  # pragma: allowlist secret
    with pytest.raises(ConfigError) as excinfo:
        load_config("live", config_dir=repo_config_dir, environ=environ)
    assert "fake-secret-value" not in str(excinfo.value)
    assert "fake-secret-value" not in repr(excinfo.value.__cause__)
