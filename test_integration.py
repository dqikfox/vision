"""
Test script to validate the 3D avatar integration in the main UI
Checks for common issues and reports status
"""

import requests


def test_integration():
    base_url = "http://localhost:8765"

    tests = []

    # Test 1: Main UI loads
    print("Testing main UI...")
    try:
        resp = requests.get(base_url, timeout=5)
        success = resp.status_code == 200 and "heroAvatar" in resp.text
        tests.append(("Main UI loads", success))
        if success:
            # Check if it's using canvas instead of img
            has_canvas = '<canvas id="heroAvatar"' in resp.text
            has_img = '<img id="heroAvatar"' in resp.text
            tests.append(("Canvas element present", has_canvas))
            tests.append(("Old img element removed", not has_img))
            # Three.js may be loaded via import map (three.module.js) or classic script (three.min.js)
            has_three = "three.min.js" in resp.text or "three.module.js" in resp.text or '"three"' in resp.text
            tests.append(("Three.js script tag present", has_three))
            tests.append(("GLTFLoader script tag present", "GLTFLoader" in resp.text))
            tests.append(("init3DAvatar function present", "init3DAvatar" in resp.text))
    except Exception as e:
        tests.append(("Main UI loads", False))
        print(f"  Error: {e}")

    # Test 2: GLB file accessible
    print("\nTesting GLB asset route...")
    try:
        resp = requests.head(f"{base_url}/assets/ultron-avatar.glb", timeout=5)
        if resp.status_code == 405:
            # HEAD not supported by this server version — fall back to GET
            resp = requests.get(f"{base_url}/assets/ultron-avatar.glb", timeout=5, stream=True)
        success = resp.status_code == 200
        tests.append(("GLB route responds", success))
        if success:
            tests.append(("Correct MIME type", resp.headers.get('content-type') == 'model/gltf-binary'))
            tests.append(("Cache headers present", 'cache-control' in resp.headers))
    except Exception as e:
        tests.append(("GLB route responds", False))
        print(f"  Error: {e}")

    # Test 3: Test page accessible
    print("\nTesting standalone test page...")
    try:
        resp = requests.get(f"{base_url}/test_3d_avatar.html", timeout=5)
        success = resp.status_code == 200
        tests.append(("Test page loads", success))
    except Exception as e:
        tests.append(("Test page loads", False))
        print(f"  Error: {e}")

    # Test 4: API health check
    print("\nTesting backend health...")
    try:
        resp = requests.get(f"{base_url}/api/health", timeout=5)
        success = resp.status_code == 200
        tests.append(("Backend healthy", success))
    except Exception as e:
        tests.append(("Backend healthy", False))
        print(f"  Error: {e}")

    # Print results
    print("\n" + "="*60)
    print("INTEGRATION TEST RESULTS")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("="*60)
    print(f"Total: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 All tests passed! The 3D avatar integration is working.")
        print("\nNext steps:")
        print("1. Open http://localhost:8765 in your browser")
        print("2. Wait for boot screen, then click to enter")
        print("3. Check that the center avatar is 3D and animated")
        print("4. Watch for state changes (listening, thinking, speaking)")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

    assert failed == 0, f"{failed} integration check(s) failed"

if __name__ == "__main__":
    test_integration()
