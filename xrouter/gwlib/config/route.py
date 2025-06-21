from pathlib import Path
from typing import cast

from pydantic import BaseModel, IPvAnyNetwork


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

        # flush rules
        ip_batch_lines.extend(
            [
                "rule flush",
                "rule add from all lookup main pref 1",
                "rule add from all lookup main pref 32766",
                "rule add from all lookup local pref 32767",
            ]
        )
        for rule in self.rules:
            ip_batch_lines.append(f"rule add {rule}")

        # flush tables
        for table, entries in self.tables.items():
            ip_batch_lines.extend(self.create_table_batch_lines(table, entries))

        content_lines = [
            "#!/bin/bash",
            "#set -e",
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

        zone_file = gw.zones_root / f"manual-{target}.txt"
        if zone_file.exists():
            return ("zone", zone_file)

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
