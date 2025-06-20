from typing import Annotated

import typer

from .reload import app as app_reload
from .setup import app as app_setup

app = typer.Typer(no_args_is_help=True)


@app.callback()
def global_options(
    verbose: Annotated[bool | None, typer.Option("--verbose/--silent")] = None,
):
    from xrouter.gwlib import gw
    from xrouter.utils.run_as_root import run_as_root

    run_as_root()

    if verbose is not None:
        gw.setup(verbose=verbose)


app.add_typer(app_setup, name="setup")
app.add_typer(app_reload, name="reload")


@app.command("shell")
def start_shell():
    import IPython

    from xrouter.gwlib import gw

    gw.setup(verbose=True)

    IPython.start_ipython(argv=[], user_ns={"gw": gw})
