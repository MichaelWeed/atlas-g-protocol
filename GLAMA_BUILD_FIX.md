# Glama build failure: "Expected server to respond to ping"

## What Glama does

Glama runs your server in a container with:

- **Build:** `uv sync`
- **Run:** `mcp-proxy python -m backend.mcp_server`
- **Ping:** They send an MCP request and expect a response within ~1s. If the process exits or doesn't respond you get:
  - `DockerContainerError: Expected server to respond to ping`
  - `RequestError: other side closed`

## Likely cause

The process was **exiting on startup** (e.g. missing `data/resume.txt` in the cloned repo, or an exception during resume/verifier init). That closes the connection → "other side closed".

## Fixes applied in this repo

1. **Resume load** — Now falls back to `data/resume.template.txt` when `data/resume.txt` is missing (e.g. in Glama's clone where resume.txt is gitignored).
2. **Import-time init** — Wrapped in try/except so the server always starts even if resume load or get_settings() fails; tools get empty content instead of a crash.

## What you do

1. Commit and push these changes.
2. In Glama, use **Sync Server** (admin) then re-run the build test.

If it still fails, startup may be slower than Glama's 1s timeout (e.g. heavy imports); consider deferring non-essential init or asking Glama for a longer timeout.
