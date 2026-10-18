"""The ``network`` marker skips tests by default (AGENTS.md, prohibited item 7)."""

from pathlib import Path

import pytest

ROOT_CONFTEST = Path(__file__).parent / "conftest.py"

NETWORK_TEST = """
import pytest

@pytest.mark.network
def test_needs_network():
    pass

def test_offline():
    pass
"""


@pytest.fixture
def network_suite(pytester: pytest.Pytester) -> pytest.Pytester:
    pytester.makeconftest(ROOT_CONFTEST.read_text())
    pytester.makepyfile(NETWORK_TEST)
    return pytester


def test_network_tests_are_skipped_by_default(network_suite: pytest.Pytester) -> None:
    result = network_suite.runpytest("--strict-markers")
    result.assert_outcomes(passed=1, skipped=1)


def test_network_tests_run_only_with_explicit_flag(network_suite: pytest.Pytester) -> None:
    result = network_suite.runpytest("--strict-markers", "--run-network")
    result.assert_outcomes(passed=2)


def test_marker_selection_alone_does_not_enable_network_tests(
    network_suite: pytest.Pytester,
) -> None:
    result = network_suite.runpytest("--strict-markers", "-m", "network")
    result.assert_outcomes(skipped=1, deselected=1)
