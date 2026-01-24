import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

async def verify_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Skipping test: GOOGLE_API_KEY not found")
        return

    client = genai.Client(api_key=api_key)
    
    # "Law" models from images
    models_to_test = [
        "gemini-3-flash-preview",
        "gemini-3-pro-preview"
    ]
    
    print(f"Verifying access to models: {models_to_test}")
    
    for model_id in models_to_test:
        print(f"\nTesting {model_id}...")
        try:
            # Simple generation request
            response = await client.aio.models.generate_content(
                model=model_id,
                contents="Hello, verify your identity.",
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                )
            )
            if response.text:
                print(f"✅ SUCCESS: {model_id} responded: {response.text.strip()}")
            else:
                 print(f"⚠️  SUCCESS (Empty Response): {model_id} (Check safety filters?)")
        except Exception as e:
            print(f"❌ FAILED: {model_id}")
            print(f"Error details: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_models())
