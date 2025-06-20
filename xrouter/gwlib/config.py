from pathlib import Path
from typing import Annotated, Literal, cast

import sh
from pydantic import BaseModel, Field, IPvAnyInterface, IPvAnyNetwork, computed_field


class InterfaceCommon(BaseModel):
    name: str
    description: str = ""
    address: IPvAnyInterface | None = None
    addresses: list[IPvAnyInterface] = []
    dhcp: bool = False
    group: int | Literal["wan", "lan", "guest"] | None = None

    @property
    def all_addresses(self):
        if self.address:
            return [self.address, *self.addresses]
        else:
            return [*self.addresses]

    def pre_reload(self):
        """
        大多数 interface 在配置后只需要运行 networkctl reload 即可，少数 interface 可能需要额外的命令。

        `networkctl reload` 由 cli 的 `reload interfaces` 统一执行，这里为在 networkctl reload 之前要执行的命令。
        """
        pass

    def post_reload(self):
        """
        大多数 interface 在配置后只需要运行 networkctl reload 即可，少数 interface 可能需要额外的命令。

        `networkctl reload` 由 cli 的 `reload interfaces` 统一执行，这里为在 networkctl reload 之后要执行的命令。
        """
        pass

    @computed_field  # type: ignore[prop-decorator]
    @property
    def devgroup(self) -> int | None:
        if self.group is None:
            return None
        if isinstance(self.group, int):
            return self.group
        if self.group == "wan":
            return 1
        if self.group == "lan":
            return 2
        if self.group == "guest":
            return 3

        raise Exception(f"Unknown group: {self.group}")


class Lo(InterfaceCommon):
    type: Literal["lo"] = "lo"

    def apply(self):
        from .gwlib import gw

        gw.install_template_file(
            "/etc/systemd/network/01-xrouter-lo.network",
            "interfaces/lo.network",
            dict(iface=self),
        )


class VlanBridgePort(BaseModel):
    name: str
    pvid: int | None = None
    description: str = ""
    allowed_vlans: list[str | int] = Field(default=["1-4094"])


class VlanBridgeInterface(InterfaceCommon):
    vlan: int


class VlanBridge(InterfaceCommon):
    type: Literal["vlan-bridge"] = "vlan-bridge"
    allowed_vlans: list[str | int] = Field(default=["1-4094"])
    ports: list[VlanBridgePort] = []
    vlan_interfaces: list[VlanBridgeInterface] = []

    def apply(self):
        from .gwlib import gw

        gw.install_template_file(
            f"/etc/systemd/network/01-xrouter-{self.name}.netdev",
            "interfaces/vlan-bridge/vlan-bridge.netdev",
            dict(iface=self),
        )
        gw.install_template_file(
            f"/etc/systemd/network/01-xrouter-{self.name}.network",
            "interfaces/vlan-bridge/vlan-bridge.network",
            dict(iface=self),
        )
        for port in self.ports:
            gw.install_template_file(
                f"/etc/systemd/network/02-xrouter-{port.name}.network",
                "interfaces/vlan-bridge/vlan-bridge-port.network",
                dict(iface=self, port=port),
            )
        for svi in self.vlan_interfaces:
            gw.install_template_file(
                f"/etc/systemd/network/02-xrouter-{svi.name}.netdev",
                "interfaces/vlan-bridge/vlan-bridge-svi.netdev",
                dict(iface=self, svi=svi),
            )
            gw.install_template_file(
                f"/etc/systemd/network/02-xrouter-{svi.name}.network",
                "interfaces/vlan-bridge/vlan-bridge-svi.network",
                dict(iface=self, svi=svi),
            )


class PPPoE(InterfaceCommon):
    type: Literal["pppoe"] = "pppoe"
    ethport: str = "eth0"
    username: str = "USERNAME"
    password: str = "PASSWORD"

    def apply(self):
        from .gwlib import gw

        gw.install_template_file(
            "/etc/systemd/system/pppd@.service",
            "interfaces/pppoe/pppd@.service",
            dict(),
        )

        gw.install_template_file(
            f"/etc/ppp/peers/{self.name}",
            "interfaces/pppoe/peer",
            dict(iface=self),
        )

        gw.install_template_file(
            f"/etc/ppp/ip-up.d/10-reconfigure-{self.name}",
            "interfaces/pppoe/ip-up",
            dict(iface=self),
            mode="755",
        )

        gw.install_template_file(
            f"/etc/systemd/network/02-{self.name}.network",
            "interfaces/pppoe/iface.network",
            dict(iface=self),
        )

    def pre_reload(self):
        from .gwlib import gw

        gw.run_command(sh.systemctl.bake("daemon-reload"))
        gw.run_command(sh.systemctl.bake("enable", f"pppd@{self.name}.service"))
        gw.run_command(sh.systemctl.bake("start", "--no-block", f"pppd@{self.name}.service"))


class WireguardPeer(BaseModel):
    name: str
    allowed_ips: list[IPvAnyNetwork] = []
    public_key: str
    endpoint: str | None = None
    persistent_keepalive: int | None = None

    @computed_field
    def allowed_ips_str(self) -> str:
        return ",".join([ip.with_prefixlen for ip in self.allowed_ips])


class Wireguard(InterfaceCommon):
    type: Literal["wireguard"] = "wireguard"
    private_key: str
    listen_port: str
    peers: list[WireguardPeer] = []

    def apply(self):
        from .gwlib import gw

        gw.install_template_file(
            f"/etc/systemd/network/02-xrouter-{self.name}.netdev",
            "interfaces/wireguard/iface.netdev",
            dict(iface=self),
        )
        gw.install_template_file(
            f"/etc/systemd/network/02-xrouter-{self.name}.network",
            "interfaces/wireguard/iface.network",
            dict(iface=self),
        )


Interface = Annotated[
    Lo | VlanBridge | PPPoE | Wireguard,
    Field(discriminator="type"),
]


class Route(BaseModel):
    # gateway: {name: nexthop}
    gateways: dict[str, str] = {}
    # table: [number, entries]
    # entries: (cidr|zone, gateway_name)
    tables: dict[int, list[tuple[str, str]]] = {}
    # rules: rule
    rules: list[str] = []

    def apply(self, bin_file: Path):
        from xrouter.gwlib import gw

        ip_batch_lines = []

        for table, entries in self.tables.items():
            ip_batch_lines.extend(self.create_table_batch_lines(table, entries))

        # flush rules
        ip_batch_lines.extend(
            [
                "rule flush",
                "rule add from all lookup main pref 32766",
                "rule add from all lookup local pref 32767",
            ]
        )

        for rule in self.rules:
            ip_batch_lines.append(f"rule add {rule}")

        content_lines = [
            "#!/bin/bash",
            "set -e",
            "sudo ip -batch - <<EOF",
            *ip_batch_lines,
            "EOF",
            "",
            # delete default route in table main if exists
            "if ip route show table main | grep -q '^default'; then",
            "    sudo ip route del default table main",
            "fi",
            "",
            "echo Done!",
            "",
        ]

        content = "\n".join(content_lines)

        gw.install_text_file(bin_file, content, "755", show_diff=False)
        gw.print(f"Route file updated: {bin_file}")

    def create_table_batch_lines(self, table: int, entries: list[tuple[str, str]]):
        """
        创建表

        返回 `ip -batch` 的输入内容
        """
        from xrouter.gwlib import gw

        lines = []
        lines.append(f"route flush table {table}")

        for target, gateway_name in entries:
            type, val = self.parse_route_target(target)

            gateway = self.gateways.get(gateway_name)
            if not gateway:
                gw.logger.error(f"Bad gateway name in table {table}: {gateway_name}, skipped")
                continue

            if type == "cidr":
                lines.append(f"route replace table {table} {val} {gateway}")
                continue

            elif type == "zone":
                zone_file = cast(Path, val)
                for zone_line in self.read_zone_lines(zone_file):
                    lines.append(f"route replace table {table} {zone_line} {gateway}")
                continue

            elif type == "error":
                gw.logger.error(f"Bad route target in table {table}: {target}, skipped")
                continue

        return lines

    def parse_route_target(self, target: str):
        """
        return:
        * ('cidr', '{cidr}')
        * ('zone', '{zone_file}')
        * ('error', None)
        """
        from xrouter.gwlib import gw

        try:
            ipv = IPvAnyNetwork(target)  # type: ignore[operator]
            return ("cidr", ipv.with_prefixlen)
        except ValueError:
            pass

        zone_file = gw.zones_root / f"{target}.txt"
        if zone_file.exists():
            return ("zone", zone_file)

        return ("error", None)

    def read_zone_lines(self, zone_file: Path):
        text = zone_file.read_text()
        for line in text.splitlines():
            line = line.split("#", 1)[0]
            line = line.split(" ", 1)[0]
            line = line.strip()

            if not line:
                continue

            try:
                ipv = IPvAnyNetwork(line)  # type: ignore[operator]
                yield ipv.with_prefixlen
            except ValueError:
                pass


class Firewall(BaseModel):
    def apply(self):
        from .gwlib import gw

        setup_file = gw.bin_root / "setup-firewall.nft"
        gw.print(f"setup file: {setup_file}")
        gw.install_template_file(
            setup_file,
            "firewall.nft",
            dict(),
            mode="755",
        )

        custom_file = gw.config_root / "firewall.nft"
        gw.print(f"custom file: {custom_file}")
        if custom_file.exists():
            gw.print(f"Custom firewall file exists, skip updating: {custom_file}")
            return

        gw.install_template_file(
            custom_file,
            "firewall-custom.nft",
            dict(),
        )


class XrouterConfig(BaseModel):
    devgroups: dict[str, int] = {}
    interfaces: list[Interface]
    route: Route
    firewall: Firewall
