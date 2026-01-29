
import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent import AtlasAgent, AgentSession
from backend.config import get_settings

async def test_streaming():
    print("🧪 Testing AtlasAgent Streaming...")
    settings = get_settings()
    
    # Load resume
    resume_path = "data/resume.txt"
    with open(resume_path, "r") as f:
        resume_content = f.read()
        
    agent = AtlasAgent(resume_content=resume_content)
    session = agent.create_session()
    
    query = "Tell me about Michael's experience."
    print(f"Query: {query}")
    
    stream_count = 0
    full_text = ""
    
    async for update in agent.think(query, session):
        u_type = update["type"]
        if u_type == "stream":
            chunk = update["data"]["chunk"]
            stream_count += 1
            full_text += chunk
            print(f"  [STREAM] chunk {stream_count}: {repr(chunk[:20])}...")
        elif u_type == "response":
            print(f"✅ Final Response received: {len(update['data']['content'])} chars")
            
    if stream_count > 0:
        print(f"✨ SUCCESS: Received {stream_count} stream chunks.")
    else:
        print("❌ FAILURE: No stream chunks received!")

if __name__ == "__main__":
    asyncio.run(test_streaming())
