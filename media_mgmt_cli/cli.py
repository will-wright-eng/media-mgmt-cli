import click


@click.group()
@click.version_option()
def cli():
    "A simple CLI to search and manage media assets in S3 and locally"


@cli.command(name="command")
@click.argument(
    "example"
)
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def first_command(example, option):
    "Command description goes here"
    click.echo("Here is some output")
