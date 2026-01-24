"""
Atlas-G Protocol - Persistence Layer
Handles session persistence using Google Cloud Firestore.
"""

import json
from typing import Optional, Any
from google.cloud import firestore
from .config import get_settings

class FirestoreSessionStore:
    """Manages agent session persistence in Firestore."""
    
    def __init__(self):
        self.settings = get_settings()
        # Initialize Firestore client
        # Note: In a real Cloud Run env, credentials are provided by the service account
        self.db = firestore.AsyncClient(project=self.settings.firestore_project_id)
        self.collection = self.db.collection("agent_sessions")
    
    async def save_session(self, session_id: str, session_data: dict):
        """
        Save session data to Firestore.
        
        Args:
            session_id: Unique session identifier
            session_data: Dictionary containing session state
        """
        try:
            doc_ref = self.collection.document(session_id)
            await doc_ref.set(session_data, merge=True)
            # print(f"[PERSISTENCE] Saved session {session_id}")
        except Exception as e:
            print(f"[PERSISTENCE] Error saving session {session_id}: {e}")
            
    async def load_session(self, session_id: str) -> Optional[dict]:
        """
        Load session data from Firestore.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dictionary containing session state or None if not found
        """
        try:
            doc_ref = self.collection.document(session_id)
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"[PERSISTENCE] Error loading session {session_id}: {e}")
        return None

    async def delete_session(self, session_id: str):
        """Delete session from Firestore."""
        try:
            await self.collection.document(session_id).delete()
        except Exception as e:
            print(f"[PERSISTENCE] Error deleting session {session_id}: {e}")
