"""Command line entry point, exposed as the ``centinela`` console script (spec ARQ-01b).

Only a skeleton for now; the commands are implemented in task T13.
"""

import typer

from centinela_trade import __version__

app = typer.Typer(name="centinela", no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """Centinela Trade: BTC/USDT spot trading bot."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(__version__)
