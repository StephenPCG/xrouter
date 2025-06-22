from typing import Annotated

from pydantic import BaseModel, Field, PrivateAttr

from .container import ContainerConfig
from .dnsmasq import DnsmasqConfig
from .firewall import Firewall
from .interface import Interface, InterfaceCommon, VlanBridge
from .route import Route


class XrouterConfig(BaseModel):
    devgroups: dict[str, int] = {}
    interfaces: list[Interface] = []
    route: Annotated[Route, Field(default_factory=Route)]
    firewall: Annotated[Firewall, Field(default_factory=Firewall)]
    dnsmasq: Annotated[DnsmasqConfig, Field(default_factory=DnsmasqConfig)]
    containers: Annotated[ContainerConfig, Field(default_factory=ContainerConfig)]

    # 所有接口，包括 VlanBridgeInterface，在 model_post_init 中设置。
    all_interfaces: Annotated[dict[str, InterfaceCommon], PrivateAttr()] = {}

    def model_post_init(self, _context):
        for iface in self.interfaces:
            self.all_interfaces[iface.name] = iface

            if isinstance(iface, VlanBridge):
                for svi in iface.vlan_interfaces:
                    self.all_interfaces[svi.name] = svi

        for iface in self.all_interfaces.values():  # type: ignore[assignment]
            if not iface.devgroup:
                continue
            if iface.devgroup not in self.devgroups:
                raise ValueError(f"Invalid devgroup in iface: {iface.name}, {iface.devgroup}")
            iface.devgroup_number = self.devgroups[iface.devgroup]

    def apply_devgroups(self):
        from ..gwlib import gw

        gw.install_template_file(
            "/etc/iproute2/group",
            "iproute2-group",
            dict(devgroups=self.devgroups),
        )
