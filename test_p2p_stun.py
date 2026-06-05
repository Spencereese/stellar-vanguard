#!/usr/bin/env python3
"""
Test script for P2P multiplayer with STUN NAT traversal
"""

import time
import threading
from network import P2PNetworkManager
from game import Game
import pygame

def test_p2p_networking():
    """Test P2P networking with STUN integration"""
    print("Testing P2P Multiplayer with STUN NAT Traversal")
    print("=" * 50)

    # Initialize pygame and game
    pygame.init()
    game = Game()

    # Create P2P network manager
    p2p = P2PNetworkManager(game, 'TestPlayer1')

    print("Starting P2P network...")
    p2p.start()

    print(f"Player ID: {p2p.player_id}")
    print(f"Public address: {p2p.public_address}")
    print(f"NAT type: {p2p.nat_type}")
    print(f"STUN discovered: {p2p.stun_discovered}")

    # Test message sending
    print("\nTesting message sending...")
    test_message = {
        "test": "Hello from P2P network!",
        "timestamp": time.time()
    }
    p2p.send_message(test_message)
    print("Test message sent")

    # Listen for messages for a few seconds
    print("\nListening for messages (5 seconds)...")
    start_time = time.time()
    messages_received = 0

    while time.time() - start_time < 5:
        message = p2p.receive_message()
        if message:
            messages_received += 1
            print(f"Received: {message}")

        time.sleep(0.1)

    print(f"Messages received: {messages_received}")

    # Stop network
    print("\nStopping P2P network...")
    p2p.stop()

    print("Test completed successfully!")
    return True

if __name__ == "__main__":
    test_p2p_networking()