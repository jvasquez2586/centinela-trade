"""Root pytest configuration.

Tests marked ``@pytest.mark.network`` need network access or credentials. They are
skipped unless ``--run-network`` is passed explicitly, and only a human runs them
(AGENTS.md, prohibited item 7).

It also holds the fixtures shared by the configuration tests (spec CFG-01 to CFG-04).
"""

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

NETWORK_MARKER = "network"

REPO_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="Run tests marked 'network' (network access or credentials; humans only).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{NETWORK_MARKER}: requires network access or credentials; "
        "skipped unless --run-network is given (run by a human only)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-network"):
        return
    skip_network = pytest.mark.skip(
        reason="requires network or credentials; run by a human with --run-network"
    )
    for item in items:
        if NETWORK_MARKER in item.keywords:
            item.add_marker(skip_network)


# --- Configuration fixtures ---------------------------------------------------------


@pytest.fixture
def repo_config_dir() -> Path:
    return REPO_CONFIG_DIR


@pytest.fixture
def config_data() -> dict[str, Any]:
    """A valid ``AppConfig`` payload: the repo's ``base.yaml`` as a backtest config."""
    data: dict[str, Any] = yaml.safe_load((REPO_CONFIG_DIR / "base.yaml").read_text())
    data["environment"] = "backtest"
    return data


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """A temporary copy of the repo's config directory, safe to modify."""
    target = tmp_path / "config"
    shutil.copytree(REPO_CONFIG_DIR, target)
    return target


@pytest.fixture
def write_yaml() -> Callable[[Path, str, dict[str, Any]], None]:
    """Write ``data`` as ``<directory>/<name>``, keeping the given key order."""

    def _write(directory: Path, name: str, data: dict[str, Any]) -> None:
        (directory / name).write_text(yaml.safe_dump(data, sort_keys=False))

    return _write
