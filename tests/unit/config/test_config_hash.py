"""Configuration fingerprint (spec CFG-04)."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from centinela_trade.config import config_hash, load_config

WriteYaml = Callable[[Path, str, dict[str, Any]], None]

FAKE_SECRETS = {
    "BINANCE_TESTNET_API_KEY": "fake-testnet-key",  # pragma: allowlist secret
    "BINANCE_TESTNET_API_SECRET": "fake-testnet-secret",  # pragma: allowlist secret
    "TELEGRAM_BOT_TOKEN": "fake-token",  # pragma: allowlist secret
}


def _hash(env: str, config_dir: Path, environ: dict[str, str] | None = None) -> str:
    return config_hash(load_config(env, config_dir=config_dir, environ=environ or {}))


def _reverse_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _reverse_keys(value[key]) for key in reversed(list(value))}
    return value


def test_cfg_04_hash_is_sha256_hex_and_deterministic(repo_config_dir: Path) -> None:
    first = _hash("backtest", repo_config_dir)
    assert len(first) == 64
    assert int(first, 16) >= 0
    assert first == _hash("backtest", repo_config_dir)


def test_cfg_04_hash_ignores_yaml_key_order(
    repo_config_dir: Path, config_dir: Path, write_yaml: WriteYaml
) -> None:
    base = yaml.safe_load((config_dir / "base.yaml").read_text())
    reordered = _reverse_keys(base)
    assert list(reordered) != list(base)
    write_yaml(config_dir, "base.yaml", reordered)

    assert _hash("backtest", config_dir) == _hash("backtest", repo_config_dir)


def test_cfg_04_hash_ignores_number_formatting(
    repo_config_dir: Path, config_dir: Path, write_yaml: WriteYaml
) -> None:
    base = yaml.safe_load((config_dir / "base.yaml").read_text())
    base["risk"]["risk_per_trade_pct"] = 1  # 1.0 in the repo file
    base["risk"]["max_capital_usd"] = "100.00"  # 100 in the repo file
    write_yaml(config_dir, "base.yaml", base)

    assert _hash("backtest", config_dir) == _hash("backtest", repo_config_dir)


def test_cfg_04_hash_changes_when_a_value_changes(
    repo_config_dir: Path, config_dir: Path, write_yaml: WriteYaml
) -> None:
    write_yaml(
        config_dir, "backtest.yaml", {"environment": "backtest", "risk": {"max_drawdown_pct": 14}}
    )
    assert _hash("backtest", config_dir) != _hash("backtest", repo_config_dir)


def test_cfg_04_hash_depends_on_environment(repo_config_dir: Path) -> None:
    assert _hash("backtest", repo_config_dir) != _hash("paper", repo_config_dir)


def test_cfg_04_hash_does_not_include_secrets(repo_config_dir: Path) -> None:
    without = _hash("paper", repo_config_dir)
    with_secrets = _hash("paper", repo_config_dir, FAKE_SECRETS)
    other_secrets = _hash("paper", repo_config_dir, {"TELEGRAM_BOT_TOKEN": "another-fake"})
    assert without == with_secrets == other_secrets
