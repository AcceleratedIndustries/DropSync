"""Command-line interface for DropSync."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from .config import ConfigManager
from .dbus_service import DropSyncDBusService
from .rules import organize_once
from .server import app as fastapi_app, app_state

console = Console()
app = typer.Typer(help="DropSync command-line interface")
config_cli = typer.Typer(help="Configuration utilities")
app.add_typer(config_cli, name="config")

DEPENDENCIES = {
    "readability-cli": ["readability-cli", "--version"],
    "monolith": ["monolith", "--version"],
    "yt-dlp": ["yt-dlp", "--version"],
    "gallery-dl": ["gallery-dl", "--version"],
}


def _setup_logging(log_level: str = "info") -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )


async def run_daemon_async(host: Optional[str] = None, port: Optional[int] = None) -> None:
    config_manager = app_state.config_manager
    config_manager.ensure_directories()
    config = config_manager.config
    bind_host = host or config.bind_host
    bind_port = port or config.port

    _setup_logging()

    server_config = uvicorn.Config(
        fastapi_app,
        host=bind_host,
        port=bind_port,
        log_level="info",
        loop="asyncio",
    )
    server = uvicorn.Server(server_config)
    dbus_service = DropSyncDBusService(app_state.collector)
    await dbus_service.start()
    try:
        await server.serve()
    finally:
        await dbus_service.stop()
        await app_state.processor_manager.shutdown()


@app.command()
def run(
    host: Optional[str] = typer.Option(None, help="Override bind host"),
    port: Optional[int] = typer.Option(None, help="Override bind port"),
) -> None:
    """Start the DropSync daemon (HTTP + DBus)."""

    asyncio.run(run_daemon_async(host=host, port=port))


@app.command()
def doctor() -> None:
    """Check external dependencies and report versions."""

    table = Table(title="DropSync Doctor", show_header=True, header_style="bold magenta")
    table.add_column("Dependency")
    table.add_column("Status")
    table.add_column("Version / Notes")

    for name, command in DEPENDENCIES.items():
        executable = shutil.which(command[0])
        if not executable:
            table.add_row(name, "missing", "not found in PATH")
            continue
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip() or result.stderr.strip()
            status = "ok" if result.returncode == 0 else f"exit {result.returncode}"
            table.add_row(name, status, output.splitlines()[0] if output else "")
        except OSError as exc:
            table.add_row(name, "error", str(exc))
    console.print(table)


@config_cli.command("init")
def config_init(force: bool = typer.Option(False, "--force", help="Overwrite existing config")) -> None:
    """Create a default configuration file."""

    manager = ConfigManager()
    try:
        path = manager.write_default_config(force=force)
        console.print(f"[green]Wrote default config to[/green] {path}")
    except FileExistsError as exc:
        console.print(f"[yellow]{exc}[/yellow]")


@config_cli.command("print")
def config_print() -> None:
    """Print the effective configuration."""

    manager = ConfigManager()
    config = manager.config
    console.print_json(json.dumps(config.model_dump(mode="json"), indent=2))


@app.command()
def organize(force: bool = typer.Option(False, help="Force re-run of processors")) -> None:
    """Apply rules and run post-processors once."""

    config = app_state.config_manager.config
    app_state.collector.update_rules()
    actions = organize_once(config, app_state.collector.rule_engine, app_state.processor_manager, force=force)
    if not actions:
        console.print("[green]No actions needed[/green]")
        return
    for action in actions:
        console.print(f"- {action}")


def run_daemon() -> None:
    """Console-script entry point for dropsyncd."""

    asyncio.run(run_daemon_async())


__all__ = ["app", "run_daemon", "run_daemon_async"]
