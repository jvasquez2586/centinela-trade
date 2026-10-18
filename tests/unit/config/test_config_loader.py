"""Loading the effective configuration per environment (spec CFG-01, CFG-02, CFG-03)."""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

from centinela_trade.config import ConfigError, load_config
from centinela_trade.config.loader import SECRET_ENV_VARS

WriteYaml = Callable[[Path, str, dict[str, Any]], None]

NO_SECRETS: dict[str, str] = {}


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
    config_dir: Path,
) -> None:
    live = config_dir / "live.yaml"
    text = live.read_text()
    text = text.replace("name: null", "name: mean_reversion", 1)
    text = text.replace("timeframe: null", "timeframe: 4h", 1)
    live.write_text(text)

    config = load_config("live", config_dir=config_dir, environ=NO_SECRETS)

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


def test_secrets_are_read_from_environment_variables(repo_config_dir: Path) -> None:
    environ = {
        "BINANCE_TESTNET_API_KEY": "fake-testnet-key",  # pragma: allowlist secret
        "BINANCE_TESTNET_API_SECRET": "fake-testnet-secret",  # pragma: allowlist secret
        "BINANCE_DEMO_API_KEY": "fake-demo-key",  # pragma: allowlist secret
        "BINANCE_DEMO_API_SECRET": "fake-demo-secret",  # pragma: allowlist secret
        "TELEGRAM_BOT_TOKEN": "fake-token",  # pragma: allowlist secret
        "TELEGRAM_CHAT_ID": "fake-chat",  # pragma: allowlist secret
    }
    secrets = load_config("paper", config_dir=repo_config_dir, environ=environ).secrets

    assert secrets.binance_testnet_api_key is not None
    assert secrets.binance_testnet_api_key.get_secret_value() == "fake-testnet-key"
    assert secrets.binance_demo_api_secret is not None
    assert secrets.binance_demo_api_secret.get_secret_value() == "fake-demo-secret"
    assert secrets.telegram_chat_id is not None
    assert secrets.telegram_chat_id.get_secret_value() == "fake-chat"


def test_unset_or_empty_secrets_are_none(repo_config_dir: Path) -> None:
    environ = {"BINANCE_TESTNET_API_KEY": ""}
    secrets = load_config("backtest", config_dir=repo_config_dir, environ=environ).secrets
    assert secrets.binance_testnet_api_key is None
    assert secrets.telegram_bot_token is None


def test_secrets_default_to_process_environment(
    repo_config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token-from-env")
    secrets = load_config("backtest", config_dir=repo_config_dir).secrets
    assert secrets.telegram_bot_token is not None
    assert secrets.telegram_bot_token.get_secret_value() == "fake-token-from-env"


def test_secret_env_vars_match_env_example(repo_config_dir: Path) -> None:
    lines = (repo_config_dir.parent / ".env.example").read_text().splitlines()
    declared = {line.split("=", 1)[0] for line in lines if line and not line.startswith("#")}
    assert set(SECRET_ENV_VARS.values()) == declared


def test_validation_errors_do_not_leak_secrets(repo_config_dir: Path) -> None:
    environ = {"BINANCE_TESTNET_API_SECRET": "fake-secret-value"}  # pragma: allowlist secret
    with pytest.raises(ConfigError) as excinfo:
        load_config("live", config_dir=repo_config_dir, environ=environ)
    assert "fake-secret-value" not in str(excinfo.value)
    assert "fake-secret-value" not in repr(excinfo.value.__cause__)
