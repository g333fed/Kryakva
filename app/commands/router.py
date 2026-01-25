from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

Intent = Literal["cmd","llm"]

@dataclass
class RouteResult:
    intent: Intent
    command: Optional[str] = None
    argument: Optional[str] = None

class CommandRouter:
    def route(self, text: str) -> RouteResult:
        t = (text or "").lower().strip()
        if not t:
            return RouteResult("llm", argument="")

        # allow phrase like: "кряква, ..."
        if t.startswith("кряква"):
            t = t.replace("кряква", "", 1).strip(" ,.!")

        # desktop / window mgmt
        if ("прибери" in t or "убери" in t) and ("рабоч" in t and "стол" in t):
            return RouteResult("cmd","show_desktop")
        if ("показ" in t or "открой" in t) and ("рабоч" in t and "стол" in t):
            return RouteResult("cmd","show_desktop")
        if ("закрой" in t and "все" in t and "окна" in t):
            return RouteResult("cmd","show_desktop")
        if ("закрой" in t and "окно" in t) or t == "закрой окно":
            return RouteResult("cmd","close_active_window")
        if ("сверни" in t and "окно" in t):
            return RouteResult("cmd","minimize_window")
        if ("разверни" in t and "окно" in t):
            return RouteResult("cmd","maximize_window")
        if ("прижм" in t or "прикреп" in t) and ("влево" in t or "слева" in t):
            return RouteResult("cmd","snap_left")
        if ("прижм" in t or "прикреп" in t) and ("вправо" in t or "справа" in t):
            return RouteResult("cmd","snap_right")

        # open apps
        if "проводник" in t or "explorer" in t:
            return RouteResult("cmd","open_explorer")
        if "загрузк" in t:
            return RouteResult("cmd","open_downloads")
        if "документ" in t:
            return RouteResult("cmd","open_documents")
        if "диспетчер задач" in t or ("диспетчер" in t and "задач" in t):
            return RouteResult("cmd","open_taskmgr")
        if "настройк" in t:
            return RouteResult("cmd","open_settings")
        if "безопасн" in t or "защит" in t:
            return RouteResult("cmd","open_security")
        if "панель управления" in t:
            return RouteResult("cmd","open_control_panel")
        if "диспетчер устройств" in t:
            return RouteResult("cmd","open_device_manager")
        if "служб" in t:
            return RouteResult("cmd","open_services")
        if "блокнот" in t:
            return RouteResult("cmd","open_notepad")
        if "калькулятор" in t:
            return RouteResult("cmd","open_calc")
        if t == "cmd" or "командн" in t:
            return RouteResult("cmd","open_cmd")
        if "powershell" in t or "пауэр" in t:
            return RouteResult("cmd","open_powershell")

        # system quick
        if ("очист" in t or "пуст" in t) and "корзин" in t:
            return RouteResult("cmd","empty_recycle_bin")
        if ("открой" in t or "покажи" in t) and "корзин" in t:
            return RouteResult("cmd","open_recycle_bin")
        if "заблок" in t or "lock" in t:
            return RouteResult("cmd","lock_pc")
        if "спящий" in t or "усни" in t or "sleep" in t:
            return RouteResult("cmd","sleep_pc")

        # sound
        if "громче" in t:
            return RouteResult("cmd","volume_up")
        if "тише" in t:
            return RouteResult("cmd","volume_down")
        if "без звука" in t or "mute" in t:
            return RouteResult("cmd","volume_mute")

        # web
        if t.startswith("поищи "):
            return RouteResult("cmd","web_search", t.replace("поищи","",1).strip())
        if t.startswith("открой "):
            arg = t.replace("открой","",1).strip()
            if arg and not arg.startswith("http"):
                arg = "https://" + arg
            return RouteResult("cmd","open_url", arg)

        return RouteResult("llm", argument=text)
