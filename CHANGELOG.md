# Changelog

## v2.1.0 — 2026-09-23

### Fixed
- **Subprocess Permission Prompt Blocking:** Added `--dangerously-skip-permissions` to the AGY command line so the headless background subprocess never blocks on unhandled interactive permission prompts.
- **Agent Mode Conflation:** Removed the hardcoded `--mode plan` flag from default execution to prevent AGY from hijacking conversational turns into autonomous planning artifacts. This eliminates multi-minute planning delays and restores standard, low-latency LLM responses. Custom modes remain accessible via the `AGY_MODE` environment variable.
- **Streaming Tool-Call Schema:** Fixed streaming tool-call responses to emit OpenAI-compliant `chat.completion.chunk` structures containing `delta` objects rather than non-streaming `message` objects, eliminating `ValidationError` crashes in OpenAI client libraries.
- **SSE Keepalive Heartbeats:** Added periodic `: keep-alive\n\n` comments during inference latency to maintain active TCP sockets and prevent HTTP client read and gateway timeouts.
- **Model Name & Prefix Resolution:** Added `_resolve_model()` with fuzzy and provider prefix normalization (`antigravity/`, `custom/`) so Hermes and other client model configurations resolve accurately without strict ID mismatch errors (HTTP 400).
- **Tool JSON Parsing:** Added automatic stripping of markdown code fences (```json ... ```) from model-generated `<<<TOOL_CALLS>>>` payloads to prevent `JSONDecodeError`.

## v2.0.0 — 2026-09-06

Initial open-source release.

### Features
- OpenAI-compatible `/v1/chat/completions` endpoint (streaming + non-streaming)
- `/v1/models` and `/v1/models/{id}` for model discovery
- `/health` endpoint for monitoring
- Full tool calling support via OpenAI function-calling protocol
- Prompt passed via stdin to bypass Windows 32K argument length limit
- UTF-8 encoding enforcement for cross-platform Unicode support
- ANSI escape code stripping from AGY output
- Model list caching (5 minute TTL)
- Cross-platform support (Windows, macOS, Linux)

### Tested With
- Hermes Agent (Nous Research)
- Python OpenAI SDK
- curl
