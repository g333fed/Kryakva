# Kryakva 🦆

> Desktop duck assistant for Windows: voice commands, quick automation, local AI, and cute pet vibes.

Kryakva is a Python desktop pet assistant for Windows. It sits on your desktop as a duck widget and helps you automate daily actions: opening tools, controlling windows, handling audio, launching search, and (optionally) using a local LLM via Ollama.

---

## ✨ What’s New

- ✅ Source-blocker logic is removed — app now works normally from ZIP/extracted folders.
- 🧩 Modular architecture (UI/voice/commands/llm split by responsibility).
- 🛠️ Expanded quick actions: **Run dialog**, **Clipboard history**, **Desktop screenshot**.

---

## 🚀 Features

### Desktop Duck UI
- Transparent always-on-top widget.
- Drag-and-drop positioning.
- Replaceable duck PNG skin.
- Scale control via context menu.
- Toast notifications and message log window.

### Voice Control (Vosk)
- Hotword activation: **`кряква`**.
- Push-to-talk: **`Ctrl+Shift+K`**.
- Vosk model picker from GUI.
- Input microphone selection from GUI.

### Windows Automation
- Open Explorer, Downloads, Documents, Task Manager, Settings, Security.
- Launch CMD / PowerShell / Control Panel / Services / Device Manager.
- Window actions: close, minimize, maximize, snap left/right.
- System actions: show desktop, lock PC, sleep, recycle bin operations.
- Sound controls: volume up/down, mute.
- Extra productivity actions:
  - Open **Run dialog** (`Win + R`)
  - Open **Clipboard history** (`Win + V`)
  - Save **desktop screenshot** to Desktop folder

### Local LLM (Optional)
- Ollama integration for local AI command interpretation.
- Tool-call mode with risk-level checks.
- Works with Gemma-family models (configurable).

---

## 🏗️ Architecture Overview

```text
app/
  main.py                # entrypoint
  config.py              # config schema + defaults + validation
  logging_config.py      # logging setup
  commands/
    router.py            # phrase -> command/llm intent
    registry.py          # command registry + dynamic dispatch
    windows.py           # Windows automation layer
  voice/
    vosk_engine.py       # PTT + hotword recognition
  llm/
    ollama.py            # Ollama API client
    tools.py             # tool parsing + risk policy
  ui/
    duck_pet.py          # application coordinator
    widget.py            # visual widget + drag/toasts
    menu.py              # context menu builder
    messages.py          # messages log window
    voice_ui.py          # voice-related UI orchestration
```

---

## 📦 Installation

### 1) Prerequisites
- Windows 10/11 (7+ partially supported).
- Python 3.10+
- Optional: [Ollama](https://ollama.com/) for local LLM mode.

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Prepare config
```bash
copy config.example.json config.json
```

### 4) (Optional) Pull local model
```bash
ollama pull gemma2:2b
```

---

## ▶️ Usage

```bash
python -m app.main
```

Quick start flow:
1. Right-click duck → **Голос → Выбрать Vosk-модель…**
2. Say **«кряква»** or press **Ctrl+Shift+K**
3. Give command (e.g. “открой проводник”, “сделай скриншот”)

---

## 🧪 Development

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest flake8
```

### Checks
```bash
pytest -q
flake8 app tests --max-line-length=120
```

### Build .exe
```bash
python build_exe.py
```

`build_exe.py` runs PyInstaller and produces `dist/kryakva.exe`.

---

## 🖼️ Screenshots

> You can place screenshots in `docs/screenshots/`.

Example:

```md
![Duck widget](docs/screenshots/widget.png)
![Context menu](docs/screenshots/menu.png)
![Messages window](docs/screenshots/messages.png)
```

---

## 🤝 Contributing

PRs are welcome.

1. Fork the repo
2. Create a branch
3. Add tests for behavior changes
4. Run checks locally
5. Open a PR with clear motivation and test notes

Also see:
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## 📄 License

Kryakva Non-Commercial Open License (KNCOL) v1.0.

The code is open for study, modification, and redistribution in non-commercial scenarios.
See [LICENSE](LICENSE).
