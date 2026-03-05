from __future__ import annotations

import tkinter as tk


class MessagesWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.win = tk.Toplevel(root)
        self.win.title("Кряква — сообщения")
        self.win.geometry("520x320+120+120")
        self.text = tk.Text(self.win, wrap="word")
        self.text.pack(fill="both", expand=True)
        self.text.configure(state="disabled")

    def append(self, line: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", f"{line}\n")
        self.text.see("end")
        self.text.configure(state="disabled")
