"""CLI for hanzo-node installer and runner."""

import os
import sys
import subprocess

import click

from . import __version__
from .installer import (
    install,
    uninstall,
    is_installed,
    get_binary_path,
    get_installed_version,
)


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def main(ctx, version):
    """
    Hanzo Node - AI infrastructure node.

    If hanzo-node binary is installed, runs it directly.
    Otherwise, use 'hanzo-node install' to install it first.
    """
    if version:
        print(f"hanzo-node {__version__} (installer)")
        if is_installed():
            node_ver = get_installed_version()
            print(f"hanzo-node {node_ver or '?'} (binary) at {get_binary_path()}")
        return

    # If no subcommand and binary is installed, run it
    if ctx.invoked_subcommand is None:
        if is_installed():
            # Pass through to the actual binary
            binary = get_binary_path()
            sys.exit(subprocess.call([str(binary)] + sys.argv[1:]))
        else:
            click.echo("hanzo-node is not installed. run: hanzo-node install")
            ctx.invoke(status)


@main.command()
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
@click.option("--version", "-V", "ver", help="Specific version to install")
def install_cmd(force, ver):
    """Install the hanzo-node binary."""
    click.echo()
    try:
        install(force=force, version=ver)
    except Exception as e:
        click.echo(f"  ✗ {e}", err=True)
        sys.exit(1)
    click.echo()


# Alias 'install' command
main.add_command(install_cmd, name="install")


@main.command()
def uninstall_cmd():
    """Uninstall the hanzo-node binary."""
    click.echo()
    uninstall()
    click.echo()


main.add_command(uninstall_cmd, name="uninstall")


@main.command()
@click.option("--force", "-f", is_flag=True, help="Force upgrade")
def upgrade(force):
    """Upgrade to the latest version."""
    click.echo()
    try:
        install(force=True)
    except Exception as e:
        click.echo(f"  ✗ {e}", err=True)
        sys.exit(1)
    click.echo()


@main.command()
def status():
    """Show installation status."""
    click.echo()
    if is_installed():
        binary = get_binary_path()
        ver = get_installed_version()
        click.echo(f"  ✓ hanzo-node {ver or '?'}")
        click.echo(f"    path: {binary}")
    else:
        click.echo("  ○ hanzo-node not installed")
        click.echo("    run: hanzo-node install")
    click.echo()


@main.command()
@click.argument("args", nargs=-1)
def run(args):
    """Run hanzo-node with arguments."""
    if not is_installed():
        click.echo("hanzo-node is not installed. run: hanzo-node install", err=True)
        sys.exit(1)

    binary = get_binary_path()
    sys.exit(subprocess.call([str(binary)] + list(args)))


@main.command()
def path():
    """Print the binary path."""
    print(get_binary_path())


if __name__ == "__main__":
    main()
