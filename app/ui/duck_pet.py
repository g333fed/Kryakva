from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Dict, List, Optional

from app.commands import windows as win
from app.commands.registry import execute_command
from app.commands.router import CommandRouter
from app.config import load_config, save_config
from app.llm.ollama import OllamaProvider
from app.llm.tools import parse_tool_call, risk_level, tool_schema_text
from app.ui.menu import build_main_menu
from app.ui.messages import MessagesWindow
from app.ui.voice_ui import VoiceUIController
from app.ui.widget import DuckWidgetWindow

logger = logging.getLogger(__name__)


def _beep(freq: int, ms: int) -> None:
    try:
        import winsound

        winsound.Beep(freq, ms)
    except Exception:
        pass


class DuckDesktopWidget:
    """Main application coordinator for the desktop duck assistant."""

    def __init__(self) -> None:
        self.cfg = load_config()
        self.router = CommandRouter()
        self.messages_window: Optional[MessagesWindow] = None
        self.message_buffer: List[str] = []

        self.widget = DuckWidgetWindow(self.cfg, self._popup)
        self.root = self.widget.root
        self.hotword_var = tk.BooleanVar(value=bool(self.cfg.get("voice", {}).get("hotword_enabled", True)))
        self.llm_var = tk.BooleanVar(value=bool(self.cfg.get("llm", {}).get("enabled", False)))

        self.voice = VoiceUIController(self.cfg, self.root, self.widget.toast, _beep)
        self.menu = build_main_menu(self)
        self.root.bind_all("<Control-Shift-k>", lambda _event: self.listen_ptt())
        self.voice.ensure_hotword(force=False, on_hotword=self.on_hotword)
        self.widget.toast("Кряква v0.1.6 (ПКМ — меню)", 1400)

    def _popup(self, event: tk.Event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _msg(self, line: str) -> None:
        self.message_buffer.append(line)
        self.message_buffer = self.message_buffer[-300:]
        if self.messages_window and self.messages_window.win.winfo_exists():
            self.messages_window.append(line)

    def show_messages(self) -> None:
        if self.messages_window and self.messages_window.win.winfo_exists():
            self.messages_window.win.lift()
            return
        self.messages_window = MessagesWindow(self.root)
        for line in self.message_buffer[-200:]:
            self.messages_window.append(line)

    def rebuild_device_menu(self) -> None:
        self.voice.rebuild_device_menu(self.dev_menu, on_rebuild=lambda: self.voice.ensure_hotword(force=True, on_hotword=self.on_hotword))

    def pick_vosk_model(self) -> None:
        self.voice.pick_vosk_model()
        self.voice.ensure_hotword(force=True, on_hotword=self.on_hotword)

    def toggle_hotword(self) -> None:
        self.cfg.setdefault("voice", {})["hotword_enabled"] = bool(self.hotword_var.get())
        save_config(self.cfg)
        self.voice.ensure_hotword(force=True, on_hotword=self.on_hotword)

    def listen_ptt(self) -> None:
        self.widget.set_dot("listen")
        self.voice.listen_ptt(self.on_stt)

    def on_hotword(self) -> None:
        _beep(990, 70)
        self.widget.toast("Кряква тут. Говори команду…", 1400)
        self._msg("HOTWORD: кряква")
        self.listen_ptt()

    def on_stt(self, ok: bool, text: str, err: str) -> None:
        self.widget.set_dot("off")
        _beep(660, 70)
        if not ok:
            self.widget.toast(err, 1800)
            self._msg("STT ❌ " + err)
            logger.warning("STT failed: %s", err)
            return
        self.widget.toast("Ты: " + text, 1800)
        self._msg("Ты: " + text)
        self.handle_text(text)

    def toggle_llm(self) -> None:
        self.cfg.setdefault("llm", {})["enabled"] = bool(self.llm_var.get())
        save_config(self.cfg)

    def _ollama(self) -> OllamaProvider:
        llm = self.cfg.get("llm", {})
        return OllamaProvider(
            base_url=llm.get("base_url", "http://localhost:11434"),
            model=llm.get("model", "gemma2:2b"),
            temperature=float(llm.get("temperature", 0.4)),
            max_tokens=int(llm.get("max_tokens", 512)),
        )

    def llm_check(self) -> None:
        provider = self._ollama()
        if provider.ping():
            self.widget.toast("Ollama: OK ✅", 1400)
            return
        messagebox.showwarning("Ollama", "Не найден. Установи/запусти Ollama и скачай модель (например: ollama pull gemma2:2b).")

    def ask_search(self) -> None:
        query = simpledialog.askstring("Поиск", "Что ищем?")
        if query:
            self.handle_text("поищи " + query)

    def ask_text(self) -> None:
        query = simpledialog.askstring("Кряква", "Напиши команду или вопрос:")
        if query:
            self._msg("Ты (текст): " + query)
            self.handle_text(query)

    def handle_text(self, text: str) -> None:
        route = self.router.route(text)
        if route.intent == "cmd":
            self.exec_cmd(route.command or "", route.argument)
            self._msg(f"Кряква: ✅ {route.command}")
            return

        if not bool(self.cfg.get("llm", {}).get("enabled", False)):
            self.widget.toast("Нейросеть выключена (ПКМ → Мозг ▶)", 1800)
            self._msg("Кряква: нейросеть выключена")
            return

        self.widget.set_dot("think")
        self.widget.toast("Думаю…", 900)
        self._msg("Кряква: думаю…")

        def worker() -> None:
            try:
                logger.info("Sending request to LLM")
                system_prompt = (
                    "Ты — Кряква, помощник Windows. Выполняй команды пользователя.\n"
                    "Если нужно действие в Windows — верни ТОЛЬКО JSON инструмента.\n"
                    "Никогда не открывай панель управления, если пользователь прямо не попросил.\n\n"
                    + tool_schema_text()
                )
                messages: List[Dict[str, str]] = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (route.argument or "")},
                ]
                answer = (self._ollama().chat(messages) or "").strip()
                self.root.after(0, lambda: self.on_llm(answer, parse_tool_call(answer), (route.argument or "")))
            except Exception as error:
                logger.exception("LLM request failed")
                self.root.after(0, lambda: self.widget.toast(f"LLM ошибка: {error}", 2200))
            finally:
                self.root.after(0, lambda: self.widget.set_dot("off"))

        threading.Thread(target=worker, daemon=True).start()

    def on_llm(self, answer: str, tool_call, user_text: str) -> None:
        if tool_call:
            if tool_call.name == "open_control_panel" and ("панель" not in user_text.lower() and "control panel" not in user_text.lower()):
                self._msg("Кряква: ❗ отклонено open_control_panel (не просили)")
                messagebox.showinfo("Кряква", "Я не буду открывать Панель управления без запроса. Скажи конкретную команду.")
                return

            level = risk_level(tool_call.name)
            self._msg(f"Кряква: 🛠 {tool_call.name} ({level})")
            if level == "med":
                confirmed = messagebox.askyesno("Подтверждение", f"Выполнить действие: {tool_call.name}?")
                if not confirmed:
                    self._msg("Кряква: отмена")
                    return

            argument = (tool_call.args or {}).get("query") if tool_call.name == "web_search" else (tool_call.args or {}).get("url") if tool_call.name == "open_url" else None
            self.exec_cmd(tool_call.name, argument)
            self._msg("Кряква: ✅ выполнено (через мозг)")
            return

        self._msg("Кряква: " + answer)
        messagebox.showinfo("Кряква", answer)

    def exec_cmd(self, command: str, argument: Optional[str]) -> None:
        try:
            if command == "take_screenshot":
                screenshot_path = win.screenshot_to_desktop()
                if screenshot_path:
                    self.widget.toast(f"Скриншот сохранён: {screenshot_path}", 2600)
                    self._msg(f"Кряква: 📸 {screenshot_path}")
                else:
                    self.widget.toast("Не удалось сделать скриншот", 1800)
                return

            if not execute_command(command, argument):
                self.widget.toast(f"Неизвестная команда: {command}", 1600)
                return
            logger.info("Executed command: %s arg=%s", command, argument)
        except Exception as error:
            logger.exception("Command execution error")
            self.widget.toast(f"Ошибка команды: {error}", 2200)

    def quit(self) -> None:
        self.voice.stop_hotword()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
