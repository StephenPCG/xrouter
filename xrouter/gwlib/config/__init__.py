from typing import Annotated

from pydantic import BaseModel, Field

from .container import ContainerConfig
from .dnsmasq import DnsmasqConfig
from .firewall import Firewall
from .interface import Interface, VlanBridge
from .route import Route


class XrouterConfig(BaseModel):
    devgroups: dict[str, int] = {}
    interfaces: list[Interface] = []
    route: Annotated[Route, Field(default_factory=Route)]
    firewall: Annotated[Firewall, Field(default_factory=Firewall)]
    dnsmasq: Annotated[DnsmasqConfig, Field(default_factory=DnsmasqConfig)]
    containers: Annotated[ContainerConfig, Field(default_factory=ContainerConfig)]

    def model_post_init(self, _context):
        for iface in self.interfaces:
            if isinstance(iface, VlanBridge):
                for svi in iface.vlan_interfaces:
                    if not svi.devgroup:
                        continue
                    if svi.devgroup not in self.devgroups:
                        raise ValueError(f"Invalid devgroup in iface: {iface.name}, {iface.devgroup}")
                    svi.devgroup_number = self.devgroups[svi.devgroup]

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
