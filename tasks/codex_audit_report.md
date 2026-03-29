# Codex Audit Report: PureClaw CLI

_Date: 2026-03-29_

## 1. Executive Summary
PureClaw CLI is clean and appropriately small, but its trust boundary is too thin for a terminal client that accepts arbitrary streamed text from a remote agent. The biggest risks are plaintext WebSocket transport, raw terminal escape-sequence rendering, and weak interruption/recovery behavior during long streams. The single-file design is still the right choice; the fixes should stay proportional.

## 2. Critical / High Findings

### High — Security — Plaintext transport by default
- **Evidence:** `pureclaw-cli.py:204-210`
- **Issue:** The client hardcodes `ws://` and sends the auth token over that connection. That is fine only if the user is always on localhost/Tailscale, but the tool itself does not enforce that assumption.
- **Recommendation:** Add configurable scheme support (`ws`/`wss`), default to `wss` for non-local hosts, and document certificate handling.
- **Priority:** Do now

### High — Security — Raw server text is written directly to the terminal
- **Evidence:** `pureclaw-cli.py:247-250`
- **Issue:** The client writes `text_delta` payloads straight to stdout. A malicious or compromised server can emit OSC/control sequences (clipboard write, title change, cursor movement, screen rewrite).
- **Recommendation:** Strip or allowlist escape sequences before rendering. Permit only a tiny ANSI subset if colors are needed.
- **Priority:** Do now

### High — Reliability / UX — Ctrl+C does not cancel the server-side generation
- **Evidence:** `pureclaw-cli.py:307-310`, `353-356`
- **Issue:** During streaming, Ctrl+C only prints `(interrupt)` locally and keeps waiting. The backend continues generating and consuming resources.
- **Recommendation:** Add a cancel frame or force-close/reconnect the socket for the active request.
- **Priority:** Do now

## 3. Medium / Low Findings

### Medium — UX — Streamed replies print the separator twice
- **Evidence:** `pureclaw-cli.py:257-267`; server also emits both `stream_end` and `result` in `nexus/channels/terminal/__init__.py:343-374`
- **Issue:** Fully streamed replies hit `_print_separator()` on `stream_end` and again on `result`, so the UI adds duplicate dividers.
- **Recommendation:** Treat `result` as metadata-only when streaming already completed, or suppress the second separator when `text` is empty.
- **Priority:** Next sprint

### Medium — Reliability — Config file overrides environment variables
- **Evidence:** `pureclaw-cli.py:61-64`
- **Issue:** Env vars normally override config files, but here the JSON file wins.
- **Recommendation:** Reverse precedence so env vars override file values.
- **Priority:** Next sprint

### Medium — Security — Config file is read without any ownership/permission checks
- **Evidence:** `pureclaw-cli.py:46-57`
- **Issue:** Tokens can be sourced from a world-readable or symlinked config file without warning.
- **Recommendation:** Warn on loose permissions and reject symlinked configs unless explicitly allowed.
- **Priority:** Next sprint

### Medium — Performance — Per-token flush can become expensive on large streams
- **Evidence:** `pureclaw-cli.py:247-250`
- **Issue:** Every delta triggers an immediate flush. Large responses can become CPU-heavy and visually noisy.
- **Recommendation:** Batch deltas on a short timer (e.g. 20–50 ms) before flushing.
- **Priority:** Backlog

### Low — UX — Server version is ignored
- **Evidence:** `pureclaw-cli.py:118-120`, `216-219`
- **Issue:** The banner can show a server version, but `auth_ok` only updates backend/model.
- **Recommendation:** Capture and display `server_version` from the handshake.
- **Priority:** Backlog

## 4. UX Assessment
The prompt-toolkit path is sensible and the reconnect loop is easy to follow. The weakest UX areas are cancellation, duplicate separators, and lack of visibility into whether reconnect resumes the prior in-flight request or starts clean. Power users would also expect a `/cancel`, optional transcript logging, and cleaner rendering for code blocks.

## 5. Prioritized Roadmap
1. Add `wss://` support and safe defaults for remote hosts.
2. Sanitize streamed terminal control sequences.
3. Implement real request cancellation on Ctrl+C.
4. Fix double-separator handling for streamed responses.
5. Reverse config precedence and warn on unsafe config file permissions.
