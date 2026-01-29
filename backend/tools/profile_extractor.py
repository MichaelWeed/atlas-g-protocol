"""
Atlas-G Protocol - Profile Extractor
Parses resume content into structured professional profile data.
"""

import re
from typing import Dict, List, Any


def extract_professional_profile(resume_content: str) -> Dict[str, Any]:
    """
    Extract structured professional profile from resume content.
    
    Args:
        resume_content: Raw resume text
        
    Returns:
        Structured profile object with summary, experience, and skills
    """
    if not resume_content:
        return {"error": "No content provided"}

    return {
        "summary": _extract_summary(resume_content),
        "experience": _extract_experience(resume_content),
        "skills": _extract_skills_categorized(resume_content)
    }


def _extract_summary(content: str) -> str:
    """Extract professional summary section."""
    match = re.search(r'PROFESSIONAL SUMMARY\s*\n(.*?)(?=\n\n|\nCORE EXPERTISE)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_experience(content: str) -> List[Dict[str, str]]:
    """
    Extract experience history.
    Note: This uses regex heuristics based on the specific resume format.
    """
    experiences = []
    
    # Find the Professional Experience section
    exp_section_match = re.search(
        r'PROFESSIONAL EXPERIENCE\s*\n(.*?)(?=\nPROJECT PORTFOLIO)', 
        content, 
        re.DOTALL
    )
    
    if not exp_section_match:
        return []
        
    exp_text = exp_section_match.group(1)
    
    # Split by role blocks (heuristic: ALL CAPS lines followed by parens or content)
    # Looking for patterns like "NEURAFLASH (Senior Consultant...)"
    # or "INDEPENDENT AI ENGINEER (Current)"
    
    # Simple line-based parser for robustness
    lines = exp_text.split('\n')
    current_role = None
    buffer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect Header: "COMPANY (Role)" or "ROLE (Context)"
        # Heuristic: Upper case start, contains parens
        if re.match(r'^[A-Z][A-Z\s]+', line) and '(' in line and ')' in line:
            # Save previous
            if current_role:
                current_role["description"] = "\n".join(buffer).strip()
                experiences.append(current_role)
                buffer = []
            
            # Start new
            parts = line.split('(', 1)
            title_company = parts[0].strip()
            details = parts[1].rstrip(')')
            
            current_role = {
                "title": title_company, # Mixed field in this resume format
                "context": details,
                "description": ""
            }
        elif current_role:
            buffer.append(line)
            
    # Save last
    if current_role:
        current_role["description"] = "\n".join(buffer).strip()
        experiences.append(current_role)
            
    return experiences


def _extract_skills_categorized(content: str) -> Dict[str, List[str]]:
    """Extract skills sections."""
    skills = {}
    
    # Extract CORE EXPERTISE
    core_match = re.search(r'CORE EXPERTISE\s*\n(.*?)(?=\n\n|\nPROFESSIONAL)', content, re.DOTALL)
    if core_match:
        core_lines = [line.strip().lstrip('- ') for line in core_match.group(1).split('\n') if line.strip()]
        skills["core"] = core_lines
        
    return skills
