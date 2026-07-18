import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

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


class SettingsScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(name="settings", **kwargs)
        self.app_state = app_state
        self._build()

    def on_enter(self):
        s = self.app_state["settings"]
        self._user_input.text = s.get("username", "User")
        self._port_input.text = str(s.get("port", utils.DEFAULT_PORT))
        self._local_ip_label.text = f"Local IP: {utils.get_local_ip()}"
        self._pub_ip_label.text = "Public IP: fetching..."
        threading.Thread(target=self._fetch_pub_ip, daemon=True).start()
        self._refresh_blocked()

    def _fetch_pub_ip(self):
        ip = utils.get_public_ip()
        Clock.schedule_once(lambda dt: setattr(self._pub_ip_label, "text", f"Public IP: {ip}"), 0)

    def _build(self):
        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        _bg(outer, theme.BG)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        back_btn = Button(text="< Back", size_hint_x=None, width=dp(70),
                          background_color=theme.SURFACE2, color=theme.TEXT,
                          font_size=theme.FS_SMALL)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "connect"))
        header.add_widget(back_btn)
        header.add_widget(Label(text="Settings", font_size=theme.FS_TITLE,
                                bold=True, color=theme.ACCENT))
        outer.add_widget(header)

        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None,
                            spacing=dp(10), padding=[0, dp(4)])
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)

        # Fields
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(8),
                          row_default_height=dp(42))
        grid.bind(minimum_height=grid.setter("height"))

        grid.add_widget(Label(text="Username", font_size=theme.FS_LABEL,
                              color=theme.TEXT, halign="right"))
        self._user_input = TextInput(
            multiline=False, background_color=theme.SURFACE2,
            foreground_color=theme.TEXT, font_size=theme.FS_BODY,
            padding=[dp(8), dp(8)]
        )
        grid.add_widget(self._user_input)

        grid.add_widget(Label(text="Port", font_size=theme.FS_LABEL,
                              color=theme.TEXT, halign="right"))
        self._port_input = TextInput(
            multiline=False, background_color=theme.SURFACE2,
            foreground_color=theme.TEXT, font_size=theme.FS_BODY,
            input_filter="int", padding=[dp(8), dp(8)]
        )
        grid.add_widget(self._port_input)
        content.add_widget(grid)

        # IP info labels
        self._local_ip_label = Label(text="Local IP: ...", font_size=theme.FS_SMALL,
                                     color=theme.TEXT_DIM, size_hint_y=None, height=dp(24))
        self._pub_ip_label = Label(text="Public IP: ...", font_size=theme.FS_SMALL,
                                   color=theme.TEXT_DIM, size_hint_y=None, height=dp(24))
        content.add_widget(self._local_ip_label)
        content.add_widget(self._pub_ip_label)

        # Blocked IPs section
        self._blocked_label = Label(text="", font_size=theme.FS_SMALL,
                                    color=theme.WARNING_FG, size_hint_y=None,
                                    height=dp(24), halign="left")
        self._blocked_label.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        content.add_widget(self._blocked_label)

        self._clear_blocked_btn = Button(
            text="Clear Blocked IPs", size_hint_y=None, height=dp(38),
            background_color=theme.SURFACE2, color=theme.TEXT,
            font_size=theme.FS_SMALL, opacity=0, disabled=True
        )
        self._clear_blocked_btn.bind(on_press=self._clear_blocked)
        content.add_widget(self._clear_blocked_btn)

        # Save button
        save_btn = Button(text="Save Settings", size_hint_y=None, height=dp(44),
                          background_color=theme.ACCENT, color=theme.WHITE,
                          font_size=theme.FS_BODY)
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)

        self._feedback = Label(text="", font_size=theme.FS_SMALL,
                               color=theme.SUCCESS, size_hint_y=None, height=dp(24))
        content.add_widget(self._feedback)

        outer.add_widget(scroll)
        self.add_widget(outer)

    def _refresh_blocked(self):
        blocked = self.app_state["settings"].get("blocked_ips", [])
        if blocked:
            self._blocked_label.text = "Blocked: " + ", ".join(blocked)
            self._clear_blocked_btn.opacity = 1
            self._clear_blocked_btn.disabled = False
        else:
            self._blocked_label.text = ""
            self._clear_blocked_btn.opacity = 0
            self._clear_blocked_btn.disabled = True

    def _clear_blocked(self, *_):
        self.app_state["settings"]["blocked_ips"] = []
        cfg.save(self.app_state["settings"])
        self._refresh_blocked()

    def _save(self, *_):
        try:
            port = int(self._port_input.text.strip())
        except ValueError:
            self._feedback.text = "Invalid port."
            self._feedback.color = theme.DANGER
            return

        old_port = self.app_state["settings"].get("port")
        self.app_state["settings"]["username"] = self._user_input.text.strip() or "User"
        self.app_state["settings"]["port"] = port
        cfg.save(self.app_state["settings"])

        if port != old_port:
            restart = self.app_state.get("restart_server")
            if restart:
                restart(port)

        self._feedback.text = "Saved."
        self._feedback.color = theme.SUCCESS
        Clock.schedule_once(lambda dt: setattr(self._feedback, "text", ""), 2)
