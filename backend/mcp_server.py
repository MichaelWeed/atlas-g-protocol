"""
Atlas-G Protocol - MCP Server
Exposes tools via the Model Context Protocol using FastMCP.
"""

from pathlib import Path
from typing import Optional
import os

import fastmcp
from fastmcp import FastMCP

# Set FastMCP to handle requests at the root of its mount point
fastmcp.settings.streamable_http_path = "/"

from .config import get_settings
from .tools.resume_rag import query_resume, get_resume_sections, initialize_index
from .tools.verification import (
    verify_employment_history,
    audit_project_architecture,
    initialize_verifier
)
from .tools.profile_extractor import extract_professional_profile
from .tools.availability import check_current_availability


# Initialize MCP server
mcp = FastMCP(
    name="atlas-g-protocol",
    instructions="Agentic Portfolio System - Query and verify resume data via MCP"
)


def load_resume_content() -> str:
    """Load resume content from file. Falls back to template if main file missing (e.g. in Glama/CI)."""
    settings = get_settings()
    root = Path(__file__).parent.parent
    resume_path = root / settings.resume_path
    fallback_path = root / "data" / "resume.template.txt"
    content = ""
    try:
        if resume_path.exists():
            content = resume_path.read_text(encoding="utf-8")
        elif fallback_path.exists():
            content = fallback_path.read_text(encoding="utf-8")
    except Exception:
        content = ""
    initialize_index(content)
    initialize_verifier(content)
    return content


# Load resume on import; never crash so Glama/inspection can ping the server
try:
    _resume_content = load_resume_content()
except Exception:
    _resume_content = ""
    initialize_index("")
    initialize_verifier("")


# ============================================================================
# Security & Auth
# ============================================================================

def check_auth(ctx: Optional[str] = None) -> bool:
    """
    Validate access token if configured.
    Returns True if authorized or no token required (public mode).
    """
    settings = get_settings()
    # If no key is set in production, default to OPEN (or change to closed based on preference)
    # Here we assume if key is set, we check it.
    required_token = os.environ.get("ATLAS_MCP_TOKEN")
    
    if not required_token:
        # Open mode (Public Framework)
        return True
        
    # Check if context contains the token (simple bearer pattern)
    # In a real MCP client, this might be passed via headers or specific context field
    if ctx and required_token in ctx:
        return True
        
    return False

def get_unauthorized_response() -> dict:
    return {
        "success": False,
        "error": "Unauthorized. Please provide a valid ATLAS_MCP_TOKEN in the context.",
        "code": 401
    }

# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def mcp_query_resume(
    query: str,
    context: Optional[str] = None
) -> dict:
    """
    Query the candidate's resume using semantic search.
    Publicly accessible for general queries.
    """
    return query_resume(query=query, context=context, resume_content=_resume_content)


@mcp.tool()
def mcp_verify_employment(
    employer: str,
    role: Optional[str] = None,
    dates: Optional[str] = None,
    auth_token: Optional[str] = None
) -> dict:
    """
    Cross-reference employment claims against the verified resume knowledge graph.
    [PROTECTED] Requires auth_token for detailed verification.
    """
    if not check_auth(auth_token):
        return get_unauthorized_response()
        
    return verify_employment_history(
        employer=employer,
        role=role,
        dates=dates,
        resume_content=_resume_content
    )


@mcp.tool()
def mcp_audit_project(project: str, auth_token: Optional[str] = None) -> dict:
    """
    Deep-dive into a specific project's technical architecture.
    [PROTECTED] Requires auth_token for deep architectural audits.
    """
    if not check_auth(auth_token):
        return get_unauthorized_response()

    return audit_project_architecture(
        project=project,
        resume_content=_resume_content
    )


@mcp.tool()
def mcp_list_sections() -> dict:
    """List all sections available (Public)."""
    sections = get_resume_sections(resume_content=_resume_content)
    return {
        "success": True,
        "sections": sections,
        "count": len(sections)
    }


@mcp.tool()
def mcp_get_capabilities() -> dict:
    """Get core capabilities (Public)."""
    result = query_resume(
        query="core competencies expertise skills",
        resume_content=_resume_content
    )
    
    return {
        "success": True,
        "capabilities": result.get("sections", []),
        "domains": ["Healthcare/HIPAA", "FinTech/PCI-DSS", "Agentic AI", "Cloud Architecture"]
    }


@mcp.tool()
def mcp_get_professional_profile(include_summary: bool = True) -> dict:
    """
    Get structured professional profile.
    Returns summary, experience, and skills.
    """
    profile = extract_professional_profile(_resume_content)
    if not include_summary:
        profile.pop("summary", None)
    return profile


@mcp.tool()
def mcp_check_availability(inquiry_type: Optional[str] = None) -> dict:
    """
    Check current availability and rate cards.
    """
    return check_current_availability(inquiry_type)


# ============================================================================
# MCP Resources
# ============================================================================

@mcp.resource("resume://summary")
def get_resume_summary() -> str:
    """Get a high-level summary of the resume."""
    if not _resume_content:
        return "Resume not loaded"
    
    # Extract identity section
    lines = _resume_content.split('\n')
    summary_lines = []
    in_identity = False
    
    for line in lines[:50]:  # Only first 50 lines
        if "IDENTITY" in line:
            in_identity = True
            continue
        if in_identity and line.startswith("==="):
            break
        if in_identity and line.strip():
            summary_lines.append(line.strip())
    
    return "\n".join(summary_lines) if summary_lines else "Atlas-G Protocol Portfolio"


@mcp.resource("resume://projects")
def get_projects_list() -> str:
    """Get list of all projects in the resume."""
    result = audit_project_architecture("", resume_content=_resume_content)
    projects = result.get("available_projects", [])
    return "\n".join(f"- {p}" for p in projects) if projects else "No projects found"


# ============================================================================
# Entry Point
# ============================================================================

def run_server():
    """Run the MCP server."""
    import asyncio
    asyncio.run(mcp.run_async())


if __name__ == "__main__":
    run_server()
