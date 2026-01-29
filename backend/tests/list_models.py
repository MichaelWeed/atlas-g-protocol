
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from google import genai

def list_models():
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)
    try:
        print("Listing models...")
        for model in client.models.list():
            if "gemini" in model.name:
                print(f"- {model.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
