from typing import Annotated

import typer

from .apply import app as app_apply
from .reload import app as app_reload
from .setup import app as app_setup

app = typer.Typer(no_args_is_help=True)


@app.callback()
def global_options(
    verbose: Annotated[bool | None, typer.Option("--verbose/--silent")] = None,
    system_root: Annotated[str | None, typer.Option("--system-root")] = None,
):
    from xrouter.utils import run_as_root

    from .base import global_options

    run_as_root()

    if verbose is not None:
        global_options.verbose = verbose
    if system_root is not None:
        global_options.system_root = system_root


app.add_typer(app_apply, name="apply")
app.add_typer(app_reload, name="reload")
app.add_typer(app_setup, name="setup")


@app.command("shell")
def start_shell():
    print("Starting shell...")
