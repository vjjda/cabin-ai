import deepgram
print(f"Deepgram Path: {deepgram.__file__}")
try:
    from deepgram import PrerecordedOptions
    print("✅ PrerecordedOptions found in root")
except ImportError:
    print("❌ PrerecordedOptions NOT found in root")
    
    # Try searching
    import pkgutil
    import inspect
    
    print("\nScanning submodules...")
    # (Simple scan logic or manual check)
