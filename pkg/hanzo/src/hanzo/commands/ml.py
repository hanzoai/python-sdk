"""Hanzo ML - Machine learning platform CLI.

End-to-end MLOps: notebooks, pipelines, training, serving, registry.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

ML_URL = os.getenv("HANZO_ML_URL", "https://ml.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(ML_URL, method, path, **kwargs)


@click.group(name="ml")
def ml_group():
    """Hanzo ML - End-to-end machine learning platform (Kubeflow-compatible).

    \b
    Develop:
      hanzo ml notebooks           # Jupyter notebook management
      hanzo ml datasets            # Versioned dataset management

    \b
    Train:
      hanzo ml training            # Training jobs
      hanzo ml pipelines           # ML pipelines (Kubeflow Pipelines)
      hanzo ml experiments         # Experiment tracking
      hanzo ml tune                # Hyperparameter tuning (Katib)

    \b
    Features:
      hanzo ml features            # Feature store management

    \b
    AutoML:
      hanzo ml automl              # Automated machine learning

    \b
    Serve:
      hanzo ml serving             # Model serving (KServe)
      hanzo ml registry            # Model registry
    """
    pass


# ============================================================================
# Notebooks
# ============================================================================


@ml_group.group()
def notebooks():
    """Manage Jupyter notebooks."""
    pass


@notebooks.command(name="list")
def notebooks_list():
    """List all notebooks."""
    resp = _request("get", "/v1/notebooks")
    data = check_response(resp)
    items = data.get("notebooks", data.get("items", []))

    table = Table(title="Notebooks", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Instance", style="white")
    table.add_column("Status", style="green")
    table.add_column("GPU", style="yellow")
    table.add_column("Created", style="dim")

    for n in items:
        n_status = n.get("status", "stopped")
        style = "green" if n_status == "running" else "yellow"
        table.add_row(
            n.get("name", ""),
            n.get("instance", "-"),
            f"[{style}]{n_status}[/{style}]",
            n.get("gpu", "None"),
            str(n.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print(
            "[dim]No notebooks found. Create one with 'hanzo ml notebooks create'[/dim]"
        )


@notebooks.command(name="create")
@click.option("--name", "-n", prompt=True, help="Notebook name")
@click.option("--instance", "-i", default="cpu-small", help="Instance type")
@click.option("--gpu", is_flag=True, help="Enable GPU")
def notebooks_create(name: str, instance: str, gpu: bool):
    """Create a new notebook instance."""
    body = {"name": name, "instance": instance, "gpu": gpu}

    console.print(f"[cyan]Creating notebook '{name}'...[/cyan]")
    resp = _request("post", "/v1/notebooks", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Notebook '{name}' created")
    console.print(f"  Instance: {instance}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")
    if data.get("url"):
        console.print(f"  URL: {data['url']}")


@notebooks.command(name="start")
@click.argument("name")
def notebooks_start(name: str):
    """Start a notebook."""
    resp = _request("post", f"/v1/notebooks/{name}/start")
    check_response(resp)
    console.print(f"[green]✓[/green] Notebook '{name}' started")


@notebooks.command(name="stop")
@click.argument("name")
def notebooks_stop(name: str):
    """Stop a notebook."""
    resp = _request("post", f"/v1/notebooks/{name}/stop")
    check_response(resp)
    console.print(f"[green]✓[/green] Notebook '{name}' stopped")


@notebooks.command(name="delete")
@click.argument("name")
def notebooks_delete(name: str):
    """Delete a notebook."""
    from rich.prompt import Confirm

    if not Confirm.ask(f"[red]Delete notebook '{name}'?[/red]"):
        return

    resp = _request("delete", f"/v1/notebooks/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Notebook '{name}' deleted")


# ============================================================================
# Training
# ============================================================================


@ml_group.group()
def training():
    """Manage training jobs."""
    pass


@training.command(name="list")
@click.option(
    "--status",
    type=click.Choice(["running", "completed", "failed", "all"]),
    default="all",
)
def training_list(status: str):
    """List training jobs."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/training", params=params)
    data = check_response(resp)
    items = data.get("jobs", data.get("items", []))

    table = Table(title="Training Jobs", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Framework", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="dim")
    table.add_column("GPU", style="yellow")

    for j in items:
        j_status = j.get("status", "unknown")
        status_style = {"running": "cyan", "completed": "green", "failed": "red"}.get(
            j_status, "white"
        )
        table.add_row(
            str(j.get("id", ""))[:16],
            j.get("name", "-"),
            j.get("framework", "-"),
            f"[{status_style}]{j_status}[/{status_style}]",
            f"{j.get('duration_ms', '-')}ms" if j.get("duration_ms") else "-",
            j.get("gpu", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No training jobs found[/dim]")


@training.command(name="create")
@click.option("--name", "-n", prompt=True, help="Job name")
@click.option(
    "--framework",
    "-f",
    type=click.Choice(["pytorch", "tensorflow", "xgboost"]),
    default="pytorch",
)
@click.option("--script", "-s", required=True, help="Training script path")
@click.option("--gpu", "-g", default="1", help="Number of GPUs")
@click.option("--instance", "-i", default="gpu-a10g", help="Instance type")
def training_create(name: str, framework: str, script: str, gpu: str, instance: str):
    """Create a training job."""
    body = {
        "name": name,
        "framework": framework,
        "script": script,
        "gpu": gpu,
        "instance": instance,
    }

    console.print(f"[cyan]Creating training job '{name}'...[/cyan]")
    resp = _request("post", "/v1/training", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Training job '{name}' started")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Framework: {framework}")
    console.print(f"  Script: {script}")
    console.print(f"  Instance: {instance} ({gpu} GPUs)")


@training.command(name="logs")
@click.argument("job_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
def training_logs(job_id: str, follow: bool):
    """View training job logs."""
    params = {}
    if follow:
        params["follow"] = "true"

    resp = _request("get", f"/v1/training/{job_id}/logs", params=params)
    data = check_response(resp)
    lines = data.get("logs", data.get("lines", []))

    console.print(f"[cyan]Logs for job {job_id}:[/cyan]")
    for line in lines:
        if isinstance(line, dict):
            console.print(
                f"[dim]{str(line.get('timestamp', ''))[:19]}[/dim] {line.get('message', '')}"
            )
        else:
            console.print(str(line))

    if not lines:
        console.print("[dim]No logs available[/dim]")


@training.command(name="stop")
@click.argument("job_id")
def training_stop(job_id: str):
    """Stop a training job."""
    resp = _request("post", f"/v1/training/{job_id}/stop")
    check_response(resp)
    console.print(f"[green]✓[/green] Training job '{job_id}' stopped")


# ============================================================================
# Pipelines
# ============================================================================


@ml_group.group()
def pipelines():
    """Manage ML pipelines."""
    pass


@pipelines.command(name="list")
def pipelines_list():
    """List all pipelines."""
    resp = _request("get", "/v1/pipelines")
    data = check_response(resp)
    items = data.get("pipelines", data.get("items", []))

    table = Table(title="ML Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Status", style="green")
    table.add_column("Last Run", style="dim")

    for p in items:
        p_status = p.get("status", "idle")
        style = "green" if p_status == "active" else "dim"
        table.add_row(
            p.get("name", ""),
            str(p.get("version", "-")),
            f"[{style}]{p_status}[/{style}]",
            str(p.get("last_run_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No pipelines found[/dim]")


@pipelines.command(name="create")
@click.option("--name", "-n", prompt=True, help="Pipeline name")
@click.option("--file", "-f", required=True, help="Pipeline definition file")
def pipelines_create(name: str, file: str):
    """Create a pipeline from definition file."""
    with open(file) as f:
        definition = json.load(f)

    resp = _request(
        "post", "/v1/pipelines", json={"name": name, "definition": definition}
    )
    data = check_response(resp)

    console.print(f"[green]✓[/green] Pipeline '{name}' created from {file}")
    console.print(f"  ID: {data.get('id', '-')}")


@pipelines.command(name="run")
@click.argument("pipeline_name")
@click.option("--params", "-p", help="JSON parameters")
def pipelines_run(pipeline_name: str, params: str):
    """Run a pipeline."""
    body = {}
    if params:
        body["params"] = json.loads(params)

    console.print(f"[cyan]Running pipeline '{pipeline_name}'...[/cyan]")
    resp = _request("post", f"/v1/pipelines/{pipeline_name}/run", json=body)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Pipeline run started")
    console.print(f"  Run ID: {data.get('id', data.get('run_id', '-'))}")


# ============================================================================
# Serving
# ============================================================================


@ml_group.group()
def serving():
    """Manage model serving."""
    pass


@serving.command(name="list")
def serving_list():
    """List model deployments."""
    resp = _request("get", "/v1/serving")
    data = check_response(resp)
    items = data.get("deployments", data.get("items", []))

    table = Table(title="Model Deployments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Version", style="white")
    table.add_column("Status", style="green")
    table.add_column("Replicas", style="dim")
    table.add_column("Endpoint", style="dim")

    for d in items:
        d_status = d.get("status", "unknown")
        style = "green" if d_status == "ready" else "yellow"
        table.add_row(
            d.get("name", ""),
            d.get("model", "-"),
            str(d.get("version", "-")),
            f"[{style}]{d_status}[/{style}]",
            str(d.get("replicas", 0)),
            d.get("endpoint", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No deployments found[/dim]")


@serving.command(name="deploy")
@click.option("--name", "-n", prompt=True, help="Deployment name")
@click.option("--model", "-m", required=True, help="Model path or registry URI")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--gpu", is_flag=True, help="Enable GPU inference")
def serving_deploy(name: str, model: str, replicas: int, gpu: bool):
    """Deploy a model for inference."""
    body = {"name": name, "model": model, "replicas": replicas, "gpu": gpu}

    console.print(f"[cyan]Deploying model '{name}'...[/cyan]")
    resp = _request("post", "/v1/serving", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Model deployed")
    console.print(f"  Endpoint: {data.get('endpoint', '-')}")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")


@serving.command(name="scale")
@click.argument("name")
@click.option("--replicas", "-r", required=True, type=int, help="Target replicas")
def serving_scale(name: str, replicas: int):
    """Scale a deployment."""
    resp = _request("put", f"/v1/serving/{name}/scale", json={"replicas": replicas})
    check_response(resp)
    console.print(f"[green]✓[/green] Deployment '{name}' scaled to {replicas} replicas")


@serving.command(name="delete")
@click.argument("name")
def serving_delete(name: str):
    """Delete a deployment."""
    resp = _request("delete", f"/v1/serving/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Deployment '{name}' deleted")


# ============================================================================
# Registry
# ============================================================================


@ml_group.group()
def registry():
    """Manage model registry."""
    pass


@registry.command(name="list")
@click.option("--model", "-m", help="Filter by model name")
def registry_list(model: str):
    """List registered models."""
    params = {}
    if model:
        params["model"] = model

    resp = _request("get", "/v1/registry", params=params)
    data = check_response(resp)
    items = data.get("models", data.get("items", []))

    table = Table(title="Model Registry", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Stage", style="green")
    table.add_column("Framework", style="dim")
    table.add_column("Created", style="dim")

    for m in items:
        stage = m.get("stage", "none")
        style = (
            "green"
            if stage == "production"
            else "yellow" if stage == "staging" else "dim"
        )
        table.add_row(
            m.get("name", ""),
            str(m.get("version", "-")),
            f"[{style}]{stage}[/{style}]",
            m.get("framework", "-"),
            str(m.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No models registered[/dim]")


@registry.command(name="push")
@click.option("--name", "-n", required=True, help="Model name")
@click.option("--path", "-p", required=True, help="Model path")
@click.option("--framework", "-f", default="pytorch", help="Framework")
@click.option("--version", "-v", help="Version (auto-incremented if not specified)")
def registry_push(name: str, path: str, framework: str, version: str):
    """Push a model to the registry."""
    body = {"name": name, "path": path, "framework": framework}
    if version:
        body["version"] = version

    console.print(f"[cyan]Pushing model '{name}'...[/cyan]")
    resp = _request("post", "/v1/registry", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Model '{name}' pushed to registry")
    console.print(f"  Version: {data.get('version', '-')}")
    console.print(f"  Framework: {framework}")


@registry.command(name="pull")
@click.argument("model_uri")
@click.option("--output", "-o", default=".", help="Output directory")
def registry_pull(model_uri: str, output: str):
    """Pull a model from the registry."""
    console.print(f"[cyan]Pulling model {model_uri}...[/cyan]")
    resp = _request(
        "post", "/v1/registry/pull", json={"uri": model_uri, "output": output}
    )
    data = check_response(resp)
    console.print(f"[green]✓[/green] Model downloaded to {data.get('path', output)}")


@registry.command(name="promote")
@click.argument("model_uri")
@click.option(
    "--stage", "-s", type=click.Choice(["staging", "production"]), required=True
)
def registry_promote(model_uri: str, stage: str):
    """Promote a model version to a stage."""
    resp = _request(
        "post", "/v1/registry/promote", json={"uri": model_uri, "stage": stage}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Model promoted to {stage}")


# ============================================================================
# Experiments (Kubeflow-style experiment tracking)
# ============================================================================


@ml_group.group()
def experiments():
    """Manage ML experiments (Kubeflow-style)."""
    pass


@experiments.command(name="create")
@click.argument("name")
@click.option("--description", "-d", help="Experiment description")
@click.option("--namespace", "-n", default="default", help="Namespace")
def experiments_create(name: str, description: str, namespace: str):
    """Create an experiment."""
    body = {"name": name, "namespace": namespace}
    if description:
        body["description"] = description

    resp = _request("post", "/v1/experiments", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Experiment '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    if description:
        console.print(f"  Description: {description}")


@experiments.command(name="list")
@click.option("--namespace", "-n", default="default", help="Namespace")
def experiments_list(namespace: str):
    """List experiments."""
    resp = _request("get", "/v1/experiments", params={"namespace": namespace})
    data = check_response(resp)
    items = data.get("experiments", data.get("items", []))

    table = Table(title="Experiments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Runs", style="green")
    table.add_column("Best Metric", style="yellow")
    table.add_column("Created", style="dim")

    for e in items:
        table.add_row(
            e.get("name", ""),
            str(e.get("run_count", 0)),
            str(e.get("best_metric", "-")),
            str(e.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No experiments found[/dim]")


@experiments.command(name="runs")
@click.argument("experiment")
@click.option(
    "--status",
    type=click.Choice(["running", "completed", "failed", "all"]),
    default="all",
)
def experiments_runs(experiment: str, status: str):
    """List runs in an experiment."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", f"/v1/experiments/{experiment}/runs", params=params)
    data = check_response(resp)
    items = data.get("runs", data.get("items", []))

    table = Table(title=f"Runs in '{experiment}'", box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Metrics", style="yellow")
    table.add_column("Duration", style="dim")

    for r in items:
        r_status = r.get("status", "unknown")
        style = {"running": "cyan", "completed": "green", "failed": "red"}.get(
            r_status, "white"
        )
        metrics = (
            json.dumps(r.get("metrics", {}), default=str)[:40]
            if r.get("metrics")
            else "-"
        )
        table.add_row(
            str(r.get("id", ""))[:16],
            f"[{style}]{r_status}[/{style}]",
            metrics,
            f"{r.get('duration_ms', '-')}ms" if r.get("duration_ms") else "-",
        )

    console.print(table)
    if not items:
        console.print("[dim]No runs found[/dim]")


@experiments.command(name="compare")
@click.argument("run_ids", nargs=-1, required=True)
def experiments_compare(run_ids: tuple):
    """Compare experiment runs."""
    resp = _request("post", "/v1/experiments/compare", json={"run_ids": list(run_ids)})
    data = check_response(resp)

    console.print(f"[cyan]Comparing {len(run_ids)} runs...[/cyan]")
    table = Table(title="Run Comparison", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    for run_id in run_ids:
        table.add_column(run_id[:8], style="white")

    for metric in data.get("metrics", []):
        row = [metric.get("name", "")]
        for run_id in run_ids:
            row.append(str(metric.get("values", {}).get(run_id, "-")))
        table.add_row(*row)

    console.print(table)


@experiments.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def experiments_delete(name: str, force: bool):
    """Delete an experiment."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete experiment '{name}' and all runs?[/red]"):
            return

    resp = _request("delete", f"/v1/experiments/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Experiment '{name}' deleted")


# ============================================================================
# Hyperparameter Tuning (Katib-style)
# ============================================================================


@ml_group.group()
def tune():
    """Hyperparameter tuning (Katib-style AutoML)."""
    pass


@tune.command(name="create")
@click.argument("name")
@click.option("--experiment", "-e", required=True, help="Parent experiment")
@click.option("--objective", "-o", required=True, help="Metric to optimize")
@click.option(
    "--goal", "-g", type=click.Choice(["minimize", "maximize"]), default="minimize"
)
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(["random", "grid", "bayesian", "hyperband", "tpe"]),
    default="bayesian",
)
@click.option("--max-trials", "-m", default=10, help="Maximum trials")
@click.option("--parallel-trials", "-p", default=2, help="Parallel trials")
@click.option("--config", "-c", help="Tuning config file (YAML)")
def tune_create(
    name: str,
    experiment: str,
    objective: str,
    goal: str,
    algorithm: str,
    max_trials: int,
    parallel_trials: int,
    config: str,
):
    """Create a hyperparameter tuning job.

    \b
    Examples:
      hanzo ml tune create hpo-1 -e my-exp -o val_loss --algorithm bayesian
      hanzo ml tune create grid-search -e exp -o accuracy -g maximize -a grid -m 100
      hanzo ml tune create custom -e exp -o f1 -c tuning.yaml
    """
    body = {
        "name": name,
        "experiment": experiment,
        "objective": objective,
        "goal": goal,
        "algorithm": algorithm,
        "max_trials": max_trials,
        "parallel_trials": parallel_trials,
    }
    if config:
        with open(config) as f:
            body["config"] = json.load(f)

    console.print(f"[cyan]Creating tuning job '{name}'...[/cyan]")
    resp = _request("post", "/v1/tune", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Tuning job created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Experiment: {experiment}")
    console.print(f"  Objective: {objective} ({goal})")
    console.print(f"  Algorithm: {algorithm}")
    console.print(f"  Max trials: {max_trials}")


@tune.command(name="list")
@click.option("--experiment", "-e", help="Filter by experiment")
def tune_list(experiment: str):
    """List tuning jobs."""
    params = {}
    if experiment:
        params["experiment"] = experiment

    resp = _request("get", "/v1/tune", params=params)
    data = check_response(resp)
    items = data.get("jobs", data.get("items", []))

    table = Table(title="Tuning Jobs", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Algorithm", style="white")
    table.add_column("Trials", style="green")
    table.add_column("Best", style="yellow")
    table.add_column("Status", style="dim")

    for j in items:
        j_status = j.get("status", "unknown")
        style = {"running": "cyan", "completed": "green", "failed": "red"}.get(
            j_status, "white"
        )
        table.add_row(
            j.get("name", ""),
            j.get("algorithm", "-"),
            f"{j.get('completed_trials', 0)}/{j.get('max_trials', 0)}",
            str(j.get("best_metric", "-")),
            f"[{style}]{j_status}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No tuning jobs found[/dim]")


@tune.command(name="trials")
@click.argument("name")
@click.option("--best", "-b", type=int, help="Show top N trials")
def tune_trials(name: str, best: int):
    """List trials in a tuning job."""
    params = {}
    if best:
        params["top"] = best

    resp = _request("get", f"/v1/tune/{name}/trials", params=params)
    data = check_response(resp)
    items = data.get("trials", data.get("items", []))

    table = Table(title=f"Trials for '{name}'", box=box.ROUNDED)
    table.add_column("Trial", style="cyan")
    table.add_column("Parameters", style="white")
    table.add_column("Metric", style="yellow")
    table.add_column("Status", style="dim")

    for t in items:
        params_str = json.dumps(t.get("parameters", {}), default=str)[:40]
        table.add_row(
            str(t.get("id", "")),
            params_str,
            str(t.get("metric", "-")),
            t.get("status", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No trials found[/dim]")


@tune.command(name="best")
@click.argument("name")
def tune_best(name: str):
    """Get best trial parameters."""
    resp = _request("get", f"/v1/tune/{name}/best")
    data = check_response(resp)

    console.print(f"[cyan]Best trial for '{name}':[/cyan]")
    if data.get("parameters"):
        console.print(f"  Metric: {data.get('metric', '-')}")
        console.print(f"  Parameters:")
        for k, v in data["parameters"].items():
            console.print(f"    {k}: {v}")
    else:
        console.print("[dim]No trials completed[/dim]")


@tune.command(name="stop")
@click.argument("name")
def tune_stop(name: str):
    """Stop a tuning job."""
    resp = _request("post", f"/v1/tune/{name}/stop")
    check_response(resp)
    console.print(f"[green]✓[/green] Tuning job '{name}' stopped")


# ============================================================================
# Feature Store
# ============================================================================


@ml_group.group()
def features():
    """Manage feature store."""
    pass


@features.command(name="create")
@click.argument("name")
@click.option("--description", "-d", help="Feature group description")
@click.option("--schema", "-s", help="Schema file (YAML/JSON)")
@click.option("--source", help="Data source (table, stream)")
def features_create(name: str, description: str, schema: str, source: str):
    """Create a feature group."""
    body = {"name": name}
    if description:
        body["description"] = description
    if schema:
        with open(schema) as f:
            body["schema"] = json.load(f)
    if source:
        body["source"] = source

    resp = _request("post", "/v1/features", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Feature group '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")


@features.command(name="list")
def features_list():
    """List feature groups."""
    resp = _request("get", "/v1/features")
    data = check_response(resp)
    items = data.get("feature_groups", data.get("items", []))

    table = Table(title="Feature Groups", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Features", style="green")
    table.add_column("Entities", style="white")
    table.add_column("Updated", style="dim")

    for fg in items:
        table.add_row(
            fg.get("name", ""),
            str(fg.get("feature_count", 0)),
            fg.get("entity", "-"),
            str(fg.get("updated_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No feature groups found[/dim]")


@features.command(name="describe")
@click.argument("name")
def features_describe(name: str):
    """Show feature group details."""
    resp = _request("get", f"/v1/features/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Features:[/cyan] {data.get('feature_count', 0)}\n"
            f"[cyan]Entities:[/cyan] {data.get('entity', '-')}\n"
            f"[cyan]Source:[/cyan] {data.get('source', '-')}\n"
            f"[cyan]Updated:[/cyan] {str(data.get('updated_at', ''))[:19]}",
            title="Feature Group",
            border_style="cyan",
        )
    )


@features.command(name="ingest")
@click.argument("name")
@click.option(
    "--from", "source", required=True, help="Data source (file, table, stream)"
)
@click.option("--mode", type=click.Choice(["append", "overwrite"]), default="append")
def features_ingest(name: str, source: str, mode: str):
    """Ingest data into feature group."""
    console.print(f"[cyan]Ingesting into '{name}'...[/cyan]")
    resp = _request(
        "post", f"/v1/features/{name}/ingest", json={"source": source, "mode": mode}
    )
    data = check_response(resp)
    console.print(f"[green]✓[/green] Ingestion complete")
    console.print(f"  Records: {data.get('records', 0)}")


@features.command(name="get")
@click.argument("feature_group")
@click.option("--entity", "-e", required=True, help="Entity ID(s)")
@click.option("--features", "-f", help="Specific features (comma-separated)")
@click.option("--timestamp", "-t", help="Point-in-time (for historical features)")
def features_get(feature_group: str, entity: str, features: str, timestamp: str):
    """Get feature values."""
    params = {"entity": entity}
    if features:
        params["features"] = features
    if timestamp:
        params["timestamp"] = timestamp

    resp = _request("get", f"/v1/features/{feature_group}/values", params=params)
    data = check_response(resp)
    values = data.get("values", data.get("features", {}))

    console.print(f"[cyan]Features for '{entity}':[/cyan]")
    if values:
        for k, v in values.items():
            console.print(f"  {k}: {v}")
    else:
        console.print("[dim]No features found[/dim]")


@features.command(name="materialize")
@click.argument("name")
@click.option("--start", "-s", help="Start time")
@click.option("--end", "-e", help="End time")
def features_materialize(name: str, start: str, end: str):
    """Materialize features to online store."""
    body = {}
    if start:
        body["start"] = start
    if end:
        body["end"] = end

    console.print(f"[cyan]Materializing '{name}'...[/cyan]")
    resp = _request("post", f"/v1/features/{name}/materialize", json=body)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Features materialized to online store")
    console.print(f"  Records: {data.get('records', 0)}")


# ============================================================================
# Datasets
# ============================================================================


@ml_group.group()
def datasets():
    """Manage ML datasets."""
    pass


@datasets.command(name="create")
@click.argument("name")
@click.option("--from", "source", required=True, help="Source path or URI")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["csv", "parquet", "tfrecord", "jsonl"]),
    help="Data format",
)
@click.option("--split", help="Train/val/test split (e.g., 80:10:10)")
def datasets_create(name: str, source: str, fmt: str, split: str):
    """Create a versioned dataset."""
    body = {"name": name, "source": source}
    if fmt:
        body["format"] = fmt
    if split:
        body["split"] = split

    resp = _request("post", "/v1/datasets", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Dataset '{name}' created")
    console.print(f"  Version: {data.get('version', '1')}")
    console.print(f"  Source: {source}")
    if split:
        console.print(f"  Split: {split}")


@datasets.command(name="list")
def datasets_list():
    """List datasets."""
    resp = _request("get", "/v1/datasets")
    data = check_response(resp)
    items = data.get("datasets", data.get("items", []))

    table = Table(title="Datasets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Size", style="green")
    table.add_column("Format", style="yellow")
    table.add_column("Created", style="dim")

    for d in items:
        table.add_row(
            d.get("name", ""),
            str(d.get("version", "-")),
            d.get("size", "-"),
            d.get("format", "-"),
            str(d.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No datasets found[/dim]")


@datasets.command(name="versions")
@click.argument("name")
def datasets_versions(name: str):
    """List dataset versions."""
    resp = _request("get", f"/v1/datasets/{name}/versions")
    data = check_response(resp)
    items = data.get("versions", data.get("items", []))

    table = Table(title=f"Versions of '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Created", style="dim")

    for v in items:
        table.add_row(
            str(v.get("version", "")),
            v.get("size", "-"),
            str(v.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No versions found[/dim]")


# ============================================================================
# AutoML
# ============================================================================


@ml_group.group()
def automl():
    """Automated Machine Learning."""
    pass


@automl.command(name="create")
@click.argument("name")
@click.option("--dataset", "-d", required=True, help="Training dataset")
@click.option("--target", "-t", required=True, help="Target column")
@click.option(
    "--task",
    type=click.Choice(["classification", "regression", "forecasting", "nlp", "vision"]),
    required=True,
)
@click.option("--time-limit", default=3600, help="Time limit in seconds")
@click.option("--metric", "-m", help="Optimization metric")
def automl_create(
    name: str, dataset: str, target: str, task: str, time_limit: int, metric: str
):
    """Create an AutoML job.

    \b
    Examples:
      hanzo ml automl create fraud-detect -d transactions -t is_fraud --task classification
      hanzo ml automl create sales-forecast -d sales -t revenue --task forecasting
      hanzo ml automl create sentiment -d reviews -t label --task nlp --time-limit 7200
    """
    body = {
        "name": name,
        "dataset": dataset,
        "target": target,
        "task": task,
        "time_limit": time_limit,
    }
    if metric:
        body["metric"] = metric

    console.print(f"[cyan]Creating AutoML job '{name}'...[/cyan]")
    resp = _request("post", "/v1/automl", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] AutoML job started")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Dataset: {dataset}")
    console.print(f"  Target: {target}")
    console.print(f"  Task: {task}")
    console.print(f"  Time limit: {time_limit}s")


@automl.command(name="list")
def automl_list():
    """List AutoML jobs."""
    resp = _request("get", "/v1/automl")
    data = check_response(resp)
    items = data.get("jobs", data.get("items", []))

    table = Table(title="AutoML Jobs", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Best Model", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Status", style="dim")

    for j in items:
        j_status = j.get("status", "unknown")
        style = {"running": "cyan", "completed": "green", "failed": "red"}.get(
            j_status, "white"
        )
        table.add_row(
            j.get("name", ""),
            j.get("task", "-"),
            j.get("best_model", "-"),
            str(j.get("best_metric", "-")),
            f"[{style}]{j_status}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No AutoML jobs found[/dim]")


@automl.command(name="status")
@click.argument("name")
def automl_status(name: str):
    """Show AutoML job status."""
    resp = _request("get", f"/v1/automl/{name}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    status_style = {"running": "cyan", "completed": "green", "failed": "red"}.get(
        status, "yellow"
    )

    console.print(
        Panel(
            f"[cyan]Job:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{status}[/{status_style}]\n"
            f"[cyan]Progress:[/cyan] {data.get('progress', 0)}%\n"
            f"[cyan]Models tried:[/cyan] {data.get('models_tried', 0)}\n"
            f"[cyan]Best so far:[/cyan] {data.get('best_metric', '-')}\n"
            f"[cyan]Time remaining:[/cyan] {data.get('time_remaining', '-')}",
            title="AutoML Status",
            border_style="cyan",
        )
    )


@automl.command(name="leaderboard")
@click.argument("name")
@click.option("--top", "-n", default=10, help="Show top N models")
def automl_leaderboard(name: str, top: int):
    """Show AutoML leaderboard."""
    resp = _request("get", f"/v1/automl/{name}/leaderboard", params={"top": top})
    data = check_response(resp)
    items = data.get("models", data.get("items", []))

    table = Table(title=f"Leaderboard for '{name}'", box=box.ROUNDED)
    table.add_column("Rank", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Metric", style="green")
    table.add_column("Training Time", style="dim")

    for i, m in enumerate(items, 1):
        table.add_row(
            str(i),
            m.get("model", "-"),
            str(m.get("metric", "-")),
            f"{m.get('training_time_s', '-')}s" if m.get("training_time_s") else "-",
        )

    console.print(table)
    if not items:
        console.print("[dim]No models trained yet[/dim]")


@automl.command(name="deploy")
@click.argument("name")
@click.option("--model", "-m", help="Specific model (default: best)")
@click.option("--endpoint", "-e", help="Endpoint name")
def automl_deploy(name: str, model: str, endpoint: str):
    """Deploy best AutoML model."""
    body = {}
    if model:
        body["model"] = model
    if endpoint:
        body["endpoint"] = endpoint

    console.print(f"[cyan]Deploying best model from '{name}'...[/cyan]")
    resp = _request("post", f"/v1/automl/{name}/deploy", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Model deployed")
    console.print(f"  Endpoint: {data.get('endpoint', '-')}")
    console.print(f"  Model: {data.get('model', '-')}")
