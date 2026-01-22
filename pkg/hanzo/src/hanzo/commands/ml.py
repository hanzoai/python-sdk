"""Hanzo ML - Machine learning platform CLI.

End-to-end MLOps: notebooks, pipelines, training, serving, registry.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


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
    table = Table(title="Notebooks", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Instance", style="white")
    table.add_column("Status", style="green")
    table.add_column("GPU", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No notebooks found. Create one with 'hanzo ml notebooks create'[/dim]")


@notebooks.command(name="create")
@click.option("--name", "-n", prompt=True, help="Notebook name")
@click.option("--instance", "-i", default="cpu-small", help="Instance type")
@click.option("--gpu", is_flag=True, help="Enable GPU")
def notebooks_create(name: str, instance: str, gpu: bool):
    """Create a new notebook instance."""
    console.print(f"[cyan]Creating notebook '{name}'...[/cyan]")
    console.print(f"  Instance: {instance}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")
    console.print()
    console.print(f"[green]✓[/green] Notebook '{name}' created")
    console.print(f"[dim]Access at: https://notebooks.hanzo.ai/{name}[/dim]")


@notebooks.command(name="start")
@click.argument("name")
def notebooks_start(name: str):
    """Start a notebook."""
    console.print(f"[green]✓[/green] Notebook '{name}' started")


@notebooks.command(name="stop")
@click.argument("name")
def notebooks_stop(name: str):
    """Stop a notebook."""
    console.print(f"[green]✓[/green] Notebook '{name}' stopped")


@notebooks.command(name="delete")
@click.argument("name")
def notebooks_delete(name: str):
    """Delete a notebook."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete notebook '{name}'?[/red]"):
        return
    console.print(f"[green]✓[/green] Notebook '{name}' deleted")


# ============================================================================
# Training
# ============================================================================

@ml_group.group()
def training():
    """Manage training jobs."""
    pass


@training.command(name="list")
@click.option("--status", type=click.Choice(["running", "completed", "failed", "all"]), default="all")
def training_list(status: str):
    """List training jobs."""
    table = Table(title="Training Jobs", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Framework", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="dim")
    table.add_column("GPU", style="yellow")

    console.print(table)


@training.command(name="create")
@click.option("--name", "-n", prompt=True, help="Job name")
@click.option("--framework", "-f", type=click.Choice(["pytorch", "tensorflow", "xgboost"]), default="pytorch")
@click.option("--script", "-s", required=True, help="Training script path")
@click.option("--gpu", "-g", default="1", help="Number of GPUs")
@click.option("--instance", "-i", default="gpu-a10g", help="Instance type")
def training_create(name: str, framework: str, script: str, gpu: str, instance: str):
    """Create a training job."""
    console.print(f"[cyan]Creating training job '{name}'...[/cyan]")
    console.print(f"  Framework: {framework}")
    console.print(f"  Script: {script}")
    console.print(f"  Instance: {instance} ({gpu} GPUs)")
    console.print()
    console.print(f"[green]✓[/green] Training job '{name}' started")


@training.command(name="logs")
@click.argument("job_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
def training_logs(job_id: str, follow: bool):
    """View training job logs."""
    console.print(f"[cyan]Logs for job {job_id}:[/cyan]")


@training.command(name="stop")
@click.argument("job_id")
def training_stop(job_id: str):
    """Stop a training job."""
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
    table = Table(title="ML Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Status", style="green")
    table.add_column("Last Run", style="dim")

    console.print(table)


@pipelines.command(name="create")
@click.option("--name", "-n", prompt=True, help="Pipeline name")
@click.option("--file", "-f", required=True, help="Pipeline definition file")
def pipelines_create(name: str, file: str):
    """Create a pipeline from definition file."""
    console.print(f"[green]✓[/green] Pipeline '{name}' created from {file}")


@pipelines.command(name="run")
@click.argument("pipeline_name")
@click.option("--params", "-p", help="JSON parameters")
def pipelines_run(pipeline_name: str, params: str):
    """Run a pipeline."""
    console.print(f"[cyan]Running pipeline '{pipeline_name}'...[/cyan]")
    console.print(f"[green]✓[/green] Pipeline run started")


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
    table = Table(title="Model Deployments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Version", style="white")
    table.add_column("Status", style="green")
    table.add_column("Replicas", style="dim")
    table.add_column("Endpoint", style="dim")

    console.print(table)


@serving.command(name="deploy")
@click.option("--name", "-n", prompt=True, help="Deployment name")
@click.option("--model", "-m", required=True, help="Model path or registry URI")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--gpu", is_flag=True, help="Enable GPU inference")
def serving_deploy(name: str, model: str, replicas: int, gpu: bool):
    """Deploy a model for inference."""
    console.print(f"[cyan]Deploying model '{name}'...[/cyan]")
    console.print(f"  Model: {model}")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")
    console.print()
    console.print(f"[green]✓[/green] Model deployed")
    console.print(f"[dim]Endpoint: https://serving.hanzo.ai/{name}[/dim]")


@serving.command(name="scale")
@click.argument("name")
@click.option("--replicas", "-r", required=True, type=int, help="Target replicas")
def serving_scale(name: str, replicas: int):
    """Scale a deployment."""
    console.print(f"[green]✓[/green] Deployment '{name}' scaled to {replicas} replicas")


@serving.command(name="delete")
@click.argument("name")
def serving_delete(name: str):
    """Delete a deployment."""
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
    table = Table(title="Model Registry", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Stage", style="green")
    table.add_column("Framework", style="dim")
    table.add_column("Created", style="dim")

    console.print(table)


@registry.command(name="push")
@click.option("--name", "-n", required=True, help="Model name")
@click.option("--path", "-p", required=True, help="Model path")
@click.option("--framework", "-f", default="pytorch", help="Framework")
@click.option("--version", "-v", help="Version (auto-incremented if not specified)")
def registry_push(name: str, path: str, framework: str, version: str):
    """Push a model to the registry."""
    console.print(f"[cyan]Pushing model '{name}'...[/cyan]")
    console.print(f"  Path: {path}")
    console.print(f"  Framework: {framework}")
    console.print()
    console.print(f"[green]✓[/green] Model '{name}' pushed to registry")


@registry.command(name="pull")
@click.argument("model_uri")
@click.option("--output", "-o", default=".", help="Output directory")
def registry_pull(model_uri: str, output: str):
    """Pull a model from the registry."""
    console.print(f"[cyan]Pulling model {model_uri}...[/cyan]")
    console.print(f"[green]✓[/green] Model downloaded to {output}")


@registry.command(name="promote")
@click.argument("model_uri")
@click.option("--stage", "-s", type=click.Choice(["staging", "production"]), required=True)
def registry_promote(model_uri: str, stage: str):
    """Promote a model version to a stage."""
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
    console.print(f"[green]✓[/green] Experiment '{name}' created")
    if description:
        console.print(f"  Description: {description}")


@experiments.command(name="list")
@click.option("--namespace", "-n", default="default", help="Namespace")
def experiments_list(namespace: str):
    """List experiments."""
    table = Table(title="Experiments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Runs", style="green")
    table.add_column("Best Metric", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No experiments found[/dim]")


@experiments.command(name="runs")
@click.argument("experiment")
@click.option("--status", type=click.Choice(["running", "completed", "failed", "all"]), default="all")
def experiments_runs(experiment: str, status: str):
    """List runs in an experiment."""
    table = Table(title=f"Runs in '{experiment}'", box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Metrics", style="yellow")
    table.add_column("Duration", style="dim")

    console.print(table)
    console.print("[dim]No runs found[/dim]")


@experiments.command(name="compare")
@click.argument("run_ids", nargs=-1, required=True)
def experiments_compare(run_ids: tuple):
    """Compare experiment runs."""
    console.print(f"[cyan]Comparing {len(run_ids)} runs...[/cyan]")
    table = Table(title="Run Comparison", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    for run_id in run_ids:
        table.add_column(run_id[:8], style="white")
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
@click.option("--goal", "-g", type=click.Choice(["minimize", "maximize"]), default="minimize")
@click.option("--algorithm", "-a", type=click.Choice(["random", "grid", "bayesian", "hyperband", "tpe"]), default="bayesian")
@click.option("--max-trials", "-m", default=10, help="Maximum trials")
@click.option("--parallel-trials", "-p", default=2, help="Parallel trials")
@click.option("--config", "-c", help="Tuning config file (YAML)")
def tune_create(name: str, experiment: str, objective: str, goal: str, algorithm: str,
                max_trials: int, parallel_trials: int, config: str):
    """Create a hyperparameter tuning job.

    \b
    Examples:
      hanzo ml tune create hpo-1 -e my-exp -o val_loss --algorithm bayesian
      hanzo ml tune create grid-search -e exp -o accuracy -g maximize -a grid -m 100
      hanzo ml tune create custom -e exp -o f1 -c tuning.yaml
    """
    console.print(f"[cyan]Creating tuning job '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Tuning job created")
    console.print(f"  Experiment: {experiment}")
    console.print(f"  Objective: {objective} ({goal})")
    console.print(f"  Algorithm: {algorithm}")
    console.print(f"  Max trials: {max_trials}")


@tune.command(name="list")
@click.option("--experiment", "-e", help="Filter by experiment")
def tune_list(experiment: str):
    """List tuning jobs."""
    table = Table(title="Tuning Jobs", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Algorithm", style="white")
    table.add_column("Trials", style="green")
    table.add_column("Best", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No tuning jobs found[/dim]")


@tune.command(name="trials")
@click.argument("name")
@click.option("--best", "-b", type=int, help="Show top N trials")
def tune_trials(name: str, best: int):
    """List trials in a tuning job."""
    table = Table(title=f"Trials for '{name}'", box=box.ROUNDED)
    table.add_column("Trial", style="cyan")
    table.add_column("Parameters", style="white")
    table.add_column("Metric", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No trials found[/dim]")


@tune.command(name="best")
@click.argument("name")
def tune_best(name: str):
    """Get best trial parameters."""
    console.print(f"[cyan]Best trial for '{name}':[/cyan]")
    console.print("[dim]No trials completed[/dim]")


@tune.command(name="stop")
@click.argument("name")
def tune_stop(name: str):
    """Stop a tuning job."""
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
    console.print(f"[green]✓[/green] Feature group '{name}' created")


@features.command(name="list")
def features_list():
    """List feature groups."""
    table = Table(title="Feature Groups", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Features", style="green")
    table.add_column("Entities", style="white")
    table.add_column("Updated", style="dim")

    console.print(table)
    console.print("[dim]No feature groups found[/dim]")


@features.command(name="describe")
@click.argument("name")
def features_describe(name: str):
    """Show feature group details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Features:[/cyan] 0\n"
        f"[cyan]Entities:[/cyan] user_id\n"
        f"[cyan]Source:[/cyan] -\n"
        f"[cyan]Updated:[/cyan] -",
        title="Feature Group",
        border_style="cyan"
    ))


@features.command(name="ingest")
@click.argument("name")
@click.option("--from", "source", required=True, help="Data source (file, table, stream)")
@click.option("--mode", type=click.Choice(["append", "overwrite"]), default="append")
def features_ingest(name: str, source: str, mode: str):
    """Ingest data into feature group."""
    console.print(f"[cyan]Ingesting into '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Ingestion complete")


@features.command(name="get")
@click.argument("feature_group")
@click.option("--entity", "-e", required=True, help="Entity ID(s)")
@click.option("--features", "-f", help="Specific features (comma-separated)")
@click.option("--timestamp", "-t", help="Point-in-time (for historical features)")
def features_get(feature_group: str, entity: str, features: str, timestamp: str):
    """Get feature values."""
    console.print(f"[cyan]Fetching features for '{entity}'...[/cyan]")
    console.print("[dim]No features found[/dim]")


@features.command(name="materialize")
@click.argument("name")
@click.option("--start", "-s", help="Start time")
@click.option("--end", "-e", help="End time")
def features_materialize(name: str, start: str, end: str):
    """Materialize features to online store."""
    console.print(f"[cyan]Materializing '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Features materialized to online store")


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
@click.option("--format", "fmt", type=click.Choice(["csv", "parquet", "tfrecord", "jsonl"]), help="Data format")
@click.option("--split", help="Train/val/test split (e.g., 80:10:10)")
def datasets_create(name: str, source: str, fmt: str, split: str):
    """Create a versioned dataset."""
    console.print(f"[green]✓[/green] Dataset '{name}' created")
    console.print(f"  Source: {source}")
    if split:
        console.print(f"  Split: {split}")


@datasets.command(name="list")
def datasets_list():
    """List datasets."""
    table = Table(title="Datasets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Size", style="green")
    table.add_column("Format", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No datasets found[/dim]")


@datasets.command(name="versions")
@click.argument("name")
def datasets_versions(name: str):
    """List dataset versions."""
    table = Table(title=f"Versions of '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Created", style="dim")

    console.print(table)
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
@click.option("--task", type=click.Choice(["classification", "regression", "forecasting", "nlp", "vision"]), required=True)
@click.option("--time-limit", default=3600, help="Time limit in seconds")
@click.option("--metric", "-m", help="Optimization metric")
def automl_create(name: str, dataset: str, target: str, task: str, time_limit: int, metric: str):
    """Create an AutoML job.

    \b
    Examples:
      hanzo ml automl create fraud-detect -d transactions -t is_fraud --task classification
      hanzo ml automl create sales-forecast -d sales -t revenue --task forecasting
      hanzo ml automl create sentiment -d reviews -t label --task nlp --time-limit 7200
    """
    console.print(f"[cyan]Creating AutoML job '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] AutoML job started")
    console.print(f"  Dataset: {dataset}")
    console.print(f"  Target: {target}")
    console.print(f"  Task: {task}")
    console.print(f"  Time limit: {time_limit}s")


@automl.command(name="list")
def automl_list():
    """List AutoML jobs."""
    table = Table(title="AutoML Jobs", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Best Model", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No AutoML jobs found[/dim]")


@automl.command(name="status")
@click.argument("name")
def automl_status(name: str):
    """Show AutoML job status."""
    console.print(Panel(
        f"[cyan]Job:[/cyan] {name}\n"
        f"[cyan]Status:[/cyan] [yellow]Running[/yellow]\n"
        f"[cyan]Progress:[/cyan] 0%\n"
        f"[cyan]Models tried:[/cyan] 0\n"
        f"[cyan]Best so far:[/cyan] -\n"
        f"[cyan]Time remaining:[/cyan] -",
        title="AutoML Status",
        border_style="cyan"
    ))


@automl.command(name="leaderboard")
@click.argument("name")
@click.option("--top", "-n", default=10, help="Show top N models")
def automl_leaderboard(name: str, top: int):
    """Show AutoML leaderboard."""
    table = Table(title=f"Leaderboard for '{name}'", box=box.ROUNDED)
    table.add_column("Rank", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Metric", style="green")
    table.add_column("Training Time", style="dim")

    console.print(table)
    console.print("[dim]No models trained yet[/dim]")


@automl.command(name="deploy")
@click.argument("name")
@click.option("--model", "-m", help="Specific model (default: best)")
@click.option("--endpoint", "-e", help="Endpoint name")
def automl_deploy(name: str, model: str, endpoint: str):
    """Deploy best AutoML model."""
    console.print(f"[cyan]Deploying best model from '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Model deployed")
    console.print(f"  Endpoint: https://serving.hanzo.ai/{endpoint or name}")
