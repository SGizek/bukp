import socket
import threading
import os
import json
from utils import (
    send_packet, recv_packet, ensure_received_dir,
    CHUNK_SIZE, MAX_MESSAGE_SIZE,
    MSG_TYPE_TEXT, MSG_TYPE_IMAGE_HEADER, MSG_TYPE_IMAGE_CHUNK,
    MSG_TYPE_IMAGE_END, MSG_TYPE_IMAGE_CANCEL,
    MSG_TYPE_DISCONNECT, MSG_TYPE_USERNAME
)


class PeerConnection:
    def __init__(self, sock: socket.socket, callbacks: dict):
        self.sock = sock
        self.peer_ip = sock.getpeername()[0]
        self.peer_username = self.peer_ip
        self.callbacks = callbacks
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._cancel_transfer = False
        self._active = True

    def start(self):
        self._recv_thread.start()

    def send_username(self, username: str):
        send_packet(self.sock, MSG_TYPE_USERNAME, username.encode())

    def send_message(self, text: str):
        if len(text) > MAX_MESSAGE_SIZE:
            text = text[:MAX_MESSAGE_SIZE]
        send_packet(self.sock, MSG_TYPE_TEXT, text.encode())

    def send_image(self, filepath: str, username: str, progress_cb=None, done_cb=None):
        def _send():
            try:
                filename = os.path.basename(filepath)
                size = os.path.getsize(filepath)
                header = json.dumps({"filename": filename, "size": size, "sender": username}).encode()
                send_packet(self.sock, MSG_TYPE_IMAGE_HEADER, header)
                sent = 0
                with open(filepath, "rb") as f:
                    while True:
                        if self._cancel_transfer:
                            send_packet(self.sock, MSG_TYPE_IMAGE_CANCEL, b"")
                            self._cancel_transfer = False
                            if done_cb:
                                done_cb(False, "Transfer cancelled")
                            return
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        send_packet(self.sock, MSG_TYPE_IMAGE_CHUNK, chunk)
                        sent += len(chunk)
                        if progress_cb:
                            progress_cb(sent, size)
                send_packet(self.sock, MSG_TYPE_IMAGE_END, b"")
                if done_cb:
                    done_cb(True, filename)
            except Exception as e:
                if done_cb:
                    done_cb(False, str(e))
        threading.Thread(target=_send, daemon=True).start()

    def cancel_transfer(self):
        self._cancel_transfer = True

    def disconnect(self):
        if not self._active:
            return
        self._active = False
        try:
            send_packet(self.sock, MSG_TYPE_DISCONNECT, b"")
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

    def _recv_loop(self):
        image_meta = None
        image_buf = b""
        try:
            while self._active:
                msg_type, payload = recv_packet(self.sock)
                if msg_type == MSG_TYPE_USERNAME:
                    self.peer_username = payload.decode()
                elif msg_type == MSG_TYPE_TEXT:
                    text = payload.decode(errors="replace")
                    cb = self.callbacks.get("on_message")
                    if cb:
                        cb(self.peer_username, text)
                elif msg_type == MSG_TYPE_IMAGE_HEADER:
                    image_meta = json.loads(payload.decode())
                    image_buf = b""
                elif msg_type == MSG_TYPE_IMAGE_CHUNK:
                    if image_meta:
                        image_buf += payload
                        cb = self.callbacks.get("on_progress")
                        if cb:
                            cb(len(image_buf), image_meta.get("size", 1))
                elif msg_type == MSG_TYPE_IMAGE_END:
                    if image_meta:
                        save_dir = ensure_received_dir()
                        save_path = os.path.join(save_dir, image_meta["filename"])
                        base, ext = os.path.splitext(save_path)
                        counter = 1
                        while os.path.exists(save_path):
                            save_path = f"{base}_{counter}{ext}"
                            counter += 1
                        with open(save_path, "wb") as f:
                            f.write(image_buf)
                        cb = self.callbacks.get("on_image")
                        if cb:
                            cb(image_meta.get("sender", self.peer_username), save_path, image_meta["filename"])
                        image_meta = None
                        image_buf = b""
                elif msg_type == MSG_TYPE_IMAGE_CANCEL:
                    image_meta = None
                    image_buf = b""
                    cb = self.callbacks.get("on_image_cancel")
                    if cb:
                        cb()
                elif msg_type == MSG_TYPE_DISCONNECT:
                    break
        except Exception:
            pass
        finally:
            self._active = False
            try:
                self.sock.close()
            except Exception:
                pass
            cb = self.callbacks.get("on_disconnect")
            if cb:
                cb(self.peer_username)


class Server:
    def __init__(self, port: int, on_incoming):
        self.port = port
        self.on_incoming = on_incoming
        self._server_sock = None
        self._thread = None
        self._running = False

    def start(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("", self.port))
        self._server_sock.listen(1)
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        try:
            self._server_sock.close()
        except Exception:
            pass

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._server_sock.accept()
                self.on_incoming(conn, addr)
            except Exception:
                break


def connect_to_peer(ip: str, port: int, timeout: int = 10) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((ip, port))
    s.settimeout(None)
    return s
