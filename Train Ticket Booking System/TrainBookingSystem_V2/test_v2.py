import sys
print("=" * 60)
print("Testing V2 System...")
print("=" * 60)

try:
    print("\n1. Testing API Server Connection...")
    import requests
    import time
    time.sleep(1)

    try:
        r = requests.get('http://127.0.0.1:5001/', timeout=2)
        if 'V2' in str(r.json()):
            print("   ✓ API V2 server is RUNNING on port 5001")
            print(f"   Response: {r.json()}")
        else:
            print("   ✗ Wrong API version running")
    except Exception as e:
        print(f"   ✗ API V2 server is NOT running")
        print(f"   Error: {e}")
        print("\n   To start the server, run: python api_server_v2.py")
        sys.exit(1)

    print("\n2. Testing imports...")
    import tkinter as tk
    print("   ✓ tkinter imported")

    import matplotlib.pyplot as plt
    print("   ✓ matplotlib imported")

    from api_client_v2 import TrainAPIClientV2
    print("   ✓ api_client_v2 imported")

    print("\n3. Testing API client...")
    api = TrainAPIClientV2()
    if api.check_api_connection():
        print("   ✓ API client can connect to server")
    else:
        print("   ✗ API client cannot connect")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now run: python main_v2.py")
    print("\nOr double-click: START_V2.bat")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

