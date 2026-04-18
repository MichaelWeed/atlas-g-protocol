# Atlas-G Protocol Architecture

The Atlas-G Protocol is built on a "Private-by-Design" architecture that allows a high-performance agentic system to interact with public users or AI IDEs while ensuring sensitive background data is strictly governed and never leaked.

```mermaid
flowchart TD
    %% Styling
    classDef external fill:#1a1a1a,stroke:#333,stroke-width:2px,color:#fff
    classDef frontend fill:#0a192f,stroke:#64ffda,stroke-width:2px,color:#e6f1ff
    classDef backend fill:#112240,stroke:#64ffda,stroke-width:2px,color:#e6f1ff
    classDef governance fill:#4a154b,stroke:#ff6b6b,stroke-width:2px,color:#fff
    classDef mcp fill:#2d1b4e,stroke:#9d4edd,stroke-width:2px,color:#fff
    classDef data fill:#1e1e1e,stroke:#4caf50,stroke-width:2px,color:#fff
    classDef thirdparty fill:#333,stroke:#ffb74d,stroke-width:2px,color:#fff

    %% Actors
    User([Human Visitor\nvia Web Browser]):::external
    ClientAI([AI IDE / Agent\nvia MCP]):::external

    subgraph CloudRun["☁️ Cloud Run Deployment Environment"]
        %% Frontend Architecture
        subgraph FE["Frontend UI (React)"]
            UI["Terminal Interface\n(WebSocket & HTTP)"]:::frontend
        end

        %% Backend Architecture
        subgraph BE["Backend Services (FastAPI + Python)"]
            Router["FastAPI Router\n(REST & WS)"]:::backend

            subgraph Core["Agentic Core"]
                Agent["AtlasAgent\n(Thought-Action Loop)"]:::backend
            end

            subgraph GovLayer["C-GAS Layer (Governance)"]
                Gov["GovernanceLayer\n(Fact & PII Verification)"]:::governance
                Audit["Audit Logger & Status Streamer"]:::governance
            end

            subgraph MCPServer["Model Context Protocol"]
                FastMCP["FastMCP Wrapper"]:::mcp
                Tools["MCP Tools\n(query_resume, verify_employment)"]:::mcp
            end
            
            Sessions[("Session Store\n(Firestore/Volatile)")]:::data
        end

        %% Data Store
        subgraph Data["Knowledge Graph"]
            ResumeText["resume.txt / template\n(Private & Local)"]:::data
        end
    end

    %% External Dependencies
    Gemini["Google Gemini API\n(LLM Inference)"]:::thirdparty

    %% Web Connections
    User <-->|WebSocket Stream \n& REST| UI
    UI <--> Router
    Router <--> Agent
    
    %% MCP Connections
    ClientAI <-->|JSON-RPC \nover stdio/HTTP| FastMCP
    FastMCP --> Tools
    Tools --> Gov

    %% Agent Flow
    Agent -->|1. Generate Context| Gemini
    Gemini -->|2. Stream Content| Agent
    Agent -->|3. Validate Response| Gov
    Gov -->|4. Allow/Warn/Block| Agent

    %% Data Verification
    Gov <-->|Check Facts| ResumeText
    Tools <-->|Query| ResumeText

    %% State
    Agent <--> Sessions

    %% Event Stream to UI
    Audit -.->|"Stream: [PASS/WARN/BLOCK]"| UI

    %% Note for architecture intent
    class CloudRun external
```

### Key Architectural Concepts

**1. Dual Interfacing (Human & Machine)**
The protocol can be interacted with directly via a web browser (React Terminal UI streaming WebSockets) or programmatically via the Model Context Protocol (MCP) by any AI IDE.

**2. Governance Layer (C-GAS 2.0)**
Acts as an interception proxy between the LLM Output and the user. It enforces deterministic rules over probabilistic LLM inputs, validating every claim against the local knowledge graph (`resume.txt`) and striking down jailbreaks, credential probes, and hallucinated facts before they transmit.

**3. Private-by-Design Data Abstraction**
The real capability is driven by an ingestion of local, private files (such as `data/resume.txt`). Public deployments use `resume.template.txt`. No external remote or hardcoded state is strictly required in the open-source release, preventing accidental personal info leakage.
