from typing import Annotated

import typer
from rich import print

app = typer.Typer(
    no_args_is_help=True,
    help="Reload xrouter",
)


@app.command("ifaces")
def reload_ifaces(
    ifaces: Annotated[list[str] | None, typer.Argument()] = None,
):
    if ifaces:
        print("reload ifaces:", ifaces)

    else:
        print("reload all ifaces")
