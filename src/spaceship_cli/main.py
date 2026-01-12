import typer
from spaceship_cli.commands import domains, dns, contacts

app = typer.Typer(
    name="spaceship",
    help="Spaceship.com CLI Tool",
    add_completion=False,
)

app.add_typer(domains.app, name="domains", help="Manage domains")
app.add_typer(dns.app, name="dns", help="Manage DNS records")
app.add_typer(contacts.app, name="contacts", help="Manage contacts")

if __name__ == "__main__":
    app()