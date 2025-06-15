from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path


@dataclass
class GlobalOption:
    verbose: bool = True
    project_root: Path = field(default_factory=lambda: get_project_root())
    config_root: Path = field(default_factory=lambda: get_config_root())
    log_root: Path = field(default_factory=lambda: get_log_root())
    backup_root: Path = field(default_factory=lambda: get_backup_root())

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
    def file_backup_path(self):
        return self.backup_root / "files"

    @cached_property
    def xrouter_config_file(self):
        return self.config_root / "xrouter.yml"

    def print(self, message: str):
        self.logger.info(message)


def get_project_root():
    """
    xRouter code root

    The project should be cloned to /opt/xrouter, and xrouter package lives in /opt/xrouter/xrouter

    Later, this code can be changed to:

    ```py
    import xrouter
    return Path(xrouter.__file__).parent
    ```

    so that we can install xrouter package to system (like /usr/local/lib/python3.11/site-packages/).

    Currently, for simplicity, we hardcode the path to /opt/xrouter/xrouter
    """
    return Path("/opt/xrouter/xrouter")


def get_config_root():
    """
    We maintain all instance files in /opt/xrouter, so configs are stored in /opt/xrouter/configs.

    Now this is inside the xrouter project, so the configs/ path should be ignored in .gitignore.
    """
    return Path("/opt/xrouter/configs")


def get_log_root():
    """
    All logs are stored in /opt/xrouter/logs.

    Now this is inside the xrouter project, so the logs/ path should be ignored in .gitignore.
    """
    return Path("/opt/xrouter/logs")


def get_backup_root():
    """
    All backups are stored in /opt/xrouter/backups.
    """
    return Path("/opt/xrouter/backups")


global_options = GlobalOption()
