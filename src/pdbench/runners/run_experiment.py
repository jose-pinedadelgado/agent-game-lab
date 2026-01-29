"""Experiment runner: orchestrates replicates × conditions, writes artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pdbench.core.horizon import create_horizon
from pdbench.core.logging import (
    RoundLogger,
    compute_config_hash,
    write_manifest,
)
from pdbench.core.metrics import compute_metrics_for_replicate
from pdbench.core.payoff import PayoffMatrix
from pdbench.core.transcript import TranscriptBuilder
from pdbench.core.types import (
    Action,
    FullExperimentConfig,
    RoundResult,
)
from pdbench.runners.registry import AgentRegistry
from pdbench.storage.aggregate import write_aggregates


def run_single_game(
    agent_a: Any,
    agent_b: Any,
    payoff_matrix: PayoffMatrix,
    horizon: Any,
    transcript_builder: TranscriptBuilder,
    logger: RoundLogger,
    condition: str,
    replicate: int,
    config: FullExperimentConfig,
) -> list[dict[str, Any]]:
    """Run a single game between two agents.

    Returns list of round records for metrics computation.
    """
    # Reset agents and transcript
    agent_a.reset()
    agent_b.reset()
    transcript_builder.reset()
    horizon.reset()

    rounds: list[dict[str, Any]] = []
    cum_a = 0
    cum_b = 0
    round_index = 0

    while not horizon.should_stop(round_index):
        # Build observations for each agent
        obs_a = transcript_builder.build_observation(round_index + 1, "a")
        obs_b = transcript_builder.build_observation(round_index + 1, "b")

        # Get actions
        action_a_str = agent_a.act(obs_a)
        action_b_str = agent_b.act(obs_b)

        action_a = Action(action_a_str)
        action_b = Action(action_b_str)

        # Compute payoffs
        payoff_a, payoff_b = payoff_matrix.get_payoffs(action_a, action_b)
        cum_a += payoff_a
        cum_b += payoff_b

        # Create round result
        result = RoundResult(
            round_index=round_index,
            agent_a_action=action_a,
            agent_b_action=action_b,
            agent_a_payoff=payoff_a,
            agent_b_payoff=payoff_b,
            agent_a_cum_payoff=cum_a,
            agent_b_cum_payoff=cum_b,
        )
        transcript_builder.add_round(result)

        # Get prompts and raw responses if available
        prompts = None
        raw_responses = None
        if config.run.store_prompts:
            prompts = {}
            if hasattr(agent_a, "last_prompts") and agent_a.last_prompts:
                prompts["agent_a"] = agent_a.last_prompts
            if hasattr(agent_b, "last_prompts") and agent_b.last_prompts:
                prompts["agent_b"] = agent_b.last_prompts

        if config.run.store_raw_responses:
            raw_responses = {}
            if hasattr(agent_a, "last_raw_response") and agent_a.last_raw_response:
                raw_responses["agent_a"] = agent_a.last_raw_response
            if hasattr(agent_b, "last_raw_response") and agent_b.last_raw_response:
                raw_responses["agent_b"] = agent_b.last_raw_response

        # Log the round
        logger.log_round(
            condition=condition,
            replicate=replicate,
            round_index=round_index,
            agent_a_action=action_a,
            agent_b_action=action_b,
            agent_a_payoff=payoff_a,
            agent_b_payoff=payoff_b,
            agent_a_cum_payoff=cum_a,
            agent_b_cum_payoff=cum_b,
            horizon_type=horizon.horizon_type,
            fixed_n=horizon.total_rounds if horizon.horizon_type == "fixed" else None,
            stop_prob=config.horizon.stop_prob if horizon.horizon_type == "geometric" else None,
            prompts=prompts if prompts else None,
            raw_responses=raw_responses if raw_responses else None,
        )

        # Store round data for metrics
        rounds.append({
            "round_index": round_index,
            "agent_a_action": action_a.value,
            "agent_b_action": action_b.value,
            "agent_a_payoff": payoff_a,
            "agent_b_payoff": payoff_b,
            "agent_a_cum_payoff": cum_a,
            "agent_b_cum_payoff": cum_b,
        })

        round_index += 1

    return rounds


def run_experiment(
    config: FullExperimentConfig,
    config_base_path: Path,
    replicates_override: int | None = None,
    dry_run: bool = False,
) -> Path:
    """Run the full experiment.

    Args:
        config: Full experiment configuration.
        config_base_path: Base path for config files.
        replicates_override: Override the number of replicates.
        dry_run: If True, validate but don't run.

    Returns:
        Path to the output directory.
    """
    output_dir = Path(config.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print(f"Dry run: would write to {output_dir}")
        return output_dir

    # Write manifest
    config_dict = config.model_dump()
    config_hash = compute_config_hash(config_dict)
    write_manifest(output_dir, config.run.run_id, config_dict, config_hash)

    # Create logger
    logger = RoundLogger(output_dir, config.run.run_id)

    # Create registry
    registry = AgentRegistry(config_base_path)

    # Create payoff matrix
    payoff_matrix = PayoffMatrix(config.game.payoff_matrix)

    # Determine replicates
    replicates = replicates_override or config.experiment.replicates

    # Store all metrics for aggregation
    all_metrics = []

    # Run all conditions × replicates
    for condition in config.experiment.conditions:
        print(f"Running condition: {condition.name}")

        for replicate in range(replicates):
            print(f"  Replicate {replicate + 1}/{replicates}")

            # Create agents with replicate-specific seed
            seed = config.run.seed + replicate
            agent_a = registry.create_agent(condition.agent_a, seed=seed)
            agent_b = registry.create_agent(condition.agent_b, seed=seed + 1000)

            # Create horizon
            horizon = create_horizon(config.horizon, seed=seed)

            # Create transcript builder
            transcript = TranscriptBuilder(
                history_window=10,  # Default, can be made configurable
                include_cumulative_totals=True,
                payoff_matrix=payoff_matrix.to_dict(),
                horizon_type=config.horizon.type,
                total_rounds=config.horizon.n_rounds if config.horizon.type == "fixed" else None,
            )

            # Run the game
            rounds = run_single_game(
                agent_a=agent_a,
                agent_b=agent_b,
                payoff_matrix=payoff_matrix,
                horizon=horizon,
                transcript_builder=transcript,
                logger=logger,
                condition=condition.name,
                replicate=replicate,
                config=config,
            )

            # Compute metrics
            metrics = compute_metrics_for_replicate(
                rounds=rounds,
                condition=condition.name,
                replicate=replicate,
                collapse_k=config.metrics.collapse.k,
                collapse_threshold=config.metrics.collapse.cooperation_threshold,
            )
            all_metrics.append(metrics)

    # Write aggregates
    write_aggregates(output_dir, all_metrics)

    print(f"Experiment complete. Output: {output_dir}")
    return output_dir
