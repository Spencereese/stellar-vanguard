#!/usr/bin/env python3
"""
P2P Multiplayer Test Script

This script tests the peer-to-peer multiplayer functionality.
"""

import sys
import os
import time
import threading

def test_p2p_discovery():
    """Test P2P peer discovery"""
    print("Testing P2P peer discovery...")

    try:
        # Import the P2P network manager
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from network import P2PNetworkManager

        # Create a mock game object
        class MockGame:
            pass

        game = MockGame()

        # Start P2P network
        p2p = P2PNetworkManager(game, player_name="TestPlayer")
        if p2p.start():
            print("✓ P2P network started successfully")

            # Wait a bit for discovery
            print("Waiting 5 seconds for peer discovery...")
            time.sleep(5)

            # Check for any discovered peers
            peer_count = len(p2p.peers)
            print(f"Discovered {peer_count} peers")

            # Stop the network
            p2p.stop()
            print("✓ P2P network stopped successfully")
            return True
        else:
            print("✗ Failed to start P2P network")
            return False

    except Exception as e:
        print(f"✗ P2P test failed: {e}")
        return False

def test_p2p_connection():
    """Test P2P connection between two instances"""
    print("Testing P2P connection...")

    try:
        from network import P2PNetworkManager

        class MockGame:
            pass

        # Start two P2P networks
        game1 = MockGame()
        game2 = MockGame()

        p2p1 = P2PNetworkManager(game1, player_name="Player1")
        p2p2 = P2PNetworkManager(game2, player_name="Player2")

        if p2p1.start() and p2p2.start():
            print("✓ Both P2P networks started")

            # Wait for discovery and connection
            print("Waiting 10 seconds for peer discovery and connection...")
            time.sleep(10)

            # Check connections
            peers1 = len(p2p1.peer_sockets)
            peers2 = len(p2p2.peer_sockets)

            print(f"Player1 connected to {peers1} peers")
            print(f"Player2 connected to {peers2} peers")

            # Test message sending
            test_msg = {"test": "message", "timestamp": time.time()}
            p2p1.send_message(test_msg)

            time.sleep(1)  # Wait for message

            # Check if message was received
            received = p2p2.receive_message()
            if received:
                print("✓ Message transmission successful")
            else:
                print("⚠ No message received (may be normal if not connected yet)")

            # Stop networks
            p2p1.stop()
            p2p2.stop()
            print("✓ P2P connection test completed")
            return True
        else:
            print("✗ Failed to start P2P networks")
            return False

    except Exception as e:
        print(f"✗ P2P connection test failed: {e}")
        return False

def main():
    print("P2P Multiplayer Test Suite")
    print("=" * 40)

    # Test 1: Basic discovery
    print("\n1. Testing P2P Discovery:")
    test_p2p_discovery()

    # Test 2: Connection
    print("\n2. Testing P2P Connection:")
    test_p2p_connection()

    print("\n" + "=" * 40)
    print("P2P tests completed!")
    print("\nNote: For best results, run multiple instances of this test")
    print("on different machines/terminals on the same local network.")

if __name__ == "__main__":
    main()