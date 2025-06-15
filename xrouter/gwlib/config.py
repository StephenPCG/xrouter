from typing import Annotated, Literal

import sh
from pydantic import BaseModel, Field, IPvAnyInterface


class InterfaceCommon(BaseModel):
    name: str
    description: str = ""
    address: IPvAnyInterface | None = None
    addresses: list[IPvAnyInterface] = []
    dhcp: bool = False

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


Interface = Annotated[
    Lo | VlanBridge | PPPoE,
    Field(discriminator="type"),
]


class XrouterConfig(BaseModel):
    interfaces: list[Interface]
