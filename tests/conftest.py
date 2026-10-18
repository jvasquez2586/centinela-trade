"""Root pytest configuration.

Tests marked ``@pytest.mark.network`` need network access or credentials. They are
skipped unless ``--run-network`` is passed explicitly, and only a human runs them
(AGENTS.md, prohibited item 7).
"""

import pytest

NETWORK_MARKER = "network"


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
