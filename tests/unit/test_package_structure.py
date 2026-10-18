"""Placeholder tests for the package skeleton (task T01)."""

import importlib

import pytest

import centinela_trade

SUBPACKAGES = [
    "core",
    "config",
    "data",
    "strategies",
    "risk",
    "execution",
    "connectors",
    "backtesting",
    "monitoring",
    "logging",
    "journal",
]


def test_root_package_exposes_version() -> None:
    assert centinela_trade.__version__ == "0.1.0"


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_is_importable_and_documented(name: str) -> None:
    module = importlib.import_module(f"centinela_trade.{name}")
    assert module.__doc__
    assert module.__doc__.strip()
