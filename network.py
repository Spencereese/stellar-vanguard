import socket
import threading
import json
import time
import queue
import select
from config import *
from stun import get_public_address, detect_nat_type

class NetworkManager:
    """Handles network communication for multiplayer"""

    def __init__(self, game, is_server=False, host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT):
        self.game = game
        self.is_server = is_server
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        self.receive_thread = None
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue()
        self.players = {}  # player_id -> player_data
        self.player_id = None
        self.last_update = time.time()

    def start(self):
        """Start the network connection"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)

            if self.is_server:
                self.socket.bind((self.host, self.port))
                self.socket.listen(MAX_PLAYERS)
                print(f"Server started on {self.host}:{self.port}")
                self.running = True
                self.receive_thread = threading.Thread(target=self._server_listen)
                self.receive_thread.daemon = True
                self.receive_thread.start()
            else:
                self.socket.connect((self.host, self.port))
                self.connected = True
                self.running = True
                self.receive_thread = threading.Thread(target=self._client_receive)
                self.receive_thread.daemon = True
                self.receive_thread.start()
                # Send connect message
                self.send_message({MSG_CONNECT: {"name": f"Player_{len(self.players) + 1}"}})

            # Start send thread
            send_thread = threading.Thread(target=self._send_loop)
            send_thread.daemon = True
            send_thread.start()

            return True
        except Exception as e:
            print(f"Failed to start network: {e}")
            return False

    def stop(self):
        """Stop the network connection"""
        self.running = False
        self.connected = False
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)

    def send_message(self, message):
        """Queue a message to be sent"""
        if self.connected:
            self.send_queue.put(message)

    def receive_message(self):
        """Get a received message from the queue"""
        try:
            return self.receive_queue.get_nowait()
        except queue.Empty:
            return None

    def update_player(self, player_data):
        """Send player update to server/other clients"""
        if self.connected and time.time() - self.last_update > 1.0 / NETWORK_UPDATE_RATE:
            self.send_message({
                MSG_PLAYER_UPDATE: {
                    "id": self.player_id,
                    "x": player_data["x"],
                    "y": player_data["y"],
                    "health": player_data["health"],
                    "weapon": player_data["weapon"],
                    "powerups": player_data["powerups"]
                }
            })
            self.last_update = time.time()

    def _send_loop(self):
        """Continuously send queued messages"""
        while self.running:
            try:
                message = self.send_queue.get(timeout=0.1)
                if self.socket:
                    data = json.dumps(message).encode('utf-8')
                    if self.is_server:
                        # Server broadcasts to all clients
                        for client_socket in self.players.values():
                            try:
                                client_socket.send(len(data).to_bytes(4, byteorder='big'))
                                client_socket.send(data)
                            except:
                                pass
                    else:
                        # Client sends to server
                        self.socket.send(len(data).to_bytes(4, byteorder='big'))
                        self.socket.send(data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Send error: {e}")
                self.connected = False
                break

    def _client_receive(self):
        """Client receive loop"""
        while self.running and self.connected:
            try:
                # Receive message length
                length_bytes = self.socket.recv(4)
                if not length_bytes:
                    break
                length = int.from_bytes(length_bytes, byteorder='big')

                # Receive message data
                data = self.socket.recv(length)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))
                self.receive_queue.put(message)

            except Exception as e:
                print(f"Receive error: {e}")
                self.connected = False
                break

    def _server_listen(self):
        """Server listen for new connections"""
        self.socket.settimeout(1.0)  # Add timeout to make it non-blocking
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"New connection from {address}")

                # Generate unique player ID
                player_id = f"player_{len(self.players) + 1}"
                self.players[player_id] = client_socket

                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, player_id))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue  # Timeout is expected, continue listening
            except OSError:
                break  # Socket closed
            except Exception as e:
                print(f"Server listen error: {e}")
                break

    def _handle_client(self, client_socket, player_id):
        """Handle individual client connection"""
        print(f"Handling client {player_id}")
        self.players[player_id] = client_socket

        try:
            while self.running:
                # Receive message length
                length_bytes = client_socket.recv(4)
                if not length_bytes:
                    break
                length = int.from_bytes(length_bytes, byteorder='big')

                # Receive message data
                data = client_socket.recv(length)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))

                # Handle message
                if MSG_CONNECT in message:
                    # Send welcome message with player ID
                    welcome_msg = {
                        "welcome": {
                            "player_id": player_id,
                            "game_state": self._get_game_state()
                        }
                    }
                    self._send_to_client(client_socket, welcome_msg)
                    print(f"Sent welcome to {player_id}")
                elif MSG_PLAYER_UPDATE in message:
                    # Store player data and broadcast to other clients
                    update_data = message[MSG_PLAYER_UPDATE]
                    update_data["id"] = player_id  # Ensure ID is set

                    # Broadcast to all other clients
                    for pid, sock in list(self.players.items()):
                        if pid != player_id:
                            try:
                                self._send_to_client(sock, {MSG_PLAYER_UPDATE: update_data})
                            except Exception as e:
                                print(f"Failed to send to {pid}: {e}")
                                # Remove disconnected client
                                if pid in self.players:
                                    del self.players[pid]
                elif MSG_PROJECTILE_UPDATE in message:
                    # Broadcast projectile updates to other clients
                    projectile_data = message[MSG_PROJECTILE_UPDATE]
                    projectile_data["id"] = player_id

                    for pid, sock in list(self.players.items()):
                        if pid != player_id:
                            try:
                                self._send_to_client(sock, {MSG_PROJECTILE_UPDATE: projectile_data})
                            except Exception as e:
                                print(f"Failed to send projectile update to {pid}: {e}")
                                if pid in self.players:
                                    del self.players[pid]
                elif MSG_ENEMY_UPDATE in message:
                    # Broadcast enemy updates to all clients
                    enemy_data = message[MSG_ENEMY_UPDATE]
                    enemy_data["id"] = player_id

                    for pid, sock in list(self.players.items()):
                        if pid != player_id:
                            try:
                                self._send_to_client(sock, {MSG_ENEMY_UPDATE: enemy_data})
                            except Exception as e:
                                print(f"Failed to send enemy update to {pid}: {e}")
                                if pid in self.players:
                                    del self.players[pid]

        except Exception as e:
            print(f"Client {player_id} handler error: {e}")
        finally:
            print(f"Client {player_id} disconnected")
            if player_id in self.players:
                del self.players[player_id]
            try:
                client_socket.close()
            except:
                pass

    def _send_to_client(self, client_socket, message):
        """Send message to specific client"""
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.send(len(data).to_bytes(4, byteorder='big'))
            client_socket.send(data)
        except:
            pass

    def _get_game_state(self):
        """Get current game state for new players"""
        return {
            "level": self.game.level if hasattr(self.game, 'level') else 1,
            "enemies": len(self.game.enemies) if hasattr(self.game, 'enemies') else 0,
            "powerups": len(self.game.powerups) if hasattr(self.game, 'powerups') else 0
        }


class P2PNetworkManager:
    """Handles peer-to-peer network communication for multiplayer"""

    def __init__(self, game, player_name="Player", broadcast_port=5556):
        self.game = game
        self.player_name = player_name
        self.broadcast_port = broadcast_port
        self.peers = {}  # peer_id -> (ip, port, socket)
        self.peer_info = {}  # peer_id -> player_data
        self.player_id = f"p2p_{int(time.time())}_{player_name}"
        self.running = False
        self.receive_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.broadcast_socket = None
        self.peer_sockets = {}  # peer_id -> socket
        self.threads = []
        self.last_broadcast = 0
        self.last_update = time.time()

        # STUN/NAT traversal
        self.public_address = None
        self.nat_type = None
        self.stun_discovered = False

    def _discover_public_address(self):
        """Discover public IP and port using STUN"""
        try:
            self.public_address = get_public_address()
            self.nat_type, _ = detect_nat_type()
            self.stun_discovered = True
            print(f"P2P: STUN discovered public address: {self.public_address}, NAT type: {self.nat_type}")
        except Exception as e:
            print(f"P2P: STUN discovery failed: {e}")
            # Fallback to local address
            self.public_address = (socket.gethostbyname(socket.gethostname()), self.broadcast_port)
            self.nat_type = "unknown"
            self.stun_discovered = False

    def start(self):
        """Start P2P networking"""
        try:
            # Discover public address using STUN
            self._discover_public_address()

            # Start broadcast listener for peer discovery
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.broadcast_socket.bind(('', self.broadcast_port))

            self.running = True

            # Start threads
            broadcast_thread = threading.Thread(target=self._broadcast_listener)
            broadcast_thread.daemon = True
            broadcast_thread.start()
            self.threads.append(broadcast_thread)

            peer_thread = threading.Thread(target=self._peer_listener)
            peer_thread.daemon = True
            peer_thread.start()
            self.threads.append(peer_thread)

            send_thread = threading.Thread(target=self._send_loop)
            send_thread.daemon = True
            send_thread.start()
            self.threads.append(send_thread)

            print(f"P2P network started for {self.player_name} (ID: {self.player_id})")
            return True

        except Exception as e:
            print(f"Failed to start P2P network: {e}")
            return False

    def stop(self):
        """Stop P2P networking"""
        self.running = False

        # Close all sockets
        if self.broadcast_socket:
            self.broadcast_socket.close()

        for sock in self.peer_sockets.values():
            try:
                sock.close()
            except:
                pass

        self.peer_sockets.clear()
        self.peers.clear()
        self.peer_info.clear()

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=1.0)

        print("P2P network stopped")

    def send_message(self, message):
        """Queue a message to be sent to all peers"""
        if self.running:
            self.send_queue.put(message)

    def receive_message(self):
        """Get a received message"""
        try:
            return self.receive_queue.get_nowait()
        except queue.Empty:
            return None

    def update_player(self, player_data):
        """Send player update to all peers"""
        if self.running and time.time() - self.last_update > 1.0 / NETWORK_UPDATE_RATE:
            self.send_message({
                MSG_PLAYER_UPDATE: {
                    "id": self.player_id,
                    "timestamp": time.time(),
                    **player_data
                }
            })
            self.last_update = time.time()

    def _broadcast_listener(self):
        """Listen for peer discovery broadcasts"""
        while self.running:
            try:
                data, addr = self.broadcast_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))

                if message.get("type") == "peer_discovery":
                    peer_id = message.get("peer_id")
                    peer_name = message.get("name")
                    peer_ip = addr[0]
                    public_address = message.get("public_address")
                    nat_type = message.get("nat_type")

                    if peer_id != self.player_id and peer_id not in self.peers:
                        print(f"Discovered peer: {peer_name} ({peer_id}) at {peer_ip}")
                        if public_address:
                            print(f"  Public address: {public_address}, NAT type: {nat_type}")
                        self.peers[peer_id] = (peer_ip, 5557, None)  # Use different port for peer connections
                        self.peer_info[peer_id] = {
                            "name": peer_name,
                            "public_address": public_address,
                            "nat_type": nat_type
                        }
                        self._connect_to_peer(peer_id, peer_ip, 5557)

            except Exception as e:
                if self.running:
                    print(f"Broadcast listener error: {e}")
                break

    def _peer_listener(self):
        """Listen for incoming peer connections"""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('', 5557))
        listener.listen(5)
        listener.settimeout(1.0)

        while self.running:
            try:
                client_socket, addr = listener.accept()
                peer_thread = threading.Thread(target=self._handle_peer_connection, args=(client_socket, addr))
                peer_thread.daemon = True
                peer_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Peer listener error: {e}")
                break

        listener.close()

    def _connect_to_peer(self, peer_id, ip, port):
        """Connect to a discovered peer"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((ip, port))

            self.peer_sockets[peer_id] = sock
            self.peers[peer_id] = (ip, port, sock)

            # Send handshake
            handshake = {
                "type": "handshake",
                "peer_id": self.player_id,
                "name": self.player_name
            }
            sock.send(len(json.dumps(handshake).encode()).to_bytes(4, byteorder='big'))
            sock.send(json.dumps(handshake).encode())

            # Start peer handler thread
            peer_thread = threading.Thread(target=self._handle_peer_connection, args=(sock, (ip, port)))
            peer_thread.daemon = True
            peer_thread.start()

            print(f"Connected to peer: {peer_id}")

        except Exception as e:
            print(f"Failed to connect to peer {peer_id}: {e}")
            # Try NAT traversal if we have public address info
            if peer_id in self.peer_info and self.peer_info[peer_id].get("public_address"):
                self._try_nat_traversal(peer_id)

    def _try_nat_traversal(self, peer_id):
        """Attempt NAT traversal using public address"""
        try:
            public_addr = self.peer_info[peer_id]["public_address"]
            if not public_addr or len(public_addr) != 2:
                return

            public_ip, public_port = public_addr
            print(f"Attempting NAT traversal to {peer_id} at {public_ip}:{public_port}")

            # Try connecting to public address
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((public_ip, public_port))

            self.peer_sockets[peer_id] = sock
            self.peers[peer_id] = (public_ip, public_port, sock)

            # Send handshake
            handshake = {
                "type": "handshake",
                "peer_id": self.player_id,
                "name": self.player_name
            }
            sock.send(len(json.dumps(handshake).encode()).to_bytes(4, byteorder='big'))
            sock.send(json.dumps(handshake).encode())

            # Start peer handler thread
            peer_thread = threading.Thread(target=self._handle_peer_connection, args=(sock, (public_ip, public_port)))
            peer_thread.daemon = True
            peer_thread.start()

            print(f"NAT traversal successful for peer: {peer_id}")

        except Exception as e:
            print(f"NAT traversal failed for {peer_id}: {e}")

    def _handle_peer_connection(self, sock, addr):
        """Handle communication with a connected peer"""
        peer_id = None

        try:
            while self.running:
                # Use select to check if data is available
                ready, _, _ = select.select([sock], [], [], 0.1)
                if not ready:
                    continue

                # Receive message length
                length_bytes = sock.recv(4)
                if not length_bytes:
                    break

                length = int.from_bytes(length_bytes, byteorder='big')

                # Receive message data
                data = sock.recv(length)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))

                # Handle handshake
                if message.get("type") == "handshake":
                    peer_id = message.get("peer_id")
                    if peer_id and peer_id not in self.peer_sockets:
                        self.peer_sockets[peer_id] = sock
                        print(f"Handshake completed with {message.get('name')} ({peer_id})")

                # Handle game messages
                elif MSG_PLAYER_UPDATE in message:
                    self.receive_queue.put(message)

                elif MSG_PROJECTILE_UPDATE in message:
                    self.receive_queue.put(message)

                elif MSG_ENEMY_UPDATE in message:
                    self.receive_queue.put(message)

        except Exception as e:
            print(f"Peer connection error: {e}")

        finally:
            if peer_id and peer_id in self.peer_sockets:
                del self.peer_sockets[peer_id]
            try:
                sock.close()
            except:
                pass
            if peer_id:
                print(f"Disconnected from peer: {peer_id}")

    def _send_loop(self):
        """Send queued messages to all peers"""
        while self.running:
            try:
                message = self.send_queue.get(timeout=0.1)

                # Broadcast to all connected peers
                for peer_id, sock in list(self.peer_sockets.items()):
                    try:
                        data = json.dumps(message).encode('utf-8')
                        sock.send(len(data).to_bytes(4, byteorder='big'))
                        sock.send(data)
                    except Exception as e:
                        print(f"Failed to send to peer {peer_id}: {e}")
                        # Remove disconnected peer
                        if peer_id in self.peer_sockets:
                            del self.peer_sockets[peer_id]

                # Send periodic broadcast for peer discovery
                if time.time() - self.last_broadcast > 2.0:  # Every 2 seconds
                    discovery_msg = {
                        "type": "peer_discovery",
                        "peer_id": self.player_id,
                        "name": self.player_name,
                        "public_address": self.public_address,
                        "nat_type": str(self.nat_type) if self.nat_type else "unknown",
                        "timestamp": time.time()
                    }
                    try:
                        data = json.dumps(discovery_msg).encode('utf-8')
                        self.broadcast_socket.sendto(data, ('<broadcast>', self.broadcast_port))
                    except Exception as e:
                        print(f"Broadcast error: {e}")

                    self.last_broadcast = time.time()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Send loop error: {e}")
                break