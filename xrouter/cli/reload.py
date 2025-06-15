import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Reload xrouter configuration",
)


@app.command("system")
def reload_system():
    pass
