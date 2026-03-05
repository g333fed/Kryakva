from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]

LOW_RISK = {
    "show_desktop","open_explorer","open_downloads","open_documents","open_taskmgr",
    "open_settings","open_security","open_notepad","open_calc","open_cmd","open_powershell",
    "open_control_panel","open_device_manager","open_services","open_recycle_bin",
    "open_run_dialog","open_clipboard_history","take_screenshot",
    "volume_up","volume_down","volume_mute","snap_left","snap_right",
    "minimize_window","maximize_window","web_search","open_url"
}
MED_RISK = {"empty_recycle_bin","close_active_window","lock_pc","sleep_pc"}

def parse_tool_call(text: str) -> Optional[ToolCall]:
    if not text:
        return None
    s = text.strip()
    # prefer full JSON answer
    if s.startswith("{") and s.endswith("}"):
        try:
            obj = json.loads(s)
            tool = obj.get("tool") or obj.get("action")
            args = obj.get("args") or {}
            if isinstance(tool, str) and isinstance(args, dict):
                return ToolCall(tool, args)
        except Exception:
            return None
    # fallback: search JSON chunk
    a = s.find("{")
    b = s.rfind("}")
    if a != -1 and b != -1 and b > a:
        try:
            obj = json.loads(s[a:b+1])
            tool = obj.get("tool") or obj.get("action")
            args = obj.get("args") or {}
            if isinstance(tool, str) and isinstance(args, dict):
                return ToolCall(tool, args)
        except Exception:
            return None
    return None

def risk_level(tool: str) -> str:
    if tool in LOW_RISK: return "low"
    if tool in MED_RISK: return "med"
    return "unknown"

def tool_schema_text() -> str:
    tools = sorted(list(LOW_RISK | MED_RISK))
    return (
        "Ты — Кряква, локальный ассистент Windows.\n"
        "Ты МОЖЕШЬ выполнять действия через инструменты.\n"
        "ВАЖНО: возвращай JSON ТОЛЬКО если нужно действие.\n"
        "Иначе отвечай обычным текстом.\n\n"
        "Формат:\n"
        "{\"tool\":\"<name>\",\"args\":{...}}\n\n"
        "Доступные инструменты:\n- "
        + "\n- ".join(tools)
        + "\n\n"
        "Примеры:\n"
        "Пользователь: прибери рабочий стол\n"
        "{\"tool\":\"show_desktop\",\"args\":{}}\n"
    )

