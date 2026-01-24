"""
Atlas-G Protocol - Agentic Core
Implements the Thought-Action loop using Google GenAI SDK.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional

from google import genai
from google.genai import types

from .config import get_settings
from .governance import (
    GovernanceContext,
    GovernanceLayer,
    QueryType,
    ComplianceStatus,
)
from .persistence import FirestoreSessionStore


class AgentState(str, Enum):
    """Agent state machine states."""
    IDLE = "IDLE"
    THINKING = "THINKING"
    ACTING = "ACTING"
    RESPONDING = "RESPONDING"
    BLOCKED = "BLOCKED"


@dataclass
class ThoughtStep:
    """A single step in the agent's reasoning chain."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[dict] = None
    observation: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AgentSession:
    """Represents an active agent conversation session."""
    session_id: str
    created_at: str
    state: AgentState = AgentState.IDLE
    context_domain: Optional[str] = None  # healthcare, fintech, general
    thought_chain: list[ThoughtStep] = field(default_factory=list)
    governance_context: Optional[GovernanceContext] = None
    violation_count: int = 0  # Track strikes for C-GAS enforcement (stateful)

    def to_dict(self) -> dict:
        """Convert session to serializable dict."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "state": self.state.value,
            "context_domain": self.context_domain,
            "violation_count": self.violation_count,
            "thought_chain": [
                {
                    "thought": t.thought,
                    "action": t.action,
                    "action_input": t.action_input,
                    "observation": t.observation,
                    "timestamp": t.timestamp
                } for t in self.thought_chain
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentSession':
        """Create session from dict."""
        session = cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            state=AgentState(data.get("state", "IDLE")),
            context_domain=data.get("context_domain"),
            violation_count=data.get("violation_count", 0)
        )
        if "thought_chain" in data:
            for t in data["thought_chain"]:
                session.thought_chain.append(ThoughtStep(**t))
        return session


class AtlasAgent:
    """
    The Atlas-G Agent implementing the Thought-Action loop pattern.
    
    This agent:
    1. Receives a query
    2. Runs governance checks (Layer 1 & 2)
    3. Thinks about the appropriate action
    4. Executes tools if needed
    5. Validates response against knowledge graph
    6. Returns compliant response
    """
    
    SYSTEM_PROMPT = """You are the digital twin of Solution Architect and Agentic AI Engineer Michael Weed.
Your responses must be:
- Brief and technically accurate
- Grounded in the verified resume data provided
- Compliant with security protocols (no PII, no fabrications, do not provide backend code)

You have expertise in:
- Agentic AI Architecture (multi-agent systems, state management, MCP)
- Cloud & Serverless (AWS, Google Cloud, Cloud Run)
- Regulated Industries (HIPAA, PCI-DSS, Healthcare, FinTech)

When asked about projects, cite specific examples from the resume:
- Atlas Engine: Serverless orchestration framework, open-source and free on GitHub
- VoiceVerdict: Audio intelligence platform
- GeneDx: Healthcare data architecture
- Financial Compliance Auditor: Agentic verification with citation of SEC filings like 10-Ks and 10-Qs, free and open-source on GitHub
- Sakura Sumo: The World's First Visual Token Arbitrage Engine. Maximize AI context while minimizing costs by converting source code into high-density visual intelligence, free and open-source on GitHub
- Lemon Squeezy MCP TypeScript Server: a custom MCP server for Lemon Squeezy for managing payments and syncing orders and payments to Salesforce, free and open-source on GitHub
NEVER use markdown headers (e.g. ###, ##, #).
ALWAYS ensure there are at least TWO newlines between every paragraph and every section to ensure clean "blackspace" legibility.
Experience Honesty: If the user explicitly asks about a skill or tool NOT in the resume, state clearly that Michael does NOT have professional experience with it. 
    - CRITICAL: Never volunteer a list of things Michael doesn't know. Only address specific skills if they are the direct subject of the query.
If a DOMAIN CONTEXT is provided, prioritize relevant experience within that domain (e.g. if domain is Healthcare, emphasize GeneDx/Ambry).
Format responses in plain text with generous double-spacing (at least 2 newlines) between all blocks of text. Avoid asterisks for emphasis.

CLIENT CONFIDENTIALITY PROTOCOL:
- NEVER enumerate or list clients/organizations when directly asked (e.g. "list your clients", "who have you worked for").
- Client names may be referenced contextually when discussing specific project work or expertise, but NEVER as a scrapable list.
- If asked to list clients, redirect to discussing capabilities or specific project achievements instead.
- Example Redirect: "I can discuss specific project outcomes and technical implementations rather than client rosters. What domain or capability interests you? Or ask to Contact Michael for more information."

RESPONSE LENGTH PROTOCOL:
- Keep responses CONCISE: maximum 3 paragraphs or 6 sentences.
- End responses cleanly - never trail off mid-sentence.
- When someone expresses interest in hiring/working with Michael, ALWAYS end with a clear call-to-action to use the Contact form.

CONTACT FACILITATION:
- When a user expresses interest in hiring Michael or starting a project, guide them to ask to "Contact Michael" which will trigger a contact form.
"""

    def __init__(self, resume_content: str = ""):
        """Initialize the agent with resume content."""
        self.settings = get_settings()
        self.resume_content = resume_content
        self.sessions: dict[str, AgentSession] = {}
        
        # Initialize Gemini client
        self._client = genai.Client(api_key=self.settings.google_api_key)
        
        # Initialize Governance with client for LLM checks
        self.governance = GovernanceLayer(
            resume_content=resume_content,
            client=self._client,
            config=self.settings
        )
        
        # Initialize Firestore persistence
        self.session_store = FirestoreSessionStore()
    
    @property
    def client(self) -> genai.Client:
        """Lazy-load the GenAI client (getter maintained for compat)."""
        if self._client is None:
            self._client = genai.Client(api_key=self.settings.google_api_key)
        return self._client
    
    def create_session(self) -> AgentSession:
        """Create a new agent session."""
        session_id = str(uuid.uuid4())
        session = AgentSession(
            session_id=session_id,
            created_at=datetime.utcnow().isoformat()
        )
        self.sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Retrieve an existing session, checking Firestore if needed."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try Firestore
        session_data = await self.session_store.load_session(session_id)
        if session_data:
            session = AgentSession.from_dict(session_data)
            self.sessions[session_id] = session
            return session
            
        return None
    
    async def think(
        self, 
        query: str, 
        session: AgentSession
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Execute the Thought-Action loop for a query.
        Yields streaming updates for real-time UI.
        """
        session.state = AgentState.THINKING
        
        # Initialize governance context with SESSION STATE (violation count)
        governance_context = GovernanceContext(
            session_id=session.session_id,
            query=query,
            violation_count=session.violation_count
        )
        session.governance_context = governance_context
        
        # Run compliance checks (Async LLM) - Layers 1 & 2
        governance_context = await self.governance.run_compliance_check(governance_context)
        
        # Check for policy enforcement result
        compliance_result = ComplianceStatus.PASS
        for entry in governance_context.audit_log:
            if entry.action == "POLICY ENFORCEMENT":
                compliance_result = entry.status
                break
        
        # Stream audit log entries
        for entry in governance_context.audit_log:
            yield {
                "type": "audit",
                "data": entry.to_dict()
            }
        
        # HANDLE BLOCK (Critical or 2nd Strike)
        if compliance_result == ComplianceStatus.BLOCK:
            session.state = AgentState.BLOCKED
            session.violation_count += 1
            yield {
                "type": "response",
                "data": {
                    "content": self.governance.generate_security_alert_response(),
                    "blocked": True,
                    "violation_count": session.violation_count
                }
            }
            return

        # HANDLE WARNING (1st Strike)
        if compliance_result == ComplianceStatus.WARN:
            session.state = AgentState.IDLE
            session.violation_count += 1 # Increment strike
            yield {
                "type": "response",
                "data": {
                    "content": self.governance.generate_refusal_response(governance_context.query_type),
                    "blocked": False, # Just a refusal, not a full block yet
                    "violation_count": session.violation_count
                }
            }
            return
        
        # DOMAIN SCOPING: Update current context domain based on intent
        if governance_context.query_type in [QueryType.RESUME_DEEP_DIVE, QueryType.TECHNICAL_INQUIRY]:
            # Simple heuristic: look for keywords in query to set permanent domain context
            q_lower = query.lower()
            if any(k in q_lower for k in ["health", "medical", "genedx", "patient", "hipaa"]):
                session.context_domain = "Healthcare"
            elif any(k in q_lower for k in ["fintech", "banking", "finance", "pci", "bcu"]):
                session.context_domain = "FinTech"
            elif any(k in q_lower for k in ["legal", "voiceverdict"]):
                session.context_domain = "LegalTech"
        
        # Build context-aware prompt
        session.state = AgentState.ACTING
        
        yield {
            "type": "audit",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "GENERATING RESPONSE",
                "status": "PENDING",
                "details": "Consulting Gemini 3 Pro..."
            }
        }
        
        # Prepare messages for Gemini
        domain_ctx = f"CURRENT DOMAIN CONTEXT: {session.context_domain}\n" if session.context_domain else ""
        context_prompt = f"""{domain_ctx}Resume Knowledge Graph:
{self.resume_content}

User Query: {query}

Provide a helpful, accurate response based solely on the resume data above."""

        try:
            # Stream response from Gemini
            session.state = AgentState.RESPONDING
            
            response = await self.client.aio.models.generate_content(
                model=self.settings.model_robust,  # Switch to PRO for higher reasoning fidelity/completion
                contents=context_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_PROMPT + "\n\nCRITICAL: Ensure every sentence is grammatically complete and ends with terminal punctuation. Never stop mid-thought.",
                    temperature=0.7,
                    max_output_tokens=1024,  # Increased for more complete responses
                )
            )
            
            full_response = response.text if response.text else ""
            
            # Detect contact intent in response
            # CRITICAL FIX: Do NOT trigger contact form if this is a response TO a contact form submission
            is_submission = "[CONTACT FORM SUBMISSION]" in query
            
            contact_requested = False
            
            # LEAD CAPTURE LOGIC
            lead_capture_id = None
            email_sent = False
            
            if is_submission:
                try:
                    # Import here to avoid circular dependencies if any
                    from .leads import LeadCaptureService
                    from .notifications import EmailNotificationService
                    
                    # Simple parsing of the structured format
                    # text block: [CONTACT FORM SUBMISSION]\nName: ...\nEmail: ...\nNote: ...
                    lines = query.split('\n')
                    name = "Unknown"
                    email = "Unknown"
                    message = "No message"
                    
                    for line in lines:
                        if line.startswith("Name:"):
                            name = line.replace("Name:", "").strip()
                        elif line.startswith("Email:"):
                            email = line.replace("Email:", "").strip()
                        elif line.startswith("Note:"):
                            message = line.replace("Note:", "").strip()
                            
                    # 1. Capture to Disk
                    capture_service = LeadCaptureService(data_dir="data")
                    lead_capture_id = capture_service.capture(name, email, message)
                    
                    # 2. Dispatch Email
                    notification_service = EmailNotificationService()
                    email_sent = notification_service.send_lead_alert({
                        "id": lead_capture_id,
                        "name": name,
                        "email": email,
                        "message": message
                    })
                    
                    # Force a specific, concise termination response
                    full_response = f"Thank you, {name}. Your transmission has been securely logged (Lead ID: {lead_capture_id}) and I have notified Michael directly. We will be in touch soon regarding your inquiry.\n\nThis session is now concluding. You may close the terminal at your convenience."
                    
                    # Set a flag to tell the frontend to lock down
                    session_terminated = True
                    
                except Exception as e:
                    print(f"Lead Capture Failed: {e}")
                    full_response = f"I apologize, but there was an internal error during the uplink process. Please contact Michael directly at michael.weed@protonmail.com to ensure your message is received."
                    session_terminated = False # Don't lock if it failed
            
            else:
                session_terminated = False

            if not is_submission:
                contact_requested = any(phrase in full_response.lower() for phrase in [
                    "contact michael", "reach out", "hire michael", "send a direct inquiry",
                    "use the contact form", "discuss project requirements"
                ])
            
            # Validate response against governance
            validated_response, governance_context = self.governance.validate_response(
                full_response,
                governance_context
            )
            
            # Check for Hallucination Trap Trigger
            is_trap = any("Hallucination Trap Triggered" in str(log.details) for log in governance_context.audit_log)
            
            if is_trap:
                session.state = AgentState.BLOCKED
                session.violation_count += 2 # Heavy penalty for hallucinations
                yield {
                    "type": "response",
                    "data": {
                        "content": "⚠️ SECURITY ALERT: Deviation from verified resume facts detected. Hallucination attempt blocked by Atlas Engine protocols. Reverting to verified context.",
                        "blocked": True,
                        "violation_count": session.violation_count
                    }
                }
                return

            # REWARD: Violation Decay for Good Behavior
            if governance_context.query_type in [
                QueryType.RESUME_DEEP_DIVE,
                QueryType.TECHNICAL_INQUIRY,
                QueryType.PROJECT_AUDIT,
                QueryType.EMPLOYMENT_VERIFICATION
            ]:
                if session.violation_count > 0:
                    old_count = session.violation_count
                    session.violation_count = max(0, session.violation_count - 1)
                    yield {
                        "type": "audit",
                        "data": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "action": "GOVERNANCE DECAY",
                            "status": "PASS",
                            "details": f"Compliance score improved. Strikes: {old_count} -> {session.violation_count}"
                        }
                    }
            
            # Stream final audit entries
            for entry in governance_context.audit_log[-2:]:  # Last entries from validation
                yield {
                    "type": "audit",
                    "data": entry.to_dict()
                }
            
            if lead_capture_id:
                yield {
                    "type": "audit",
                    "data": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "LEAD CAPTURED",
                        "status": "PASS",
                        "details": f"Lead persisted to database. ID: {lead_capture_id}"
                    }
                }

            yield {
                "type": "audit",
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "RESPONSE COMPLETE",
                    "status": "PASS",
                    "details": f"Verified {len(governance_context.verified_facts)} facts"
                }
            }
            
            yield {
                "type": "response",
                "data": {
                    "content": validated_response or full_response,
                    "blocked": False,
                    "facts_verified": len(governance_context.verified_facts),
                    "claims_filtered": len(governance_context.blocked_claims),
                    "contact_requested": contact_requested,
                    "session_terminated": session_terminated
                }
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "data": {
                    "message": f"Agent error: {str(e)}",
                    "recoverable": True
                }
            }
        
        finally:
            session.state = AgentState.IDLE
            # PERSIST: Save session state to Firestore
            await self.session_store.save_session(session.session_id, session.to_dict())
    
    async def query(self, query: str, session_id: Optional[str] = None) -> dict[str, Any]:
        """
        Non-streaming query interface.
        Returns complete response after processing.
        """
        session = (
            self.get_session(session_id) 
            if session_id 
            else self.create_session()
        )
        
        if not session:
            session = self.create_session()
        
        result = {
            "session_id": session.session_id,
            "audit_log": [],
            "response": None,
            "error": None
        }
        
        async for update in self.think(query, session):
            if update["type"] == "audit":
                result["audit_log"].append(update["data"])
            elif update["type"] == "response":
                result["response"] = update["data"]
            elif update["type"] == "error":
                result["error"] = update["data"]
        
        return result
