# IPv6

常规配置：

* 使用 wide-dhcpv6-client，在为 pppoe 接口获取 IPv6 地址，并请求 Prefix Delegation，将获取到的 prefix 分配到各个接口（不太清楚这一步的 dhcpv6 具体干了啥）。
* 使用 radvd 在各个 LAN 口上广播 RA。也可以用 dnsmasq 的 --enable-ra 来实现，替代 radvd。

这里尝试的配置：

* 直接使用 systemd 的 DHCP=ipv6 来为 pppoe 获取 ipv6 地址，并用 DHCPPrefixDelegation=yes 来开启 PD。
* 在 LAN 口上，使用 IPv6SendRA 来发送 RA，并通过 [DHCPPrefixDelegation] 来配置 subnet
* 使用 dnsmasq 通过 dhcpv6 发送 DNS

一些说明：

IPv6 的两种配置方式，SLAAC（通过RA报文）和 DHCPv6，其中：
* SLAAC 只能获取地址，不能配置 DNS
* DHCPv6 既可以分配地址，也能分配 DNS， 但兼容性不好（安卓不支持 DHCPv6）
因此一般会组合来，通过 SLAAC 分配地址，通过 DHCPv6 来分配 DNS
