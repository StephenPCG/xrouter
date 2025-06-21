def merge_cidr_list(cidrs: list[str]) -> list[str]:
    from netaddr import IPNetwork, cidr_merge

    ip_networks = [IPNetwork(cidr) for cidr in cidrs]
    merged_networks = cidr_merge(ip_networks)
    return [str(network) for network in merged_networks]


def merge_cidr_list_split_version(cidrs: list[str]) -> tuple[list[str], list[str]]:
    from netaddr import IPNetwork, cidr_merge

    ip_networks = [IPNetwork(cidr) for cidr in cidrs]

    merged_v4 = cidr_merge([n for n in ip_networks if n.version == 4])
    merged_v6 = cidr_merge([n for n in ip_networks if n.version == 6])

    return [str(network) for network in merged_v4], [str(network) for network in merged_v6]


def safe_parse_cidr(v: str) -> str | None:
    from netaddr import IPNetwork

    try:
        return str(IPNetwork(v))
    except Exception:
        return None
