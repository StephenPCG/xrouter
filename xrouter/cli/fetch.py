from typing import Annotated

import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Fetch xrouter configuration",
)


@app.command("china-ips")
def fetch_china_ips():
    from xrouter.gwlib import gw
    from xrouter.utils.download import download_text

    for file in [
        "china",
        "china6",
        # 电信
        "chinanet",
        "chinanet6",
        # 移动
        "cmcc",
        "cmcc6",
        # 科技网
        "cstnet",
        "cstnet6",
        # 鹏博士
        "drpeng",
        "drpeng6",
        # 谷歌中国
        "googlecn",
        "googlecn6",
        # 教育网
        "cernet",
        "cernet6",
        # 联通
        "unicom",
        "unicom6",
    ]:
        url = f"https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/{file}.txt"
        path = gw.zones_root / f"{file}.txt"

        gw.print(f"Downloading {url} ...")
        content = download_text(url, "text")

        gw.print(f"Saving to {path} ...")
        gw.install_text_file(path, content, show_diff=False)


@app.command("github-ips")
def fetch_github_ips():
    from xrouter.gwlib import gw
    from xrouter.utils.cidr import merge_cidr_list_split_version, safe_parse_cidr
    from xrouter.utils.download import download_text

    content = download_text(
        "https://api.github.com/meta",
        "json",
    )

    # extract all ipv4 and ipv6 addresses from json
    cidrs_all = []

    # Process each service in the JSON
    for service_name, networks in content.items():
        if isinstance(networks, list):
            for network in networks:
                cidr = safe_parse_cidr(network)
                if cidr:
                    cidrs_all.append(cidr)

    cidrs_v4, cidrs_v6 = merge_cidr_list_split_version(cidrs_all)

    # Save IPv4 networks
    ipv4_path = gw.zones_root / "github-ipv4.txt"
    ipv4_content = "\n".join(cidrs_v4) + "\n"
    gw.print(f"Saving {len(cidrs_v4)} IPv4 networks to {ipv4_path} ...")
    gw.install_text_file(ipv4_path, ipv4_content, show_diff=False)

    # Save IPv6 networks
    ipv6_path = gw.zones_root / "github-ipv6.txt"
    ipv6_content = "\n".join(cidrs_v6) + "\n"
    gw.print(f"Saving {len(cidrs_v6)} IPv6 networks to {ipv6_path} ...")
    gw.install_text_file(ipv6_path, ipv6_content, show_diff=False)


@app.command("google-ips")
def fetch_google_ips():
    from xrouter.gwlib import gw
    from xrouter.utils.cidr import merge_cidr_list_split_version
    from xrouter.utils.download import download_text

    content = download_text(
        "https://www.gstatic.com/ipranges/goog.json",
        "json",
    )

    cidrs_all = []

    for prefixes in content.get("prefixes", []):
        if "ipv4Prefix" in prefixes:
            cidrs_all.append(prefixes["ipv4Prefix"])
        elif "ipv6Prefix" in prefixes:
            cidrs_all.append(prefixes["ipv6Prefix"])

    cidrs_v4, cidrs_v6 = merge_cidr_list_split_version(cidrs_all)

    ipv4_path = gw.zones_root / "google-ipv4.txt"
    ipv4_content = "\n".join(cidrs_v4) + "\n"
    gw.print(f"Saving {len(cidrs_v4)} IPv4 networks to {ipv4_path} ...")
    gw.install_text_file(ipv4_path, ipv4_content, show_diff=False)

    ipv6_path = gw.zones_root / "google-ipv6.txt"
    ipv6_content = "\n".join(cidrs_v6) + "\n"
    gw.print(f"Saving {len(cidrs_v6)} IPv6 networks to {ipv6_path} ...")
    gw.install_text_file(ipv6_path, ipv6_content, show_diff=False)


@app.command("cloudflare-ips")
def fetch_cloudflare_ips():
    from xrouter.gwlib import gw
    from xrouter.utils.cidr import merge_cidr_list_split_version
    from xrouter.utils.download import download_text

    content = download_text(
        "https://api.cloudflare.com/client/v4/ips",
        "json",
    )

    cidrs_all = []

    for cidr in content.get("result", {}).get("ipv4_cidrs", []):
        cidrs_all.append(cidr)

    for cidr in content.get("result", {}).get("ipv6_cidrs", []):
        cidrs_all.append(cidr)

    cidrs_v4, cidrs_v6 = merge_cidr_list_split_version(cidrs_all)

    ipv4_path = gw.zones_root / "cloudflare-ipv4.txt"
    ipv4_content = "\n".join(cidrs_v4) + "\n"
    gw.print(f"Saving {len(cidrs_v4)} IPv4 networks to {ipv4_path} ...")
    gw.install_text_file(ipv4_path, ipv4_content, show_diff=False)

    ipv6_path = gw.zones_root / "cloudflare-ipv6.txt"
    ipv6_content = "\n".join(cidrs_v6) + "\n"
    gw.print(f"Saving {len(cidrs_v6)} IPv6 networks to {ipv6_path} ...")
    gw.install_text_file(ipv6_path, ipv6_content, show_diff=False)


@app.command("fastly-ips")
def fetch_fastly_ips():
    from xrouter.gwlib import gw
    from xrouter.utils.cidr import merge_cidr_list_split_version
    from xrouter.utils.download import download_text

    content = download_text(
        "https://api.fastly.com/public-ip-list",
        "json",
    )

    cidrs_all = []

    for cidr in content.get("addresses", []):
        cidrs_all.append(cidr)

    for cidr in content.get("ipv6_addresses", []):
        cidrs_all.append(cidr)

    cidrs_v4, cidrs_v6 = merge_cidr_list_split_version(cidrs_all)

    ipv4_path = gw.zones_root / "fastly-ipv4.txt"
    ipv4_content = "\n".join(cidrs_v4) + "\n"
    gw.print(f"Saving {len(cidrs_v4)} IPv4 networks to {ipv4_path} ...")
    gw.install_text_file(ipv4_path, ipv4_content, show_diff=False)

    ipv6_path = gw.zones_root / "fastly-ipv6.txt"
    ipv6_content = "\n".join(cidrs_v6) + "\n"
    gw.print(f"Saving {len(cidrs_v6)} IPv6 networks to {ipv6_path} ...")
    gw.install_text_file(ipv6_path, ipv6_content, show_diff=False)


@app.command("china-names")
def fetch_china_names(show_diff: Annotated[bool, typer.Option("--show-diff", help="Show diff")] = False):
    from xrouter.gwlib import gw
    from xrouter.utils.download import download_text

    gw.print("Downloading accelerated-domains.china.conf ...")
    content = download_text(
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/refs/heads/master/accelerated-domains.china.conf",
        "text",
    )
    gw.install_text_file(
        gw.dnsmasq_config_root / "china-114.conf",
        content,
        show_diff=show_diff,
    )
    gw.install_text_file(
        gw.dnsmasq_config_root / "china-223.conf",
        content.replace("114.114.114.114", "223.5.5.5"),
        show_diff=show_diff,
    )

    gw.print("Downloading apple.china.conf ...")
    content = download_text(
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/refs/heads/master/apple.china.conf",
        "text",
    )
    gw.install_text_file(
        gw.dnsmasq_config_root / "apple-114.conf",
        content,
        show_diff=show_diff,
    )
    gw.install_text_file(
        gw.dnsmasq_config_root / "apple-223.conf",
        content.replace("114.114.114.114", "223.5.5.5"),
        show_diff=show_diff,
    )

    gw.print("Downloading bogus-nxdomain.china.conf ...")
    content = download_text(
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/refs/heads/master/bogus-nxdomain.china.conf",
        "text",
    )
    gw.install_text_file(
        gw.dnsmasq_config_root / "bogus-nxdomain-china.conf",
        content,
        show_diff=show_diff,
    )


@app.command("wgsd-client")
def fetch_wgsd_client():
    from pathlib import Path

    import sh

    from xrouter.gwlib import gw

    gw.print("Downloading wgsd-client ...")

    url = "https://github.com/jwhited/wgsd/releases/download/v0.3.6/wgsd-client_0.3.6_linux_amd64.tar.gz"
    binary_name = "wgsd-client"
    install_path = Path("/usr/local/bin")

    gw.run_command(sh.wget.bake(url, "-O", "/tmp/wgsd-client.tar.gz"), stream=True)
    gw.run_command(sh.tar.bake("-x", "-f", "/tmp/wgsd-client.tar.gz", "-C", "/tmp", binary_name))
    gw.run_command(sh.mv.bake("/tmp/wgsd-client", install_path))
    gw.run_command(sh.chmod.bake("+x", install_path / binary_name))
