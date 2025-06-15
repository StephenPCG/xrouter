import sh
import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Reload xrouter configuration",
)


@app.command("system")
def reload_system():
    from .base import global_options as go

    logger = go.logger

    logger.info("[reload system]")
    logger.info(" > sysctl -p --system")
    logger.info(sh.sysctl("-p", "--system"))


@app.command("interfaces")
def reload_interfaces():
    from .base import global_options as go

    logger = go.logger

    logger.info("[reload interfaces]")
    logger.info(" > networkctl reload")
    logger.info(sh.networkctl("reload"))
