
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agent import AtlasAgent, AgentSession

async def test_streaming():
    print("🧪 Testing AtlasAgent Streaming...")
    
    # Minimal resume content for testing
    resume = "Michael Weed is an Agentic AI Engineer with experience in Atlas-G Protocol."
    agent = AtlasAgent(resume_content=resume)
    session = agent.create_session()
    
    query = "Tell me about Michael's experience."
    
    print(f"Query: {query}")
    
    event_counts = {
        "audit": 0,
        "stream": 0,
        "response": 0,
        "error": 0
    }
    
    full_text = ""
    
    async for update in agent.think(query, session):
        u_type = update["type"]
        event_counts[u_type] += 1
        
        if u_type == "stream":
            full_text += update["data"]["chunk"]
            # Print first few chunks to verify visually
            if event_counts["stream"] <= 3:
                print(f"  [STREAM] chunk: {update['data']['chunk'][:20]}...")
        
        elif u_type == "response":
            print(f"✅ Final Response received: {len(update['data']['content'])} chars")
            print(f"   Facts Verified: {update['data'].get('facts_verified')}")
        
    print("\nEvent Statistics:")
    for t, count in event_counts.items():
        print(f"  - {t}: {count}")
    
    assert event_counts["stream"] > 0, "No stream events generated"
    assert event_counts["response"] == 1, "Expected exactly one final response event"
    print("\n✨ Streaming Test PASSED")

if __name__ == "__main__":
    asyncio.run(test_streaming())
