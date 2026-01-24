"""
Atlas-G Protocol - Verification Tools
Tools for verifying employment and project claims.
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Result of a verification check."""
    verified: bool
    confidence: str  # high, medium, low
    evidence: list[str]
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "verified": self.verified,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "notes": self.notes
        }


class ResumeVerifier:
    """Verifies claims against resume content."""
    
    def __init__(self, resume_content: str):
        self.content = resume_content
        self.employers = self._extract_employers()
        self.projects = self._extract_projects()
        self.skills = self._extract_skills()
    
    def _extract_employers(self) -> dict[str, dict]:
        """Extract employer information."""
        employers = {}
        
        # Pattern: Company: Name
        company_matches = re.findall(
            r'Company:\s*(.+?)(?:\n|$)',
            self.content,
            re.IGNORECASE
        )
        
        for company in company_matches:
            employers[company.strip().lower()] = {
                "name": company.strip(),
                "verified": True
            }
        
        # Look for known employers in text
        known_patterns = [
            (r'GeneDx', 'GeneDx'),
            (r'Healthcare Technology', 'Healthcare Technology'),
            (r'Financial Services', 'Financial Services'),
        ]
        
        for pattern, name in known_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                employers[name.lower()] = {"name": name, "verified": True}
        
        return employers
    
    def _extract_projects(self) -> dict[str, dict]:
        """Extract project information."""
        projects = {}
        
        # Pattern: [PROJECT: Name]
        project_matches = re.findall(
            r'\[PROJECT:\s*(.+?)\]',
            self.content
        )
        
        for project in project_matches:
            project_name = project.strip()
            # Find project details that follow
            pattern = rf'\[PROJECT:\s*{re.escape(project_name)}\](.*?)(?=\[PROJECT:|$)'
            details_match = re.search(pattern, self.content, re.DOTALL)
            
            details = {}
            if details_match:
                detail_text = details_match.group(1)
                
                # Extract type
                type_match = re.search(r'Type:\s*(.+?)(?:\n|$)', detail_text)
                if type_match:
                    details["type"] = type_match.group(1).strip()
                
                # Extract challenge
                challenge_match = re.search(r'Challenge:\s*(.+?)(?:\n|$)', detail_text)
                if challenge_match:
                    details["challenge"] = challenge_match.group(1).strip()
            
            projects[project_name.lower()] = {
                "name": project_name,
                "verified": True,
                **details
            }
        
        return projects
    
    def _extract_skills(self) -> set[str]:
        """Extract skills mentioned."""
        skills = set()
        
        # Look for common skill keywords
        skill_keywords = [
            "Python", "TypeScript", "JavaScript", "FastAPI", "React",
            "AWS", "Google Cloud", "Docker", "Kubernetes",
            "HIPAA", "PCI-DSS", "PostgreSQL", "DynamoDB", "Firestore",
            "MCP", "LangChain", "RAG", "agentic"
        ]
        
        content_lower = self.content.lower()
        for skill in skill_keywords:
            if skill.lower() in content_lower:
                skills.add(skill)
        
        return skills


# Global verifier instance
_verifier: Optional[ResumeVerifier] = None


def initialize_verifier(resume_content: str):
    """Initialize the verifier with resume content."""
    global _verifier
    _verifier = ResumeVerifier(resume_content)


def get_verifier() -> Optional[ResumeVerifier]:
    """Get the current verifier instance."""
    return _verifier


def verify_employment_history(
    employer: str,
    role: Optional[str] = None,
    dates: Optional[str] = None,
    resume_content: Optional[str] = None
) -> dict:
    """
    MCP Tool: Verify employment claims against resume data.
    
    Args:
        employer: Employer name to verify
        role: Optional role/title to verify
        dates: Optional date range to verify
        resume_content: Optional resume content for standalone use
    
    Returns:
        Verification result with evidence
    """
    global _verifier
    
    if resume_content and not _verifier:
        initialize_verifier(resume_content)
    
    if not _verifier:
        return {
            "success": False,
            "error": "Resume not loaded for verification"
        }
    
    employer_lower = employer.lower()
    evidence = []
    verified = False
    confidence = "low"
    
    # Check if employer is in our records
    for known_employer, info in _verifier.employers.items():
        if employer_lower in known_employer or known_employer in employer_lower:
            verified = True
            evidence.append(f"Found employer match: {info['name']}")
            confidence = "high"
            break
    
    # Also search raw content for mentions
    if not verified and employer in _verifier.content:
        verified = True
        evidence.append(f"Employer '{employer}' mentioned in resume")
        confidence = "medium"
    
    # Verify role if provided
    if role and verified:
        if role.lower() in _verifier.content.lower():
            evidence.append(f"Role '{role}' found in resume")
            confidence = "high"
        else:
            evidence.append(f"Role '{role}' not explicitly found")
            confidence = "medium"
    
    result = VerificationResult(
        verified=verified,
        confidence=confidence,
        evidence=evidence,
        notes=f"Verification ran against {len(_verifier.employers)} known employers"
    )
    
    return {
        "success": True,
        "employer": employer,
        "role": role,
        "dates": dates,
        **result.to_dict()
    }


def audit_project_architecture(
    project: str,
    resume_content: Optional[str] = None
) -> dict:
    """
    MCP Tool: Deep-dive into a project's technical architecture.
    
    Args:
        project: Project name (e.g., 'Atlas Engine', 'GeneDx')
        resume_content: Optional resume content for standalone use
    
    Returns:
        Project architecture details if found
    """
    global _verifier
    
    if resume_content and not _verifier:
        initialize_verifier(resume_content)
    
    if not _verifier:
        return {
            "success": False,
            "error": "Resume not loaded for audit"
        }
    
    project_lower = project.lower()
    
    # Search for project
    for known_project, info in _verifier.projects.items():
        if project_lower in known_project or known_project in project_lower:
            # Extract full project section
            pattern = rf'\[PROJECT:\s*{re.escape(info["name"])}\](.*?)(?=\[PROJECT:|VERIFICATION|$)'
            match = re.search(pattern, _verifier.content, re.DOTALL | re.IGNORECASE)
            
            architecture_details = {}
            if match:
                section = match.group(1)
                
                # Parse structured fields
                fields = ["Type", "Challenge", "Solution", "Outcome"]
                for field in fields:
                    field_match = re.search(
                        rf'{field}:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                        section,
                        re.DOTALL
                    )
                    if field_match:
                        architecture_details[field.lower()] = field_match.group(1).strip()
            
            return {
                "success": True,
                "project": info["name"],
                "found": True,
                "verified": info.get("verified", True),
                "architecture": architecture_details
            }
    
    return {
        "success": True,
        "project": project,
        "found": False,
        "verified": False,
        "message": f"Project '{project}' not found in verified resume data",
        "available_projects": list(_verifier.projects.keys())
    }
