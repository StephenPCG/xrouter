from typing import Annotated

import sh
import typer
from rich import print

from .fetch import app as app_fetch
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
app.add_typer(app_fetch, name="fetch")


@app.command("shell")
def start_shell():
    import IPython

    from xrouter.gwlib import gw

    gw.setup(verbose=True)

    IPython.start_ipython(argv=[], user_ns={"gw": gw})


@app.command("print-config")
def print_config():
    from xrouter.gwlib import gw

    print(gw.config)


@app.command("fix-perms")
def fix_perms():
    import os

    from xrouter.gwlib import gw

    sudo_user = os.environ.get("SUDO_USER")

    if not sudo_user:
        print("Not running as sudo, can not fix perms")
        raise typer.Exit(1)

    gw.run_command(sh.chown.bake("-R", f"{sudo_user}", gw.config_root))


@app.command("system-startup")
def system_startup_script():
    from xrouter.gwlib import gw

    from .setup import setup_firewall, setup_route

    gw.print("==== invoked by system startup script ====")

    setup_route()
    setup_firewall()


@app.command("dispatcher-routable-hook")
def dispatcher_routable_hook():
    import os

    from xrouter.gwlib import gw

    from .setup import setup_firewall, setup_route

    gw.print("==== invoked by networkd-dispatcher routable hook ====")
    gw.print("==== BEGIN INFO ====")
    for env in ["IFACE", "STATE", "ADDR", "IP_ADDRS", "IP6_ADDRS", "AdministrativeState", "OperationalState"]:
        gw.print(f"{env}: {os.environ.get(env)}")
    gw.print("==== END INFO ====")

    iface_name = os.environ.get("IFACE")
    iface = gw.config.all_interfaces.get(iface_name)
    if iface:
        gw.print("Calling iface up hook...")
        iface.up_hook()

    setup_route()
    setup_firewall()
