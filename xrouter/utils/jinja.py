from jinja2 import Environment, PackageLoader

env = Environment(
    loader=PackageLoader("xrouter", "templates"),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(template_file: str, context: dict):
    template = env.get_template(template_file)

    return template.render(context)
