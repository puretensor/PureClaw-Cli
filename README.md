# PureClaw Cli

Terminal interface to [PureClaw](https://github.com/puretensor/PureClaw) -- the agentic platform from [PureTensor](https://puretensor.ai).

```
    /\___/\
   ( o   o )       PureClaw Cli v1.0.0
   (  =^=  )       Claude Opus 4.6 (Bedrock)
    )     (         ~
   (  |||  )
  ( ||| ||| )
```

PureClaw Cli connects to a running Nexus server over WebSocket and gives you a streaming terminal interface with slash command autocomplete, model switching, session management, and live UK rail departures.

## Part of the PureClaw Family

| Repository | Description |
|---|---|
| [PureClaw](https://github.com/puretensor/PureClaw) | Nexus -- the core agent platform (Telegram, Discord, WhatsApp, Email, Terminal channels) |
| **PureClaw Cli** | This repo -- standalone terminal client |

PureClaw is the agentic identity for PureTensor infrastructure. It runs on Nexus, a multi-channel agent platform that provides tool access, memory, session management, and streaming responses across Telegram, Discord, WhatsApp, email, and terminal. This CLI is the terminal channel's client side -- a single-file Python script that talks to Nexus over WebSocket.

## Install

```bash
pip install websockets
pip install prompt_toolkit  # optional, enables slash command autocomplete dropdown
```

No other dependencies. Python 3.10+.

## Configure

Create `~/.config/pureclaw/cli.conf`:

```json
{
  "host": "your-nexus-host",
  "port": 9877,
  "token": "YOUR_TOKEN"
}
```

Or use environment variables:

```bash
export NEXUS_HOST=your-nexus-host
export NEXUS_PORT=9877
export NEXUS_TOKEN=your-token
```

## Run

```bash
python3 pureclaw-cli.py
```

Recommended alias:

```bash
alias nex='python3 ~/PureClaw-Cli/pureclaw-cli.py'
```

## Features

**Streaming responses** -- text streams token-by-token as the model generates. Tool use status shows inline (dim italic) and is replaced by actual output.

**Slash command autocomplete** -- type `/` and a dropdown appears with all available commands and descriptions (requires `prompt_toolkit`).

**Model switching** -- switch between backends mid-session:
- `/nemotron` -- Nemotron Super on local GPUs (vLLM)
- `/opus` -- Claude Opus (Bedrock)
- `/sonnet` -- Claude Sonnet (Bedrock)

**Session management**:
- `/new` -- clear history, start fresh
- `/status` -- current session info (model, message count, summary)
- `/sessions` -- list recent sessions

**Live train departures** (Darwin Push Port via Kafka):
- `/central` -- Windsor Central to Paddington (shuttle + Elizabeth line + GWR)
- `/riverside` -- Windsor Riverside to Waterloo
- `/waterloo` -- Waterloo to Windsor Riverside
- `/train <from> to <to>` -- any route by station name or CRS code

**Auto-reconnect** -- exponential backoff on disconnect, resumes automatically.

## WebSocket Protocol

The client speaks a simple JSON protocol over WebSocket:

**Client to server:**
```json
{"type": "auth", "token": "..."}
{"type": "message", "text": "..."}
{"type": "command", "cmd": "new", "args": ""}
```

**Server to client:**
```json
{"type": "auth_ok", "backend": "vllm", "model": "sonnet"}
{"type": "text_delta", "text": "..."}
{"type": "tool_status", "status": "Searching files..."}
{"type": "stream_end"}
{"type": "result", "text": "...", "session_id": "..."}
{"type": "command_result", "text": "..."}
{"type": "error", "message": "..."}
```

## Architecture

```
Your machine                         Nexus server (K3s)
+-----------------+    WebSocket    +----------------------+
| pureclaw-cli.py |----------------| TerminalChannel      |
| (readline/ptk)  |   Tailscale    |   -> engine          |
+-----------------+                |   -> tools/memory    |
                                   |   -> Claude/vLLM/etc |
                                   +----------------------+
```

The client is intentionally minimal -- a single file, two pip dependencies, no framework. All intelligence lives server-side in Nexus.

## License

MIT
