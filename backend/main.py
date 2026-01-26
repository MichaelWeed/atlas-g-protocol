"""
Atlas-G Protocol - Main FastAPI Application
Exposes REST and WebSocket endpoints for the agentic portfolio.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import socketio

from .config import get_settings
from .agent import AtlasAgent


# ============================================================================
# Application Lifespan
# ============================================================================

def load_resume() -> str:
    """Load resume content from file."""
    settings = get_settings()
    resume_path = Path(__file__).parent.parent / settings.resume_path
    
    if resume_path.exists():
        return resume_path.read_text(encoding="utf-8")
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    resume_content = load_resume()
    app.state.agent = AtlasAgent(resume_content=resume_content)
    app.state.resume_content = resume_content
    print("🚀 Atlas-G Protocol initialized")
    print(f"📄 Resume loaded: {len(resume_content)} characters")
    
    yield
    
    # Shutdown
    print("👋 Atlas-G Protocol shutting down")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Atlas-G Protocol",
    description="Agentic Portfolio System - A compliance-grade MCP server",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Security Middleware (CSP Headers for DEV.to embedding)
# ============================================================================

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers including CSP for iframe embedding."""
    response = await call_next(request)
    
    # Content Security Policy - Allow embedding by DEV.to
    response.headers["Content-Security-Policy"] = (
        "frame-ancestors 'self' https://dev.to https://*.dev.to https://forem.dev"
    )
    
    # Remove X-Frame-Options (superseded by CSP frame-ancestors)
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    
    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


# ============================================================================
# CORS Configuration
# ============================================================================

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Socket.IO Server
# ============================================================================

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"  # More permissive for production debugging
)
socket_app = socketio.ASGIApp(sio, app, socketio_path="/socket.io")


@sio.event
async def connect(sid, environ):
    """Handle new WebSocket connection."""
    origin = environ.get('HTTP_ORIGIN', 'unknown')
    print(f"🔌 Client connected: {sid} | Origin: {origin}")
    await sio.emit("audit", {
        "action": "CONNECTION ESTABLISHED",
        "status": "PASS",
        "details": f"Session: {sid[:8]}... from {origin}",
        "timestamp": datetime.utcnow().isoformat()
    }, room=sid)


@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection."""
    print(f"🔌 Client disconnected: {sid}")


@sio.event
async def chat(sid, data):
    """Handle incoming chat messages via WebSocket."""
    query = data.get("message", "")
    session_id = data.get("session_id")
    
    if not query:
        await sio.emit("error", {"message": "Empty query"}, room=sid)
        return
    
    agent: AtlasAgent = app.state.agent
    session = await agent.get_session(session_id) if session_id else agent.create_session()
    
    if not session:
        session = agent.create_session()
    
    # Stream updates to client
    async for update in agent.think(query, session):
        event_type = update["type"]
        await sio.emit(event_type, update["data"], room=sid)


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request body."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response body."""
    session_id: str
    response: Optional[dict] = None
    audit_log: list[dict] = []
    error: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    resume_loaded: bool


# ============================================================================
# REST Endpoints
# ============================================================================

# ============================================================================
# Static Files & Frontend Routing
# ============================================================================

# Define frontend path
FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "dist"

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve frontend if build exists, otherwise show API info."""
    index_html = FRONTEND_PATH / "index.html"
    if index_html.exists():
        return index_html.read_text(encoding="utf-8")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Atlas-G Protocol</title>
        <style>
            body {
                font-family: 'JetBrains Mono', monospace;
                background: #0a0a0a;
                color: #00ff00;
                padding: 2rem;
            }
            h1 { border-bottom: 1px solid #00ff00; }
            a { color: #00ffff; }
            code { background: #1a1a1a; padding: 0.2rem 0.5rem; }
        </style>
    </head>
    <body>
        <h1>🔒 ATLAS-G PROTOCOL</h1>
        <p>Agentic Portfolio System - Compliance-Grade MCP Server</p>
        <div style="background: #1a1a1a; padding: 1rem; border: 1px solid #333; margin: 1rem 0;">
            <strong>⚠️ Frontend build not detected</strong><br/>
            Run <code>cd frontend && npm run build</code> to enable the Web UI.
        </div>
        <h2>Endpoints</h2>
        <ul>
            <li><code>GET /health</code> - Health check</li>
            <li><code>POST /api/chat</code> - Chat with the agent</li>
            <li><code>GET /api/mcp/tools</code> - List available MCP tools</li>
            <li><code>WebSocket /socket.io</code> - Real-time streaming</li>
        </ul>
        <h2>Documentation</h2>
        <p><a href="/docs">OpenAPI Documentation</a></p>
    </body>
    </html>
    """

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        resume_loaded=bool(app.state.resume_content)
    )



# ============================================================================
# API Endpoints (Defined BEFORE catch-all for precedence)
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """REST endpoint for chat queries."""
    agent: AtlasAgent = app.state.agent
    
    result = await agent.query(
        query=request.message,
        session_id=request.session_id
    )
    
    return ChatResponse(
        session_id=result["session_id"],
        response=result.get("response"),
        audit_log=result.get("audit_log", []),
        error=result.get("error")
    )


@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools for discovery."""
    return {
        "tools": [
            {
                "name": "query_resume",
                "description": "Query the candidate's resume using semantic search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "context": {"type": "string", "enum": ["healthcare", "fintech", "general"]}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "verify_employment_history",
                "description": "Cross-reference employment claims against verified data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "employer": {"type": "string"},
                        "role": {"type": "string"}
                    },
                    "required": ["employer"]
                }
            },
            {
                "name": "audit_project_architecture",
                "description": "Deep-dive into a project's technical architecture",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string"}
                    },
                    "required": ["project"]
                }
            }
        ]
    }


@app.get("/api/resume/summary")
async def resume_summary():
    """Get a brief summary of the resume."""
    if not app.state.resume_content:
        raise HTTPException(status_code=404, detail="Resume not loaded")
    
    # Extract key sections
    content = app.state.resume_content
    lines = content.split("\n")
    
    return {
        "loaded": True,
        "character_count": len(content),
        "sections": [
            line.strip("=").strip() 
            for line in lines 
            if line.startswith("===") and line.endswith("===")
        ]
    }


# ============================================================================
# Static Files & Frontend Routing (Catch-all - MUST BE LAST)
# ============================================================================

if FRONTEND_PATH.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_PATH / "assets"), name="assets")
    
    @app.get("/{file_path:path}")
    async def get_static_file(file_path: str):
        # Prevent hijacking API or docs
        if file_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
            raise HTTPException(status_code=404)
            
        file = FRONTEND_PATH / file_path
        if file.exists() and file.is_file():
            from fastapi.responses import FileResponse
            return FileResponse(file)
        
        # Fallback to index.html for SPA routing
        index_html = FRONTEND_PATH / "index.html"
        if index_html.exists():
            return HTMLResponse(content=index_html.read_text(encoding="utf-8"))
        
        raise HTTPException(status_code=404)


# ============================================================================
# WebSocket Native Endpoint (fallback)
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Native WebSocket endpoint for direct connections."""
    await websocket.accept()
    
    agent: AtlasAgent = app.state.agent
    session = agent.create_session()
    
    await websocket.send_json({
        "type": "connected",
        "session_id": session.session_id
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("message", "")
            
            async for update in agent.think(query, session):
                await websocket.send_json(update)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session.session_id}")


# ============================================================================
# Application Mount
# ============================================================================

# Export the socket.io wrapped app for uvicorn
application = socket_app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:application",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production
    )
