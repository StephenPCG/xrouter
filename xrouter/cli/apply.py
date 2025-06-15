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

    install_template_file(
        "/etc/sysctl.d/99-xrouter.conf",
        "99-xrouter.sysctl.conf",
        {},
        show_diff=go.verbose,
        backup_path=go.file_backup_path,
    )
