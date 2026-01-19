import os
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

try:
    client = DeepgramClient() 
    print(f"\nChecking client.listen.v1.media...")
    media = client.listen.v1.media
    print(f"Media Attributes: {dir(media)}")

except Exception as e:
    print(f"Error: {e}")
