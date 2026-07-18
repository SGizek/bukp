import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

import network
import settings as cfg
import utils
import theme


def _bg(widget, color):
    def _draw(instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*color)
            Rectangle(pos=instance.pos, size=instance.size)
    widget.bind(pos=_draw, size=_draw)


class ConnectScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(name="connect", **kwargs)
        self.app_state = app_state  # shared dict: server, connection, settings
        self._build()

    def on_enter(self):
        s = self.app_state["settings"]
        self._port_input.text = str(s.get("port", utils.DEFAULT_PORT))
        self._user_input.text = s.get("username", "User")

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        _bg(root, theme.BG)

        # Title
        root.add_widget(Label(
            text="Bukp", font_size=theme.FS_TITLE, bold=True,
            color=theme.ACCENT, size_hint_y=None, height=dp(40)
        ))

        # Status row
        self._status_label = Label(
            text="Not connected", font_size=theme.FS_SMALL,
            color=theme.DANGER, size_hint_y=None, height=dp(24)
        )
        root.add_widget(self._status_label)

        # Fields
        fields = GridLayout(cols=2, size_hint_y=None, spacing=dp(8), row_default_height=dp(40))
        fields.bind(minimum_height=fields.setter("height"))

        def field(label, hint, default=""):
            fields.add_widget(Label(text=label, font_size=theme.FS_LABEL,
                                    color=theme.TEXT, halign="right"))
            ti = TextInput(text=default, hint_text=hint, multiline=False,
                           background_color=theme.SURFACE2, foreground_color=theme.TEXT,
                           font_size=theme.FS_BODY, padding=[dp(8), dp(8)])
            fields.add_widget(ti)
            return ti

        self._ip_input   = field("Peer IP",   "e.g. 192.168.1.10")
        self._port_input = field("Port",      "5050", "5050")
        self._user_input = field("Username",  "Your name", "User")
        root.add_widget(fields)

        # Buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self._connect_btn = Button(text="Connect", background_color=theme.ACCENT2,
                                   color=theme.WHITE, font_size=theme.FS_BODY)
        self._connect_btn.bind(on_press=self._do_connect)

        self._disconnect_btn = Button(text="Disconnect", background_color=theme.DANGER,
                                      color=theme.WHITE, font_size=theme.FS_BODY,
                                      disabled=True)
        self._disconnect_btn.bind(on_press=self._do_disconnect)

        btn_row.add_widget(self._connect_btn)
        btn_row.add_widget(self._disconnect_btn)
        root.add_widget(btn_row)

        # Nav buttons
        nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        for label, target in [("Chat", "chat"), ("Settings", "settings"), ("IP Info", "ipinfo")]:
            b = Button(text=label, background_color=theme.SURFACE2,
                       color=theme.TEXT, font_size=theme.FS_BODY)
            b.bind(on_press=lambda x, t=target: self._go(t))
            nav.add_widget(b)
        root.add_widget(nav)

        root.add_widget(Label())  # spacer
        self.add_widget(root)

    def _go(self, screen):
        self.manager.current = screen

    # ── Connection logic ───────────────────────────────────────────────────────
    def _do_connect(self, *_):
        ip = self._ip_input.text.strip()
        port_str = self._port_input.text.strip()
        username = self._user_input.text.strip() or "User"

        if not ip:
            self._set_status("Enter a peer IP address.", theme.DANGER)
            return
        try:
            port = int(port_str)
        except ValueError:
            self._set_status("Invalid port number.", theme.DANGER)
            return

        self.app_state["settings"]["username"] = username
        cfg.save(self.app_state["settings"])
        self._connect_btn.disabled = True
        self._set_status("Connecting...", theme.TEXT_DIM)

        def _connect():
            try:
                sock = network.connect_to_peer(ip, port)
                Clock.schedule_once(lambda dt: self._on_connected(sock), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_connect_fail(str(e)), 0)

        threading.Thread(target=_connect, daemon=True).start()

    def _on_connected(self, sock):
        self._establish(sock)

    def _on_connect_fail(self, err):
        self._connect_btn.disabled = False
        self._set_status(f"Failed: {err}", theme.DANGER)

    def _do_disconnect(self, *_):
        conn = self.app_state.get("connection")
        if conn:
            conn.disconnect()
        self._reset_ui()

    def _establish(self, sock):
        callbacks = {
            "on_message":      self.app_state["on_message"],
            "on_image":        self.app_state["on_image"],
            "on_disconnect":   self._on_peer_disconnect,
            "on_progress":     self.app_state["on_progress"],
            "on_image_cancel": self.app_state["on_image_cancel"],
        }
        conn = network.PeerConnection(sock, callbacks)
        conn.start()
        conn.send_username(self.app_state["settings"].get("username", "User"))
        self.app_state["connection"] = conn
        self._connect_btn.disabled = True
        self._disconnect_btn.disabled = False
        self._set_status(f"Connected to {conn.peer_ip}", theme.SUCCESS)

    def _on_peer_disconnect(self, username):
        Clock.schedule_once(lambda dt: self._handle_disconnect(username), 0)

    def _handle_disconnect(self, username):
        self.app_state["on_sys_msg"](f"{username} disconnected.")
        self._reset_ui()

    def _reset_ui(self):
        self.app_state["connection"] = None
        self._connect_btn.disabled = False
        self._disconnect_btn.disabled = True
        self._set_status("Not connected", theme.DANGER)

    def _set_status(self, text, color):
        self._status_label.text = text
        self._status_label.color = color

    # ── Incoming connection popup ──────────────────────────────────────────────
    def show_incoming_popup(self, ip, sock):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        _bg(content, theme.SURFACE)

        content.add_widget(Label(text="Incoming Connection",
                                 font_size=theme.FS_BODY, bold=True, color=theme.ACCENT,
                                 size_hint_y=None, height=dp(30)))
        content.add_widget(Label(text=f"From: {ip}", font_size=theme.FS_BODY,
                                 color=theme.TEXT, size_hint_y=None, height=dp(26)))

        warn = Label(
            text="Security: You are connecting via your public IP.\nOnly accept from people you trust.",
            font_size=theme.FS_SMALL, color=theme.WARNING_FG,
            size_hint_y=None, height=dp(48), halign="center"
        )
        warn.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        content.add_widget(warn)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title="", content=content, size_hint=(0.88, None),
                      height=dp(260), separator_height=0,
                      background_color=theme.SURFACE)

        def accept(*_):
            popup.dismiss()
            Clock.schedule_once(lambda dt: self._establish(sock), 0)

        def reject(*_):
            popup.dismiss()
            try:
                sock.close()
            except Exception:
                pass

        def block(*_):
            popup.dismiss()
            self.app_state["settings"].setdefault("blocked_ips", []).append(ip)
            cfg.save(self.app_state["settings"])
            try:
                sock.close()
            except Exception:
                pass
            self.app_state["on_sys_msg"](f"Blocked IP: {ip}")

        for label, color, fn in [
            ("Accept", theme.SUCCESS, accept),
            ("Reject", theme.DANGER, reject),
            ("Block",  theme.SURFACE2, block),
        ]:
            b = Button(text=label, background_color=color,
                       color=theme.WHITE, font_size=theme.FS_BODY)
            b.bind(on_press=fn)
            btn_row.add_widget(b)

        content.add_widget(btn_row)
        popup.open()
