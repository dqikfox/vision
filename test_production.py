"""Production readiness test suite for Vision accessibility operator."""

import asyncio
import json
import os
import sys
from pathlib import Path

import requests
import websockets


class ProductionTestSuite:
    """Test suite for verifying Vision is production ready."""

    def __init__(self):
        self.base_url = "http://localhost:8765"
        self.ws_url = "ws://localhost:8765/ws"
        self.test_results = []

    def log_result(self, test_name, passed, details=""):
        """Log a test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({"test": test_name, "status": status, "details": details})
        print(f"{'✓' if passed else '✗'} {test_name}: {status}")
        if details and not passed:
            print(f"  Details: {details}")

    def test_http_endpoints(self):
        """Test HTTP endpoints for production readiness."""
        print("\n=== Testing HTTP Endpoints ===")

        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            passed = response.status_code == 200
            self.log_result("Health endpoint", passed, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Health endpoint", False, str(e))

        # Test models endpoint
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=10)
            passed = response.status_code == 200
            self.log_result("Models endpoint", passed, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Models endpoint", False, str(e))

        # Test voices endpoint
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=10)
            passed = response.status_code == 200
            self.log_result("Voices endpoint", passed, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Voices endpoint", False, str(e))

    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time features."""
        print("\n=== Testing WebSocket Connection ===")

        try:
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                # Wait for initial message
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                self.log_result("WebSocket connection", True, "Connected successfully")

                # Parse initial message
                try:
                    init_msg = json.loads(response)
                    if init_msg.get("type") == "init":
                        self.log_result(
                            "WebSocket init message",
                            True,
                            f"Provider: {init_msg.get('provider')}, Model: {init_msg.get('model')}",
                        )
                except json.JSONDecodeError:
                    self.log_result("WebSocket init message", False, "Invalid JSON in init message")

                # Test model switching
                switch_message = {"type": "set_model", "provider": "ollama", "model": "cogito:latest"}

                await websocket.send(json.dumps(switch_message))
                self.log_result("Model switch command sent", True)

                # Wait for response (up to 3 messages)
                model_changed_received = False
                for i in range(3):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        response_data = json.loads(response)
                        if response_data.get("type") == "model_changed":
                            model_changed_received = True
                            self.log_result(
                                "Model changed notification",
                                True,
                                f"Provider: {response_data.get('provider')}, Model: {response_data.get('model')}",
                            )
                            break
                    except (TimeoutError, json.JSONDecodeError):
                        continue

                if not model_changed_received:
                    self.log_result("Model changed notification", False, "No model_changed message received")

        except Exception as e:
            self.log_result("WebSocket connection", False, str(e))

    def test_file_permissions(self):
        """Test file permissions and security."""
        print("\n=== Testing File Permissions ===")

        # Check if critical files exist and are readable
        critical_files = ["live_chat_app.py", "live_chat_ui.html", "requirements.txt"]

        for file_path in critical_files:
            if Path(file_path).exists():
                try:
                    # Try to read the file with proper encoding
                    with open(file_path, encoding="utf-8") as f:
                        f.read(1)  # Read just one character to test readability
                    self.log_result(f"File access: {file_path}", True)
                except PermissionError:
                    self.log_result(f"File access: {file_path}", False, "Permission denied")
                except Exception as e:
                    self.log_result(f"File access: {file_path}", False, str(e))
            else:
                self.log_result(f"File existence: {file_path}", False, "File not found")

    def test_environment_variables(self):
        """Test environment variable configuration."""
        print("\n=== Testing Environment Variables ===")

        # Check for required environment variables
        required_vars = ["ELEVENLABS_API_KEY"]

        optional_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GITHUB_TOKEN"]

        for var in required_vars:
            if os.getenv(var):
                self.log_result(f"Required env var: {var}", True)
            else:
                self.log_result(f"Required env var: {var}", False, "Not set")

        for var in optional_vars:
            if os.getenv(var):
                self.log_result(f"Optional env var: {var}", True, "Set")
            else:
                self.log_result(f"Optional env var: {var}", True, "Not set (optional)")

    def test_dependencies(self):
        """Test that all dependencies are installed."""
        print("\n=== Testing Dependencies ===")

        # Try importing key modules
        key_modules = ["fastapi", "uvicorn", "websockets", "numpy", "pyautogui", "elevenlabs", "openai", "ollama"]

        for module in key_modules:
            try:
                __import__(module)
                self.log_result(f"Import module: {module}", True)
            except ImportError as e:
                self.log_result(f"Import module: {module}", False, str(e))

    def test_accessibility_features(self):
        """Test accessibility features."""
        print("\n=== Testing Accessibility Features ===")

        # Test that high contrast mode can be enabled via API
        # This would require a specific endpoint, but we can check if the feature exists
        try:
            # Check if the UI has accessibility features by examining the HTML
            with open("live_chat_ui.html", encoding="utf-8") as f:
                content = f.read()

            accessibility_checks = [
                ("High contrast mode", "toggleHighContrast"),
                ("Keyboard navigation", "toggleKeyboardNav"),
                ("Voice settings", "set_voice_settings"),
            ]

            for feature_name, feature_function in accessibility_checks:
                if feature_function in content:
                    self.log_result(f"Accessibility feature: {feature_name}", True)
                else:
                    self.log_result(f"Accessibility feature: {feature_name}", False, "Not found in UI")

        except FileNotFoundError:
            self.log_result("Accessibility features", False, "UI file not found")
        except Exception as e:
            self.log_result("Accessibility features", False, str(e))

    def run_all_tests(self):
        """Run all production readiness tests."""
        print("=== Vision Production Readiness Test Suite ===")

        # Run synchronous tests
        self.test_http_endpoints()
        self.test_file_permissions()
        self.test_environment_variables()
        self.test_dependencies()
        self.test_accessibility_features()

        # Run async tests
        asyncio.run(self.test_websocket_connection())

        # Print summary
        print("\n=== Test Summary ===")
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        total_tests = len(self.test_results)

        print(f"Passed: {passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("🎉 All tests passed! Vision is ready for production.")
            return True
        else:
            print("⚠️  Some tests failed. Please review the results above.")
            return False


def main():
    """Run the production test suite."""
    tester = ProductionTestSuite()
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
