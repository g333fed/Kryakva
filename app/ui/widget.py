from __future__ import annotations

import os
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog
from typing import Any, Callable

from app.config import ROOT_DIR, save_config

ASSETS_DIR = ROOT_DIR / "assets"
DUCK_PNG = ASSETS_DIR / "duck.png"


class DuckWidgetWindow:
    """Tk window with draggable duck image, status indicator and toast notifications."""

    def __init__(self, cfg: dict[str, Any], on_popup: Callable[[tk.Event], None]) -> None:
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.title("Kryakva")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", bool(cfg.get("ui", {}).get("always_on_top", True)))
        self.root.configure(bg="#00ff00")
        try:
            self.root.wm_attributes("-transparentcolor", "#00ff00")
        except Exception:
            pass

        x = int(cfg.get("ui", {}).get("start_x", 40))
        y = int(cfg.get("ui", {}).get("start_y", 60))
        self.root.geometry(f"+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=260, height=260, highlightthickness=0, bg="#00ff00")
        self.canvas.pack()

        self._duck_img: Any = None
        self._drag = {"x": 0, "y": 0}
        self._dot = self.canvas.create_oval(10, 10, 26, 26, fill="#2b3137", outline="#000000")
        self._dot_text = self.canvas.create_text(18, 18, text="", font=("Segoe UI", 9), fill="#0b0f14")

        self.load_duck()

        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Button-3>", on_popup)

    def set_dot(self, state: str) -> None:
        if not bool(self.cfg.get("ui", {}).get("listen_indicator", True)):
            return
        color = {"off": "#2b3137", "listen": "#ff3b30", "think": "#ffcc00"}.get(state, "#2b3137")
        icon = {"off": "", "listen": "🎙", "think": "🧠"}.get(state, "")
        self.canvas.itemconfig(self._dot, fill=color)
        self.canvas.itemconfig(self._dot_text, text=icon)

    def toast(self, text: str, ms: int = 1400) -> None:
        if not bool(self.cfg.get("ui", {}).get("show_bubbles", True)):
            return
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#0b0f14")
        label = tk.Label(
            popup,
            text=text,
            bg="#0b0f14",
            fg="#e6edf3",
            font=("Segoe UI", 9),
            padx=10,
            pady=6,
            wraplength=360,
            justify="left",
        )
        label.pack()
        popup.geometry(f"+{self.root.winfo_x() + 10}+{self.root.winfo_y() + 275}")
        popup.after(ms, popup.destroy)

    def load_duck(self) -> None:
        self.canvas.delete("duck")
        try:
            from PIL import Image, ImageTk

            if DUCK_PNG.exists():
                image = Image.open(DUCK_PNG).convert("RGBA")
                scale = float(self.cfg.get("ui", {}).get("scale", 1.0))
                target = int(250 * max(0.35, min(2.5, scale)))
                image.thumbnail((target, target))
                self._duck_img = ImageTk.PhotoImage(image)
                self.canvas.create_image(130, 140, image=self._duck_img, tags=("duck",))
            else:
                self.canvas.create_text(
                    130,
                    140,
                    text="Нет duck.png\nНастройки → выбрать PNG",
                    fill="white",
                    font=("Segoe UI", 10),
                    tags=("duck",),
                )
        except Exception as error:
            self.canvas.create_text(130, 140, text=f"PNG ошибка: {error}", fill="white", font=("Segoe UI", 9), tags=("duck",))

    def pick_duck_png(self) -> None:
        picked_path = filedialog.askopenfilename(title="Выбери PNG утки", filetypes=[("PNG", "*.png"), ("All", "*.*")])
        if not picked_path:
            return
        os.makedirs(ASSETS_DIR, exist_ok=True)
        shutil.copy2(picked_path, DUCK_PNG)
        self.load_duck()
        self.toast("Утка обновлена 🦆", 1100)

    def set_scale(self) -> None:
        current = float(self.cfg.get("ui", {}).get("scale", 1.0))
        value = simpledialog.askfloat("Масштаб", "0.7 / 1.0 / 1.3", initialvalue=current, minvalue=0.35, maxvalue=2.5)
        if value is None:
            return
        self.cfg.setdefault("ui", {})["scale"] = float(value)
        save_config(self.cfg)
        self.load_duck()

    def _start_drag(self, event: tk.Event) -> None:
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root

    def _do_drag(self, event: tk.Event) -> None:
        dx = event.x_root - self._drag["x"]
        dy = event.y_root - self._drag["y"]
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root
        self.root.geometry(f"+{self.root.winfo_x() + dx}+{self.root.winfo_y() + dy}")

    def _end_drag(self, _event: tk.Event) -> None:
        ui = self.cfg.setdefault("ui", {})
        ui["start_x"] = int(self.root.winfo_x())
        ui["start_y"] = int(self.root.winfo_y())
        save_config(self.cfg)
