"""Streamlit UI for running and viewing PDBench experiments."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from pdbench.core.logging import load_manifest, load_rounds_jsonl
from pdbench.core.types import (
    Action,
    AgentRef,
    ConditionConfig,
    ExperimentConfig,
    FullExperimentConfig,
    GameConfig,
    HorizonConfig,
    MetricsConfig,
    PayoffMatrixConfig,
    RunConfig,
)
from pdbench.runners.run_experiment import run_experiment
from pdbench.storage.aggregate import load_aggregates


# =============================================================================
# Constants
# =============================================================================

POLICY_AGENTS = ["ALLC", "ALLD", "TFT", "GRIM", "GTFT", "WSLS"]

CREWAI_AGENTS = ["strategic_cooperator", "ruthless_optimizer", "adaptive_diplomat"]

ALL_AGENTS = POLICY_AGENTS + ["MockLLM"] + CREWAI_AGENTS

AGENT_DESCRIPTIONS = {
    "ALLC": ("Always Cooperate", "🕊️", "Always plays C. Naive but hopeful."),
    "ALLD": ("Always Defect", "😈", "Always plays D. Pure exploitation."),
    "TFT": ("Tit-for-Tat", "🪞", "Starts C, then copies opponent's last move."),
    "GRIM": ("Grim Trigger", "💀", "Cooperates until betrayed, then defects forever."),
    "GTFT": ("Generous TFT", "😇", "Like TFT, but sometimes forgives."),
    "WSLS": ("Win-Stay Lose-Shift", "🎰", "Repeats action if it worked, switches if not."),
    "MockLLM": ("Mock LLM", "🤖", "Simulated LLM agent (always cooperates)."),
    "strategic_cooperator": ("Strategic Cooperator", "🧠", "CrewAI LLM focused on mutual benefit."),
    "ruthless_optimizer": ("Ruthless Optimizer", "🦈", "CrewAI LLM focused on self-interest."),
    "adaptive_diplomat": ("Adaptive Diplomat", "🕊️", "CrewAI LLM that reads opponent behavior."),
}

ACTION_COLORS = {"C": "#4CAF50", "D": "#F44336"}  # Green for cooperate, red for defect
ACTION_EMOJI = {"C": "🤝", "D": "🗡️"}


# =============================================================================
# Helper Functions
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PDBench Streamlit Viewer")
    parser.add_argument("--run-dir", type=Path, help="Path to run directory")
    # Handle Streamlit's extra arguments gracefully
    args, _ = parser.parse_known_args()
    return args


def load_run_data(run_dir: Path) -> tuple[dict, list[dict], pd.DataFrame]:
    """Load all data from a run directory."""
    manifest = load_manifest(run_dir / "run_manifest.json")
    rounds = load_rounds_jsonl(run_dir / "rounds.jsonl")
    aggregates = load_aggregates(run_dir)
    return manifest, rounds, aggregates


def build_agent_ref(agent_name: str) -> AgentRef:
    """Build an AgentRef for a given agent name."""
    if agent_name in CREWAI_AGENTS:
        return AgentRef(
            ref="agents/crewai_base.yaml",
            overrides={"agent_key": agent_name},
        )
    elif agent_name == "MockLLM":
        return AgentRef(ref="agents/llm_default.yaml", overrides={})
    else:
        return AgentRef(ref="agents/policies.yaml", overrides={"policy": agent_name})


def get_project_root() -> Path:
    """Get the project root directory."""
    # Navigate from src/pdbench/ui to project root
    return Path(__file__).parent.parent.parent.parent


def get_available_runs() -> list[Path]:
    """Get list of available run directories."""
    runs_dir = get_project_root() / "data" / "runs"
    if not runs_dir.exists():
        return []
    return sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)


# =============================================================================
# Visualization Components
# =============================================================================

def render_agent_card(agent_name: str, side: str = "left") -> None:
    """Render an agent card with emoji and description."""
    full_name, emoji, desc = AGENT_DESCRIPTIONS.get(
        agent_name, (agent_name, "🤖", "Unknown agent")
    )
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; border-radius: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; margin: 5px;">
        <div style="font-size: 48px;">{emoji}</div>
        <div style="font-size: 18px; font-weight: bold;">{full_name}</div>
        <div style="font-size: 12px; opacity: 0.8;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)


def render_action_display(action_a: str, action_b: str, payoff_a: int, payoff_b: int) -> None:
    """Render a single round's actions with visual feedback."""
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        color = ACTION_COLORS[action_a]
        emoji = ACTION_EMOJI[action_a]
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px;
                    background-color: {color}; color: white;">
            <div style="font-size: 36px;">{emoji}</div>
            <div style="font-size: 24px; font-weight: bold;">{action_a}</div>
            <div style="font-size: 18px;">+{payoff_a} points</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; font-size: 24px;">
            ⚔️
        </div>
        """, unsafe_allow_html=True)

    with col3:
        color = ACTION_COLORS[action_b]
        emoji = ACTION_EMOJI[action_b]
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px;
                    background-color: {color}; color: white;">
            <div style="font-size: 36px;">{emoji}</div>
            <div style="font-size: 24px; font-weight: bold;">{action_b}</div>
            <div style="font-size: 18px;">+{payoff_b} points</div>
        </div>
        """, unsafe_allow_html=True)


def render_game_history_visual(rounds_df: pd.DataFrame, max_display: int = 50) -> None:
    """Render a visual timeline of the game using colored blocks."""
    if rounds_df.empty:
        return

    # Limit display for performance
    display_df = rounds_df.head(max_display)

    # Build visual using emoji (more reliable than HTML in Streamlit)
    a_line = ""
    b_line = ""

    for _, row in display_df.iterrows():
        a_emoji = "🟢" if row["agent_a_action"] == "C" else "🔴"
        b_emoji = "🟢" if row["agent_b_action"] == "C" else "🔴"
        a_line += a_emoji
        b_line += b_emoji

    st.text(f"A: {a_line}")
    st.text(f"B: {b_line}")
    st.caption("🟢 = Cooperate (C), 🔴 = Defect (D)")


def render_payoff_matrix_visual() -> None:
    """Render the payoff matrix as a visual table."""
    st.markdown("""
    <table style="width: 100%; text-align: center; border-collapse: collapse;">
        <tr>
            <th style="border: 1px solid #ddd; padding: 8px;"></th>
            <th style="border: 1px solid #ddd; padding: 8px; background: #4CAF50; color: white;">Opponent C</th>
            <th style="border: 1px solid #ddd; padding: 8px; background: #F44336; color: white;">Opponent D</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background: #4CAF50; color: white;"><b>You C</b></td>
            <td style="border: 1px solid #ddd; padding: 8px;">3, 3 ✅</td>
            <td style="border: 1px solid #ddd; padding: 8px;">0, 5 😢</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background: #F44336; color: white;"><b>You D</b></td>
            <td style="border: 1px solid #ddd; padding: 8px;">5, 0 😈</td>
            <td style="border: 1px solid #ddd; padding: 8px;">1, 1 💀</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)


# =============================================================================
# Tab: Run Experiment
# =============================================================================

def render_run_experiment_tab() -> None:
    """Render the experiment configuration and execution tab."""
    st.header("🧪 Run New Experiment")

    # Two columns for agent selection
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Agent A")
        agent_a_type = st.selectbox(
            "Strategy",
            ALL_AGENTS,
            key="agent_a",
            help="Select the strategy for Agent A"
        )
        render_agent_card(agent_a_type)

    with col2:
        st.subheader("Agent B")
        agent_b_type = st.selectbox(
            "Strategy",
            ALL_AGENTS,
            index=1,  # Default to ALLD
            key="agent_b",
            help="Select the strategy for Agent B"
        )
        render_agent_card(agent_b_type)

    st.divider()

    # Game configuration
    st.subheader("⚙️ Game Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        horizon_type = st.radio(
            "Horizon Type",
            ["Fixed", "Geometric (Random)"],
            help="Fixed = exact number of rounds. Geometric = each round has a chance to be the last."
        )

    with col2:
        if horizon_type == "Fixed":
            n_rounds = st.slider(
                "Number of Rounds",
                min_value=5,
                max_value=200,
                value=50,
                step=5,
                help="Exact number of rounds to play"
            )
            stop_prob = 0.0
        else:
            stop_prob = st.slider(
                "Stop Probability",
                min_value=0.01,
                max_value=0.20,
                value=0.02,
                step=0.01,
                format="%.2f",
                help="Probability of game ending after each round"
            )
            expected_rounds = int(1 / stop_prob) if stop_prob > 0 else 100
            st.info(f"Expected ~{expected_rounds} rounds (varies each game)")
            n_rounds = 500  # Max rounds for geometric

    with col3:
        replicates = st.slider(
            "Replicates",
            min_value=1,
            max_value=20,
            value=3,
            help="Number of times to repeat the experiment"
        )

    st.divider()

    # Payoff matrix (collapsible)
    with st.expander("📊 Payoff Matrix (Default PD)"):
        render_payoff_matrix_visual()
        st.caption("(You, Opponent) payoffs for each action combination")

    st.divider()

    # Run button
    run_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = get_project_root() / "data" / "runs" / run_id

    col1, col2 = st.columns([1, 3])
    with col1:
        run_button = st.button("🚀 Run Experiment", type="primary", use_container_width=True)
    with col2:
        st.caption(f"Output will be saved to: `{output_dir}`")

    if run_button:
        with st.spinner("Running experiment..."):
            try:
                # Build config
                config = FullExperimentConfig(
                    run=RunConfig(
                        run_id=run_id,
                        seed=int(time.time()),
                        output_dir=str(output_dir),
                        store_prompts=True,
                        store_raw_responses=True,
                    ),
                    game=GameConfig(),
                    horizon=HorizonConfig(
                        type="fixed" if horizon_type == "Fixed" else "geometric",
                        n_rounds=n_rounds,
                        stop_prob=stop_prob,
                    ),
                    experiment=ExperimentConfig(
                        replicates=replicates,
                        conditions=[
                            ConditionConfig(
                                name=f"{agent_a_type}_vs_{agent_b_type}",
                                agent_a=build_agent_ref(agent_a_type),
                                agent_b=build_agent_ref(agent_b_type),
                            ),
                        ],
                    ),
                    metrics=MetricsConfig(),
                )

                # Run experiment
                result_dir = run_experiment(
                    config=config,
                    config_base_path=get_project_root(),
                    replicates_override=replicates,
                )

                st.success(f"✅ Experiment complete! Results saved to `{result_dir}`")
                st.balloons()

                # Store in session state for immediate viewing
                st.session_state["last_run_dir"] = result_dir
                st.session_state["show_results"] = True

                # Show quick results
                st.subheader("📈 Quick Results")
                manifest, rounds, aggregates = load_run_data(result_dir)

                # Show visual timeline
                rounds_df = pd.DataFrame(rounds)
                st.write("**Game Timeline (first replicate):**")
                first_rep = rounds_df[rounds_df["replicate"] == 0]
                render_game_history_visual(first_rep)

                # Show metrics
                col1, col2, col3, col4 = st.columns(4)
                avg_metrics = aggregates.mean(numeric_only=True)

                with col1:
                    st.metric("Avg Rounds", f"{avg_metrics['total_rounds']:.0f}")
                with col2:
                    st.metric("A Coop Rate", f"{avg_metrics['agent_a_cooperation_rate']:.1%}")
                with col3:
                    st.metric("B Coop Rate", f"{avg_metrics['agent_b_cooperation_rate']:.1%}")
                with col4:
                    st.metric("A Total Payoff", f"{avg_metrics['agent_a_total_payoff']:.0f}")

            except Exception as e:
                st.error(f"❌ Experiment failed: {e}")
                import traceback
                st.code(traceback.format_exc())


# =============================================================================
# Tab: View Results
# =============================================================================

def render_view_results_tab() -> None:
    """Render the results viewer tab."""
    st.header("📊 View Results")

    # Select run directory
    available_runs = get_available_runs()

    if not available_runs:
        st.warning("No experiment runs found. Run an experiment first!")
        return

    # Check for last run in session state
    default_idx = 0
    if "last_run_dir" in st.session_state:
        try:
            default_idx = available_runs.index(st.session_state["last_run_dir"])
        except ValueError:
            pass

    run_dir = st.selectbox(
        "Select Run",
        available_runs,
        index=default_idx,
        format_func=lambda x: x.name,
    )

    if not run_dir or not run_dir.exists():
        st.error("Run directory not found")
        return

    # Load data
    try:
        manifest, rounds, aggregates = load_run_data(run_dir)
    except Exception as e:
        st.error(f"Failed to load run data: {e}")
        return

    # Run info
    with st.expander("ℹ️ Run Information", expanded=False):
        st.write(f"**Run ID:** {manifest['run_id']}")
        st.write(f"**Config Hash:** {manifest['config_hash']}")
        st.write(f"**Timestamp:** {manifest['environment']['timestamp_utc']}")

    # Get unique conditions and replicates
    rounds_df = pd.DataFrame(rounds)
    conditions = sorted(rounds_df["condition"].unique())
    replicates = sorted(rounds_df["replicate"].unique())

    # Selection
    col1, col2 = st.columns(2)
    with col1:
        selected_condition = st.selectbox("Condition", conditions)
    with col2:
        selected_replicate = st.selectbox("Replicate", replicates)

    # Filter data
    filtered_rounds = rounds_df[
        (rounds_df["condition"] == selected_condition)
        & (rounds_df["replicate"] == selected_replicate)
    ].sort_values("round_index")

    st.divider()

    # Visual game history
    st.subheader("🎮 Game Timeline")
    render_game_history_visual(filtered_rounds)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Actions Over Time")
        if not filtered_rounds.empty:
            actions_data = filtered_rounds[["round_index", "agent_a_action", "agent_b_action"]].copy()
            actions_data["Agent A"] = actions_data["agent_a_action"].map({"C": 1, "D": 0})
            actions_data["Agent B"] = actions_data["agent_b_action"].map({"C": 1, "D": 0})
            st.line_chart(actions_data.set_index("round_index")[["Agent A", "Agent B"]])
            st.caption("1 = Cooperate, 0 = Defect")

    with col2:
        st.subheader("Cumulative Payoffs")
        if not filtered_rounds.empty:
            payoff_data = filtered_rounds[["round_index", "agent_a_cum_payoff", "agent_b_cum_payoff"]].copy()
            payoff_data = payoff_data.rename(columns={
                "agent_a_cum_payoff": "Agent A",
                "agent_b_cum_payoff": "Agent B",
            })
            st.line_chart(payoff_data.set_index("round_index")[["Agent A", "Agent B"]])

    # Metrics
    st.subheader("📈 Metrics")
    selected_metrics = aggregates[
        (aggregates["condition"] == selected_condition)
        & (aggregates["replicate"] == selected_replicate)
    ]

    if not selected_metrics.empty:
        m = selected_metrics.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rounds", int(m["total_rounds"]))
            st.metric("Overall Coop", f"{m['overall_cooperation_rate']:.1%}")
        with col2:
            st.metric("A Coop Rate", f"{m['agent_a_cooperation_rate']:.1%}")
            st.metric("B Coop Rate", f"{m['agent_b_cooperation_rate']:.1%}")
        with col3:
            st.metric("A Payoff", int(m["agent_a_total_payoff"]))
            st.metric("B Payoff", int(m["agent_b_total_payoff"]))
        with col4:
            collapse = m["time_to_collapse"]
            st.metric("Time to Collapse", int(collapse) if pd.notna(collapse) else "Never")
            ret = m["agent_a_retaliation_rate"]
            st.metric("A Retaliation", f"{ret:.1%}" if pd.notna(ret) else "N/A")

    # Round details (collapsible)
    with st.expander("📋 Round Details"):
        st.dataframe(
            filtered_rounds[[
                "round_index", "agent_a_action", "agent_b_action",
                "agent_a_payoff", "agent_b_payoff",
                "agent_a_cum_payoff", "agent_b_cum_payoff",
            ]],
            use_container_width=True,
        )

    # Condition averages
    st.subheader("📊 Condition Averages (All Replicates)")
    condition_avgs = aggregates.groupby("condition").agg({
        "overall_cooperation_rate": "mean",
        "agent_a_cooperation_rate": "mean",
        "agent_b_cooperation_rate": "mean",
        "agent_a_total_payoff": "mean",
        "agent_b_total_payoff": "mean",
    }).round(3)
    st.dataframe(condition_avgs, use_container_width=True)


# =============================================================================
# Tab: Animated Replay
# =============================================================================

def render_replay_tab() -> None:
    """Render animated game replay."""
    st.header("🎬 Animated Replay")

    available_runs = get_available_runs()
    if not available_runs:
        st.warning("No experiment runs found. Run an experiment first!")
        return

    run_dir = st.selectbox(
        "Select Run",
        available_runs,
        format_func=lambda x: x.name,
        key="replay_run"
    )

    if not run_dir:
        return

    try:
        manifest, rounds, aggregates = load_run_data(run_dir)
    except Exception as e:
        st.error(f"Failed to load: {e}")
        return

    rounds_df = pd.DataFrame(rounds)
    conditions = sorted(rounds_df["condition"].unique())

    col1, col2, col3 = st.columns(3)
    with col1:
        condition = st.selectbox("Condition", conditions, key="replay_cond")
    with col2:
        replicate = st.selectbox(
            "Replicate",
            sorted(rounds_df[rounds_df["condition"] == condition]["replicate"].unique()),
            key="replay_rep"
        )
    with col3:
        speed = st.slider("Speed (ms)", 100, 1000, 300, 50)

    filtered = rounds_df[
        (rounds_df["condition"] == condition) &
        (rounds_df["replicate"] == replicate)
    ].sort_values("round_index")

    if filtered.empty:
        st.warning("No data for this selection")
        return

    # Parse agent names from condition
    agent_names = condition.split("_vs_")
    agent_a_name = agent_names[0] if len(agent_names) > 0 else "Agent A"
    agent_b_name = agent_names[1] if len(agent_names) > 1 else "Agent B"

    # Agent cards
    col1, col2 = st.columns(2)
    with col1:
        render_agent_card(agent_a_name)
    with col2:
        render_agent_card(agent_b_name)

    st.divider()

    # Replay controls
    if st.button("▶️ Play Replay", type="primary"):
        progress = st.progress(0)
        round_display = st.empty()
        action_display = st.empty()
        score_display = st.empty()
        history_display = st.empty()

        total_rounds = len(filtered)
        history_a = []
        history_b = []

        for i, (_, row) in enumerate(filtered.iterrows()):
            progress.progress((i + 1) / total_rounds)

            with round_display.container():
                st.subheader(f"Round {row['round_index'] + 1} of {total_rounds}")

            with action_display.container():
                render_action_display(
                    row["agent_a_action"],
                    row["agent_b_action"],
                    row["agent_a_payoff"],
                    row["agent_b_payoff"]
                )

            with score_display.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        f"{agent_a_name} Total",
                        row["agent_a_cum_payoff"],
                        delta=row["agent_a_payoff"]
                    )
                with col2:
                    st.metric(
                        f"{agent_b_name} Total",
                        row["agent_b_cum_payoff"],
                        delta=row["agent_b_payoff"]
                    )

            # Build history
            history_a.append(row["agent_a_action"])
            history_b.append(row["agent_b_action"])

            with history_display.container():
                st.caption("History (last 20 rounds):")
                recent_a = history_a[-20:]
                recent_b = history_b[-20:]

                html = '<div style="font-family: monospace;">'
                html += f'<div>A: {"".join(["🟢" if a == "C" else "🔴" for a in recent_a])}</div>'
                html += f'<div>B: {"".join(["🟢" if b == "C" else "🔴" for b in recent_b])}</div>'
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

            time.sleep(speed / 1000)

        st.success("🎉 Replay complete!")

        # Final summary
        final = filtered.iloc[-1]
        st.subheader("Final Results")
        col1, col2, col3 = st.columns(3)
        with col1:
            winner = agent_a_name if final["agent_a_cum_payoff"] > final["agent_b_cum_payoff"] else agent_b_name
            if final["agent_a_cum_payoff"] == final["agent_b_cum_payoff"]:
                winner = "Tie!"
            st.metric("Winner", winner)
        with col2:
            st.metric(f"{agent_a_name} Final Score", final["agent_a_cum_payoff"])
        with col3:
            st.metric(f"{agent_b_name} Final Score", final["agent_b_cum_payoff"])


# =============================================================================
# Tab: Tournament (Multi-strategy comparison)
# =============================================================================

def render_tournament_results(aggregates: pd.DataFrame) -> None:
    """Render tournament leaderboard and matchup breakdown from aggregates."""
    # Average across replicates per condition
    avg = aggregates.groupby("condition").agg({
        "agent_a_cooperation_rate": "mean",
        "agent_b_cooperation_rate": "mean",
        "agent_a_total_payoff": "mean",
        "agent_b_total_payoff": "mean",
        "overall_cooperation_rate": "mean",
        "time_to_collapse": "mean",
    }).round(2)

    # Extract unique agent names from conditions
    agent_a_names = set()
    agent_b_names = set()
    matchup_data = []
    for cond, row in avg.iterrows():
        parts = cond.split("_vs_")
        if len(parts) == 2:
            a_name, b_name = parts
            agent_a_names.add(a_name)
            agent_b_names.add(b_name)
            matchup_data.append({
                "Agent A": a_name,
                "Agent B": b_name,
                "A Coop Rate": row["agent_a_cooperation_rate"],
                "B Coop Rate": row["agent_b_cooperation_rate"],
                "A Payoff": row["agent_a_total_payoff"],
                "B Payoff": row["agent_b_total_payoff"],
                "Overall Coop": row["overall_cooperation_rate"],
                "Collapse": int(row["time_to_collapse"]) if pd.notna(row["time_to_collapse"]) else None,
            })

    # Leaderboard: total payoff per agent_a across all opponents
    st.subheader("🏅 Leaderboard")
    scores: dict[str, list[float]] = {}
    for m in matchup_data:
        scores.setdefault(m["Agent A"], []).append(m["A Payoff"])

    leaderboard_rows = []
    for agent, payoffs in sorted(scores.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        desc = AGENT_DESCRIPTIONS.get(agent, (agent, "🤖", ""))
        leaderboard_rows.append({
            "Agent": agent,
            "Emoji": desc[1],
            "Full Name": desc[0],
            "Avg Payoff": sum(payoffs) / len(payoffs),
            "Total Payoff": sum(payoffs),
            "Matches": len(payoffs),
        })

    for i, row in enumerate(leaderboard_rows):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
        st.markdown(
            f"{medal} {row['Emoji']} **{row['Full Name']}** (`{row['Agent']}`) — "
            f"**{row['Avg Payoff']:.1f}** avg payoff across {row['Matches']} opponents "
            f"({row['Total Payoff']:.0f} total)"
        )

    st.divider()

    # Matchup detail table
    st.subheader("📊 Matchup Breakdown")
    matchup_df = pd.DataFrame(matchup_data)
    matchup_df["Collapse"] = matchup_df["Collapse"].apply(lambda x: "Never" if x is None else str(int(x)))
    matchup_df["A Coop Rate"] = matchup_df["A Coop Rate"].apply(lambda x: f"{x:.0%}")
    matchup_df["B Coop Rate"] = matchup_df["B Coop Rate"].apply(lambda x: f"{x:.0%}")
    matchup_df["Overall Coop"] = matchup_df["Overall Coop"].apply(lambda x: f"{x:.0%}")
    matchup_df["A Payoff"] = matchup_df["A Payoff"].apply(lambda x: f"{x:.0f}")
    matchup_df["B Payoff"] = matchup_df["B Payoff"].apply(lambda x: f"{x:.0f}")
    st.dataframe(matchup_df, use_container_width=True, hide_index=True)

    # Payoff heatmap as a pivot table
    if len(agent_a_names) > 1 or len(agent_b_names) > 1:
        st.subheader("🗺️ Payoff Matrix (Agent A payoff)")
        raw_matchup_df = pd.DataFrame(matchup_data)
        pivot = raw_matchup_df.pivot_table(
            index="Agent A", columns="Agent B", values="A Payoff", aggfunc="mean"
        ).round(0)
        st.dataframe(pivot.style.background_gradient(cmap="RdYlGn", axis=None), use_container_width=True)

        st.subheader("🤝 Cooperation Heatmap (Agent A coop rate)")
        coop_pivot = raw_matchup_df.pivot_table(
            index="Agent A", columns="Agent B", values="A Coop Rate", aggfunc="mean"
        ).round(2)
        st.dataframe(
            coop_pivot.style.background_gradient(cmap="RdYlGn", axis=None, vmin=0, vmax=1)
                .format("{:.0%}"),
            use_container_width=True,
        )


def render_tournament_tab() -> None:
    """Render tournament mode - all strategies compete against each other."""
    st.header("🏆 Tournament Mode")

    # View saved tournament results
    tournament_runs = [
        d for d in get_available_runs()
        if d.name.startswith("tournament")
    ]

    if tournament_runs:
        st.subheader("📂 Saved Tournament Results")
        selected_run = st.selectbox(
            "Select a tournament run",
            tournament_runs,
            format_func=lambda x: x.name,
            key="tournament_saved_run",
        )
        if selected_run:
            try:
                _, _, aggregates = load_run_data(selected_run)
                render_tournament_results(aggregates)
            except Exception as e:
                st.error(f"Failed to load tournament: {e}")

        st.divider()

    st.subheader("🚀 Run New Tournament")
    st.info("Run a round-robin tournament where all strategies play against each other.")

    # Strategy selection
    selected_strategies = st.multiselect(
        "Select Strategies",
        ALL_AGENTS,
        default=["ALLC", "ALLD", "TFT", "GRIM"],
        help="Choose which strategies to include in the tournament"
    )

    if len(selected_strategies) < 2:
        st.warning("Select at least 2 strategies")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        n_rounds = st.slider("Rounds per Match", 10, 200, 50, key="tourn_rounds")
    with col2:
        replicates = st.slider("Replicates", 1, 10, 3, key="tourn_reps")
    with col3:
        horizon_type = st.radio("Horizon", ["Fixed", "Geometric"], key="tourn_horizon")

    if st.button("🚀 Run Tournament", type="primary"):
        # Build all matchups
        conditions = []
        for i, a in enumerate(selected_strategies):
            for b in selected_strategies[i:]:  # Include self-play
                conditions.append(
                    ConditionConfig(
                        name=f"{a}_vs_{b}",
                        agent_a=build_agent_ref(a),
                        agent_b=build_agent_ref(b),
                    )
                )

        run_id = f"tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = get_project_root() / "data" / "runs" / run_id

        config = FullExperimentConfig(
            run=RunConfig(
                run_id=run_id,
                seed=int(time.time()),
                output_dir=str(output_dir),
            ),
            game=GameConfig(),
            horizon=HorizonConfig(
                type="fixed" if horizon_type == "Fixed" else "geometric",
                n_rounds=n_rounds,
                stop_prob=0.02 if horizon_type == "Geometric" else 0.0,
            ),
            experiment=ExperimentConfig(replicates=replicates, conditions=conditions),
            metrics=MetricsConfig(),
        )

        with st.spinner(f"Running tournament with {len(conditions)} matchups..."):
            try:
                result_dir = run_experiment(config, get_project_root(), replicates)
                st.success(f"✅ Tournament complete!")
                st.session_state["last_run_dir"] = result_dir

                # Load and display results
                _, _, aggregates = load_run_data(result_dir)

                # Calculate total scores per strategy
                scores = {s: 0 for s in selected_strategies}
                for _, row in aggregates.iterrows():
                    parts = row["condition"].split("_vs_")
                    if len(parts) == 2:
                        a, b = parts
                        scores[a] = scores.get(a, 0) + row["agent_a_total_payoff"]
                        scores[b] = scores.get(b, 0) + row["agent_b_total_payoff"]

                # Average across replicates
                n_matches = (len(selected_strategies) + 1) * replicates  # Each plays everyone including self
                avg_scores = {k: v / n_matches for k, v in scores.items()}

                # Display leaderboard
                st.subheader("🏅 Leaderboard")
                leaderboard = pd.DataFrame([
                    {"Strategy": k, "Avg Score": v, "Emoji": AGENT_DESCRIPTIONS.get(k, (k, "🤖", ""))[1]}
                    for k, v in sorted(avg_scores.items(), key=lambda x: -x[1])
                ])

                for i, row in leaderboard.iterrows():
                    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
                    st.write(f"{medal} {row['Emoji']} **{row['Strategy']}**: {row['Avg Score']:.1f} avg points")

                # Matchup matrix
                st.subheader("📊 Matchup Results")
                st.dataframe(
                    aggregates.groupby("condition").agg({
                        "agent_a_total_payoff": "mean",
                        "agent_b_total_payoff": "mean",
                        "overall_cooperation_rate": "mean",
                    }).round(1),
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Tournament failed: {e}")


# =============================================================================
# Main App
# =============================================================================

def main() -> None:
    """Main Streamlit app."""
    st.set_page_config(
        page_title="PDBench",
        page_icon="🎮",
        layout="wide",
    )

    st.title("🎮 PDBench: Prisoner's Dilemma Benchmark")
    st.caption("Explore cooperation and defection strategies in the iterated Prisoner's Dilemma")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧪 Run Experiment",
        "📊 View Results",
        "🎬 Animated Replay",
        "🏆 Tournament"
    ])

    with tab1:
        render_run_experiment_tab()

    with tab2:
        render_view_results_tab()

    with tab3:
        render_replay_tab()

    with tab4:
        render_tournament_tab()

    # Footer
    st.divider()
    st.caption(
        "Inspired by [The Evolution of Trust](https://ncase.me/trust/) by Nicky Case | "
        "Built with Streamlit"
    )


if __name__ == "__main__":
    main()
