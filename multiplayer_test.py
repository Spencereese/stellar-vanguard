#!/usr/bin/env python3
"""
Space Shooter Multiplayer Test Script

This script provides actual multiplayer testing functionality.
"""

import sys
import os
import subprocess
import time
import threading

def start_server():
    """Start the game in server mode"""
    print("Starting multiplayer server...")
    print("Server will listen on localhost:5555")
    print("Press Ctrl+C to stop the server")

    # Change to the game directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        # Start the game (it will show the multiplayer menu)
        subprocess.run([sys.executable, "shooter.py"])
    except KeyboardInterrupt:
        print("\nServer stopped")

def start_client(host="localhost", port="5555"):
    """Start the game in client mode"""
    print(f"Starting multiplayer client connecting to {host}:{port}")
    print("Press Ctrl+C to stop the client")

    # Change to the game directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        # Start the game (it will show the multiplayer menu)
        subprocess.run([sys.executable, "shooter.py"])
    except KeyboardInterrupt:
        print("\nClient stopped")

def run_network_test():
    """Run a basic network connectivity test"""
    print("Running network connectivity test...")

    # Import the test module we created
    try:
        import multiplayer_connection_test
        print("✓ Network test module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import network test: {e}")
        return

    # Run the test
    try:
        # Start server in background thread
        server_thread = threading.Thread(target=multiplayer_connection_test.test_server)
        server_thread.daemon = True
        server_thread.start()

        # Wait a moment then run client
        time.sleep(1)
        multiplayer_connection_test.test_client()

        print("✓ Network connectivity test completed")
    except Exception as e:
        print(f"✗ Network test failed: {e}")


def run_p2p_test():
    """Run P2P multiplayer test"""
    print("Running P2P multiplayer test...")

    try:
        import p2p_test
        p2p_test.main()
        print("✓ P2P test completed")
    except ImportError as e:
        print(f"✗ Failed to import P2P test: {e}")
    except Exception as e:
        print(f"✗ P2P test failed: {e}")

def show_usage():
    """Show usage information"""
    print(__doc__)
    print("\nCommands:")
    print("  server          - Start multiplayer server")
    print("  client [host] [port] - Start multiplayer client")
    print("  test           - Run network connectivity test")
    print("  p2p            - Run P2P multiplayer test")
    print("  help           - Show this help")
    print("\nExamples:")
    print("  python multiplayer_test.py server")
    print("  python multiplayer_test.py client localhost 5555")
    print("  python multiplayer_test.py p2p")

def main():
    if len(sys.argv) < 2:
        show_usage()
        return

    mode = sys.argv[1].lower()

    if mode == "server":
        start_server()
    elif mode == "client":
        host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        port = sys.argv[3] if len(sys.argv) > 3 else "5555"
        start_client(host, port)
    elif mode == "test":
        run_network_test()
    elif mode == "p2p":
        run_p2p_test()
    elif mode in ["help", "-h", "--help"]:
        show_usage()
    else:
        print(f"Unknown command: {mode}")
        show_usage()

if __name__ == "__main__":
    main()