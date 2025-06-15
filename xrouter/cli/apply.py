import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Apply xrouter configuration to the system",
)


@app.command("system")
def apply_system():
    """
    Install these files:

    * /etc/sysctl.d/99-xrouter.conf
    * kernel modules, like bbr
    """
    from xrouter.utils.install_file import install_template_file

    from .base import global_options as go

    logger = go.logger

    logger.info("[apply system]")
    logger.info("Applying /etc/sysctl.d/99-xrouter.conf ...")
    install_template_file(
        "/etc/sysctl.d/99-xrouter.conf",
        "99-xrouter.sysctl.conf",
        {},
        print=go.print,
        backup_path=go.file_backup_path,
    )


@app.command("interfaces")
def apply_interfaces():
    from xrouter.config import load_xrouter_config
    from xrouter.utils.install_file import install_text_file

    from .base import global_options as go

    logger = go.logger

    logger.info("[apply interfaces]")
    logger.info(f"config file: {go.xrouter_config_file}")
    config = load_xrouter_config(go.xrouter_config_file)

    logger.info("Applying network unit files ...")

    for iface in config.interfaces:
        for (
            filename,
            content,
        ) in iface.get_systemd_network_files():
            install_text_file(filename, content, print=go.print, backup_path=go.file_backup_path)
