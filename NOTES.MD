# Atlas-G Protocol Notes

## 🛑 HARD CONSTRAINTS (DO NOT ALTER)

- **Model**: Must ALWAYS be `gemini-3-flash-preview`. DO NOT downgrade to 2.0 or Pro.
- **Port**: Must be `8080` for Cloud Run compliance.
- **FS**: No local writes allowed in production (use Firestore).

## Task Log

- [2026-01-28] RESOLVED: Perceived streaming buffering. Root cause: blocking governance. Solution: Async Audit Streaming. (Path: `notes_archive/streaming_resolved_2026-01-28.md`) [Anchor: `anchor/2026-01-28T10-05-anchor.md`]
- [2026-01-28] ENFORCED: Model Law. Locked to `gemini-3-flash-preview` with AI-trap comments.
- [2026-01-27] Fixed Startup Crash (SyntaxError in agent.py).

## 2026-01-23 Session Anchor Protocol

- Initialized session.
- Reviewing ChatPane.tsx and AudioInput.tsx.
- Verifying microphone permission handling and UI states.
