from __future__ import annotations

import logging
import os
import threading
from typing import Any, Callable, Optional
from tkinter import filedialog, messagebox

from app.config import ROOT_DIR, save_config
from app.voice.vosk_engine import HotwordListener, VoskPTT, is_vosk_model_folder, list_input_devices

logger = logging.getLogger(__name__)


class VoiceUIController:
    def __init__(self, cfg: dict[str, Any], root, toast: Callable[[str, int], None], beep: Callable[[int, int], None]) -> None:
        self.cfg = cfg
        self.root = root
        self.toast = toast
        self.beep = beep
        self.hotword_listener: Optional[HotwordListener] = None

    def vosk_path(self) -> Optional[str]:
        path = self.cfg.get("voice", {}).get("vosk_model_path", "")
        if not path:
            return None
        return path if str(path).startswith(("/", "\\")) or ":" in str(path) else str(ROOT_DIR / path)

    def pick_vosk_model(self) -> None:
        path = filedialog.askdirectory(title="Выбери папку Vosk-модели (vosk-model-...)")
        if not path:
            return
        if not is_vosk_model_folder(path):
            messagebox.showwarning("Vosk", "Нужна папка модели (где есть am/final.mdl или conf/mfcc.conf).")
            return
        rel = os.path.relpath(path, ROOT_DIR)
        self.cfg.setdefault("voice", {})["vosk_model_path"] = rel
        save_config(self.cfg)
        self.toast("Vosk-модель сохранена 🎙", 1200)
        self.ensure_hotword(force=True, on_hotword=lambda: None)

    def rebuild_device_menu(self, dev_menu, on_rebuild: Callable[[], None]) -> None:
        dev_menu.delete(0, "end")
        devices = list_input_devices()

        def set_dev(idx: Optional[int]) -> None:
            self.cfg.setdefault("voice", {})["input_device"] = idx
            save_config(self.cfg)
            self.toast("Микрофон: " + ("по умолчанию" if idx is None else f"#{idx}"), 1300)
            on_rebuild()

        dev_menu.add_command(label="По умолчанию", command=lambda: set_dev(None))
        dev_menu.add_separator()
        for idx, name in (devices or [])[:25]:
            dev_menu.add_command(label=f"{idx}: {name[:60]}", command=lambda i=idx: set_dev(i))

    def ensure_hotword(self, force: bool, on_hotword: Callable[[], None]) -> None:
        enabled = bool(self.cfg.get("voice", {}).get("hotword_enabled", True))
        if not enabled:
            self.stop_hotword()
            return

        model = self.vosk_path()
        if not model:
            self.stop_hotword()
            return

        if self.hotword_listener and not force:
            return

        self.stop_hotword()
        hotword = self.cfg.get("voice", {}).get("hotword", "кряква")
        device = self.cfg.get("voice", {}).get("input_device")
        samplerate = int(self.cfg.get("voice", {}).get("samplerate", 16000))

        self.hotword_listener = HotwordListener(model, hotword=hotword, samplerate=samplerate, device=device)
        self.hotword_listener.start(lambda: self.root.after(0, on_hotword))
        logger.info("Hotword listener started")

    def stop_hotword(self) -> None:
        if self.hotword_listener:
            self.hotword_listener.stop()
            self.hotword_listener = None

    def listen_ptt(self, on_result: Callable[[bool, str, str], None]) -> None:
        model = self.vosk_path()
        if not model:
            self.toast("ПКМ → Голос ▶ → выбери Vosk-модель", 1800)
            return

        self.beep(880, 80)
        self.toast("Слушаю…", 900)

        def worker() -> None:
            device = self.cfg.get("voice", {}).get("input_device")
            samplerate = int(self.cfg.get("voice", {}).get("samplerate", 16000))
            seconds = float(self.cfg.get("voice", {}).get("ptt_seconds", 4.0))
            logger.info("Voice recognition started")
            result = VoskPTT(model, samplerate=samplerate, device=device).transcribe_once(seconds=seconds)
            logger.info("Voice recognition finished: ok=%s text=%s", result.ok, result.text)
            self.root.after(0, lambda: on_result(result.ok, result.text, result.error))

        threading.Thread(target=worker, daemon=True).start()
