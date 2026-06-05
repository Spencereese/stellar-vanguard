#!/usr/bin/env python3
"""
STUN (Session Traversal Utilities for NAT) Client

Implements RFC 5389 STUN protocol for NAT traversal.
Used to discover public IP address and NAT type for P2P connections.
"""

import socket
import struct
import random
import time
import hashlib
import hmac
from enum import Enum

# STUN Message Types
STUN_BINDING_REQUEST = 0x0001
STUN_BINDING_RESPONSE = 0x0101
STUN_BINDING_ERROR_RESPONSE = 0x0111

# STUN Attributes
STUN_ATTR_MAPPED_ADDRESS = 0x0001
STUN_ATTR_RESPONSE_ADDRESS = 0x0002
STUN_ATTR_CHANGE_REQUEST = 0x0003
STUN_ATTR_SOURCE_ADDRESS = 0x0004
STUN_ATTR_CHANGED_ADDRESS = 0x0005
STUN_ATTR_USERNAME = 0x0006
STUN_ATTR_PASSWORD = 0x0007
STUN_ATTR_MESSAGE_INTEGRITY = 0x0008
STUN_ATTR_ERROR_CODE = 0x0009
STUN_ATTR_UNKNOWN_ATTRIBUTES = 0x000A
STUN_ATTR_REFLECTED_FROM = 0x000B
STUN_ATTR_XOR_MAPPED_ADDRESS = 0x0020

# STUN Servers (public STUN servers)
STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("stun2.l.google.com", 19302),
    ("stun3.l.google.com", 19302),
    ("stun4.l.google.com", 19302),
    ("stun.ekiga.net", 3478),
    ("stun.ideasip.com", 3478),
    ("stun.softjoys.com", 3478),
]

class NatType(Enum):
    """NAT Type enumeration"""
    UNKNOWN = "unknown"
    OPEN_INTERNET = "open_internet"
    FULL_CONE = "full_cone"
    RESTRICTED_CONE = "restricted_cone"
    PORT_RESTRICTED_CONE = "port_restricted_cone"
    SYMMETRIC = "symmetric"
    BLOCKED = "blocked"

class StunAttribute:
    """STUN attribute parser"""
    def __init__(self, type_code, value):
        self.type_code = type_code
        self.value = value

    @classmethod
    def parse_mapped_address(cls, data):
        """Parse MAPPED-ADDRESS or XOR-MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            return None

        # Skip family (1 byte) and port (2 bytes), get IP (4 bytes)
        family = data[1]
        if family == 0x01:  # IPv4
            port = struct.unpack('>H', data[2:4])[0]
            ip_bytes = data[4:8]
            ip = '.'.join(str(b) for b in ip_bytes)
            return ip, port
        return None

    @classmethod
    def parse_xor_mapped_address(cls, data, transaction_id):
        """Parse XOR-MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            return None

        family = data[1]
        if family == 0x01:  # IPv4
            # XOR the port and IP with magic cookie and transaction ID
            magic_cookie = 0x2112A442
            xor_port = struct.unpack('>H', data[2:4])[0] ^ (magic_cookie >> 16)
            ip_bytes = data[4:8]
            xor_ip_bytes = []
            for i, b in enumerate(ip_bytes):
                if i < 4:
                    xor_ip_bytes.append(b ^ ((magic_cookie >> (24 - i*8)) & 0xFF))
                else:
                    xor_ip_bytes.append(b ^ transaction_id[i-4])

            ip = '.'.join(str(b) for b in xor_ip_bytes)
            return ip, xor_port
        return None

class StunMessage:
    """STUN message builder and parser"""
    def __init__(self, msg_type=STUN_BINDING_REQUEST, transaction_id=None):
        self.msg_type = msg_type
        self.transaction_id = transaction_id or self._generate_transaction_id()
        self.attributes = []

    def _generate_transaction_id(self):
        """Generate a random 96-bit transaction ID"""
        return bytes([random.randint(0, 255) for _ in range(12)])

    def add_attribute(self, attr_type, value):
        """Add an attribute to the message"""
        self.attributes.append((attr_type, value))

    def build(self):
        """Build the STUN message"""
        # STUN header: 20 bytes
        # Type (2), Length (2), Magic Cookie (4), Transaction ID (12)
        msg_length = sum(4 + len(value) + (4 - len(value) % 4) % 4 for _, value in self.attributes)

        header = struct.pack('>HH', self.msg_type, msg_length)
        header += b'\x21\x12\xA4\x42'  # Magic cookie
        header += self.transaction_id

        message = header

        # Add attributes
        for attr_type, value in self.attributes:
            # Attribute header: Type (2), Length (2)
            attr_len = len(value)
            padded_len = attr_len + (4 - attr_len % 4) % 4
            message += struct.pack('>HH', attr_type, attr_len)
            message += value
            # Pad to 4-byte boundary
            message += b'\x00' * (padded_len - attr_len)

        return message

    @classmethod
    def parse(cls, data):
        """Parse a STUN message"""
        if len(data) < 20:
            return None

        msg_type, msg_length = struct.unpack('>HH', data[0:4])
        magic_cookie = data[4:8]
        transaction_id = data[8:20]

        if magic_cookie != b'\x21\x12\xA4\x42':
            return None  # Not a STUN message

        message = cls(msg_type, transaction_id)

        # Parse attributes
        offset = 20
        while offset < len(data) and offset < 20 + msg_length:
            if offset + 4 > len(data):
                break

            attr_type, attr_len = struct.unpack('>HH', data[offset:offset+4])
            offset += 4

            if offset + attr_len > len(data):
                break

            value = data[offset:offset + attr_len]
            message.attributes.append(StunAttribute(attr_type, value))

            # Skip padding
            offset += attr_len + (4 - attr_len % 4) % 4

        return message

class StunClient:
    """STUN client for NAT traversal"""

    def __init__(self, timeout=5.0):
        self.timeout = timeout
        self.socket = None

    def __enter__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.socket:
            self.socket.close()

    def get_mapped_address(self, stun_server, stun_port=3478, local_port=0):
        """Get the mapped (public) address from a STUN server"""
        try:
            # Bind to a local port
            self.socket.bind(('0.0.0.0', local_port))

            # Create binding request
            request = StunMessage(STUN_BINDING_REQUEST)
            message_data = request.build()

            # Send request
            self.socket.sendto(message_data, (stun_server, stun_port))

            # Receive response
            response_data, addr = self.socket.recvfrom(2048)

            # Parse response
            response = StunMessage.parse(response_data)
            if not response or response.msg_type != STUN_BINDING_RESPONSE:
                return None

            # Extract mapped address
            for attr in response.attributes:
                if attr.type_code == STUN_ATTR_XOR_MAPPED_ADDRESS:
                    result = StunAttribute.parse_xor_mapped_address(attr.value, response.transaction_id)
                    if result:
                        return result
                elif attr.type_code == STUN_ATTR_MAPPED_ADDRESS:
                    result = StunAttribute.parse_mapped_address(attr.value)
                    if result:
                        return result

        except Exception as e:
            print(f"STUN request failed: {e}")

        return None

    def detect_nat_type(self):
        """Detect the NAT type using multiple STUN tests"""
        # Test 1: Basic connectivity and mapping
        server1 = STUN_SERVERS[0]
        result1 = self.get_mapped_address(server1[0], server1[1])

        if not result1:
            return NatType.BLOCKED, None

        public_ip1, public_port1 = result1

        # Get local address
        local_ip = self.socket.getsockname()[0]
        local_port = self.socket.getsockname()[1]

        # If public IP matches local IP, we're on open internet
        if public_ip1 == local_ip:
            return NatType.OPEN_INTERNET, (public_ip1, public_port1)

        # Test 2: Try a different server
        server2 = STUN_SERVERS[1] if len(STUN_SERVERS) > 1 else server1
        result2 = self.get_mapped_address(server2[0], server2[1])

        if not result2:
            return NatType.UNKNOWN, (public_ip1, public_port1)

        public_ip2, public_port2 = result2

        # If ports are different, likely symmetric NAT
        if public_port1 != public_port2:
            return NatType.SYMMETRIC, (public_ip1, public_port1)

        # For more detailed testing, we'd need to implement full NAT detection
        # which requires multiple sockets and more complex logic
        # For now, assume port-restricted cone NAT as it's most common
        return NatType.PORT_RESTRICTED_CONE, (public_ip1, public_port1)

def get_public_address():
    """Get public IP address and port using STUN"""
    with StunClient() as client:
        for server, port in STUN_SERVERS[:3]:  # Try first 3 servers
            result = client.get_mapped_address(server, port)
            if result:
                return result
    return None

def detect_nat_type():
    """Detect NAT type"""
    with StunClient() as client:
        nat_type, address = client.detect_nat_type()
        return nat_type, address

if __name__ == "__main__":
    print("STUN Client Test")
    print("-" * 20)

    # Test public address discovery
    print("Testing public address discovery...")
    address = get_public_address()
    if address:
        ip, port = address
        print(f"✓ Public address: {ip}:{port}")
    else:
        print("✗ Failed to get public address")

    # Test NAT type detection
    print("\nTesting NAT type detection...")
    nat_type, address = detect_nat_type()
    print(f"✓ NAT Type: {nat_type.value}")
    if address:
        ip, port = address
        print(f"✓ Public address: {ip}:{port}")