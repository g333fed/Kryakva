from __future__ import annotations
import os, shutil, threading
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from typing import List, Dict, Optional

from app.config import load_config, save_config, ROOT_DIR
from app.commands.router import CommandRouter
from app.commands import windows as win
from app.voice.vosk_engine import VoskPTT, HotwordListener, is_vosk_model_folder, list_input_devices
from app.llm.ollama import OllamaProvider
from app.llm.tools import parse_tool_call, risk_level, tool_schema_text

ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
DUCK_PNG = os.path.join(ASSETS_DIR, "duck.png")

def _beep(freq: int, ms: int):
    try:
        import winsound
        winsound.Beep(freq, ms)
    except Exception:
        pass

class MessagesWindow:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("Кряква — сообщения")
        self.win.geometry("520x320+120+120")
        self.txt = tk.Text(self.win, wrap="word")
        self.txt.pack(fill="both", expand=True)
        self.txt.configure(state="disabled")

    def append(self, line: str):
        self.txt.configure(state="normal")
        self.txt.insert("end", line + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

class DuckDesktopWidget:
    def __init__(self):
        self.cfg = load_config()
        self.router = CommandRouter()
        self._hotword: Optional[HotwordListener] = None
        self._messages: Optional[MessagesWindow] = None
        self._msg_buf: List[str] = []

        self.root = tk.Tk()
        self.root.title("Kryakva")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", bool(self.cfg.get("ui",{}).get("always_on_top", True)))
        self.root.configure(bg="#00ff00")
        try:
            self.root.wm_attributes("-transparentcolor", "#00ff00")
        except Exception:
            pass

        x = int(self.cfg.get("ui",{}).get("start_x", 40))
        y = int(self.cfg.get("ui",{}).get("start_y", 60))
        self.root.geometry(f"+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=260, height=260, highlightthickness=0, bg="#00ff00")
        self.canvas.pack()

        self._duck_img = None
        self._dot = self.canvas.create_oval(10, 10, 26, 26, fill="#2b3137", outline="#000000")
        self._dot_txt = self.canvas.create_text(18, 18, text="", font=("Segoe UI", 9), fill="#0b0f14")

        self._load_duck()

        self._drag = {"x":0,"y":0}
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Button-3>", self._popup)

        self.menu = self._build_menu()
        self.root.bind_all("<Control-Shift-k>", lambda e: self.listen_ptt())

        self._ensure_hotword()
        self.toast("Кряква v0.1.6 (ПКМ — меню)", 1400)

    # ---- UI helpers ----
    def _set_dot(self, state: str):
        if not bool(self.cfg.get("ui",{}).get("listen_indicator", True)):
            return
        color = {"off":"#2b3137","listen":"#ff3b30","think":"#ffcc00"}.get(state,"#2b3137")
        icon = {"off":"","listen":"🎙","think":"🧠"}.get(state,"")
        self.canvas.itemconfig(self._dot, fill=color)
        self.canvas.itemconfig(self._dot_txt, text=icon)

    def toast(self, text: str, ms: int = 1400):
        if not bool(self.cfg.get("ui",{}).get("show_bubbles", True)):
            return
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg="#0b0f14")
        lbl = tk.Label(t, text=text, bg="#0b0f14", fg="#e6edf3", font=("Segoe UI", 9), padx=10, pady=6, wraplength=360, justify="left")
        lbl.pack()
        t.geometry(f"+{self.root.winfo_x()+10}+{self.root.winfo_y()+275}")
        t.after(ms, t.destroy)

    def _msg(self, line: str):
        self._msg_buf.append(line)
        self._msg_buf = self._msg_buf[-300:]
        if self._messages and self._messages.win.winfo_exists():
            self._messages.append(line)

    def show_messages(self):
        if self._messages and self._messages.win.winfo_exists():
            self._messages.win.lift()
            return
        self._messages = MessagesWindow(self.root)
        for ln in self._msg_buf[-200:]:
            self._messages.append(ln)

    # ---- drag ----
    def _start_drag(self, e):
        self._drag["x"] = e.x_root
        self._drag["y"] = e.y_root

    def _do_drag(self, e):
        dx = e.x_root - self._drag["x"]
        dy = e.y_root - self._drag["y"]
        self._drag["x"] = e.x_root
        self._drag["y"] = e.y_root
        self.root.geometry(f"+{self.root.winfo_x()+dx}+{self.root.winfo_y()+dy}")

    def _end_drag(self, e):
        ui = self.cfg.setdefault("ui", {})
        ui["start_x"] = int(self.root.winfo_x())
        ui["start_y"] = int(self.root.winfo_y())
        save_config(self.cfg)

    # ---- assets ----
    def _load_duck(self):
        self.canvas.delete("duck")
        try:
            from PIL import Image, ImageTk
            if os.path.exists(DUCK_PNG):
                im = Image.open(DUCK_PNG).convert("RGBA")
                scale = float(self.cfg.get("ui",{}).get("scale", 1.0))
                target = int(250 * max(0.35, min(2.5, scale)))
                im.thumbnail((target, target))
                self._duck_img = ImageTk.PhotoImage(im)
                self.canvas.create_image(130, 140, image=self._duck_img, tags=("duck",))
            else:
                self.canvas.create_text(130, 140, text="Нет duck.png\nНастройки → выбрать PNG", fill="white", font=("Segoe UI", 10), tags=("duck",))
        except Exception as e:
            self.canvas.create_text(130, 140, text=f"PNG ошибка: {e}", fill="white", font=("Segoe UI", 9), tags=("duck",))

    def pick_duck_png(self):
        p = filedialog.askopenfilename(title="Выбери PNG утки", filetypes=[("PNG", "*.png"), ("All", "*.*")])
        if not p:
            return
        os.makedirs(ASSETS_DIR, exist_ok=True)
        shutil.copy2(p, DUCK_PNG)
        self._load_duck()
        self.toast("Утка обновлена 🦆", 1100)

    def set_scale(self):
        cur = float(self.cfg.get("ui",{}).get("scale", 1.0))
        s = simpledialog.askfloat("Масштаб", "0.7 / 1.0 / 1.3", initialvalue=cur, minvalue=0.35, maxvalue=2.5)
        if s is None:
            return
        self.cfg.setdefault("ui", {})["scale"] = float(s)
        save_config(self.cfg)
        self._load_duck()

    # ---- menu ----
    def _build_menu(self) -> tk.Menu:
        menu = tk.Menu(self.root, tearoff=0)

        actions = tk.Menu(menu, tearoff=0)
        actions.add_command(label="Показать рабочий стол", command=lambda: self.handle_text("покажи рабочий стол"))
        actions.add_command(label="Открыть проводник", command=lambda: self.handle_text("открой проводник"))
        actions.add_command(label="Открыть загрузки", command=lambda: self.handle_text("открой загрузки"))
        actions.add_separator()
        actions.add_command(label="🌐 Поиск…", command=self.ask_search)
        menu.add_cascade(label="Действия ▶", menu=actions)

        windows = tk.Menu(menu, tearoff=0)
        windows.add_command(label="Диспетчер задач", command=lambda: self.handle_text("открой диспетчер задач"))
        windows.add_command(label="Настройки", command=lambda: self.handle_text("открой настройки"))
        windows.add_command(label="Безопасность", command=lambda: self.handle_text("открой безопасность"))
        windows.add_separator()
        windows.add_command(label="CMD", command=lambda: self.handle_text("cmd"))
        windows.add_command(label="PowerShell", command=lambda: self.handle_text("powershell"))
        menu.add_cascade(label="Windows ▶", menu=windows)

        wnd = tk.Menu(menu, tearoff=0)
        wnd.add_command(label="Закрыть активное окно", command=lambda: self.handle_text("закрой окно"))
        wnd.add_command(label="Свернуть активное окно", command=lambda: self.handle_text("сверни окно"))
        wnd.add_command(label="Развернуть активное окно", command=lambda: self.handle_text("разверни окно"))
        wnd.add_separator()
        wnd.add_command(label="Прижать влево", command=lambda: self.handle_text("прижми влево"))
        wnd.add_command(label="Прижать вправо", command=lambda: self.handle_text("прижми вправо"))
        menu.add_cascade(label="Окна ▶", menu=wnd)

        voice = tk.Menu(menu, tearoff=0)
        voice.add_command(label="🎙 Слушать (Ctrl+Shift+K)", command=self.listen_ptt)
        voice.add_command(label="Выбрать Vosk-модель…", command=self.pick_vosk_model)
        voice.add_separator()
        self.hotword_var = tk.BooleanVar(value=bool(self.cfg.get("voice",{}).get("hotword_enabled", True)))
        voice.add_checkbutton(label="Автослушание: «кряква»", variable=self.hotword_var, command=self.toggle_hotword)
        dev = tk.Menu(voice, tearoff=0)
        voice.add_cascade(label="Микрофон ▶", menu=dev)
        self.dev_menu = dev
        self.rebuild_device_menu()
        menu.add_cascade(label="Голос ▶", menu=voice)

        brain = tk.Menu(menu, tearoff=0)
        self.llm_var = tk.BooleanVar(value=bool(self.cfg.get("llm",{}).get("enabled", False)))
        brain.add_checkbutton(label="Включить нейросеть (Ollama)", variable=self.llm_var, command=self.toggle_llm)
        brain.add_command(label="Спросить текстом…", command=self.ask_text)
        brain.add_command(label="Проверить Ollama", command=self.llm_check)
        menu.add_cascade(label="Мозг ▶", menu=brain)

        settings = tk.Menu(menu, tearoff=0)
        settings.add_command(label="Выбрать PNG утки…", command=self.pick_duck_png)
        settings.add_command(label="Масштаб…", command=self.set_scale)
        settings.add_separator()
        settings.add_command(label="Окно сообщений", command=self.show_messages)
        menu.add_cascade(label="Настройки ▶", menu=settings)

        menu.add_separator()
        menu.add_command(label="Выход", command=self.quit)
        return menu

    def _popup(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    # ---- voice ----
    def _vosk_path(self) -> Optional[str]:
        p = self.cfg.get("voice",{}).get("vosk_model_path","")
        if not p:
            return None
        return p if os.path.isabs(p) else os.path.join(ROOT_DIR, p)

    def pick_vosk_model(self):
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
        self._ensure_hotword(force=True)

    def rebuild_device_menu(self):
        self.dev_menu.delete(0, "end")
        devs = list_input_devices()
        def set_dev(idx):
            self.cfg.setdefault("voice", {})["input_device"] = idx
            save_config(self.cfg)
            self.toast("Микрофон: " + ("по умолчанию" if idx is None else f"#{idx}"), 1300)
            self._ensure_hotword(force=True)

        self.dev_menu.add_command(label="По умолчанию", command=lambda: set_dev(None))
        self.dev_menu.add_separator()
        for idx, name in (devs or [])[:25]:
            self.dev_menu.add_command(label=f"{idx}: {name[:60]}", command=lambda i=idx: set_dev(i))

    def toggle_hotword(self):
        self.cfg.setdefault("voice", {})["hotword_enabled"] = bool(self.hotword_var.get())
        save_config(self.cfg)
        self._ensure_hotword(force=True)

    def _ensure_hotword(self, force: bool=False):
        if not bool(self.cfg.get("voice",{}).get("hotword_enabled", True)):
            if self._hotword:
                self._hotword.stop()
                self._hotword = None
            return
        model = self._vosk_path()
        if not model:
            if self._hotword:
                self._hotword.stop()
                self._hotword = None
            return
        if self._hotword and not force:
            return
        if self._hotword:
            self._hotword.stop()
        hotword = self.cfg.get("voice",{}).get("hotword","кряква")
        dev = self.cfg.get("voice",{}).get("input_device", None)
        sr = int(self.cfg.get("voice",{}).get("samplerate",16000))
        self._hotword = HotwordListener(model, hotword=hotword, samplerate=sr, device=dev)
        self._hotword.start(lambda: self.root.after(0, self.on_hotword))

    def listen_ptt(self):
        model = self._vosk_path()
        if not model:
            self.toast("ПКМ → Голос ▶ → выбери Vosk-модель", 1800)
            return
        self._set_dot("listen"); _beep(880, 80)
        self.toast("Слушаю…", 900)

        def work():
            dev = self.cfg.get("voice",{}).get("input_device", None)
            sr = int(self.cfg.get("voice",{}).get("samplerate",16000))
            sec = float(self.cfg.get("voice",{}).get("ptt_seconds",4.0))
            res = VoskPTT(model, samplerate=sr, device=dev).transcribe_once(seconds=sec)
            self.root.after(0, lambda: self.on_stt(res.ok, res.text, res.error))
        threading.Thread(target=work, daemon=True).start()

    def on_hotword(self):
        _beep(990, 70)
        self.toast("Кряква тут. Говори команду…", 1400)
        self._msg("HOTWORD: кряква")
        self.listen_ptt()

    def on_stt(self, ok: bool, text: str, err: str):
        self._set_dot("off"); _beep(660, 70)
        if not ok:
            self.toast(err, 1800)
            self._msg("STT ❌ " + err)
            return
        self.toast("Ты: " + text, 1800)
        self._msg("Ты: " + text)
        self.handle_text(text)

    # ---- LLM ----
    def toggle_llm(self):
        self.cfg.setdefault("llm", {})["enabled"] = bool(self.llm_var.get())
        save_config(self.cfg)

    def llm_check(self):
        prov = self._ollama()
        if prov.ping():
            self.toast("Ollama: OK ✅", 1400)
        else:
            messagebox.showwarning("Ollama", "Не найден. Установи/запусти Ollama и скачай модель (например: ollama pull gemma2:2b).")

    def _ollama(self) -> OllamaProvider:
        llm = self.cfg.get("llm",{})
        return OllamaProvider(
            base_url=llm.get("base_url","http://localhost:11434"),
            model=llm.get("model","gemma2:2b"),
            temperature=float(llm.get("temperature",0.4)),
            max_tokens=int(llm.get("max_tokens",512))
        )

    def ask_search(self):
        q = simpledialog.askstring("Поиск", "Что ищем?")
        if q:
            self.handle_text("поищи " + q)

    def ask_text(self):
        q = simpledialog.askstring("Кряква", "Напиши команду или вопрос:")
        if q:
            self._msg("Ты (текст): " + q)
            self.handle_text(q)

    # ---- core ----
    def handle_text(self, text: str):
        r = self.router.route(text)
        if r.intent == "cmd":
            self.exec_cmd(r.command, r.argument)
            self._msg(f"Кряква: ✅ {r.command}")
            return

        if not bool(self.cfg.get("llm",{}).get("enabled", False)):
            self.toast("Нейросеть выключена (ПКМ → Мозг ▶)", 1800)
            self._msg("Кряква: нейросеть выключена")
            return

        self._set_dot("think")
        self.toast("Думаю…", 900)
        self._msg("Кряква: думаю…")

        def work():
            try:
                sys = (
                    "Ты — Кряква, помощник Windows. Выполняй команды пользователя.\n"
                    "Если нужно действие в Windows — верни ТОЛЬКО JSON инструмента.\n"
                    "Никогда не открывай панель управления, если пользователь прямо не попросил.\n\n"
                    + tool_schema_text()
                )
                messages: List[Dict[str,str]] = [
                    {"role":"system","content": sys},
                    {"role":"user","content": (r.argument or "")},
                ]
                ans = (self._ollama().chat(messages) or "").strip()
                tc = parse_tool_call(ans)
                self.root.after(0, lambda: self.on_llm(ans, tc, (r.argument or "")))
            except Exception as e:
                self.root.after(0, lambda: self.toast(f"LLM ошибка: {e}", 2200))
            finally:
                self.root.after(0, lambda: self._set_dot("off"))
        threading.Thread(target=work, daemon=True).start()

    def on_llm(self, ans: str, tc, user_text: str):
        if tc:
            # guard: prevent random control panel
            if tc.name == "open_control_panel" and ("панель" not in user_text.lower() and "control panel" not in user_text.lower()):
                self._msg("Кряква: ❗ отклонено open_control_panel (не просили)")
                messagebox.showinfo("Кряква", "Я не буду открывать Панель управления без запроса. Скажи конкретную команду.")
                return

            lvl = risk_level(tc.name)
            self._msg(f"Кряква: 🛠 {tc.name} ({lvl})")
            if lvl == "med":
                ok = messagebox.askyesno("Подтверждение", f"Выполнить действие: {tc.name}?")
                if not ok:
                    self._msg("Кряква: отмена")
                    return
            arg = (tc.args or {}).get("query") if tc.name == "web_search" else (tc.args or {}).get("url") if tc.name == "open_url" else None
            self.exec_cmd(tc.name, arg)
            self._msg("Кряква: ✅ выполнено (через мозг)")
            return

        self._msg("Кряква: " + ans)
        messagebox.showinfo("Кряква", ans)

    def exec_cmd(self, cmd: str, arg: Optional[str]):
        try:
            if cmd == "show_desktop": win.show_desktop()
            elif cmd == "open_explorer": win.open_explorer()
            elif cmd == "open_downloads": win.open_downloads()
            elif cmd == "open_documents": win.open_documents()
            elif cmd == "open_taskmgr": win.open_taskmgr()
            elif cmd == "open_settings": win.open_settings()
            elif cmd == "open_security": win.open_security()
            elif cmd == "open_notepad": win.open_notepad()
            elif cmd == "open_calc": win.open_calc()
            elif cmd == "open_cmd": win.open_cmd()
            elif cmd == "open_powershell": win.open_powershell()
            elif cmd == "open_control_panel": win.open_control_panel()
            elif cmd == "open_device_manager": win.open_device_manager()
            elif cmd == "open_services": win.open_services()
            elif cmd == "open_recycle_bin": win.open_recycle_bin()
            elif cmd == "empty_recycle_bin": win.empty_recycle_bin(True)
            elif cmd == "lock_pc": win.lock_pc()
            elif cmd == "sleep_pc": win.sleep_pc()
            elif cmd == "volume_up": win.volume_up(5)
            elif cmd == "volume_down": win.volume_down(5)
            elif cmd == "volume_mute": win.volume_mute()
            elif cmd == "close_active_window": win.close_active_window()
            elif cmd == "minimize_window": win.minimize_window()
            elif cmd == "maximize_window": win.maximize_window()
            elif cmd == "snap_left": win.snap_left()
            elif cmd == "snap_right": win.snap_right()
            elif cmd == "open_url" and arg: win.open_url(arg)
            elif cmd == "web_search" and arg: win.web_search(arg)
            else:
                self.toast(f"Неизвестная команда: {cmd}", 1600)
        except Exception as e:
            self.toast(f"Ошибка команды: {e}", 2200)

    def quit(self):
        try:
            if self._hotword:
                self._hotword.stop()
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
