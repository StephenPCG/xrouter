from typing import Annotated, Literal

import sh
from pydantic import BaseModel, Field, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, PrivateAttr


class InterfaceCommon(BaseModel):
    name: str
    description: str = ""
    address: IPvAnyInterface | None = None
    addresses: list[IPvAnyInterface] = []
    dhcp: bool = False
    devgroup: str | None = None

    ipv6: bool = False
    ipv6_subnet_id: int | None = None

    # 该字段在 XrouterConfig.modeL_post_init 中自动设置
    devgroup_number: Annotated[int | None, PrivateAttr()] = None

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

    def up_hook(self):
        """
        当 interface up 时被调用。

        目前只有一个入口，在 networkd-dispatcher 的 routable hook 中，会检查接口名字，并执行相应的操作。
        """
        pass


class Lo(InterfaceCommon):
    type: Literal["lo"] = "lo"

    def apply(self):
        from ..gwlib import gw

        gw.install_template_file(
            "/etc/systemd/network/01-lo.network",
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
        from ..gwlib import gw

        gw.install_template_file(
            f"/etc/systemd/network/01-{self.name}.netdev",
            "interfaces/vlan-bridge/vlan-bridge.netdev",
            dict(iface=self),
        )
        gw.install_template_file(
            f"/etc/systemd/network/01-{self.name}.network",
            "interfaces/vlan-bridge/vlan-bridge.network",
            dict(iface=self),
        )
        for port in self.ports:
            gw.install_template_file(
                f"/etc/systemd/network/02-{port.name}.network",
                "interfaces/vlan-bridge/vlan-bridge-port.network",
                dict(iface=self, port=port),
            )
        for svi in self.vlan_interfaces:
            gw.install_template_file(
                f"/etc/systemd/network/02-{svi.name}.netdev",
                "interfaces/vlan-bridge/vlan-bridge-svi.netdev",
                dict(iface=self, svi=svi),
            )
            gw.install_template_file(
                f"/etc/systemd/network/02-{svi.name}.network",
                "interfaces/vlan-bridge/vlan-bridge-svi.network",
                dict(iface=self, svi=svi),
            )


class PPPoE(InterfaceCommon):
    type: Literal["pppoe"] = "pppoe"
    ethport: str = "eth0"
    username: str = "USERNAME"
    password: str = "PASSWORD"

    enable_pd: bool = False

    def apply(self):
        from ..gwlib import gw

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
        from ..gwlib import gw

        gw.run_command(sh.systemctl.bake("daemon-reload"))
        gw.run_command(sh.systemctl.bake("enable", f"pppd@{self.name}.service"))
        gw.run_command(sh.systemctl.bake("start", "--no-block", f"pppd@{self.name}.service"))


class WireguardPeer(BaseModel):
    name: str
    allowed_ips: list[IPvAnyNetwork] = []
    public_key: str
    endpoint: str | None = None
    persistent_keepalive: int | None = None

    @property
    def allowed_ips_str(self) -> str:
        return ",".join([ip.with_prefixlen for ip in self.allowed_ips])


class Wireguard(InterfaceCommon):
    type: Literal["wireguard"] = "wireguard"
    private_key: str
    listen_port: str
    peers: list[WireguardPeer] = []

    wgsd_client_dns: str | None = None
    wgsd_client_zone: str | None = None

    @property
    def wg_config_file(self):
        from xrouter.gwlib import gw

        return f"{gw.wireguard_config_root}/{self.name}.conf"

    def apply(self):
        from ..gwlib import gw

        gw.install_template_file(
            f"/etc/systemd/network/02-{self.name}.netdev",
            "interfaces/wireguard/iface.netdev",
            dict(iface=self),
        )
        gw.install_template_file(
            f"/etc/systemd/network/02-{self.name}.network",
            "interfaces/wireguard/iface.network",
            dict(iface=self),
        )
        gw.install_template_file(
            self.wg_config_file,
            "interfaces/wireguard/wg.conf",
            dict(iface=self),
        )

        if self.wgsd_client_dns and self.wgsd_client_zone:
            gw.install_template_file(
                f"/etc/systemd/system/wgsd-client-{self.name}.service",
                "interfaces/wireguard/wgsd-client@service",
                dict(iface=self),
            )
            gw.install_template_file(
                f"/etc/systemd/system/wgsd-client-{self.name}.timer",
                "interfaces/wireguard/wgsd-client@timer",
                dict(iface=self),
            )
            # gw.run_command(sh.systemctl.bake("enable", f"wgsd-client-{self.name}.service"))
            gw.run_command(sh.systemctl.bake("enable", f"wgsd-client-{self.name}.timer"))

    def up_hook(self):
        from xrouter.gwlib import gw

        gw.print("sync wireguard conf ...")
        gw.run_command(sh.wg.bake("syncconf", self.name, self.wg_config_file))


class PodmanBridgeIpamRange(BaseModel):
    subnet: IPvAnyNetwork
    # default to .1
    gateway: IPvAnyAddress | None = None
    # default to .2
    rangeStart: IPvAnyAddress | None = None
    # default to .254 for ipv4, .255 for ipv6
    rangeEnd: IPvAnyAddress | None = None


class PodmanBridge(InterfaceCommon):
    type: Literal["podman-bridge"] = "podman-bridge"
    ranges: list[PodmanBridgeIpamRange] = []

    def get_ipam_ranges(self):
        ranges = []

        for range in self.ranges:
            ranges.append([range.model_dump(mode="json", exclude_none=True)])

        return ranges

    def apply(self):
        import json

        from xrouter.gwlib import gw

        bridge_plugin = dict(
            type="bridge",
            bridge=self.name,
            isGateway=True,
            isDefaultGateway=True,
            ipam=dict(
                type="host-local",
                ranges=self.get_ipam_ranges(),
            ),
        )

        conflist = dict(
            cniVersion="0.4.0",
            name=self.name,
            plugins=[
                bridge_plugin,
            ],
        )

        content = json.dumps(conflist, indent=2, ensure_ascii=False)
        gw.install_text_file(
            f"/etc/cni/net.d/10-{self.name}.conflist",
            content,
        )

        gw.install_template_file(
            f"/etc/systemd/network/02-{self.name}.netdev",
            "interfaces/podman-bridge/iface.netdev",
            dict(iface=self),
        )
        gw.install_template_file(
            f"/etc/systemd/network/02-{self.name}.network",
            "interfaces/podman-bridge/iface.network",
            dict(iface=self),
        )


Interface = Annotated[
    Lo | VlanBridge | PPPoE | Wireguard | PodmanBridge,
    Field(discriminator="type"),
]
