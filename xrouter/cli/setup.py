import sh
import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Setup xrouter configuration",
)


@app.command("system")
def setup_system():
    from xrouter.gwlib import gw

    gw.print("[setup system]")

    gw.install_template_file(
        "/etc/sysctl.d/99-xrouter.conf",
        "99-xrouter.sysctl.conf",
        {},
    )

    gw.run_command(sh.sysctl.bake("-p", "--system"))


@app.command("interfaces")
def setup_interfaces():
    from xrouter.gwlib import gw

    gw.print("[setup interfaces]")

    for iface in gw.config.interfaces:
        iface.apply()

    for iface in gw.config.interfaces:
        iface.pre_reload()

    gw.run_command(sh.networkctl.bake("reload"))

    for iface in gw.config.interfaces:
        iface.post_reload()
