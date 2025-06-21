from pathlib import Path

import sh
from pydantic import BaseModel


def normalize_mount_path(base: Path, mount: str) -> str:
    src, target = mount.split(":", 1)
    if not src.startswith("/"):
        src = str(base / src)
    return f"{src}:{target}"


class Container(BaseModel):
    name: str
    image: str
    command: str | None = None
    network: str = "podman"
    ipv4_address: str | None = None
    env: list[str] = []
    # mount: (source, target)
    mounts: list[str] = []

    # will be joined by space directly
    podman_run_args: list[str] = []

    def model_post_init(self, __context):
        from xrouter.gwlib import gw

        self.mounts = [normalize_mount_path(gw.container_data_root / self.name, mount) for mount in self.mounts]

    def create_mount_sources(self):
        from xrouter.gwlib import gw

        for mount in self.mounts:
            source = mount.split(":", 1)[0]

            source_path = Path(source)
            if not source_path.exists():
                gw.run_command(sh.mkdir.bake("-p", source_path))

    @property
    def systemd_exec_start(self) -> str:
        args = [
            "/usr/bin/podman",
            "run",
            "--cidfile=%t/%n.ctr-id",
            "--cgroups=no-conmon",
            "--rm",
            "--sdnotify=conmon",
            "--replace",
            "--name",
            self.name,
        ]
        if self.network:
            args.extend(["--network", self.network])
        if self.ipv4_address:
            args.extend(["--ip", self.ipv4_address])
        for mount in self.mounts:
            args.extend(["-v", mount])
        for env in self.env:
            args.extend(["-e", env])

        args.append(self.image)
        args.extend(self.podman_run_args)
        if self.command:
            args.append(self.command)
        return " ".join(args)

    @property
    def systemd_exec_start_pre(self) -> str:
        return "/bin/rm -f %t/%n.ctr-id"

    @property
    def systemd_exec_stop(self) -> str:
        return "/usr/bin/podman stop --ignore -t 10 --cidfile=%t/%n.ctr-id"

    @property
    def systemd_exec_stop_post(self) -> str:
        return "/usr/bin/podman rm -f --ignore -t 10 --cidfile=%t/%n.ctr-id"


class ContainerConfig(BaseModel):
    containers: dict[str, Container] = {}

    @property
    def container_names(self) -> list[str]:
        return list(self.containers.keys())
