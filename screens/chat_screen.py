import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

import settings as cfg
import theme
from widgets import MessageBubble, SysMessage, ImageMessage

try:
    from plyer import filechooser as _fc
    _HAS_PLYER = True
except ImportError:
    _HAS_PLYER = False


def _bg(widget, color):
    def _draw(instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*color)
            Rectangle(pos=instance.pos, size=instance.size)
    widget.bind(pos=_draw, size=_draw)


class ChatScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(name="chat", **kwargs)
        self.app_state = app_state
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        _bg(root, theme.BG)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        back_btn = Button(text="< Back", size_hint_x=None, width=dp(70),
                          background_color=theme.SURFACE2, color=theme.TEXT,
                          font_size=theme.FS_SMALL)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "connect"))
        header.add_widget(back_btn)

        self._peer_label = Label(text="Bukp Chat", font_size=theme.FS_BODY,
                                 bold=True, color=theme.ACCENT)
        header.add_widget(self._peer_label)

        self._status_dot = Label(text="●", font_size=theme.FS_BODY,
                                 color=theme.DANGER, size_hint_x=None, width=dp(24))
        header.add_widget(self._status_dot)
        root.add_widget(header)

        # Message list
        self._msg_list = BoxLayout(orientation="vertical", size_hint_y=None,
                                   spacing=dp(6), padding=[0, dp(4)])
        self._msg_list.bind(minimum_height=self._msg_list.setter("height"))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self._msg_list)
        self._scroll = scroll
        root.add_widget(scroll)

        # Progress bar (hidden until transfer)
        self._progress_row = BoxLayout(size_hint_y=None, height=dp(32),
                                       spacing=dp(6), opacity=0)
        self._progress_bar = ProgressBar(max=100, value=0)
        cancel_btn = Button(text="Cancel", size_hint_x=None, width=dp(70),
                            background_color=theme.DANGER, color=theme.WHITE,
                            font_size=theme.FS_SMALL)
        cancel_btn.bind(on_press=self._cancel_transfer)
        self._progress_row.add_widget(self._progress_bar)
        self._progress_row.add_widget(cancel_btn)
        root.add_widget(self._progress_row)

        # Input row
        input_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self._msg_input = TextInput(
            hint_text="Type a message...", multiline=False,
            background_color=theme.SURFACE2, foreground_color=theme.TEXT,
            font_size=theme.FS_BODY, padding=[dp(8), dp(10)]
        )
        self._msg_input.bind(on_text_validate=self._send_message)

        send_btn = Button(text="Send", size_hint_x=None, width=dp(64),
                          background_color=theme.ACCENT, color=theme.WHITE,
                          font_size=theme.FS_BODY)
        send_btn.bind(on_press=self._send_message)

        attach_btn = Button(text="Image", size_hint_x=None, width=dp(64),
                            background_color=theme.SURFACE2, color=theme.TEXT,
                            font_size=theme.FS_SMALL)
        attach_btn.bind(on_press=self._attach_image)

        input_row.add_widget(self._msg_input)
        input_row.add_widget(attach_btn)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        self.add_widget(root)

    # ── Public methods called by app_state callbacks ───────────────────────────
    def add_message(self, username, text, is_self=False):
        bubble = MessageBubble(username, text, is_self=is_self)
        self._msg_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.05)

    def add_sys_message(self, text):
        self._msg_list.add_widget(SysMessage(text))
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.05)

    def add_image_message(self, username, filepath, filename, is_self=False):
        self._msg_list.add_widget(ImageMessage(username, filepath, filename, is_self=is_self))
        self._progress_row.opacity = 0
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.05)

    def set_progress(self, value):
        self._progress_row.opacity = 1
        self._progress_bar.value = value
        if value >= 100:
            Clock.schedule_once(lambda dt: setattr(self._progress_row, "opacity", 0), 1)

    def set_status(self, connected, peer_name=""):
        self._status_dot.color = theme.SUCCESS if connected else theme.DANGER
        self._peer_label.text = f"Chat - {peer_name}" if peer_name else "Bukp Chat"

    # ── Internal ───────────────────────────────────────────────────────────────
    def _scroll_bottom(self):
        self._scroll.scroll_y = 0

    def _send_message(self, *_):
        conn = self.app_state.get("connection")
        if not conn or not conn._active:
            self.add_sys_message("Not connected.")
            return
        text = self._msg_input.text.strip()
        if not text:
            return
        conn.send_message(text)
        username = self.app_state["settings"].get("username", "User")
        self.add_message(username, text, is_self=True)
        self._msg_input.text = ""

    def _attach_image(self, *_):
        conn = self.app_state.get("connection")
        if not conn or not conn._active:
            self.add_sys_message("Not connected.")
            return
        if _HAS_PLYER:
            try:
                _fc.open_file(
                    title="Select Image",
                    filters=[["Images", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"]],
                    on_selection=self._on_file_selected
                )
            except Exception as e:
                self.add_sys_message(f"File picker error: {e}")
        else:
            self.add_sys_message("File picker unavailable (plyer not installed).")

    def _on_file_selected(self, selection):
        if not selection:
            return
        filepath = selection[0]
        conn = self.app_state.get("connection")
        if not conn or not conn._active:
            return
        username = self.app_state["settings"].get("username", "User")
        self.add_sys_message(f"Sending image...")
        self._progress_row.opacity = 1
        self._progress_bar.value = 0

        def progress(sent, total):
            pct = (sent / total * 100) if total else 0
            Clock.schedule_once(lambda dt: self.set_progress(pct), 0)

        def done(success, info):
            if success:
                Clock.schedule_once(lambda dt: self.add_sys_message(f"Image sent: {info}"), 0)
            else:
                Clock.schedule_once(lambda dt: self.add_sys_message(f"Transfer failed: {info}"), 0)
            Clock.schedule_once(lambda dt: setattr(self._progress_row, "opacity", 0), 0)

        conn.send_image(filepath, username, progress_cb=progress, done_cb=done)

    def _cancel_transfer(self, *_):
        conn = self.app_state.get("connection")
        if conn:
            conn.cancel_transfer()
        self._progress_row.opacity = 0
