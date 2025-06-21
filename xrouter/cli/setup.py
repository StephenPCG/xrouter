from typing import Annotated

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

    gw.install_template_file(
        "/etc/systemd/networkd.conf",
        "networkd.conf",
        {},
    )
    gw.run_command(sh.systemctl.bake("restart", "systemd-networkd"))

    gw.install_template_file(
        "/etc/systemd/system/startup-xrouter.service",
        "startup-xrouter.service",
        {},
    )
    gw.run_command(sh.systemctl.bake("enable", "startup-xrouter.service"))

    gw.run_command(sh.mkdir.bake("-p", gw.config_root, gw.dnsmasq_config_root, gw.zones_root))

    gw.run_command(sh.gw.bake("fix-perms"), stream=True)


@app.command("avahi")
def setup_avahi():
    from xrouter.gwlib import gw

    gw.run_command(sh.sed.bake("-i", "s/#enable-reflector=no/enable-reflector=yes/g", "/etc/avahi/avahi-daemon.conf"))
    gw.run_command(sh.systemctl.bake("restart", "avahi-daemon"))


@app.command("ifaces")
def setup_ifaces():
    from xrouter.gwlib import gw

    gw.print("[setup interfaces]")

    # ensure devgroups are configured
    gw.config.apply_devgroups()

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

    gw.run_command(Command(gw.bin_root / "setup-route.sh"))


@app.command("firewall")
def setup_firewall():
    """
    生成 nft 文件，输出到 /etc/nftables.conf
    """
    from sh import Command

    from xrouter.gwlib import gw

    gw.print("[setup firewall]")

    # ensure devgroups are configured
    gw.config.apply_devgroups()

    gw.config.firewall.apply()

    gw.run_command(Command(gw.bin_root / "setup-firewall.nft"))


@app.command("network")
def setup_net():
    setup_ifaces()
    setup_firewall()
    setup_route()


@app.command("containers")
def setup_pods(names: Annotated[list[str] | None, typer.Argument()] = None):
    from xrouter.gwlib import gw

    gw.print("[setup containers]")

    if not names:
        names = gw.config.containers.container_names

    for name in names:
        container = gw.config.containers.containers[name]

        container.create_mount_sources()
        gw.install_template_file(
            f"/etc/systemd/system/container-{container.name}.service",
            "container/podman-container.service",
            dict(container=container),
        )
        gw.run_command(sh.systemctl.bake("enable", f"container-{name}.service"))
        gw.run_command(sh.systemctl.bake("start", f"container-{name}.service"))


@app.command("dnsmasq")
def setup_dnsmasq():
    from xrouter.gwlib import gw

    gw.print("[setup dnsmasq]")

    gw.run_command(sh.mkdir.bake("-p", "/opt/xrouter/configs/dnsmasq"))
    gw.run_command(sh.mkdir.bake("-p", "/opt/xrouter/configs/dnsmasq/manual"))

    gw.install_template_file(
        "/etc/dnsmasq.conf",
        "dnsmasq/dnsmasq.conf",
        {},
    )

    gw.install_template_file(
        "/opt/xrouter/configs/dnsmasq/dns.conf",
        "dnsmasq/dns.conf",
        {
            "conf": gw.config.dnsmasq,
        },
    )

    gw.install_template_file(
        "/opt/xrouter/configs/dnsmasq/dhcp.conf",
        "dnsmasq/dhcp.conf",
        {
            "conf": gw.config.dnsmasq,
        },
    )

    gw.run_command(sh.mkdir.bake("-p", "/var/log/dnsmasq"))
    gw.install_template_file(
        "/etc/logrotate.d/dnsmasq",
        "dnsmasq/logrotate",
        {},
    )

    gw.run_command(sh.systemctl.bake("restart", "dnsmasq"))
