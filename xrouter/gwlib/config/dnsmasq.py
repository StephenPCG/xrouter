from typing import Annotated, Sequence

from pydantic import BaseModel, Field
from pydantic.networks import IPv4Address, IPv4Network, IPv6Address, IPvAnyAddress


class DHCPRange(BaseModel):
    tag: str | None = None
    start: IPv4Address
    end: IPv4Address
    router: IPv4Address | None = None
    lease: str | None = "24h"
    # per range dns servers if configured
    dns: list[IPvAnyAddress] | None = None

    def model_post_init(self, _context):
        if self.router is None:
            net = IPv4Network(f"{self.start}/24", strict=False)
            self.router = net.network_address + 1

    @property
    def dhcp_range_line(self) -> str:
        tag = f"{self.tag}," if self.tag else ""
        return f"dhcp-range = {tag} {self.start}, {self.end}, {self.lease}"

    @property
    def dhcp_route_line(self) -> str:
        tag = f"{self.tag}," if self.tag else ""
        return f"dhcp-option = {tag} option:router, {self.router}"

    @property
    def dhcp_dns_line(self) -> str:
        if not self.dns:
            return ""
        tag = f"{self.tag}," if self.tag else ""
        return f"dhcp-option = {tag} option:dns-server, {self.dns_list}"

    @property
    def dns_list(self) -> str:
        if not self.dns:
            raise ValueError(f"dhcp range dns is not configured: {self.start}-{self.end}")
        return ",".join([str(s) for s in self.dns])


class DHCPHost(BaseModel):
    mac: str | None = None
    hostname: str | None = None
    ip: IPv4Address

    @property
    def host_line(self) -> str:
        if self.mac and self.hostname:
            return f"dhcp-host = {self.mac}, {self.ip}, {self.hostname}"
        elif self.mac:
            return f"dhcp-host = {self.mac}, {self.ip}"
        elif self.hostname:
            return f"dhcp-host = {self.ip}, {self.hostname}"

        raise ValueError("Invalid DHCP host")


class DHCP(BaseModel):
    # global dns servers
    dns: list[IPv4Address] = []
    dns_v6: list[IPv6Address] = []
    ranges: list[DHCPRange] = []
    domain: str | None = None
    hosts: list[DHCPHost] = []

    @property
    def dns_list(self) -> str:
        return ",".join([str(s) for s in self.dns])

    @property
    def dns_v6_list(self) -> str:
        return ",".join([f"[{s}]" for s in self.dns_v6])


class DNS(BaseModel):
    # servers: ip
    # servers: domain, ip
    servers: list[str | tuple[str, str]] = []
    locals: list[str] = []
    all_servers: bool = True

    # domain, ip
    hosts: list[tuple[str, str] | str] = []
    cnames: list[tuple[str, str] | str] = []
    # 太复杂，直接裸写
    srvhosts: list[str] = []

    @property
    def host_lines(self) -> Sequence[str]:
        lines = []
        for host in self.hosts:
            if isinstance(host, tuple):
                hostname, ip = host
                lines.append(f"host-record={hostname}, {ip}")
            else:
                lines.append(f"host-record={host}")

        return lines

    @property
    def cname_lines(self) -> Sequence[str]:
        lines = []
        for cname in self.cnames:
            if isinstance(cname, tuple):
                domain, cname = cname
                lines.append(f"cname={domain}, {cname}")
            else:
                lines.append(f"cname={cname}")
        return lines

    @property
    def server_lines(self) -> Sequence[str]:
        lines = []
        for server in self.servers:
            if isinstance(server, tuple):
                domain, ip = server
                lines.append(f"server=/{domain}/{ip}")
            else:
                lines.append(f"server={server}")
        return lines


class DnsmasqConfig(BaseModel):
    dns: Annotated[DNS, Field(default_factory=DNS)]
    dhcp: Annotated[DHCP, Field(default_factory=DHCP)]
