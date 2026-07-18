from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
import theme


class MessageBubble(BoxLayout):
    """A single chat message bubble with username + text."""

    def __init__(self, username, text, is_self=False, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                         padding=[dp(10), dp(6)], spacing=dp(2), **kwargs)
        bg_color = theme.MSG_SELF if is_self else theme.MSG_PEER
        align = "right" if is_self else "left"

        name_label = Label(
            text=username,
            font_size=theme.FS_SMALL,
            color=theme.ACCENT if is_self else theme.WARNING_FG,
            size_hint_y=None,
            halign=align,
            bold=True,
        )
        name_label.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        name_label.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))

        msg_label = Label(
            text=text,
            font_size=theme.FS_BODY,
            color=theme.TEXT,
            size_hint_y=None,
            halign=align,
        )
        msg_label.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        msg_label.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))

        self.add_widget(name_label)
        self.add_widget(msg_label)

        self.bind(minimum_height=self.setter("height"))

        def draw_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*bg_color)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(8)])

        self.bind(pos=draw_bg, size=draw_bg)


class SysMessage(Label):
    """Italic dimmed system/status message."""

    def __init__(self, text, **kwargs):
        super().__init__(
            text=f"-- {text} --",
            font_size=theme.FS_SMALL,
            color=theme.TEXT_DIM,
            size_hint_y=None,
            halign="center",
            italic=True,
            **kwargs,
        )
        self.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        self.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))


class ImageMessage(BoxLayout):
    """Chat entry showing a received/sent image thumbnail + caption."""

    def __init__(self, username, filepath, filename, is_self=False, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                         padding=[dp(10), dp(6)], spacing=dp(4), **kwargs)
        bg_color = theme.MSG_SELF if is_self else theme.MSG_PEER

        name_label = Label(
            text=username,
            font_size=theme.FS_SMALL,
            color=theme.ACCENT if is_self else theme.WARNING_FG,
            size_hint_y=None,
            halign="right" if is_self else "left",
            bold=True,
        )
        name_label.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        name_label.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))

        try:
            from kivy.uix.image import AsyncImage
            img_widget = AsyncImage(source=filepath, size_hint_y=None, height=dp(200))
        except Exception:
            img_widget = Label(text=f"[Image: {filename}]", font_size=theme.FS_BODY,
                               color=theme.TEXT, size_hint_y=None, height=dp(30))

        caption = Label(
            text=f"Saved: {filepath}",
            font_size=theme.FS_SMALL,
            color=theme.TEXT_DIM,
            size_hint_y=None,
            halign="left",
        )
        caption.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        caption.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))

        self.add_widget(name_label)
        self.add_widget(img_widget)
        self.add_widget(caption)
        self.bind(minimum_height=self.setter("height"))

        def draw_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*bg_color)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(8)])

        self.bind(pos=draw_bg, size=draw_bg)
