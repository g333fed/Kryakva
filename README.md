# Kryakva 🦆

Kryakva is a Windows desktop pet assistant written in Python. It places a duck widget on your desktop, listens for voice commands, executes Windows automation actions, and can optionally use a local LLM through Ollama.

## Features

- Desktop duck widget (always-on-top, draggable, scalable PNG skin).
- Voice interaction with Vosk:
  - activation hotword (`кряква`)
  - push-to-talk mode (`Ctrl+Shift+K`)
  - microphone selection from UI
- Windows automation commands:
  - Explorer, Settings, Security, Task Manager, CMD/PowerShell, etc.
  - window management (close/minimize/maximize/snap)
  - system actions (lock, sleep, recycle bin, volume controls)
- Optional local LLM mode via Ollama (Gemma and compatible models).
- Message log window and in-widget toast notifications.
- Configurable behavior through `config.json` with schema validation and defaults.

## Architecture Overview

```text
app/
  main.py                # app entrypoint
  config.py              # config schema + load/save/validation
  logging_config.py      # central logging setup
  commands/
    router.py            # phrase -> intent routing via patterns
    registry.py          # command registry (dynamic dispatch)
    windows.py           # Windows automation implementation
  voice/
    vosk_engine.py       # Vosk PTT + hotword listener
  llm/
    ollama.py            # Ollama API client
    tools.py             # tool-call parsing + risk classification
  ui/
    duck_pet.py          # thin application coordinator
    widget.py            # duck widget view + drag + toast
    menu.py              # right-click menu builder
    messages.py          # messages window
    voice_ui.py          # UI-level voice orchestration
```

## Installation

### 1) Prerequisites

- Windows 10/11 (Windows 7+ may work with limited behavior).
- Python 3.10+
- Optional for LLM mode: [Ollama](https://ollama.com/)

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure app

Copy example config and adjust:

```bash
copy config.example.json config.json
```

### 4) (Optional) Setup Ollama model

```bash
ollama pull gemma2:2b
```

## Usage

```bash
python -m app.main
```

- Right-click the duck to open the control menu.
- Choose **Голос → Выбрать Vosk-модель…** and point to a downloaded Vosk model directory.
- Speak the hotword **кряква** or use **Ctrl+Shift+K** for push-to-talk.

## Screenshots

> Add screenshots here (widget, context menu, and messages window).

Example markdown:

```md
![Duck widget](docs/screenshots/widget.png)
![Context menu](docs/screenshots/menu.png)
```

## Development

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest flake8
```

### Run checks

```bash
flake8 app tests --max-line-length=120
pytest -q
```

### Build Windows executable

```bash
python build_exe.py
```

Output executable: `dist/kryakva.exe`.

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Add/adjust tests when behavior changes.
4. Run lint + tests locally.
5. Open a pull request with clear description and rationale.

Please also review:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

MIT. See [LICENSE](LICENSE).
