# debug_google_models.py
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY missing")
    exit()

try:
    client = genai.Client(api_key=api_key)
    print("Fetching models...")
    models = list(client.models.list(config={'page_size': 100}))
    
    print("\n✅ Available Models:")
    for m in models:
        # In ra tên model (thường là 'models/gemini-1.5-flash'...) 
        print(f"- {m.name}")

except Exception as e:
    print(f"\n❌ Error: {e}")