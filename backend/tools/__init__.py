"""
Atlas-G Protocol - MCP Tools Package
"""

from .resume_rag import query_resume, get_resume_sections
from .verification import verify_employment_history, audit_project_architecture

__all__ = [
    "query_resume",
    "get_resume_sections",
    "verify_employment_history",
    "audit_project_architecture",
]
