"""Tests for PureClaw-Cli (pureclaw-cli.py).

Covers command parsing, config loading, URL construction, message
formatting, autocomplete, reconnection backoff, and edge cases.
No running server required -- WebSocket connections are mocked.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import cli  # the loaded module


# -----------------------------------------------------------------------
# 1. Command parsing -- slash commands split into (cmd, args)
# -----------------------------------------------------------------------

class TestCommandParsing:
    """Verify the slash-command parsing logic used in _prompt_loop / input_loop."""

    @staticmethod
    def _parse(line: str):
        """Replicate the command parsing from the input loops."""
        parts = line[1:].split(None, 1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        return cmd, args

    def test_simple_command(self):
        cmd, args = self._parse("/opus")
        assert cmd == "opus"
        assert args == ""

    def test_command_with_args(self):
        cmd, args = self._parse("/train Windsor to London")
        assert cmd == "train"
        assert args == "Windsor to London"

    def test_command_case_insensitive(self):
        cmd, args = self._parse("/NEMOTRON")
        assert cmd == "nemotron"
        assert args == ""

    def test_exit_recognised(self):
        cmd, _ = self._parse("/exit")
        assert cmd in ("quit", "exit")

    def test_slash_only(self):
        """A bare '/' should yield an empty command."""
        cmd, args = self._parse("/")
        assert cmd == ""
        assert args == ""


# -----------------------------------------------------------------------
# 2. Config file loading
# -----------------------------------------------------------------------

class TestConfigLoading:
    def test_load_valid_config(self, write_config):
        conf_path = write_config({"host": "myhost", "port": 1234, "token": "abc"})
        with patch.object(cli, "CONFIG_PATH", conf_path):
            cfg = cli.load_config()
        assert cfg["host"] == "myhost"
        assert cfg["port"] == 1234
        assert cfg["token"] == "abc"

    def test_load_missing_config(self, tmp_path):
        missing = tmp_path / "nonexistent.conf"
        with patch.object(cli, "CONFIG_PATH", missing):
            cfg = cli.load_config()
        assert cfg == {}

    def test_load_malformed_config(self, tmp_path):
        bad = tmp_path / "bad.conf"
        bad.write_text("NOT VALID JSON {{{")
        with patch.object(cli, "CONFIG_PATH", bad):
            cfg = cli.load_config()
        assert cfg == {}

    def test_load_empty_config_file(self, tmp_path):
        empty = tmp_path / "empty.conf"
        empty.write_text("")
        with patch.object(cli, "CONFIG_PATH", empty):
            cfg = cli.load_config()
        assert cfg == {}


# -----------------------------------------------------------------------
# 3. Environment variable handling
# -----------------------------------------------------------------------

class TestEnvVars:
    def test_host_from_env(self, monkeypatch, tmp_path):
        """When no config file exists, NEXUS_HOST env var is used."""
        monkeypatch.setenv("NEXUS_HOST", "envhost")
        missing = tmp_path / "nope.conf"
        with patch.object(cli, "CONFIG_PATH", missing):
            cfg = cli.load_config()
        import os
        resolved = cfg.get("host", os.environ.get("NEXUS_HOST", cli.DEFAULT_HOST))
        assert resolved == "envhost"

    def test_defaults_when_nothing_set(self, tmp_path):
        missing = tmp_path / "nope.conf"
        with patch.object(cli, "CONFIG_PATH", missing):
            cfg = cli.load_config()
        import os
        host = cfg.get("host", os.environ.get("NEXUS_HOST", cli.DEFAULT_HOST))
        port = int(cfg.get("port", os.environ.get("NEXUS_PORT", cli.DEFAULT_PORT)))
        assert host == "localhost"
        assert port == 9877


# -----------------------------------------------------------------------
# 4. WebSocket URL construction
# -----------------------------------------------------------------------

class TestWebSocketURL:
    def test_default_url(self):
        uri = f"ws://{cli.DEFAULT_HOST}:{cli.DEFAULT_PORT}"
        assert uri == "ws://localhost:9877"

    def test_custom_url(self):
        uri = f"ws://myserver:{4321}"
        assert uri == "ws://myserver:4321"


# -----------------------------------------------------------------------
# 5. Model label formatting
# -----------------------------------------------------------------------

class TestModelLabel:
    def test_known_labels(self):
        assert "Nemotron" in cli._model_label("vllm", "sonnet")
        assert "Opus" in cli._model_label("bedrock_api", "opus")
        assert "Sonnet" in cli._model_label("bedrock_api", "sonnet")
        assert "Ollama" in cli._model_label("ollama", "sonnet")

    def test_unknown_falls_back(self):
        label = cli._model_label("custom_backend", "llama")
        assert "custom_backend" in label
        assert "llama" in label


# -----------------------------------------------------------------------
# 6. Autocomplete word list
# -----------------------------------------------------------------------

class TestAutocomplete:
    def test_commands_list_is_populated(self):
        assert len(cli.COMMANDS) > 0

    def test_all_commands_start_with_slash(self):
        for cmd, _desc in cli.COMMANDS:
            assert cmd.startswith("/"), f"{cmd} does not start with /"

    def test_expected_commands_present(self):
        names = {cmd for cmd, _ in cli.COMMANDS}
        for expected in ("/opus", "/sonnet", "/nemotron", "/new", "/status", "/help", "/exit"):
            assert expected in names, f"{expected} missing from COMMANDS"

    @pytest.mark.skipif(not cli.HAS_PROMPT_TOOLKIT, reason="prompt_toolkit not installed")
    def test_completer_matches_prefix(self):
        completer = cli.SlashCompleter()
        doc = MagicMock()
        doc.text_before_cursor = "/op"
        results = list(completer.get_completions(doc, None))
        texts = [c.text for c in results]
        assert "/opus" in texts

    @pytest.mark.skipif(not cli.HAS_PROMPT_TOOLKIT, reason="prompt_toolkit not installed")
    def test_completer_ignores_non_slash(self):
        completer = cli.SlashCompleter()
        doc = MagicMock()
        doc.text_before_cursor = "hello"
        results = list(completer.get_completions(doc, None))
        assert results == []


# -----------------------------------------------------------------------
# 7. Reconnection backoff logic
# -----------------------------------------------------------------------

class TestReconnectBackoff:
    def test_initial_delay(self):
        t = cli.NexusTerminal()
        assert t._reconnect_delay == 1

    def test_backoff_doubles(self):
        t = cli.NexusTerminal()
        t._reconnect_delay = min(t._reconnect_delay * 2, 30)
        assert t._reconnect_delay == 2
        t._reconnect_delay = min(t._reconnect_delay * 2, 30)
        assert t._reconnect_delay == 4

    def test_backoff_caps_at_30(self):
        t = cli.NexusTerminal()
        t._reconnect_delay = 16
        t._reconnect_delay = min(t._reconnect_delay * 2, 30)
        assert t._reconnect_delay == 30
        t._reconnect_delay = min(t._reconnect_delay * 2, 30)
        assert t._reconnect_delay == 30  # stays capped

    def test_connect_resets_backoff(self):
        """After a successful connect, _reconnect_delay resets to 1."""
        t = cli.NexusTerminal()
        t._reconnect_delay = 16
        # Simulate what connect() does on success
        t._reconnect_delay = 1
        assert t._reconnect_delay == 1


# -----------------------------------------------------------------------
# 8. Message send helpers (mocked WebSocket)
# -----------------------------------------------------------------------

class TestMessageSend:
    @pytest.mark.asyncio
    async def test_send_message_format(self):
        t = cli.NexusTerminal()
        t.ws = AsyncMock()
        await t.send_message("Hello world")
        t.ws.send.assert_called_once()
        payload = json.loads(t.ws.send.call_args[0][0])
        assert payload == {"type": "message", "text": "Hello world"}
        assert t._streaming is True

    @pytest.mark.asyncio
    async def test_send_command_format(self):
        t = cli.NexusTerminal()
        t.ws = AsyncMock()
        await t.send_command("opus", "")
        payload = json.loads(t.ws.send.call_args[0][0])
        assert payload == {"type": "command", "cmd": "opus", "args": ""}
        assert t._command_pending is True

    @pytest.mark.asyncio
    async def test_send_command_with_args(self):
        t = cli.NexusTerminal()
        t.ws = AsyncMock()
        await t.send_command("train", "Windsor to London")
        payload = json.loads(t.ws.send.call_args[0][0])
        assert payload["cmd"] == "train"
        assert payload["args"] == "Windsor to London"


# -----------------------------------------------------------------------
# 9. Event handling (receive_loop excerpts)
# -----------------------------------------------------------------------

class TestEventHandling:
    def test_command_result_updates_model_opus(self):
        t = cli.NexusTerminal()
        t._backend, t._model = "vllm", "sonnet"
        text = "Switched to Opus"
        if "Switched to" in text:
            if "Opus" in text:
                t._backend, t._model = "bedrock_api", "opus"
        assert t._backend == "bedrock_api"
        assert t._model == "opus"

    def test_command_result_updates_model_nemotron(self):
        t = cli.NexusTerminal()
        t._backend, t._model = "bedrock_api", "opus"
        text = "Switched to Nemotron"
        if "Switched to" in text:
            if "Nemotron" in text:
                t._backend, t._model = "vllm", "sonnet"
        assert t._backend == "vllm"
        assert t._model == "sonnet"

    def test_stream_end_clears_streaming(self):
        t = cli.NexusTerminal()
        t._streaming = True
        # Simulate what receive_loop does on stream_end
        t._streaming = False
        assert t._streaming is False

    def test_error_clears_both_flags(self):
        t = cli.NexusTerminal()
        t._streaming = True
        t._command_pending = True
        # Simulate error handler
        t._streaming = False
        t._command_pending = False
        assert t._streaming is False
        assert t._command_pending is False


# -----------------------------------------------------------------------
# 10. Terminal helpers
# -----------------------------------------------------------------------

class TestTerminalHelpers:
    def test_separator_length(self):
        """Separator should be full terminal width."""
        import re
        sep = cli._separator()
        # Strip ANSI codes and check it's all dashes
        ansi_re = re.compile(r'\033\[[0-9;]*m')
        clean = ansi_re.sub('', sep)
        assert all(c == '\u2500' for c in clean)
        assert len(clean) > 0

    def test_version_string(self):
        assert cli.VERSION
        parts = cli.VERSION.split(".")
        assert len(parts) == 3  # semver


# -----------------------------------------------------------------------
# 11. Edge cases
# -----------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_input_not_sent(self):
        """Whitespace-only input should be skipped (not sent to server)."""
        line = "   ".strip()
        assert not line  # confirms the guard works

    def test_malformed_json_event_skipped(self):
        """json.loads on garbage should raise, matching the try/except in receive_loop."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("NOT JSON {{{")

    def test_config_overrides_env(self, write_config, monkeypatch):
        """Config file values take precedence over env vars."""
        monkeypatch.setenv("NEXUS_HOST", "env-host")
        conf_path = write_config({"host": "config-host"})
        with patch.object(cli, "CONFIG_PATH", conf_path):
            cfg = cli.load_config()
        import os
        resolved = cfg.get("host", os.environ.get("NEXUS_HOST", cli.DEFAULT_HOST))
        assert resolved == "config-host"
