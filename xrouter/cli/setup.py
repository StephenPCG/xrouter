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


@app.command("ifaces")
def setup_ifaces():
    from xrouter.gwlib import gw

    gw.print("[setup interfaces]")

    for iface in gw.config.interfaces:
        iface.apply()

    for iface in gw.config.interfaces:
        iface.pre_reload()

    gw.run_command(sh.networkctl.bake("reload"))

    for iface in gw.config.interfaces:
        iface.post_reload()


@app.command("route")
def setup_route():
    from sh import Command

    from xrouter.gwlib import gw

    gw.print("[setup route]")

    gw.config.route.apply(gw.bin_root / "setup-route.sh")

    cmd = Command(gw.bin_root / "setup-route.sh")
    gw.run_command(cmd)


@app.command("firewall")
def setup_firewall():
    """
    生成 nft 文件，输出到 /etc/nftables.conf
    """
    pass
