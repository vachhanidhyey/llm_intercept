"""Command-line interface for LLM Intercept."""

import os
import click
import uvicorn
from .database import get_engine, init_db


@click.group()
def cli():
    """LLM Intercept - Proxy server for intercepting LLM API calls."""
    pass


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind the server to",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    help="Port to bind the server to",
    show_default=True,
)
@click.option(
    "--database-url",
    default="sqlite:///./llm_intercept.db",
    help="Database URL (SQLite or PostgreSQL)",
    show_default=True,
)
@click.option(
    "--base-url",
    envvar="BASE_URL",
    default="https://openrouter.ai/api/v1/chat/completions",
    help="Base URL for the target API (can be set via BASE_URL env var)",
    show_default=True,
)
@click.option(
    "--admin-password",
    envvar="ADMIN_PASSWORD",
    required=True,
    help="Password for admin interface (can be set via ADMIN_PASSWORD env var)",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload for development",
)
def serve(host: str, port: int, database_url: str, base_url: str, admin_password: str, reload: bool):
    """Start the LLM Intercept proxy server."""
    # Set environment variables
    os.environ["DATABASE_URL"] = database_url
    os.environ["BASE_URL"] = base_url
    os.environ["ADMIN_PASSWORD"] = admin_password

    # Initialize database
    click.echo("Initializing database...")
    engine = get_engine()
    init_db(engine)
    click.echo("Database initialized successfully!")

    # Start server
    click.echo(f"Starting server on {host}:{port}")
    click.echo(f"Target API: {base_url}")
    click.echo(f"Admin interface: http://{host}:{port}/admin?password={admin_password}")
    click.echo(f"Health check: http://{host}:{port}/health")
    click.echo(f"Proxy endpoint: http://{host}:{port}/v1/chat/completions")

    uvicorn.run(
        "llm_intercept.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@cli.command()
@click.option(
    "--database-url",
    default="sqlite:///./llm_intercept.db",
    help="Database URL",
    show_default=True,
)
def init_database(database_url: str):
    """Initialize the database (create tables)."""
    os.environ["DATABASE_URL"] = database_url

    click.echo(f"Initializing database at {database_url}...")
    engine = get_engine()
    init_db(engine)
    click.echo("Database initialized successfully!")


def main():
    """Entry point for CLI."""
    cli()