from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.clock import Clock

import settings as cfg
import network
import utils

from screens.connect_screen import ConnectScreen
from screens.chat_screen import ChatScreen
from screens.settings_screen import SettingsScreen
from screens.ipinfo_screen import IpInfoScreen


class BukpApp(App):
    def build(self):
        self._settings = cfg.load()
        self._server = None

        # Shared state passed into every screen
        self.app_state = {
            "settings":       self._settings,
            "connection":     None,
            "on_message":     self._on_message,
            "on_image":       self._on_image,
            "on_sys_msg":     self._on_sys_msg,
            "on_progress":    self._on_progress,
            "on_image_cancel":self._on_image_cancel,
            "restart_server": self._restart_server,
        }

        self.sm = ScreenManager(transition=NoTransition())
        self._connect_screen  = ConnectScreen(self.app_state)
        self._chat_screen     = ChatScreen(self.app_state)
        self._settings_screen = SettingsScreen(self.app_state)
        self._ipinfo_screen   = IpInfoScreen()

        for screen in [self._connect_screen, self._chat_screen,
                       self._settings_screen, self._ipinfo_screen]:
            self.sm.add_widget(screen)

        self._start_server(self._settings.get("port", utils.DEFAULT_PORT))
        return self.sm

    # ── Server ─────────────────────────────────────────────────────────────────
    def _start_server(self, port):
        try:
            self._server = network.Server(port, self._on_incoming)
            self._server.start()
            Clock.schedule_once(
                lambda dt: self._on_sys_msg(f"Listening on port {port}"), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._on_sys_msg(f"Could not start listener: {e}"), 0
            )

    def _restart_server(self, port):
        if self._server:
            self._server.stop()
        self._start_server(port)

    # ── Incoming connection ────────────────────────────────────────────────────
    def _on_incoming(self, sock, addr):
        ip = addr[0]
        blocked = self._settings.get("blocked_ips", [])
        if ip in blocked:
            try:
                sock.close()
            except Exception:
                pass
            return
        if self.app_state.get("connection") and self.app_state["connection"]._active:
            try:
                sock.close()
            except Exception:
                pass
            return
        Clock.schedule_once(
            lambda dt: self._connect_screen.show_incoming_popup(ip, sock), 0
        )

    # ── Callbacks (called from network thread, dispatched to main thread) ──────
    def _on_message(self, username, text):
        Clock.schedule_once(
            lambda dt: self._chat_screen.add_message(username, text, is_self=False), 0
        )
        conn = self.app_state.get("connection")
        if conn:
            Clock.schedule_once(
                lambda dt: self._chat_screen.set_status(True, username), 0
            )

    def _on_image(self, sender, filepath, filename):
        Clock.schedule_once(
            lambda dt: self._chat_screen.add_image_message(sender, filepath, filename), 0
        )

    def _on_sys_msg(self, text):
        self._chat_screen.add_sys_message(text)

    def _on_progress(self, received, total):
        pct = (received / total * 100) if total else 0
        Clock.schedule_once(lambda dt: self._chat_screen.set_progress(pct), 0)

    def _on_image_cancel(self):
        Clock.schedule_once(
            lambda dt: self._chat_screen.add_sys_message("Transfer cancelled by sender."), 0
        )

    def on_stop(self):
        conn = self.app_state.get("connection")
        if conn:
            conn.disconnect()
        if self._server:
            self._server.stop()


if __name__ == "__main__":
    BukpApp().run()
