from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
CONFIG_PATH = ROOT_DIR / "config.json"
EXAMPLE_PATH = ROOT_DIR / "config.example.json"


@dataclass
class LLMConfig:
    enabled: bool = False
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = "gemma2:2b"
    temperature: float = 0.4
    max_tokens: int = 512
    allow_tools: bool = True


@dataclass
class VoiceConfig:
    vosk_model_path: str = ""
    input_device: Optional[int] = None
    ptt_seconds: float = 4.0
    hotword_enabled: bool = True
    hotword: str = "кряква"
    hotword_command_seconds: float = 5.0
    samplerate: int = 16000


@dataclass
class UIConfig:
    always_on_top: bool = True
    start_x: int = 40
    start_y: int = 60
    scale: float = 1.0
    show_bubbles: bool = True
    listen_indicator: bool = True
    beeps: bool = True
    auto_degreen: bool = True


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    ui: UIConfig = field(default_factory=UIConfig)


def _coerce_dataclass(model: type[Any], raw: Dict[str, Any]) -> Any:
    valid_fields = {f.name: f for f in fields(model)}
    out: Dict[str, Any] = {}
    for name, field in valid_fields.items():
        value = raw.get(name, getattr(model(), name))
        expected = field.type
        if expected is bool:
            out[name] = bool(value)
        elif expected is int:
            out[name] = int(value)
        elif expected is float:
            out[name] = float(value)
        elif expected is str:
            out[name] = str(value)
        else:
            out[name] = value
    return model(**out)


def validate_config(raw_cfg: Dict[str, Any]) -> AppConfig:
    """Validate user config and fill missing fields with defaults."""
    return AppConfig(
        llm=_coerce_dataclass(LLMConfig, raw_cfg.get("llm", {})),
        voice=_coerce_dataclass(VoiceConfig, raw_cfg.get("voice", {})),
        ui=_coerce_dataclass(UIConfig, raw_cfg.get("ui", {})),
    )


def load_config() -> Dict[str, Any]:
    """Load config from config.json (or example), validate, return dict."""
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    raw: Dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    validated = validate_config(raw)
    return asdict(validated)


def save_config(cfg: Dict[str, Any]) -> None:
    validated = validate_config(cfg)
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(asdict(validated), file, ensure_ascii=False, indent=2)
