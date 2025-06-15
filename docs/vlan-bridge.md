# VLAN Bridge 配置


需求描述：自己的 x86 盒子有 4-6 个以太网口，配置效果：
* 支持 VLAN，家庭内网中划分出 trusted、iot、guest 等 VLAN
* 除一个上联口以外，其他口的行为最好像 trunk 口一样，支持各种 tagged vlan 包通过，这样任何一个口都可以连接交换机（交换机的口也配置为 trunk 模式）

## 配置方式一

假设有6个口，分别为 eth0, eth1, ..., eth6，之前使用 ifupdown ，配置方式为：

```
# /etc/network/interfaces

iface br2 inet static
    address 10.250.2.1
    netmask 255.255.255.0
    bridge_ports eth0.2 eth1.2 eth2.2 eth3.2 eth4.2 eth5.2
    bridge_maxwait 0
    bridge_fd 0

iface br3 inet static
    address 10.250.2.1
    netmask 255.255.255.0
    bridge_ports eth0.3 eth1.3 eth2.3 eth3.3 eth4.3 eth5.3
    bridge_maxwait 0
    bridge_fd 0

# 其他 br 略

# 如果希望某个口 PVID 为 2，即进入的包如果为 untagged，自动加上 id=2，出去的包如果 id=2，则去除 vlan id，那么在 br2 中：
iface br2 inet static
    # 这里直接将 eth0 加入 br2 即可
    bridge_ports eth0 eth1.2 ...
```

如果将这个配置转化为 systemd-networkd 的配置，则配置文件数量会非常庞大，因为 systemd 不像 ifupdown 那样支持“自动”创建 vlan interface，例如当见到 `eth0.2` 时，ifupdown 会自动创建 `eth0.2` 这个 vlan interface，而使用 systemd，则需要手动创建：

```
# eth0.2.netdev (对于 eth0 上的每一个 vlan，都需要一个文件)
[NetDev]
Name=eth0.2
Kind=vlan

[VLAN]
Id=1

# eth0.network
[Match]
Name=eth0

[Network]
# 这里需要添加所有需要的 vlan
VLAN=eth0.2
VLAN=eth0.3
...

# 然后再创建 br
# br2.netdev
[NetDev]
Name=br2
Kind=bridge

# br2.network（即使一个接口没有任何配置，也需要 network 文件，来让这个接口被标记为 configured）
[Match]
Name=br2

# 对于每一个需要加入 br2 的 vlan 接口，需要
# eth0.2.network
[Match]
Name=eth0.2

[Network]
Bridge=br-trunk
```

我们假设有6个物理网口，需要配置5个 VLAN，则需要这么多文件
* `ethX.X.netdev`，共 6*5=30 个文件
* `ethX.X.network`，共 6*5=30 个文件
* `ethX.network`，共 6 个文件
* `brX.netdev`，共 5 个文件
* `brX.network`，共 5 个文件

这里面，ethX.network、brX.netdev、brX.network 无论如何总是要的，但前面的 30个文件则很多余。

## 配置方式二

我们可以创建 vlan aware bridge，将所有物理网口加进去，然后从这个 bridge 上再创建 vlan 接口

```
# br-trunk.netdev # 创建一个 vlan aware bridge
[NetDev]
Name=br-trunk
Kind=bridge

[Bridge]
VLANFiltering=1
DefaultPVID=none

# br-trunk.network
[Match]
Name=br-trunk

[BridgeVLAN]
VLAN=2
VLAN=3
...

[Network]
ConfigureWithoutCarrier=yes
RequiredForOnline=no
VLAN=br2
VLAN=br3
...

# 对于每一个物理口，如 eth0，加入这个 bridge
# eth0.network
[Match]
Name=enp3s0

[Network]
# 加入 bridge
Bridge=br-trunk

[BridgeVLAN]
# 允许通过的 vlan id，也可以仅指定部分 id
VLAN=1-4094
# PVID 配置，PVID 对应的是接收到的 untagged 包，EgressUntagged 控制出去的包
PVID=1
EgressUntagged=1

# 此时，br-trunk 就是一个交换机，已经可以交换数据了，每个 ethX 都配置为 trunk 口
# 接下来，可以为 br-trunk 创建 SVI（switch virtual interface）

# br2.netdev
[NetDev]
Name=br2
Kind=vlan

[VLAN]
Id=2

# br2.network
[Match]
Name=br2

[Network]
ConfigureWithoutCarrier=yes
RequiredForOnline=no
Address=10.250.2.1/24
```

这样，总的配置文件数量：
* `br-trunk.netdev`
* `br-trunk.network`
* `brX.netdev`，共 5 个
* `brX.network`，共 5 个
* `ethX.network`，共 6 个
