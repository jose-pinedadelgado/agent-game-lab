"""CLI for PDBench using Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from pdbench.core.types import FullExperimentConfig
from pdbench.runners.run_experiment import run_experiment
from pdbench.storage.aggregate import recompute_aggregates

app = typer.Typer(
    name="pdbench",
    help="Prisoner's Dilemma Benchmark for AI Agents",
    add_completion=False,
)


def get_config_base_path(config_path: Path) -> Path:
    """Get the base path for config file resolution."""
    # Go up from configs/ to project root
    return config_path.parent.parent


@app.command()
def validate(
    config_path: Annotated[Path, typer.Argument(help="Path to experiment config YAML")],
) -> None:
    """Validate an experiment configuration file."""
    if not config_path.exists():
        typer.echo(f"Error: Config file not found: {config_path}", err=True)
        raise typer.Exit(1)

    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        config = FullExperimentConfig(**raw_config)

        # Validate referenced files exist
        config_base = get_config_base_path(config_path)
        errors = []

        for condition in config.experiment.conditions:
            for agent_ref in [condition.agent_a, condition.agent_b]:
                ref_path = config_base / "configs" / agent_ref.ref
                if not ref_path.exists():
                    errors.append(f"Agent config not found: {ref_path}")
                    continue

                # Load agent config to check type-specific references
                with open(ref_path) as af:
                    agent_config = yaml.safe_load(af)
                # Apply overrides for validation
                merged = {**agent_config, **agent_ref.overrides}
                if merged.get("type") == "crewai" and merged.get("agents_file"):
                    agents_file_path = config_base / "configs" / merged["agents_file"]
                    if not agents_file_path.exists():
                        errors.append(
                            f"CrewAI agents file not found: {agents_file_path}"
                        )
                    elif merged.get("agent_key"):
                        with open(agents_file_path) as agf:
                            agents_data = yaml.safe_load(agf)
                        if merged["agent_key"] not in agents_data:
                            errors.append(
                                f"Agent key '{merged['agent_key']}' not found "
                                f"in {agents_file_path}"
                            )

        if errors:
            for err in errors:
                typer.echo(f"Error: {err}", err=True)
            raise typer.Exit(1)

        typer.echo(f"Config valid: {config_path}")
        typer.echo(f"  Run ID: {config.run.run_id}")
        typer.echo(f"  Conditions: {len(config.experiment.conditions)}")
        typer.echo(f"  Replicates: {config.experiment.replicates}")
        typer.echo(f"  Horizon: {config.horizon.type} ({config.horizon.n_rounds} rounds)")
        typer.echo(f"  Output: {config.run.output_dir}")

    except Exception as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def run(
    config_path: Annotated[Path, typer.Argument(help="Path to experiment config YAML")],
    replicates: Annotated[Optional[int], typer.Option("--replicates", "-r", help="Override number of replicates")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate without running")] = False,
) -> None:
    """Run an experiment from a configuration file."""
    if not config_path.exists():
        typer.echo(f"Error: Config file not found: {config_path}", err=True)
        raise typer.Exit(1)

    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        config = FullExperimentConfig(**raw_config)
        config_base = get_config_base_path(config_path)

        output_dir = run_experiment(
            config=config,
            config_base_path=config_base,
            replicates_override=replicates,
            dry_run=dry_run,
        )

        if not dry_run:
            typer.echo(f"Experiment complete. Output: {output_dir}")

    except Exception as e:
        typer.echo(f"Run error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def aggregate(
    run_dir: Annotated[Path, typer.Argument(help="Path to run output directory")],
    collapse_k: Annotated[int, typer.Option("--collapse-k", help="Window size for collapse metric")] = 10,
    collapse_threshold: Annotated[float, typer.Option("--collapse-threshold", help="Threshold for collapse metric")] = 0.2,
) -> None:
    """Recompute aggregated metrics from rounds JSONL (idempotent)."""
    if not run_dir.exists():
        typer.echo(f"Error: Run directory not found: {run_dir}", err=True)
        raise typer.Exit(1)

    rounds_path = run_dir / "rounds.jsonl"
    if not rounds_path.exists():
        typer.echo(f"Error: rounds.jsonl not found in: {run_dir}", err=True)
        raise typer.Exit(1)

    try:
        recompute_aggregates(
            output_dir=run_dir,
            collapse_k=collapse_k,
            collapse_threshold=collapse_threshold,
        )
        typer.echo(f"Aggregates recomputed: {run_dir / 'aggregates.parquet'}")

    except Exception as e:
        typer.echo(f"Aggregate error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def ui(
    run_dir: Annotated[Path, typer.Argument(help="Path to run output directory")],
) -> None:
    """Launch Streamlit viewer for a run directory."""
    if not run_dir.exists():
        typer.echo(f"Error: Run directory not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # Get the path to streamlit_app.py
    import pdbench.ui.streamlit_app as app_module
    app_path = Path(app_module.__file__).resolve()

    command = f"streamlit run {app_path} -- --run-dir {run_dir.resolve()}"
    typer.echo(f"To launch the UI, run:")
    typer.echo(f"  {command}")
    typer.echo()
    typer.echo("Or run directly:")

    import subprocess
    import sys

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path), "--", "--run-dir", str(run_dir.resolve())],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        typer.echo(f"Failed to launch Streamlit: {e}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("Streamlit not found. Install with: pip install streamlit", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
