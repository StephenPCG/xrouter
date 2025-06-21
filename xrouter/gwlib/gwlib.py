from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path


@dataclass
class GwLib:
    verbose: bool = True
    project_root: Path = field(default_factory=lambda: Path("/opt/xrouter/xrouter"))
    config_root: Path = field(default_factory=lambda: Path("/opt/xrouter/configs"))
    zones_root: Path = field(default_factory=lambda: Path("/opt/xrouter/configs/zones"))
    dnsmasq_config_root: Path = field(default_factory=lambda: Path("/opt/xrouter/configs/dnsmasq"))
    log_root: Path = field(default_factory=lambda: Path("/opt/xrouter/logs"))
    backup_root: Path = field(default_factory=lambda: Path("/opt/xrouter/backups"))
    bin_root: Path = field(default_factory=lambda: Path("/opt/xrouter/bin"))
    container_data_root: Path = field(default_factory=lambda: Path("/opt/xrouter/containers"))

    @cached_property
    def run_id(self):
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d-%H%M%S-%f")

    @cached_property
    def file_backup_path(self):
        return self.backup_root / "files"

    @cached_property
    def xrouter_config_file(self):
        return self.config_root / "xrouter.yml"

    @cached_property
    def logger(self):
        import logging

        from rich.logging import RichHandler

        if not self.log_root.exists():
            self.log_root.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger("xrouter")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_root / "cli.log")
        file_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        formatter = logging.Formatter("[%(levelname)s][%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = RichHandler(log_time_format="[%Y-%m-%d %H:%M:%S] ")
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Ensure the logger is not propagating to the root logger
        logger.propagate = False

        return logger

    @cached_property
    def config(self):
        import yaml

        from .config import XrouterConfig

        config_file_path = Path(self.config_root) / "xrouter.yml"

        with config_file_path.open(encoding="utf8") as fp:
            data = yaml.safe_load(fp)
            return XrouterConfig.model_validate(data)

    @cached_property
    def jinja2_env(self):
        from jinja2 import Environment, PackageLoader

        env = Environment(
            loader=PackageLoader("xrouter", "templates"),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        return env

    def print(self, msg: str):
        self.logger.info(msg)

    def run_command(self, command, stream: bool = False):
        import sys

        from sh import Command

        if not isinstance(command, Command):
            raise Exception("Invalid command, must be constructed by sh.COMMAND.bake()")

        self.logger.info(f"> {command}")
        if stream:
            command(_out=sys.stdout, _err=sys.stderr)
        else:
            self.logger.info(command())

    def render_template(self, template_name: str, context: dict):
        template = self.jinja2_env.get_template(template_name)

        return template.render(context)

    def install_text_file(
        self,
        file: str | Path,
        content: str,
        mode: str = "644",
        show_diff: bool = True,
    ):
        if isinstance(file, str):
            file = Path(file)

        has_diff, diff = check_diff(file, content, mode)
        if not has_diff:
            self.print(f"{file} is up to date")
            return

        if show_diff:
            self.print(diff)

        self.backup_file(file)

        file.parent.mkdir(parents=True, exist_ok=True)

        file.write_text(content)
        file.chmod(int(mode, 8))

    def install_template_file(
        self,
        file: str | Path,
        template_name: str,
        context: dict,
        mode: str = "644",
        show_diff: bool = True,
    ):
        content = self.render_template(template_name, context)
        return self.install_text_file(file, content, mode, show_diff)

    def install_binary_file(
        self,
        file: str | Path,
        content: Path | bytes,
        mode: str = "644",
        show_diff: bool = True,
    ):
        if isinstance(file, str):
            file = Path(file)

        if isinstance(content, Path):
            content = content.read_bytes()

        has_diff, diff = check_diff(file, content, mode)
        if not has_diff:
            self.print(f"{file} is up to date")
            return

        if show_diff:
            self.print(diff)

        self.backup_file(file)

        file.parent.mkdir(parents=True, exist_ok=True)

        file.write_bytes(content)
        file.chmod(int(mode, 8))

    def _get_backup_fullpath(self, backup_dir: Path, path: Path):
        if path.is_absolute():
            path = path.relative_to(path.anchor)

        return backup_dir / path

    def backup_file(self, file: Path):
        """
        备份系统文件，备份至 /opt/xrouter/backups/files/{run_id}/ 中
        """
        import shutil

        if not file.exists():
            return

        backup_full_path = self._get_backup_fullpath(self.file_backup_path / self.run_id, file)
        backup_full_dir = backup_full_path.parent
        backup_full_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, backup_full_path)

    def setup(self, verbose: bool):
        """
        为了方便，我们全局导出一个 gw 对象（GwUtils class），所哟地方都可以直接 import 使用。

        在脚本开始的时候，需要运行一下 gw.setup(...)，注入必要的设置信息，如果不注入，则所有设置都用默认值。
        """
        self.verbose = verbose

        # 如果修改了 verbose 的值，logger 需要重建，删除 self.logger，下一次访问时就会新建
        try:
            del self.logger
        except AttributeError:
            pass

        # 如果其他 cached_property 需要重置，也用同样的方法


def check_diff(path: Path, content: str | bytes, mode: str) -> tuple[bool, str]:
    """
    Check difference between current content/mode and filesystem.

    * Generates content diff for text files, binary status for binary files
    * Includes file mode changes
    * Appends (current)/(new) suffixes to filenames
    * Returns empty diff if content and mode are identical

    Returns:
        tuple[bool, str]: A tuple containing:
            - bool: True if there are any changes, False otherwise
            - str: The formatted diff text, empty string if no changes
    """
    import difflib

    # Get current mode
    current_mode = oct(path.stat().st_mode)[-3:] if path.exists() else None

    # Show mode changes if different
    has_diff = False
    diff = ""
    if current_mode != mode and current_mode is not None:
        has_diff = True
        diff = f"mode change {current_mode} -> {mode}\n"

    # Handle binary vs text content
    if isinstance(content, bytes):
        current_binary_content = path.read_bytes() if path.exists() else b""
        if current_binary_content == content:
            return has_diff, diff

        has_diff = True
        diff += "Binary files differ\n"
    else:
        current_text_content = path.read_text() if path.exists() else ""
        if current_text_content == content:
            return has_diff, diff

        has_diff = True
        diff += "".join(
            difflib.unified_diff(
                current_text_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                f"{path} (current)",
                f"{path} (new)",
            )
        )

    return has_diff, diff


gw = GwLib()
