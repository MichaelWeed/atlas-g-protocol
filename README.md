# Atlas-G Protocol

> **Agentic Portfolio System** - A compliance-grade MCP server that serves as both human and machine-readable portfolio.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Cloud Run](https://img.shields.io/badge/Google%20Cloud-Run-orange)
![MCP](https://img.shields.io/badge/MCP-Compatible-purple)
<a href="https://glama.ai/mcp/servers/@MichaelWeed/atlas-g-protocol">
<img width="380" height="200" src="https://glama.ai/mcp/servers/@MichaelWeed/atlas-g-protocol/badge" />
</a>

## 🎯 Overview

Atlas-G Protocol transforms a traditional developer portfolio into an **autonomous agent** that demonstrates compliance-grade engineering in real-time. Instead of reading about experience with "strict state management" and "hallucination mitigation," users interact with an agent that actively demonstrates these capabilities.

### Key Features

- **MCP Server**: Machine-readable portfolio accessible by AI development environments
- **Governance Layer**: Real-time hallucination mitigation via knowledge graph validation
- **Live Audit Log**: Streams internal compliance checks to the UI
- **WebSocket Streaming**: Real-time "Thought-Action" loop visualization
- **CSP Headers**: Configured for DEV.to iframe embedding

## 🔒 Privacy & Data Governance

The Atlas-G Protocol follows a **"Private-by-Design"** pattern to ensure sensitive career data isn't leaked in public repositories:

- **Template Pattern**: All proprietary information (work history, PII) is stored in `data/resume.txt`, which is explicitly excluded from the repository via `.gitignore`.
- **resume.template.txt**: A sanitized template is provided for open-source users to populate with their own data.
- **Hallucination Mitigation**: The agent's governance layer validates every claim against the local `resume.txt` knowledge graph before responding.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Cloud Run Instance                 │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  React Frontend │◄──►│  FastAPI Backend        │ │
│  │  (Terminal UI)  │    │  - Agent Core           │ │
│  └─────────────────┘    │  - Governance Layer     │ │
│                         │  - MCP Server           │ │
│                         └───────────┬─────────────┘ │
│                                     │               │
│                         ┌───────────▼─────────────┐ │
│                         │  Tools                  │ │
│                         │  - query_resume         │ │
│                         │  - verify_employment    │ │
│                         │  - audit_project        │ │
│                         └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud API Key (for Gemini)

### Installation

```bash
# Clone the repository
cd Atlas-G\ Protocol

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
```

### Run Locally

```bash
# Start the server
uvicorn backend.main:application --reload --port 8080

# Open http://localhost:8080
```

### Run Tests

```bash
pytest backend/tests/ -v
```

## 🔧 MCP Integration

Connect your AI development environment to the Atlas-G MCP server:

```json
{
  "mcpServers": {
    "atlas-g-protocol": {
      "command": "python",
      "args": ["-m", "backend.mcp_server"]
    }
  }
}
```

### Available Tools

| Tool                | Description                                 |
| ------------------- | ------------------------------------------- |
| `query_resume`      | Semantic search over resume knowledge graph |
| `verify_employment` | Cross-reference employment claims           |
| `audit_project`     | Deep-dive into project architecture         |

## ☁️ Deploy to Cloud Run

```bash
gcloud run deploy atlas-g-portfolio \
  --source . \
  --allow-unauthenticated \
  --region us-central1 \
  --labels dev-tutorial=devnewyear2026 \
  --set-env-vars GOOGLE_API_KEY=your_key_here
```

## 📁 Project Structure

```
Atlas-G Protocol/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── agent.py         # Thought-Action loop
│   ├── governance.py    # Hallucination mitigation
│   ├── mcp_server.py    # FastMCP wrapper
│   ├── config.py        # Settings management
│   └── tools/
│       ├── resume_rag.py
│       └── verification.py
├── frontend/            # React UI (Phase 3)
├── data/
│   └── resume.txt       # Knowledge graph source
├── Dockerfile
├── pyproject.toml
└── mcp_config.json
```

## 🔒 Security

- **CSP Headers**: `frame-ancestors 'self' https://dev.to https://*.dev.to`
- **Governance Layer**: All AI responses validated against resume data
- **PII Detection**: Automatic filtering of sensitive information
- **Jailbreak Protection**: Pattern-based detection and blocking

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 📢 Credits

- **Audio**: [Emergency Alarm.wav](https://freesound.org/s/699248/) by Mozfoo (CC0)
