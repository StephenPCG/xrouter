from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, IPvAnyInterface

from xrouter.utils.jinja import render


class InterfaceCommon(BaseModel):
    name: str
    description: str = ""
    address: IPvAnyInterface | None = None
    addresses: list[IPvAnyInterface] = []

    @property
    def all_addresses(self):
        if self.address:
            return [self.address, *self.addresses]
        else:
            return [*self.addresses]


class Lo(InterfaceCommon):
    type: Literal["lo"] = "lo"

    def get_systemd_network_files(self):
        return [
            # lo only need .network file
            (
                "/etc/systemd/network/01-xrouter-lo.network",
                render("systemd/network/lo.network", dict(iface=self)),
            ),
        ]


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

    def get_systemd_network_files(self):
        files = [
            (
                f"/etc/systemd/network/01-xrouter-{self.name}.netdev",
                render("systemd/network/vlan-bridge.netdev", dict(iface=self)),
            ),
            (
                f"/etc/systemd/network/01-xrouter-{self.name}.network",
                render("systemd/network/vlan-bridge.network", dict(iface=self)),
            ),
        ]
        for port in self.ports:
            files.append(
                (
                    f"/etc/systemd/network/02-xrouter-{port.name}.network",
                    render("systemd/network/vlan-bridge-port.network", dict(iface=self, port=port)),
                ),
            )
        for svi in self.vlan_interfaces:
            files.append(
                (
                    f"/etc/systemd/network/02-xrouter-{svi.name}.netdev",
                    render("systemd/network/vlan-bridge-svi.netdev", dict(iface=self, svi=svi)),
                ),
            )
            files.append(
                (
                    f"/etc/systemd/network/02-xrouter-{svi.name}.network",
                    render("systemd/network/vlan-bridge-svi.network", dict(iface=self, svi=svi)),
                ),
            )
        return files


Interface = Annotated[
    Lo | VlanBridge,
    Field(discriminator="type"),
]


class XrouterConfig(BaseModel):
    interfaces: list[Interface]


def load_xrouter_config(config_path: Path):
    with config_path.open(encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
        return XrouterConfig.model_validate(data)
