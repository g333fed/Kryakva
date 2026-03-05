from __future__ import annotations

import tkinter as tk
from typing import Any


def build_main_menu(app: Any) -> tk.Menu:
    menu = tk.Menu(app.root, tearoff=0)

    actions = tk.Menu(menu, tearoff=0)
    actions.add_command(label="Показать рабочий стол", command=lambda: app.handle_text("покажи рабочий стол"))
    actions.add_command(label="Открыть проводник", command=lambda: app.handle_text("открой проводник"))
    actions.add_command(label="Открыть загрузки", command=lambda: app.handle_text("открой загрузки"))
    actions.add_command(label="Окно «Выполнить»", command=lambda: app.handle_text("открой выполнить"))
    actions.add_command(label="Буфер обмена", command=lambda: app.handle_text("открой буфер обмена"))
    actions.add_command(label="Скриншот экрана", command=lambda: app.handle_text("сделай скриншот"))
    actions.add_separator()
    actions.add_command(label="🌐 Поиск…", command=app.ask_search)
    menu.add_cascade(label="Действия ▶", menu=actions)

    windows = tk.Menu(menu, tearoff=0)
    windows.add_command(label="Диспетчер задач", command=lambda: app.handle_text("открой диспетчер задач"))
    windows.add_command(label="Настройки", command=lambda: app.handle_text("открой настройки"))
    windows.add_command(label="Безопасность", command=lambda: app.handle_text("открой безопасность"))
    windows.add_separator()
    windows.add_command(label="CMD", command=lambda: app.handle_text("cmd"))
    windows.add_command(label="PowerShell", command=lambda: app.handle_text("powershell"))
    menu.add_cascade(label="Windows ▶", menu=windows)

    wnd = tk.Menu(menu, tearoff=0)
    wnd.add_command(label="Закрыть активное окно", command=lambda: app.handle_text("закрой окно"))
    wnd.add_command(label="Свернуть активное окно", command=lambda: app.handle_text("сверни окно"))
    wnd.add_command(label="Развернуть активное окно", command=lambda: app.handle_text("разверни окно"))
    wnd.add_separator()
    wnd.add_command(label="Прижать влево", command=lambda: app.handle_text("прижми влево"))
    wnd.add_command(label="Прижать вправо", command=lambda: app.handle_text("прижми вправо"))
    menu.add_cascade(label="Окна ▶", menu=wnd)

    voice = tk.Menu(menu, tearoff=0)
    voice.add_command(label="🎙 Слушать (Ctrl+Shift+K)", command=app.listen_ptt)
    voice.add_command(label="Выбрать Vosk-модель…", command=app.pick_vosk_model)
    voice.add_separator()
    voice.add_checkbutton(label="Автослушание: «кряква»", variable=app.hotword_var, command=app.toggle_hotword)
    dev = tk.Menu(voice, tearoff=0)
    voice.add_cascade(label="Микрофон ▶", menu=dev)
    app.dev_menu = dev
    app.rebuild_device_menu()
    menu.add_cascade(label="Голос ▶", menu=voice)

    brain = tk.Menu(menu, tearoff=0)
    brain.add_checkbutton(label="Включить нейросеть (Ollama)", variable=app.llm_var, command=app.toggle_llm)
    brain.add_command(label="Спросить текстом…", command=app.ask_text)
    brain.add_command(label="Проверить Ollama", command=app.llm_check)
    menu.add_cascade(label="Мозг ▶", menu=brain)

    settings = tk.Menu(menu, tearoff=0)
    settings.add_command(label="Выбрать PNG утки…", command=app.widget.pick_duck_png)
    settings.add_command(label="Масштаб…", command=app.widget.set_scale)
    settings.add_separator()
    settings.add_command(label="Окно сообщений", command=app.show_messages)
    menu.add_cascade(label="Настройки ▶", menu=settings)

    menu.add_separator()
    menu.add_command(label="Выход", command=app.quit)
    return menu
