"""
Atlas-G Protocol - Resume RAG Tool
Implements semantic search over the resume knowledge graph.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ResumeChunk:
    """A chunk of resume content with metadata."""
    section: str
    content: str
    keywords: list[str]
    
    def relevance_score(self, query: str) -> float:
        """Calculate simple relevance score based on keyword matching."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Check keywords
        keyword_matches = sum(
            1 for kw in self.keywords 
            if kw.lower() in query_words or query_lower in kw.lower()
        )
        
        # Check content
        content_lower = self.content.lower()
        content_matches = sum(
            1 for word in query_words 
            if word in content_lower
        )
        
        return (keyword_matches * 2) + content_matches


class ResumeIndex:
    """In-memory index for resume content."""
    
    def __init__(self, resume_content: str):
        self.content = resume_content
        self.chunks: list[ResumeChunk] = []
        self._build_index()
    
    def _build_index(self):
        """Parse resume into searchable chunks."""
        if not self.content:
            return
        
        # Split by major sections
        sections = re.split(r'={10,}', self.content)
        current_section = "GENERAL"
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            lines = section.split('\n')
            
            # Check if first line is a section header
            if lines and lines[0].isupper() and len(lines[0]) < 50:
                current_section = lines[0].strip()
                section_content = '\n'.join(lines[1:]).strip()
            else:
                section_content = section
            
            if not section_content:
                continue
            
            # Extract keywords from content
            keywords = self._extract_keywords(section_content)
            
            self.chunks.append(ResumeChunk(
                section=current_section,
                content=section_content,
                keywords=keywords
            ))
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text."""
        keywords = []
        
        # Extract bracketed items [PROJECT: xyz]
        bracketed = re.findall(r'\[([^\]]+)\]', text)
        keywords.extend(bracketed)
        
        # Extract items after colons
        colon_items = re.findall(r':\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        keywords.extend(colon_items)
        
        # Common domain keywords
        domain_keywords = [
            "healthcare", "fintech", "HIPAA", "PCI", "serverless",
            "AWS", "Google Cloud", "Python", "React", "FastAPI",
            "Lambda", "DynamoDB", "Firestore", "MCP", "agentic"
        ]
        
        for kw in domain_keywords:
            if kw.lower() in text.lower():
                keywords.append(kw)
        
        return list(set(keywords))
    
    def search(self, query: str, top_k: int = 3) -> list[ResumeChunk]:
        """Search for relevant chunks."""
        if not self.chunks:
            return []
        
        # Score and sort chunks
        scored = [(chunk, chunk.relevance_score(query)) for chunk in self.chunks]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results with non-zero scores
        return [chunk for chunk, score in scored[:top_k] if score > 0]


# Global index instance
_resume_index: Optional[ResumeIndex] = None


def initialize_index(resume_content: str):
    """Initialize the resume index."""
    global _resume_index
    _resume_index = ResumeIndex(resume_content)


def get_index() -> Optional[ResumeIndex]:
    """Get the current index instance."""
    return _resume_index


def query_resume(
    query: str,
    context: Optional[str] = None,
    resume_content: Optional[str] = None
) -> dict:
    """
    MCP Tool: Query the resume using semantic search.
    
    Args:
        query: The question or topic to search for
        context: Optional domain context (healthcare, fintech, general)
        resume_content: Optional resume content to search (for standalone use)
    
    Returns:
        Dictionary with relevant sections and synthesized answer
    """
    global _resume_index
    
    # Initialize index if needed
    if resume_content and not _resume_index:
        initialize_index(resume_content)
    
    if not _resume_index:
        return {
            "success": False,
            "error": "Resume not loaded",
            "sections": [],
            "synthesis": None
        }
    
    # Apply context filter if provided
    search_query = query
    if context:
        search_query = f"{context} {query}"
    
    # Search for relevant chunks
    results = _resume_index.search(search_query)
    
    if not results:
        return {
            "success": True,
            "query": query,
            "context": context,
            "sections": [],
            "synthesis": "No relevant information found in the resume for this query."
        }
    
    # Build response
    sections = []
    for chunk in results:
        sections.append({
            "section": chunk.section,
            "content": chunk.content[:500] + ("..." if len(chunk.content) > 500 else ""),
            "keywords": chunk.keywords[:10]
        })
    
    # Simple synthesis
    section_names = [s["section"] for s in sections]
    synthesis = (
        f"Found relevant information in {len(sections)} section(s): "
        f"{', '.join(section_names)}. "
        f"Key topics include: {', '.join(results[0].keywords[:5])}."
    )
    
    return {
        "success": True,
        "query": query,
        "context": context,
        "sections": sections,
        "synthesis": synthesis
    }


def get_resume_sections(resume_content: Optional[str] = None) -> list[str]:
    """
    Get list of all sections in the resume.
    
    Args:
        resume_content: Optional resume content (for standalone use)
    
    Returns:
        List of section names
    """
    global _resume_index
    
    if resume_content and not _resume_index:
        initialize_index(resume_content)
    
    if not _resume_index:
        return []
    
    return list(set(chunk.section for chunk in _resume_index.chunks))
