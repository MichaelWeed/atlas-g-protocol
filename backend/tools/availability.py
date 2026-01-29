"""
Atlas-G Protocol - Availability Tool
Checks candidate availability and rate cards.
"""

import json
from pathlib import Path
from typing import Optional
from backend.config import get_settings


def load_availability() -> dict:
    """Load availability data from JSON file."""
    try:
        settings = get_settings()
        # Find path relative to this file to be safe, or use settings base path if absolute
        # Assuming data is in project_root/data
        base_path = Path(__file__).parent.parent.parent
        data_path = base_path / "data" / "availability.json"
        
        if data_path.exists():
            return json.loads(data_path.read_text(encoding="utf-8"))
        return {}
    except Exception as e:
        print(f"Error loading availability: {e}")
        return {}


def check_current_availability(
    inquiry_type: Optional[str] = None
) -> dict:
    """
    Check current availability status.
    
    Args:
        inquiry_type: Optional type of engagement (contract, fte, advisory)
        
    Returns:
        Availability status and relevant rate info
    """
    data = load_availability()
    
    if not data:
        return {
            "success": False,
            "error": "Availability data not configured"
        }
        
    status = data.get("status", "unknown")
    available_from = data.get("available_from", "unknown")
    
    response = {
        "success": True,
        "status": status,
        "available_from": available_from,
        "timezone": data.get("timezone", "US/Pacific"),
        "preferred_engagement": data.get("preferred_engagement", [])
    }
    
    # Include rate info if explicitly asked or generally available
    # In a real scenario, might want to gate this
    response["rate_card"] = data.get("rate_card", {})
    
    return response
