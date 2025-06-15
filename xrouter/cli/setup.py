import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Setup xrouter configuration",
)


@app.command("system")
def setup_system():
    from .apply import apply_system
    from .reload import reload_system

    apply_system()
    reload_system()
