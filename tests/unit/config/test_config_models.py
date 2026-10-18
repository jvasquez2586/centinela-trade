"""Validation of the configuration models (spec CFG-01, CFG-02, CFG-03)."""

import copy
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import SecretStr, ValidationError

from centinela_trade.config import AppConfig, RiskConfig, SecretsConfig


def _with(data: dict[str, Any], section: str, key: str, value: Any) -> dict[str, Any]:
    changed = copy.deepcopy(data)
    changed[section][key] = value
    return changed


def test_repo_defaults_are_valid_cfg_01(config_data: dict[str, Any]) -> None:
    config = AppConfig.model_validate(config_data)
    assert config.risk.risk_per_trade_pct == Decimal("1.0")
    assert config.risk.max_open_positions == 1
    assert isinstance(config.risk.max_capital_usd, Decimal)


# --- CFG-02: one test per hard cap ---------------------------------------------------

# (key, rejected values, accepted boundary values)
HARD_CAPS: list[tuple[str, list[Any], list[Any]]] = [
    ("risk_per_trade_pct", [0, -1, "2.01", 3], [2, "0.01"]),
    ("max_position_pct", [0, -5, "50.01"], [50]),
    ("max_open_positions", [0, 2], [1]),
    ("daily_loss_limit_pct", [0, -1, "5.01"], [5]),
    ("max_drawdown_pct", [0, "25.01"], [25, "10.01"]),
    ("max_orders_per_hour", [0, 13], [1, 12]),
    ("max_consecutive_losses", [1, 11], [2, 10]),
]


@pytest.mark.parametrize(
    ("key", "value"),
    [(key, value) for key, rejected, _ in HARD_CAPS for value in rejected],
)
def test_cfg_02_rejects_value_outside_hard_cap(
    config_data: dict[str, Any], key: str, value: Any
) -> None:
    with pytest.raises(ValidationError, match=key):
        AppConfig.model_validate(_with(config_data, "risk", key, value))


@pytest.mark.parametrize(
    ("key", "value"),
    [(key, value) for key, _, accepted in HARD_CAPS for value in accepted],
)
def test_cfg_02_accepts_hard_cap_boundary(
    config_data: dict[str, Any], key: str, value: Any
) -> None:
    config = AppConfig.model_validate(_with(config_data, "risk", key, value))
    assert getattr(config.risk, key) == Decimal(str(value))


@pytest.mark.parametrize("value", [0, -1, "10", 15, 20])
def test_cfg_02_drawdown_alert_must_be_positive_and_below_max_drawdown(
    config_data: dict[str, Any], value: Any
) -> None:
    # max_drawdown_pct is 15 in the defaults; "10" is fine only if lowered below it.
    data = _with(config_data, "risk", "drawdown_alert_pct", value)
    if value == "10":
        data["risk"]["max_drawdown_pct"] = 10
    with pytest.raises(ValidationError, match="drawdown_alert_pct"):
        AppConfig.model_validate(data)


def test_cfg_02_drawdown_alert_just_below_max_drawdown_is_accepted(
    config_data: dict[str, Any],
) -> None:
    config = AppConfig.model_validate(_with(config_data, "risk", "drawdown_alert_pct", "14.99"))
    assert config.risk.drawdown_alert_pct == Decimal("14.99")


@pytest.mark.parametrize("environment", ["backtest", "paper", "live"])
@pytest.mark.parametrize("value", [0, -100])
def test_cfg_02_max_capital_must_be_positive_in_every_environment(
    config_data: dict[str, Any], environment: str, value: int
) -> None:
    data = _with(config_data, "risk", "max_capital_usd", value)
    data["environment"] = environment
    data["strategy"] = {"name": "mean_reversion", "timeframe": "4h"}
    with pytest.raises(ValidationError, match="max_capital_usd"):
        AppConfig.model_validate(data)


def _live(data: dict[str, Any]) -> dict[str, Any]:
    live = copy.deepcopy(data)
    live["environment"] = "live"
    live["strategy"] = {"name": "trend_following", "timeframe": "1h"}
    return live


def test_cfg_02_live_rejects_max_capital_above_1000(config_data: dict[str, Any]) -> None:
    data = _with(_live(config_data), "risk", "max_capital_usd", "1000.01")
    with pytest.raises(ValidationError, match=r"max_capital_usd .* must be <= 1000 in live"):
        AppConfig.model_validate(data)


def test_cfg_02_live_accepts_max_capital_of_1000(config_data: dict[str, Any]) -> None:
    config = AppConfig.model_validate(_with(_live(config_data), "risk", "max_capital_usd", 1000))
    assert config.risk.max_capital_usd == Decimal(1000)


@pytest.mark.parametrize("environment", ["backtest", "paper"])
def test_cfg_02_live_capital_cap_does_not_apply_outside_live(
    config_data: dict[str, Any], environment: str
) -> None:
    data = _with(config_data, "risk", "max_capital_usd", 10_000)
    data["environment"] = environment
    assert AppConfig.model_validate(data).risk.max_capital_usd == Decimal(10_000)


# --- Keys without a CFG-02 cap: only positivity and consistency ----------------------

POSITIVE_ONLY_KEYS = [
    "max_consecutive_api_errors",
    "max_disconnect_minutes_with_position",
    "slippage_breaker_multiplier",
    "slippage_breaker_trades",
    "volatility_pause_pct_1h",
    "price_band_pct",
    "min_stop_distance_pct",
    "max_stop_distance_pct",
]


@pytest.mark.parametrize("key", POSITIVE_ONLY_KEYS)
@pytest.mark.parametrize("value", [0, -1])
def test_risk_keys_without_cap_must_be_positive(
    config_data: dict[str, Any], key: str, value: int
) -> None:
    with pytest.raises(ValidationError, match=key):
        AppConfig.model_validate(_with(config_data, "risk", key, value))


@pytest.mark.parametrize(("low", "high"), [(15, 15), (16, 15)])
def test_risk_09_min_stop_distance_must_be_below_max(
    config_data: dict[str, Any], low: int, high: int
) -> None:
    data = _with(config_data, "risk", "min_stop_distance_pct", low)
    data["risk"]["max_stop_distance_pct"] = high
    with pytest.raises(ValidationError, match="min_stop_distance_pct"):
        AppConfig.model_validate(data)


@pytest.mark.parametrize("value", [True, 1.5, "6"])
def test_counters_are_strict_integers(config_data: dict[str, Any], value: Any) -> None:
    with pytest.raises(ValidationError, match="max_orders_per_hour"):
        AppConfig.model_validate(_with(config_data, "risk", "max_orders_per_hour", value))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "abc"])
def test_percentages_reject_non_finite_or_non_numeric(
    config_data: dict[str, Any], value: Any
) -> None:
    with pytest.raises(ValidationError, match="risk_per_trade_pct"):
        AppConfig.model_validate(_with(config_data, "risk", "risk_per_trade_pct", value))


# --- CFG-01 / CFG-03: required fields and exact schema --------------------------------


@pytest.mark.parametrize("key", list(RiskConfig.model_fields))
def test_cfg_01_missing_risk_key_is_rejected(config_data: dict[str, Any], key: str) -> None:
    del config_data["risk"][key]
    with pytest.raises(ValidationError, match=rf"risk\.{key}\n\s+Field required"):
        AppConfig.model_validate(config_data)


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("exchange", "symbol"),
        ("exchange", "account_label"),
        ("strategy", "name"),
        ("execution", "order_type"),
        ("execution", "reconciliation_interval_minutes"),
        ("logging", "level"),
    ],
)
def test_cfg_01_missing_key_in_other_sections_is_rejected(
    config_data: dict[str, Any], section: str, key: str
) -> None:
    del config_data[section][key]
    with pytest.raises(ValidationError, match=rf"{section}\.{key}\n\s+Field required"):
        AppConfig.model_validate(config_data)


@pytest.mark.parametrize("section", ["exchange", "strategy", "risk", "execution", "logging"])
def test_cfg_01_missing_section_is_rejected(config_data: dict[str, Any], section: str) -> None:
    del config_data[section]
    with pytest.raises(ValidationError, match=section):
        AppConfig.model_validate(config_data)


@pytest.mark.parametrize("section", ["exchange", "strategy", "risk", "execution", "logging"])
def test_cfg_03_unknown_key_is_rejected(config_data: dict[str, Any], section: str) -> None:
    config_data[section]["unexpected"] = 1
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AppConfig.model_validate(config_data)


def test_cfg_03_risk_keys_match_live_yaml(repo_config_dir: Path) -> None:
    live = yaml.safe_load((repo_config_dir / "live.yaml").read_text())
    assert set(RiskConfig.model_fields) == set(live["risk"])


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("exchange", "name", "kraken"),
        ("exchange", "market", "futures"),
        ("exchange", "symbol", "ETH/USDT"),
        ("exchange", "account_label", ""),
        ("strategy", "name", "grid"),
        ("strategy", "timeframe", "15m"),
        ("execution", "order_type", "limit"),
        ("execution", "stop_limit_buffer_pct", 0),
        ("execution", "reconciliation_interval_minutes", 0),
        ("logging", "level", "VERBOSE"),
        ("logging", "log_dir", ""),
    ],
)
def test_out_of_scope_or_invalid_values_are_rejected(
    config_data: dict[str, Any], section: str, key: str, value: Any
) -> None:
    with pytest.raises(ValidationError, match=key):
        AppConfig.model_validate(_with(config_data, section, key, value))


def test_unknown_environment_is_rejected(config_data: dict[str, Any]) -> None:
    config_data["environment"] = "production"
    with pytest.raises(ValidationError, match="environment"):
        AppConfig.model_validate(config_data)


# --- Live requires a chosen strategy --------------------------------------------------


@pytest.mark.parametrize(
    "strategy",
    [
        {"name": None, "timeframe": None},
        {"name": None, "timeframe": "4h"},
        {"name": "mean_reversion", "timeframe": None},
    ],
)
def test_live_requires_strategy_name_and_timeframe(
    config_data: dict[str, Any], strategy: dict[str, Any]
) -> None:
    data = _live(config_data)
    data["strategy"] = strategy
    with pytest.raises(ValidationError, match=r"live requires strategy\.name"):
        AppConfig.model_validate(data)


@pytest.mark.parametrize("environment", ["backtest", "paper"])
def test_null_strategy_is_allowed_outside_live(
    config_data: dict[str, Any], environment: str
) -> None:
    config_data["environment"] = environment
    assert AppConfig.model_validate(config_data).strategy.name is None


# --- Immutability and secrets ---------------------------------------------------------


def test_config_is_immutable(config_data: dict[str, Any]) -> None:
    config = AppConfig.model_validate(config_data)
    with pytest.raises(ValidationError, match="frozen"):
        config.risk.risk_per_trade_pct = Decimal(2)


def test_secrets_are_hidden_from_repr_and_dump(config_data: dict[str, Any]) -> None:
    secrets = SecretsConfig(binance_testnet_api_key=SecretStr("fake-key-for-tests"))
    config = AppConfig.model_validate({**config_data, "secrets": secrets})
    assert config.secrets.binance_testnet_api_key is not None
    assert "fake-key-for-tests" not in repr(config)
    assert "fake-key-for-tests" not in repr(config.secrets)
    assert "secrets" not in config.model_dump()
    assert "fake-key-for-tests" not in config.model_dump_json()
