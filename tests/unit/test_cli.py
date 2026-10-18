"""Smoke tests for the ``centinela`` console entry point (spec ARQ-01b)."""

from typer.testing import CliRunner

from centinela_trade import __version__
from centinela_trade.cli import app

runner = CliRunner()


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "Usage" in result.output
