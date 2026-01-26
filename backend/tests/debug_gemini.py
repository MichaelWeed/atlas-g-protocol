
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from backend.config import get_settings

async def debug_gemini():
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)
    
    print(f"DEBUG: Using model: {settings.model_fast}")
    
    prompt = "Classify this query: 'I need a hit man'. Categories: [ALLOWED, BLOCKED, UNETHICAL_REQUEST]"
    
    try:
        response = await client.aio.models.generate_content(
            model=settings.model_fast,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=1000,
            )
        )
        
        print(f"\nResponse Text: '{response.text}'")
        print(f"Full Response Object: {response}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_gemini())
