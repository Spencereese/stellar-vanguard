#!/usr/bin/env python3
"""
Simple Multiplayer Connection Test
Tests basic network connectivity without launching the full game.
"""

import socket
import threading
import time
import json

def test_server():
    """Test server functionality"""
    print("Starting test server...")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5556))  # Use different port for testing
    server_socket.listen(5)
    server_socket.settimeout(5.0)  # 5 second timeout

    clients = []

    def handle_client(client_socket, address):
        print(f"Client connected from {address}")
        try:
            # Send welcome message
            welcome = {"welcome": {"player_id": "test_player_1"}}
            data = json.dumps(welcome).encode('utf-8')
            client_socket.send(len(data).to_bytes(4, byteorder='big'))
            client_socket.send(data)

            # Wait for client message
            length_bytes = client_socket.recv(4)
            if length_bytes:
                length = int.from_bytes(length_bytes, byteorder='big')
                data = client_socket.recv(length)
                message = json.loads(data.decode('utf-8'))
                print(f"Received from client: {message}")

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    try:
        while len(clients) < 2:  # Wait for up to 2 clients
            try:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                clients.append(client_socket)
                print(f"Accepted client {len(clients)}")
            except socket.timeout:
                break
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server test complete")

def test_client():
    """Test client functionality"""
    print("Starting test client...")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5556))

        # Receive welcome message
        length_bytes = client_socket.recv(4)
        length = int.from_bytes(length_bytes, byteorder='big')
        data = client_socket.recv(length)
        message = json.loads(data.decode('utf-8'))
        print(f"Received welcome: {message}")

        # Send test message
        test_msg = {"connect": {"name": "TestClient"}}
        data = json.dumps(test_msg).encode('utf-8')
        client_socket.send(len(data).to_bytes(4, byteorder='big'))
        client_socket.send(data)
        print("Sent connect message")

        time.sleep(1)  # Wait a bit

    except Exception as e:
        print(f"Client error: {e}")
    finally:
        client_socket.close()
        print("Client test complete")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "client":
        test_client()
    else:
        # Start server in background
        server_thread = threading.Thread(target=test_server)
        server_thread.daemon = True
        server_thread.start()

        # Wait a moment then start client
        time.sleep(1)
        test_client()