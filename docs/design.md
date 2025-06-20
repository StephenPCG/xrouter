# 设计思路

路由器上要安装很多工具，配置分散，需要记忆一堆东西，管理也麻烦。但实际上日常维护所涉及到的文件、命令都比较固定。因此创建该项目，核心思路：

* 尽量将配置集中到一起，通过集中的配置文件进行配置，由脚本将状态同步到系统中。主要包括网络接口（interface）、路由（route table/rule）、防火墙规则（nftables）等。
* 一些系统不自带、但常用的工具，通过 podman 容器安装，避免“污染”系统。

之前使用过一段时间 vyos，vyos 本身设计的很好，但侧重于企业级路由，对于家用路由有点太重。vyos 有一套配置系统，所有配置都通过统一的配置机制来管理，但这有些过于“极端”，失去了很多灵活性。

例如，我需要创建一些路由表（route table），每个表中可能有数千个 cidr，直接使用 `ip route add $cidr table` 可以非常快的插入数千甚至数万条记录，在 vyos 中，一方面没有提供相应的功能（其使用 nftables 创建 set，再对命中 set 的包打 fwmark，然后再用 ip rule 控制路由），当有数千条甚至数万行配置是，每次提交配置、检查 diff 都会非常慢。

本项目使用稍微折中的方案，我们并不追求配置语言的一致性，之需要将配置文件集中在一起即可。甚至许多配置文件可以直接用工具原始的语言，但统一放在一起，再 symlink 到系统中。

## 基本操作

日常操作本质上包括这样一些步骤：

* 修改集中管理的配置文件
* 将配置文件应用到系统中（可能是copy/symlink到系统中，可能是通过模板生成新的文件更新到系统中）
* 让系统应用新的配置文件（如重启服务、执行某个命令等）

因此，我们的命令如下：

* `gw setup XXX`，生成配置文件
* `gw reload XXX`，重启相应的服务

例如：

```sh
# 对所有接口生成相应的 netdev、network 文件，部分需要独立进程的还有 service 文件
gw setup ifaces

# 重启接口，大多数 networkctl reload，少部分还需要 systemctl restart xxx.service
# reload 命令不一定要通过 gw 运行，也可以手动执行
gw reload ifaces [iface]

# 生成 route 脚本，存放到 /xxx/setup-route.sh 中
gw setup route
# 重新加载 route（也可以手动运行 setup-route.sh）
gw reload route

# 生成 /etc/nftables.conf （其中包含端口映射、podman 的规则等）
gw setup firewall

# 重启 nft 规则，也可执行 systemctl restart nftables
gw reload firewall

# 生成 dnsmasq 配置文件（当 china-names 有更新时，也可执行以更新配置）
gw setup dnsmasq
# 重启 dnsmasq
gw reload dnsmasq

# 生成 podman 容器的配置文件
gw setup containers
# 重启容器
gw reload containers [container]
```
