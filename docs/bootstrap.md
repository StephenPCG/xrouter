# Bootstrap

从新安装的 Debian 系统开始，配置的全流程。包括安装 xrouter、安装路由所需的工具包等。

### 修改 sources.list

```
deb https://mirrors.ustc.edu.cn/debian/ bookworm main non-free-firmware non-free contrib
deb https://mirrors.ustc.edu.cn/debian/ bookworm-updates main non-free-firmware non-free contrib
deb https://mirrors.ustc.edu.cn/debian/ bookworm-backports main non-free-firmware non-free contrib
deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main non-free-firmware non-free contrib
```

### 安装必要工具

```
# 以下非路由本身所需，主要是管理需要
sudo apt install git vim byobu rsync curl aptitude

sudo apt install apt-file
sudo apt-file update

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 podman
sudo apt install podman
sudo apt install podman-compose -t bookworm-backports

# interface packages
sudo apt install pppoe

# diagnostic tools
sudo apt install net-tools bind9-dnsutils tcpdump mtr-tiny
```

### 安装 xrouter

```
sudo mkdir /opt/xrouter
sudo chown $(whoami):$(whoami) /opt/xrouter
git clone https://github.com/stephenpcg/xrouter -C /opt/xrouter
cd /opt/xrouter
uv sync

sudo ln -s /opt/xrouter/.venv/bin/gw /usr/local/bin/gw
```
