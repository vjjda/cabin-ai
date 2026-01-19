import os
import inspect
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

try:
    client = DeepgramClient() 
    print(f"\nChecking signature of client.listen.v1.media.transcribe_file...")
    sig = inspect.signature(client.listen.v1.media.transcribe_file)
    print(f"Signature: {sig}")

except Exception as e:
    print(f"Error: {e}")

