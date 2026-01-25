
from __future__ import annotations
import os, json, queue, threading, time
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class VoiceResult:
    ok: bool
    text: str = ""
    error: str = ""

def is_vosk_model_folder(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    return (os.path.exists(os.path.join(path,"am","final.mdl")) or os.path.exists(os.path.join(path,"conf","mfcc.conf")))

def list_input_devices(max_n: int = 30):
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        out = []
        for i, d in enumerate(devs):
            if d.get("max_input_channels", 0) > 0:
                out.append((i, d.get("name","")))
        return out[:max_n]
    except Exception:
        return []

class VoskPTT:
    def __init__(self, model_path: str, samplerate: int = 16000, device: Optional[int] = None):
        self.model_path = model_path
        self.samplerate = samplerate
        self.device = device

    def transcribe_once(self, seconds: float = 4.0) -> VoiceResult:
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
        except Exception as e:
            return VoiceResult(False, error=f"Нет зависимостей для голоса: {e}")
        if not is_vosk_model_folder(self.model_path):
            return VoiceResult(False, error="Vosk-модель не выбрана или путь неверный.")
        try:
            model = Model(self.model_path)
            rec = KaldiRecognizer(model, self.samplerate)
            q: queue.Queue[bytes] = queue.Queue()
            def callback(indata, frames, t, status): q.put(bytes(indata))
            kwargs = dict(samplerate=self.samplerate, blocksize=8000, dtype="int16", channels=1, callback=callback)
            if self.device is not None: kwargs["device"] = self.device
            with sd.RawInputStream(**kwargs):
                start = time.time()
                while time.time() - start < seconds:
                    rec.AcceptWaveform(q.get())
            j = json.loads(rec.FinalResult())
            text = (j.get("text") or "").strip()
            if not text:
                return VoiceResult(False, error="Не удалось распознать команду.")
            return VoiceResult(True, text=text)
        except Exception as e:
            return VoiceResult(False, error=str(e))

class HotwordListener:
    def __init__(self, model_path: str, hotword: str, samplerate: int = 16000, device: Optional[int] = None):
        self.model_path = model_path
        self.hotword = (hotword or "").lower().strip()
        self.samplerate = samplerate
        self.device = device
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, on_hotword: Callable[[], None]) -> VoiceResult:
        if self._thread and self._thread.is_alive():
            return VoiceResult(True, text="already running")
        if not self.hotword:
            return VoiceResult(False, error="Hotword пустой")
        if not is_vosk_model_folder(self.model_path):
            return VoiceResult(False, error="Для hotword нужна выбранная Vosk-модель.")
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(on_hotword,), daemon=True)
        self._thread.start()
        return VoiceResult(True, text="started")

    def stop(self):
        self._stop.set()

    def _run(self, on_hotword: Callable[[], None]):
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
        except Exception:
            return
        try:
            model = Model(self.model_path)
            rec = KaldiRecognizer(model, self.samplerate)
            q: queue.Queue[bytes] = queue.Queue()
            def callback(indata, frames, t, status): q.put(bytes(indata))
            kwargs = dict(samplerate=self.samplerate, blocksize=4000, dtype="int16", channels=1, callback=callback)
            if self.device is not None: kwargs["device"] = self.device
            with sd.RawInputStream(**kwargs):
                last_fire = 0.0
                while not self._stop.is_set():
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        try:
                            txt = (json.loads(rec.Result()).get("text") or "").lower()
                        except Exception:
                            txt = ""
                        if self.hotword in txt and (time.time() - last_fire) > 1.5:
                            last_fire = time.time()
                            on_hotword()
        except Exception:
            return
