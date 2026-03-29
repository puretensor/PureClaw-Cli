"""Shared fixtures for PureClaw-Cli tests."""

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_cli_module():
    """Import pureclaw-cli.py as 'pureclaw_cli' despite the hyphen."""
    spec = importlib.util.spec_from_file_location(
        "pureclaw_cli", REPO_ROOT / "pureclaw-cli.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pureclaw_cli"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Clear NEXUS_* env vars so they don't leak between tests."""
    monkeypatch.delenv("NEXUS_HOST", raising=False)
    monkeypatch.delenv("NEXUS_PORT", raising=False)
    monkeypatch.delenv("NEXUS_TOKEN", raising=False)


@pytest.fixture
def write_config(tmp_path):
    """Return a helper that writes a JSON config file to a temp path."""
    conf_path = tmp_path / "cli.conf"

    def _write(data: dict) -> Path:
        conf_path.write_text(json.dumps(data))
        return conf_path

    return _write


# Load the module once at import time so tests can reference it.
# Module-level globals (HOST/PORT/TOKEN) are set at load time, but
# individual tests re-call load_config() or instantiate NexusTerminal
# to test dynamic behaviour.
cli = _load_cli_module()
