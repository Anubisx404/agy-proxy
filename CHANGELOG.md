# Changelog

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
