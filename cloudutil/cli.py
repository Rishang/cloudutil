import typer
from .aws.cli import app as aws_app
from .azure.cli import app as azure_app
from .k8s.cli import app as k8s_app
from .os_utils.cli import app as os_utils_app
from .sql.cli import app as sql_app
from .task.cli import app as task_app
from .psst.cli import app as psst_app

app = typer.Typer(
    pretty_exceptions_enable=False,
)

app.add_typer(aws_app, name="aws", help="AWS-related commands")
app.add_typer(azure_app, name="az", help="Azure-related commands")
app.add_typer(sql_app, name="sql", help="SQL database management commands")
app.add_typer(os_utils_app, name="os", help="OS-related commands")
app.add_typer(k8s_app, name="k8s", help="Kubernetes-related commands")
app.add_typer(
    psst_app,
    name="pwpush",
    help="Password Pusher commands ref: https://docs.pwpush.com/",
)
app.command(
    "task",
    help="Taskfile commands",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(task_app)


def main():
    app()


if __name__ == "__main__":
    main()
