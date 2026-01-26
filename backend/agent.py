
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
import asyncio

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
    Refactored for Token Efficiency (Dynamic Context Injection).
    """
    
    # 1. CORE SYSTEM PROMPT (Always Sent) - Leaner
    CORE_SYSTEM_PROMPT = """You are the digital twin of Solution Architect and Agentic AI Engineer Michael Weed.
Your responses must be:
- Brief and technically accurate
- Grounded in the verified resume data provided
- Compliant with security protocols

You have expertise in Agentic AI Architecture, Cloud & Serverless (GCP/AWS), and Regulated Industries (Healthcare/FinTech).

When asked about projects, cite specific examples from the resume:
- Atlas Engine
- VoiceVerdict
- GeneDx
- Financial Compliance Auditor
- Sakura Sumi (Visual Token Arbitrage)
- Lemon Squeezy MCP TypeScript Server

NEVER use markdown headers. Use clean "blackspace" formatting (2 newlines between paragraphs).
If asked about a skill not in the resume, admit lack of experience.
NEVER list clients; only discuss project outcomes.

CONTACT FORM TRIGGERING:
- ONLY invoke the contact form if the user explicitly expresses intent to Hire Michael, Discuss Business, or Send Private Message.
- To trigger the form, output the hidden token: [TRIGGER_CONTACT_FORM]
- DO NOT output this token for general questions.
"""

    # 2. SPECIALIZED CONTEXTS (Injected on demand)
    
    # Context A: Atlas-G Connection (How do I connect?)
    # Trigger: "connect", "integrate", "mcp setup"
    MCP_CONNECT_CONTEXT = """
MCP CONNECTION PROTOCOL:
- If user asks how to connect:
    1. Reassure them: "You are already connected to me here."
    2. Explain that specialized integration is for AI IDEs (Cursor/Windsurf).
    3. If they are an ENGINEER asking for CONFIG/JSON:
       - Repo: https://github.com/MichaelWeed/atlas-g-protocol
       - Config:
         ```json
         {
           "mcpServers": {
             "atlas-g-protocol": {
               "command": "uv",
               "args": ["run", "backend/mcp_server.py"]
             }
           }
         }
         ```
"""

    # Context B: Lemon Squeezy MCP (Specific Project)
    # Trigger: "lemon", "squeezy", "payment"
    LEMON_MCP_CONTEXT = """
LEMON SQUEEZY MCP CONTEXT:
- This is a separate open-source project by Michael.
- It is a TypeScript server for managing payments and syncing orders to Salesforce.
- Source: GitHub.
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
        """Lazy-load the GenAI client."""
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
        """
        session.state = AgentState.THINKING
        
        # Initialize governance
        governance_context = GovernanceContext(
            session_id=session.session_id,
            query=query,
            violation_count=session.violation_count
        )
        session.governance_context = governance_context
        
        # Run compliance checks
        governance_context = await self.governance.run_compliance_check(governance_context)
        
        # Check enforcement
        compliance_result = ComplianceStatus.PASS
        for entry in governance_context.audit_log:
            if entry.action == "POLICY ENFORCEMENT":
                compliance_result = entry.status
                break
        
        # Stream audit log
        for entry in governance_context.audit_log:
            yield {"type": "audit", "data": entry.to_dict()}
        
        # Handle Block
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

        # Handle Warning
        if compliance_result == ComplianceStatus.WARN:
            session.state = AgentState.IDLE
            session.violation_count += 1
            yield {
                "type": "response",
                "data": {
                    "content": self.governance.generate_refusal_response(governance_context.query_type),
                    "blocked": False,
                    "violation_count": session.violation_count
                }
            }
            return
        
        # Domain Context Logic
        if governance_context.query_type in [QueryType.RESUME_DEEP_DIVE, QueryType.TECHNICAL_INQUIRY]:
            q_lower = query.lower()
            if any(k in q_lower for k in ["health", "medical", "genedx", "patient", "hipaa"]):
                session.context_domain = "Healthcare"
            elif any(k in q_lower for k in ["fintech", "banking", "finance", "pci", "bcu"]):
                session.context_domain = "FinTech"
            elif any(k in q_lower for k in ["legal", "voiceverdict"]):
                session.context_domain = "LegalTech"
        
        # --- DYNAMIC CONTEXT INJECTION (Token Efficiency) ---
        dynamic_system_prompt = self.CORE_SYSTEM_PROMPT
        audit_details = "Consulting Gemini 3 Flash"
        
        q_lower = query.lower()
        
        # Check for MCP Connection Intent
        if any(k in q_lower for k in ["connect", "integrate", "mcp setup", "mcp config", "ide"]):
             dynamic_system_prompt += self.MCP_CONNECT_CONTEXT
             audit_details += " + MCP Protocol"
             
        # Check for Lemon Squeezy Intent
        if any(k in q_lower for k in ["lemon", "squeezy", "payment", "salesforce"]):
             dynamic_system_prompt += self.LEMON_MCP_CONTEXT
             audit_details += " + Lemon Squeezy Context"
             
        session.state = AgentState.ACTING
        
        yield {
            "type": "audit",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "CONTEXT ROUTING",
                "status": "PASS",
                "details": f"Injecting specific context layers based on intent."
            }
        }
        
        yield {
            "type": "audit",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "GENERATING RESPONSE",
                "status": "PENDING",
                "details": audit_details
            }
        }
        
        domain_ctx = f"CURRENT DOMAIN CONTEXT: {session.context_domain}\n" if session.context_domain else ""
        context_prompt = f"""{domain_ctx}Resume Knowledge Graph:
{self.resume_content}

User Query: {query}

Provide a helpful, accurate response based solely on the resume data above."""

        try:
            session.state = AgentState.RESPONDING
            
            # Start streaming content generation
            stream = await self.client.aio.models.generate_content_stream(
                model=self.settings.model_robust,
                contents=context_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=dynamic_system_prompt + "\n\nCRITICAL: Ensure every sentence is grammatically complete and ends with terminal punctuation. Never stop mid-thought.",
                    temperature=0.4,
                    max_output_tokens=2048,
                )
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.text:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    # Yield incremental stream update
                    yield {
                        "type": "stream",
                        "data": {
                            "chunk": chunk_text,
                            "session_id": session.session_id
                        }
                    }
                    await asyncio.sleep(0)  # Force event loop yield for real-time ASAR flow
            
            # Contact Form/Lead Capture Logic
            is_submission = "[CONTACT FORM SUBMISSION]" in query
            contact_requested = False
            lead_capture_id = None
            session_terminated = False
            
            if is_submission:
                try:
                    from .leads import LeadCaptureService
                    from .notifications import EmailNotificationService
                    
                    lines = query.split('\n')
                    name = "Unknown"; email = "Unknown"; message = "No message"
                    for line in lines:
                        if line.startswith("Name:"): name = line.replace("Name:", "").strip()
                        elif line.startswith("Email:"): email = line.replace("Email:", "").strip()
                        elif line.startswith("Note:"): message = line.replace("Note:", "").strip()
                            
                    capture_service = LeadCaptureService(data_dir="data")
                    lead_capture_id = capture_service.capture(name, email, message)
                    
                    notification_service = EmailNotificationService()
                    notification_service.send_lead_alert({"id": lead_capture_id, "name": name, "email": email, "message": message})
                    
                    full_response = f"Thank you, {name}. Your transmission has been securely logged (Lead ID: {lead_capture_id}) and I have notified Michael directly. We will be in touch soon regarding your inquiry.\n\nThis session is now concluding. You may close the terminal at your convenience."
                    session_terminated = True
                except Exception as e:
                    print(f"Lead Capture Failed: {e}")
                    full_response = f"I apologize, but there was an internal error during the uplink process. Please contact Michael directly."
                    session_terminated = False
            
            if not is_submission:
                 contact_requested = "[TRIGGER_CONTACT_FORM]" in full_response
            
            # Governance Validation
            validated_response, governance_context = self.governance.validate_response(
                full_response,
                governance_context
            )
            
            is_trap = any("Hallucination Trap Triggered" in str(log.details) for log in governance_context.audit_log)
            if is_trap:
                session.state = AgentState.BLOCKED
                session.violation_count += 2
                yield {
                    "type": "response",
                    "data": {
                        "content": "⚠️ SECURITY ALERT: Deviation from verified resume facts detected. Hallucination attempt blocked.",
                        "blocked": True,
                        "violation_count": session.violation_count
                    }
                }
                return

            # Governance Decay (Reward)
            if governance_context.query_type in [QueryType.RESUME_DEEP_DIVE, QueryType.TECHNICAL_INQUIRY]:
                if session.violation_count > 0:
                    old_count = session.violation_count
                    session.violation_count = max(0, session.violation_count - 1)
                    yield {"type": "audit", "data": {"timestamp": datetime.utcnow().isoformat(), "action": "GOVERNANCE DECAY", "status": "PASS", "details": f"Strikes: {old_count} -> {session.violation_count}"}}
            
            # Final Stream
            for entry in governance_context.audit_log[-2:]:
                yield {"type": "audit", "data": entry.to_dict()}
            
            if lead_capture_id:
                yield {"type": "audit", "data": {"timestamp": datetime.utcnow().isoformat(), "action": "LEAD CAPTURED", "status": "PASS", "details": f"ID: {lead_capture_id}"}}

            yield {"type": "audit", "data": {"timestamp": datetime.utcnow().isoformat(), "action": "RESPONSE COMPLETE", "status": "PASS", "details": f"Verified {len(governance_context.verified_facts)} facts"}}
            
            yield {
                "type": "response",
                "data": {
                    "content": validated_response if validated_response else full_response,
                    "blocked": False,
                    "facts_verified": len(governance_context.verified_facts),
                    "claims_filtered": len(governance_context.blocked_claims),
                    "contact_requested": contact_requested,
                    "session_terminated": session_terminated
                }
            }
            
        except Exception as e:
            yield {"type": "error", "data": {"message": f"Agent error: {str(e)}", "recoverable": True}}
        
        finally:
            session.state = AgentState.IDLE
            await self.session_store.save_session(session.session_id, session.to_dict())

    async def query(self, query: str, session_id: Optional[str] = None) -> dict[str, Any]:
        """Non-streaming query interface."""
        session = self.get_session(session_id) if session_id else self.create_session()
        if not session: session = self.create_session()
        
        result = {"session_id": session.session_id, "audit_log": [], "response": None, "error": None}
        async for update in self.think(query, session):
            if update["type"] == "audit": result["audit_log"].append(update["data"])
            elif update["type"] == "response": result["response"] = update["data"]
            elif update["type"] == "error": result["error"] = update["data"]
        return result
