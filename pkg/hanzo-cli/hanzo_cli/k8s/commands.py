"""Hanzo CLI — Kubernetes management via kubectl passthrough.

Wraps kubectl with Hanzo-managed authentication and sensible defaults.
Unrecognized subcommands pass directly through to kubectl.

Usage:
    hanzo k8s auth                    # Fetch kubeconfig from Hanzo PaaS
    hanzo k8s get pods                # kubectl get pods -n hanzo
    hanzo k8s logs <pod>              # kubectl logs <pod> -n hanzo
    hanzo k8s apply -f file.yaml      # kubectl apply -f file.yaml -n hanzo
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli.paas.client import PaaSClient

console = Console()

KUBECONFIG_DIR = Path.home() / ".hanzo" / "k8s"
KUBECONFIG_FILE = KUBECONFIG_DIR / "kubeconfig"
DEFAULT_NAMESPACE = "hanzo"


# ── helpers ────────────────────────────────────────────────────────────


def _find_kubectl() -> str:
    """Locate kubectl or exit with install instructions."""
    path = shutil.which("kubectl")
    if not path:
        console.print(
            "[red]kubectl not found.[/red] "
            "Install: https://kubernetes.io/docs/tasks/tools/"
        )
        sys.exit(1)
    return path


def _kubeconfig_env() -> dict[str, str]:
    """Return env dict with KUBECONFIG set if the managed file exists."""
    env = dict(os.environ)
    if KUBECONFIG_FILE.exists():
        env["KUBECONFIG"] = str(KUBECONFIG_FILE)
    return env


def _kubectl_run(args: list[str], namespace: str | None = None) -> int:
    """Execute kubectl with managed kubeconfig and optional namespace.

    Returns the process exit code.
    """
    kubectl = _find_kubectl()
    cmd = [kubectl]

    # Inject default namespace if not already specified
    ns_flags = {"--namespace", "-n", "--all-namespaces", "-A"}
    if namespace and not ns_flags.intersection(args):
        cmd.extend(["--namespace", namespace])

    cmd.extend(args)
    result = subprocess.run(cmd, env=_kubeconfig_env())
    return result.returncode


# ── custom group class ─────────────────────────────────────────────────


class KubectlGroup(click.Group):
    """Click group that forwards unknown subcommands to kubectl.

    Known subcommands (auth, info, context, etc.) are handled normally.
    Everything else (get, apply, describe, rollout, ...) creates a dynamic
    command that passes through to kubectl.
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Try builtin commands first
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # Dynamic kubectl passthrough command
        @click.command(
            cmd_name,
            context_settings={
                "ignore_unknown_options": True,
                "allow_extra_args": True,
                "allow_interspersed_args": False,
            },
        )
        @click.argument("args", nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def kubectl_proxy(ctx: click.Context, args: tuple[str, ...]) -> None:
            ns = (
                ctx.parent.params.get("namespace") if ctx.parent else None
            ) or DEFAULT_NAMESPACE
            all_args = [cmd_name] + list(args)
            rc = _kubectl_run(all_args, namespace=ns)
            ctx.exit(rc)

        kubectl_proxy.help = f"kubectl {cmd_name} (passthrough)"
        return kubectl_proxy

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        # Always resolve — get_command handles unknown names via passthrough
        cmd_name = args[0] if args else None
        if cmd_name is None:
            return super().resolve_command(ctx, args)

        cmd = self.get_command(ctx, cmd_name)
        if cmd is None:
            return super().resolve_command(ctx, args)

        return cmd_name, cmd, args[1:]


# ── click group ────────────────────────────────────────────────────────


@click.group(cls=KubectlGroup, invoke_without_command=True)
@click.option(
    "-n",
    "--namespace",
    default=None,
    help="Kubernetes namespace (default: hanzo).",
)
@click.pass_context
def k8s(ctx: click.Context, namespace: str | None) -> None:
    """Kubernetes management — wraps kubectl with Hanzo auth.

    Any unrecognized subcommand is forwarded directly to kubectl with
    the managed kubeconfig and default namespace.

    \b
    Examples
      hanzo k8s auth                  Set up kubeconfig
      hanzo k8s get pods              kubectl get pods -n hanzo
      hanzo k8s -n production get po  kubectl get pods -n production
      hanzo k8s logs my-pod -f        kubectl logs my-pod -f -n hanzo
      hanzo k8s apply -f deploy.yaml  kubectl apply -f deploy.yaml
    """
    ctx.ensure_object(dict)
    ctx.obj["namespace"] = namespace or DEFAULT_NAMESPACE

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ── auth ───────────────────────────────────────────────────────────────


@k8s.command("auth")
@click.option("--force", is_flag=True, help="Overwrite existing kubeconfig.")
def k8s_auth(force: bool) -> None:
    """Authenticate and fetch kubeconfig from Hanzo PaaS.

    Exchanges your IAM credentials for cluster access and stores the
    kubeconfig at ~/.hanzo/k8s/kubeconfig.
    """
    if KUBECONFIG_FILE.exists() and not force:
        console.print(f"Kubeconfig exists at [cyan]{KUBECONFIG_FILE}[/cyan]")
        console.print("Use [bold]--force[/bold] to overwrite.")
        return

    console.print("Authenticating with Hanzo PaaS...")

    client = PaaSClient.from_auth()
    try:
        kubeconfig_text = _fetch_kubeconfig(client)
    finally:
        client.close()

    if kubeconfig_text:
        KUBECONFIG_DIR.mkdir(parents=True, exist_ok=True)
        KUBECONFIG_FILE.write_text(kubeconfig_text)
        KUBECONFIG_FILE.chmod(0o600)
        console.print(f"[green]Kubeconfig saved to {KUBECONFIG_FILE}[/green]")
        console.print("Run [bold]hanzo k8s get pods[/bold] to verify.")
    else:
        default_kc = Path.home() / ".kube" / "config"
        console.print("[yellow]PaaS kubeconfig endpoint not available yet.[/yellow]")
        if default_kc.exists():
            console.print(f"kubectl will use your default config at {default_kc}")
        else:
            console.print(
                "Configure kubectl manually:\n"
                "  doctl kubernetes cluster kubeconfig save <cluster-name>"
            )


def _fetch_kubeconfig(client: PaaSClient) -> str | None:
    """Try multiple PaaS endpoints to obtain kubeconfig text."""
    # 1. Dedicated kubeconfig endpoint
    try:
        resp = client.http.get("/v1/cluster/kubeconfig")
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                data = resp.json()
                return data.get("kubeconfig", json.dumps(data, indent=2))
            return resp.text
    except Exception:
        pass

    # 2. Cluster info — may contain embedded kubeconfig
    try:
        info = client.cluster_info()
        kc = info.get("kubeconfig") or info.get("config")
        if kc:
            if isinstance(kc, dict):
                return json.dumps(kc, indent=2)
            return str(kc)
    except Exception:
        pass

    return None


# ── info ───────────────────────────────────────────────────────────────


@k8s.command("info")
def k8s_info() -> None:
    """Show cluster information from Hanzo PaaS."""
    client = PaaSClient.from_auth()
    try:
        info = client.cluster_info()
    finally:
        client.close()

    table = Table(title="Cluster Info")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    for key, value in info.items():
        display = (
            json.dumps(value, indent=2)
            if isinstance(value, (dict, list))
            else str(value)
        )
        table.add_row(key, display)

    console.print(table)


# ── context ────────────────────────────────────────────────────────────


@k8s.command("context")
def k8s_context() -> None:
    """Show current kubectl context and configuration status."""
    table = Table(title="Kubernetes Config")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    if KUBECONFIG_FILE.exists():
        table.add_row("Kubeconfig", str(KUBECONFIG_FILE))
    else:
        default_kc = Path.home() / ".kube" / "config"
        if default_kc.exists():
            table.add_row("Kubeconfig", f"{default_kc} (system default)")
        else:
            table.add_row("Kubeconfig", "[red]Not configured[/red]")

    table.add_row("Default Namespace", DEFAULT_NAMESPACE)

    kubectl = shutil.which("kubectl")
    table.add_row("kubectl", kubectl or "[red]Not installed[/red]")

    console.print(table)

    if kubectl:
        env = _kubeconfig_env()
        result = subprocess.run(
            [kubectl, "config", "current-context"],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            console.print(f"\nCurrent context: [green]{result.stdout.strip()}[/green]")
        else:
            console.print("\n[yellow]No current context set.[/yellow]")
