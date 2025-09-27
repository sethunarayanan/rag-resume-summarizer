import typer
from config.settings import chroma_client, mongo_db

cli = typer.Typer(help="Custom management commands")

@cli.command()
def clean_db(confirm: bool = typer.Option(False, help="Must be True to actually delete data")):
    """
    Caution: Run to clean cromadb and mongodb
    ./manage.py clean_db --confirm True
    """
    if not confirm:
        typer.echo("You must pass --confirm True to actually clean the databases.")
        raise typer.Exit(code=1)
    chroma_client.delete_collection("resumechunk")
    mongo_db["resumemeta"].delete_many({})
    typer.echo("Deleted all documents from MongoDB and Chromadb")

if __name__ == "__main__":
    cli()