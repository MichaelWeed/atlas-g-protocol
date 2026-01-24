import json
import uuid
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Lead:
    id: str
    timestamp: str
    name: str
    email: str
    message: str
    status: str = "NEW"
    source: str = "ATLAS_G_PROTOCOL"

class LeadCaptureService:
    def __init__(self, data_dir: str = "data", filename: str = "leads.json"):
        self.data_dir = data_dir
        self.filename = filename
        self.filepath = os.path.join(data_dir, filename)
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_leads(self) -> List[dict]:
        """Load existing leads from the JSON file."""
        if not os.path.exists(self.filepath):
            return []
        
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_leads(self, leads: List[dict]):
        """Save the list of leads to the JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(leads, f, indent=2)

    def capture(self, name: str, email: str, message: str) -> str:
        """
        Capture a new lead and persist it to storage.
        Returns the generated Lead ID.
        """
        lead_id = f"LEAD-{str(uuid.uuid4())[:8].upper()}"
        timestamp = datetime.utcnow().isoformat()
        
        new_lead = Lead(
            id=lead_id,
            timestamp=timestamp,
            name=name,
            email=email,
            message=message
        )
        
        # Load, Append, Save
        leads = self._load_leads()
        leads.append(asdict(new_lead))
        self._save_leads(leads)
        
        return lead_id
