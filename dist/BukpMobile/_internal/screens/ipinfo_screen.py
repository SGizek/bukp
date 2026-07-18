from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
import theme

_INFO_TEXT = """HOW TO FIND YOUR PUBLIC IP
==========================

Your public IP is assigned by your ISP.
It differs from your private/local IP (e.g. 192.168.x.x),
which only works inside your home network.

WINDOWS
-------
Open Command Prompt and run:
  nslookup myip.opendns.com resolver1.opendns.com

Or visit: https://www.whatismyip.com

LINUX / macOS
-------------
Open Terminal and run:
  curl ifconfig.me

IMPORTANT NOTES
---------------
- Your public IP is what peers use to connect to you.
- If behind a router, set up port forwarding:
  Forward your chosen port (default 5050) to your
  local IP in your router settings.
- Only share your IP with people you trust.
- Your IP may change when you restart your router.

PRIVATE vs PUBLIC IP
--------------------
Private (192.168.x.x): only inside your network.
Public IP: reachable from the internet.

For peers on different networks, both must use
public IPs with port forwarding configured.
"""


def _bg(widget, color):
    def _draw(instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*color)
            Rectangle(pos=instance.pos, size=instance.size)
    widget.bind(pos=_draw, size=_draw)


class IpInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="ipinfo", **kwargs)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        _bg(root, theme.BG)

        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        back_btn = Button(text="< Back", size_hint_x=None, width=dp(70),
                          background_color=theme.SURFACE2, color=theme.TEXT,
                          font_size=theme.FS_SMALL)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "connect"))
        header.add_widget(back_btn)
        header.add_widget(Label(text="IP Information", font_size=theme.FS_TITLE,
                                bold=True, color=theme.ACCENT))
        root.add_widget(header)

        scroll = ScrollView()
        info_label = Label(
            text=_INFO_TEXT,
            font_size=theme.FS_SMALL,
            color=theme.TEXT,
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        info_label.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
        info_label.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))
        scroll.add_widget(info_label)
        root.add_widget(scroll)

        self.add_widget(root)
