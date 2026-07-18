import socket
import struct
import os

APP_NAME = "Bukp"
DEFAULT_PORT = 5050
MAX_MESSAGE_SIZE = 4096
CHUNK_SIZE = 8192
RECEIVED_DIR = os.path.join(os.path.expanduser("~"), "BukpReceived")

MSG_TYPE_TEXT = "TEXT"
MSG_TYPE_IMAGE_HEADER = "IMAGE_HEADER"
MSG_TYPE_IMAGE_CHUNK = "IMAGE_CHUNK"
MSG_TYPE_IMAGE_END = "IMAGE_END"
MSG_TYPE_IMAGE_CANCEL = "IMAGE_CANCEL"
MSG_TYPE_DISCONNECT = "DISCONNECT"
MSG_TYPE_USERNAME = "USERNAME"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unavailable"


def get_public_ip():
    try:
        import requests
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "Unavailable"


def ensure_received_dir():
    os.makedirs(RECEIVED_DIR, exist_ok=True)
    return RECEIVED_DIR


def send_packet(sock, msg_type: str, payload: bytes):
    type_bytes = msg_type.encode().ljust(16)[:16]
    total = 4 + 16 + len(payload)
    header = struct.pack("!I", total) + type_bytes
    sock.sendall(header + payload)


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf


def recv_packet(sock):
    raw_len = recv_exact(sock, 4)
    total = struct.unpack("!I", raw_len)[0]
    type_bytes = recv_exact(sock, 16)
    msg_type = type_bytes.decode().strip()
    payload_len = total - 4 - 16
    payload = recv_exact(sock, payload_len) if payload_len > 0 else b""
    return msg_type, payload
