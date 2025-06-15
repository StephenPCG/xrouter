from dataclasses import dataclass, field
from functools import cached_property

from click import Path


@dataclass
class GlobalOption:
    verbose: bool = False
    system_root: str = field(default_factory=lambda: get_default_root())
    project_root: Path = field(default_factory=lambda: get_project_root())
    config_root: Path = field(default_factory=lambda: get_config_root())
    log_root: Path = field(default_factory=lambda: get_log_root())

    @cached_property
    def logger(self):
        import logging

        if not self.log_root.exists():
            self.log_root.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger("xrouter")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_root / "cli.log")
        file_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # Create formatter
        formatter = logging.Formatter("[%(levelname)s][%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Ensure the logger is not propagating to the root logger
        logger.propagate = False

        return logger


def get_default_root():
    """
    The system root.

    In case we later deploy xrouter inside a container, we can mount system root to container's `/host` dir.
    """
    return "/"


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


global_options = GlobalOption()
