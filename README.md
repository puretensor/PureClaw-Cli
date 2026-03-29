# PureClaw Cli

Terminal client for [PureClaw](https://github.com/puretensor/PureClaw). Connects over WebSocket, streams responses token-by-token, and gives you slash command autocomplete.

```
    /\___/\
   ( o   o )       PureClaw Cli v1.2.5
   (  =^=  )       Claude Opus 4.6 (Bedrock)
    )     (
   (  |||  )
  ( ||| ||| )
```

- **Streaming** -- text appears token-by-token as the model generates, with inline tool status
- **Slash command autocomplete** -- type `/` for a dropdown of all commands (via prompt_toolkit)
- **Model switching** -- `/nemotron`, `/opus`, `/sonnet` to swap backends mid-session
- **Auto-reconnect** -- exponential backoff on disconnect, resumes automatically

## Install

```bash
pip install websockets
pip install prompt_toolkit  # optional, enables autocomplete dropdown
```

Single file. Python 3.10+. No framework.

## Configure

Create `~/.config/pureclaw/cli.conf`:

```json
{
  "host": "your-nexus-host",
  "port": 9877,
  "token": "YOUR_TOKEN"
}
```

Or use environment variables: `NEXUS_HOST`, `NEXUS_PORT`, `NEXUS_TOKEN`.

## Run

```bash
python3 pureclaw-cli.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/nemotron` | Switch to Nemotron Super (local GPUs) |
| `/opus` | Switch to Claude Opus (Bedrock) |
| `/sonnet` | Switch to Claude Sonnet (Bedrock) |
| `/model` | Show current backend/model |
| `/new` | Start fresh session |
| `/status` | Current session info |
| `/sessions` | List recent sessions |
| `/central` | Windsor Central to Paddington departures |
| `/riverside` | Windsor Riverside to Waterloo |
| `/waterloo` | Waterloo to Windsor Riverside |
| `/train <from> to <to>` | Any route by station name or CRS code |
| `/help` | Show all commands |
| `/exit` | Disconnect |

## WebSocket Protocol

Simple JSON over WebSocket. Client sends `auth`, `message`, and `command` frames. Server sends `text_delta` (streaming tokens), `tool_status`, `stream_end`, `result`, `command_result`, and `error`.

```
Your machine                         Nexus server
+-----------------+    WebSocket    +----------------------+
| pureclaw-cli.py |----------------| TerminalChannel      |
| (readline/ptk)  |   Tailscale    |   -> engine           |
+-----------------+                |   -> tools/memory     |
                                   +----------------------+
```

All intelligence lives server-side. The CLI is intentionally minimal.

## Part of PureClaw

| Repository | Description |
|---|---|
| [PureClaw](https://github.com/puretensor/PureClaw) | Nexus -- the core agent platform |
| **PureClaw Cli** | This repo -- standalone terminal client |

## License

MIT

```
