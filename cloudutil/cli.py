from .aws.cli import app as aws_app
from .sql.cli import app as sql_app
import typer

app = typer.Typer(
    pretty_exceptions_enable=False,
)

app.add_typer(aws_app, name="aws", help="AWS-related commands")
app.add_typer(sql_app, name="sql", help="SQL database management commands")


def main():
    app()


if __name__ == "__main__":
    main()
