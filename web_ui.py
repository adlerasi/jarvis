from __future__ import annotations
import os
import threading
import webview
import time


class DummyRoot:
    def __init__(self, window):
        self.window = window
    
    def mainloop(self):
        # Start webview. This blocks the thread.
        webview.start(debug=False)

class Api:
    def __init__(self):
        self.ui = None

    def send_command(self, text):
        print(f"[WebUI] API received command: {text}")
        if self.ui and self.ui.on_text_command:
            self.ui.on_text_command(text)

    def toggle_pause(self, paused):
        if self.ui and self.ui.on_pause_toggle:
            self.ui.on_pause_toggle(paused)

    def toggle_mute(self, muted):
        if self.ui:
            self.ui.muted = muted

class JarvisWebUI:
    def __init__(self):
        self.muted = False
        self.on_text_command = None
        self.on_pause_toggle = None
        self.on_effects_state_change = None
        
        self.api = Api()
        self.api.ui = self
        
        # Web UI HTML (standalone file, created by JARVIS_UI_Pro.html generator)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, "web_ui.html")
        
        self.window = webview.create_window(
            "JARVIS AI", 
            url=html_path, 
            js_api=self.api, 
            width=1200, 
            height=800,
            background_color="#0B1120"
        )
        self.root = DummyRoot(self.window)

    def write_log(self, msg: str):
        level = "info"
        msg_lower = msg.lower()
        if "err" in msg_lower or "hata" in msg_lower:
            level = "error"
        elif "ok" in msg_lower or "başarı" in msg_lower or "tamam" in msg_lower:
            level = "success"
        elif "cmd" in msg_lower or "siz:" in msg_lower:
            level = "warn"
            
        msg_esc = msg.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')
        js = f"window.addJarvisLog('{msg_esc}', '{level}');"
        self._run_js(js)

    def write_debug(self, msg: str, level="DEBUG"):
        pass

    def mark_user_activity(self, val: bool):
        pass

    def set_state(self, state: str):
        js = f"window.setJarvisState('{state}');"
        self._run_js(js)

    def play_success_sfx(self):
        sfx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SFX", "Success.wav")
        if os.path.exists(sfx_path):
            def play():
                try:
                    import winsound
                    winsound.PlaySound(sfx_path, winsound.SND_FILENAME)
                except ImportError:
                    pass
            threading.Thread(target=play, daemon=True).start()

    def focus_panel(self, panel: str, duration_ms: int):
        pass

    def destroy(self):
        try:
            self.window.destroy()
        except Exception as e:
            # Log the error for debugging purposes but don't let it propagate
            # as this is called during cleanup/shutdown
            print(f"[WebUI] Error during destroy: {e}")

    def _run_js(self, js: str):
        try:
            self.window.evaluate_js(js)
        except Exception as e:
            print(f"[WebUI JS Error] {e} - JS: {js}")
