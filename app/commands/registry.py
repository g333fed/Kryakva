from __future__ import annotations

from typing import Callable, Optional

from app.commands import windows as win

CommandHandler = Callable[[Optional[str]], None]


COMMANDS: dict[str, CommandHandler] = {
    "show_desktop": lambda _arg: win.show_desktop(),
    "open_explorer": lambda _arg: win.open_explorer(),
    "open_downloads": lambda _arg: win.open_downloads(),
    "open_documents": lambda _arg: win.open_documents(),
    "open_taskmgr": lambda _arg: win.open_taskmgr(),
    "open_settings": lambda _arg: win.open_settings(),
    "open_security": lambda _arg: win.open_security(),
    "open_notepad": lambda _arg: win.open_notepad(),
    "open_calc": lambda _arg: win.open_calc(),
    "open_cmd": lambda _arg: win.open_cmd(),
    "open_powershell": lambda _arg: win.open_powershell(),
    "open_control_panel": lambda _arg: win.open_control_panel(),
    "open_device_manager": lambda _arg: win.open_device_manager(),
    "open_services": lambda _arg: win.open_services(),
    "open_recycle_bin": lambda _arg: win.open_recycle_bin(),
    "empty_recycle_bin": lambda _arg: win.empty_recycle_bin(True),
    "lock_pc": lambda _arg: win.lock_pc(),
    "sleep_pc": lambda _arg: win.sleep_pc(),
    "volume_up": lambda _arg: win.volume_up(5),
    "volume_down": lambda _arg: win.volume_down(5),
    "volume_mute": lambda _arg: win.volume_mute(),
    "close_active_window": lambda _arg: win.close_active_window(),
    "minimize_window": lambda _arg: win.minimize_window(),
    "maximize_window": lambda _arg: win.maximize_window(),
    "snap_left": lambda _arg: win.snap_left(),
    "snap_right": lambda _arg: win.snap_right(),
    "open_url": lambda arg: win.open_url(arg) if arg else None,
    "web_search": lambda arg: win.web_search(arg) if arg else None,
}


def execute_command(command: str, argument: Optional[str] = None) -> bool:
    handler = COMMANDS.get(command)
    if handler is None:
        return False
    handler(argument)
    return True
