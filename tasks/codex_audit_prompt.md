# Codex Audit: PureClaw CLI -- Terminal WebSocket Client

## What You're Reviewing

PureClaw CLI is a single-file terminal client for PureClaw agents. 441 lines of Python. Connects over WebSocket, streams LLM responses token-by-token, provides slash command autocomplete, and supports live backend switching.

Public repo: github.com/puretensor/PureClaw-Cli

## Architecture

```
pureclaw-cli.py (single file)
    |
    ├── WebSocket connection (websockets library)
    │   ├── Auto-reconnect with exponential backoff
    │   └── Token-by-token streaming display
    │
    ├── Input (prompt_toolkit or fallback to input())
    │   ├── Slash command autocomplete dropdown
    │   └── History
    │
    ├── Commands
    │   ├── /nemotron, /opus, /sonnet -- backend switching
    │   ├── /new, /status, /sessions -- session management
    │   └── /central, /riverside -- data card shortcuts
    │
    └── Config
        ├── ~/.config/pureclaw/cli.conf (JSON)
        └── NEXUS_HOST, NEXUS_PORT, NEXUS_TOKEN env vars
```

## Files to Read

One file: `pureclaw-cli.py` (441 lines). Also read `README.md`.

## What I Want From You

### 1. WebSocket Implementation
- Is the WebSocket connection handling robust? Reconnection logic? Timeout handling?
- Is the streaming display (token-by-token) correctly implemented? Buffering? Partial messages?
- How does it handle server-side disconnects, network interruptions, and stale connections?
- Is backpressure handled? What if the server sends faster than the terminal can render?

### 2. Code Quality
- Find bugs. Edge cases in message parsing, Unicode handling, terminal rendering.
- Is error handling consistent? Are there bare except clauses or swallowed errors?
- Is the prompt_toolkit integration clean? Does the fallback to basic input() work properly?
- Are there any resource leaks (unclosed connections, threads, file handles)?

### 3. Security
- Is the auth token handled safely? Could it leak through logs, error messages, or history?
- Is the config file read safely? Permissions check? Symlink attacks?
- Is the WebSocket connection encrypted (wss://)? Is there a TLS option?
- Could a malicious server response cause issues (XSS in terminal, command injection)?

### 4. UX
- Is the streaming output display clean? Markdown rendering? Code blocks? Colors?
- Is the autocomplete implementation complete? Missing commands?
- Is the reconnection UX good? Does the user know what's happening?
- Are error messages helpful and actionable?
- What features are missing that a terminal power user would expect?

### 5. Robustness
- What happens on Ctrl+C during streaming? During reconnection? During input?
- Does it handle large responses (100K+ tokens) without issues?
- Is the session management (new/status/sessions) well-implemented?
- How does it handle the server being completely unreachable at startup?

### 6. Concrete Improvement Recommendations
For each finding:
- **Severity**: Critical / High / Medium / Low
- **Category**: Bug, Security, UX, Performance, Reliability, Missing Feature
- **Description**: What's wrong or missing
- **Recommendation**: Specific fix
- **Priority**: Do now / Next sprint / Backlog

## Output Format

1. **Executive Summary** (3-5 sentences)
2. **Critical / High Findings**
3. **Medium / Low Findings**
4. **UX Assessment**
5. **Prioritized Roadmap** (top 5 improvements)

This is a small, focused tool. Keep improvements proportional -- don't over-engineer a 441-line CLI. Maintain the single-file, minimal-dependency philosophy.

After your review, commit your changes and push to GitHub.
