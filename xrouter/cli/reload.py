from typing import Annotated

import sh
import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Reload xrouter",
)


@app.command("ifaces")
def reload_ifaces():
    from xrouter.gwlib import gw

    gw.run_command(sh.networkctl.bake("reload"))


@app.command("route")
def reload_route():
    from xrouter.gwlib import gw

    gw.run_command(sh.Command(gw.bin_root / "setup-route.sh"))


@app.command("firewall")
def reload_firewall():
    from xrouter.gwlib import gw

    gw.run_command(sh.Command(gw.bin_root / "setup-firewall.nft"))


@app.command("network")
def reload_network():
    reload_ifaces()
    reload_route()
    reload_firewall()


@app.command("containers")
def reload_containers(names: Annotated[list[str] | None, typer.Argument()] = None):
    from xrouter.gwlib import gw

    if not names:
        names = gw.config.containers.container_names

    for name in names:
        gw.run_command(sh.systemctl.bake("restart", f"container-{name}.service"))


@app.command("dnsmasq")
def reload_dnsmasq():
    from xrouter.gwlib import gw

    gw.run_command(sh.systemctl.bake("restart", "dnsmasq"))
