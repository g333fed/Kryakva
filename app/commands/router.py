from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Intent = Literal["cmd", "llm"]


@dataclass
class RouteResult:
    intent: Intent
    command: Optional[str] = None
    argument: Optional[str] = None


@dataclass(frozen=True)
class CommandPattern:
    keywords: tuple[str, ...]
    command: str
    mode: Literal["any", "all"] = "any"

    def matches(self, text: str) -> bool:
        if self.mode == "all":
            return all(keyword in text for keyword in self.keywords)
        return any(keyword in text for keyword in self.keywords)


COMMAND_PATTERNS: list[CommandPattern] = [
    CommandPattern(("проводник", "explorer"), "open_explorer"),
    CommandPattern(("загрузк",), "open_downloads"),
    CommandPattern(("документ",), "open_documents"),
    CommandPattern(("диспетчер задач",), "open_taskmgr"),
    CommandPattern(("настройк",), "open_settings"),
    CommandPattern(("безопасн", "защит"), "open_security"),
    CommandPattern(("панель управления",), "open_control_panel"),
    CommandPattern(("диспетчер устройств",), "open_device_manager"),
    CommandPattern(("служб",), "open_services"),
    CommandPattern(("блокнот",), "open_notepad"),
    CommandPattern(("калькулятор",), "open_calc"),
    CommandPattern(("cmd", "командн"), "open_cmd"),
    CommandPattern(("powershell", "пауэр"), "open_powershell"),
    CommandPattern(("выполнить", "run"), "open_run_dialog"),
    CommandPattern(("буфер обмена", "clipboard"), "open_clipboard_history"),
    CommandPattern(("скриншот", "screenshot"), "take_screenshot"),
    CommandPattern(("громче",), "volume_up"),
    CommandPattern(("тише",), "volume_down"),
    CommandPattern(("без звука", "mute"), "volume_mute"),
    CommandPattern(("заблок", "lock"), "lock_pc"),
    CommandPattern(("спящий", "усни", "sleep"), "sleep_pc"),
]


class CommandRouter:
    def route(self, text: str) -> RouteResult:
        normalized = (text or "").lower().strip()
        if not normalized:
            return RouteResult("llm", argument="")

        if normalized.startswith("кряква"):
            normalized = normalized.replace("кряква", "", 1).strip(" ,.!")

        desktop_patterns = [
            CommandPattern(("рабоч", "стол"), "show_desktop", mode="all"),
            CommandPattern(("закрой", "все", "окна"), "show_desktop", mode="all"),
        ]
        if any(pattern.matches(normalized) for pattern in desktop_patterns):
            return RouteResult("cmd", "show_desktop")

        window_patterns = [
            (CommandPattern(("закрой", "окно"), "close_active_window", mode="all")),
            (CommandPattern(("сверни", "окно"), "minimize_window", mode="all")),
            (CommandPattern(("разверни", "окно"), "maximize_window", mode="all")),
            (CommandPattern(("прижм", "влево"), "snap_left", mode="all")),
            (CommandPattern(("прижм", "вправо"), "snap_right", mode="all")),
        ]
        for pattern in window_patterns:
            if pattern.matches(normalized):
                return RouteResult("cmd", pattern.command)

        if ("очист" in normalized or "пуст" in normalized) and "корзин" in normalized:
            return RouteResult("cmd", "empty_recycle_bin")
        if ("открой" in normalized or "покажи" in normalized) and "корзин" in normalized:
            return RouteResult("cmd", "open_recycle_bin")

        for pattern in COMMAND_PATTERNS:
            if pattern.matches(normalized):
                return RouteResult("cmd", pattern.command)

        if normalized.startswith("поищи "):
            return RouteResult("cmd", "web_search", normalized.replace("поищи", "", 1).strip())

        if normalized.startswith("открой "):
            argument = normalized.replace("открой", "", 1).strip()
            if argument and not argument.startswith("http"):
                argument = f"https://{argument}"
            return RouteResult("cmd", "open_url", argument)

        return RouteResult("llm", argument=text)
