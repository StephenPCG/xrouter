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
    pass
