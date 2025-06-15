# Interface 配置方式

## VLAN Bridge

见 [./vlan-bridge.md]

## PPPoE

由于 pppd 完全在用户态实现，因此 systemd-networkd 暂时不打算直接支持（不像 wireguard 那样几乎完全在内核中实现，用户态只需要执行一些配置即可）。
见：https://github.com/systemd/systemd/issues/481

因此，实际只能使用 systemd 的 service 来管理 pppd 命令。

另一项参考：https://ibug.io/blog/2024/07/pppd-with-systemd/

## Wireguard

生成 key 的命令：

```sh
wg genkey | (umask 0077 && tee peer_A.key) | wg pubkey > peer_A.pub
```
