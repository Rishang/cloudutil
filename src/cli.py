from .aws.cli import app as aws_app
import typer

app = typer.Typer()

app.add_typer(aws_app, name="aws", help="AWS-related commands")


def main():
    app()


if __name__ == "__main__":
    main()
