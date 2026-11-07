"""Quick test to verify all imports and basic functionality"""
import sys
print("Python version:", sys.version)

try:
    import tkinter as tk
    print("✓ tkinter imported")
except Exception as e:
    print(f"❌ tkinter error: {e}")

try:
    from dotenv import load_dotenv
    print("✓ dotenv imported")
except Exception as e:
    print(f"❌ dotenv error: {e}")

try:
    import qrcode
    print("✓ qrcode imported")
except Exception as e:
    print(f"❌ qrcode error: {e}")

try:
    from PIL import Image
    print("✓ PIL imported")
except Exception as e:
    print(f"❌ PIL error: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib imported")
except Exception as e:
    print(f"❌ matplotlib error: {e}")

try:
    from api_client_v2 import TrainAPIClientV2
    print("✓ api_client_v2 imported")
    
    api = TrainAPIClientV2()
    connected = api.check_api_connection()
    print(f"API Connection: {'✓ Connected' if connected else '❌ Not connected'}")
except Exception as e:
    print(f"❌ api_client_v2 error: {e}")

print("\nAll checks complete!")
input("Press Enter to exit...")

