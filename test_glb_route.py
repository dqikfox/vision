"""
Quick test to verify the GLB file can be served by the backend.
Run this after starting live_chat_app.py
"""
import requests


def test_glb_route():
    url = "http://localhost:8765/assets/ultron-avatar.glb"

    print(f"Testing GLB route: {url}")

    try:
        response = requests.head(url, timeout=5)
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"✓ Content-Length: {response.headers.get('content-length', 'N/A')} bytes")
        print(f"✓ Cache-Control: {response.headers.get('cache-control', 'N/A')}")

        if response.status_code == 200:
            print("\n✅ GLB route is working correctly!")
            return True
        else:
            print(f"\n⚠️ Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Backend not running. Start with: python live_chat_app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_glb_route()
