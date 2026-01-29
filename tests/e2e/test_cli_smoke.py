"""End-to-end smoke tests for CLI."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def config_path(project_root: Path) -> Path:
    """Get the experiment config path."""
    return project_root / "configs" / "experiment.yaml"


class TestCLISmoke:
    """Smoke tests for pdbench CLI."""

    def test_validate_command(self, config_path: Path) -> None:
        """Test pdbench validate command."""
        result = subprocess.run(
            [sys.executable, "-m", "pdbench.cli", "validate", str(config_path)],
            capture_output=True,
            text=True,
            cwd=str(config_path.parent.parent),
        )

        assert result.returncode == 0, f"Validate failed: {result.stderr}"
        assert "Config valid" in result.stdout

    def test_run_command(self, config_path: Path, project_root: Path) -> None:
        """Test pdbench run command with small replicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a modified config with temp output dir
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            config["run"]["output_dir"] = str(Path(tmpdir) / "test_run")
            config["run"]["run_id"] = "cli_smoke_test"

            # Write config to project's configs directory so agent refs work
            temp_config = project_root / "configs" / "test_config.yaml"
            with open(temp_config, "w") as f:
                yaml.dump(config, f)

            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pdbench.cli",
                        "run",
                        str(temp_config),
                        "--replicates",
                        "2",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(project_root),
                )

                assert result.returncode == 0, f"Run failed: {result.stderr}\n{result.stdout}"

                # Verify output files
                output_dir = Path(tmpdir) / "test_run"
                assert (output_dir / "run_manifest.json").exists()
                assert (output_dir / "rounds.jsonl").exists()
                assert (output_dir / "aggregates.parquet").exists()
            finally:
                # Clean up temp config
                if temp_config.exists():
                    temp_config.unlink()

    def test_validate_invalid_config(self, project_root: Path) -> None:
        """Test that validate fails on invalid config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid config
            invalid_config = Path(tmpdir) / "invalid.yaml"
            with open(invalid_config, "w") as f:
                f.write("invalid: yaml: content")

            result = subprocess.run(
                [sys.executable, "-m", "pdbench.cli", "validate", str(invalid_config)],
                capture_output=True,
                text=True,
                cwd=str(project_root),
            )

            assert result.returncode != 0

    def test_validate_missing_config(self, project_root: Path) -> None:
        """Test that validate fails on missing config."""
        result = subprocess.run(
            [sys.executable, "-m", "pdbench.cli", "validate", "nonexistent.yaml"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_no_files(self, config_path: Path, project_root: Path) -> None:
        """Test that dry-run doesn't create files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            config["run"]["output_dir"] = str(Path(tmpdir) / "dry_run")

            # Write config to project's configs directory so agent refs work
            temp_config = project_root / "configs" / "dry_config.yaml"
            with open(temp_config, "w") as f:
                yaml.dump(config, f)

            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pdbench.cli",
                        "run",
                        str(temp_config),
                        "--dry-run",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(project_root),
                )

                assert result.returncode == 0
                assert "Dry run" in result.stdout

                # No output files should be created
                output_dir = Path(tmpdir) / "dry_run"
                assert not (output_dir / "rounds.jsonl").exists()
            finally:
                # Clean up temp config
                if temp_config.exists():
                    temp_config.unlink()
