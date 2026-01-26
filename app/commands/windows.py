
import os, subprocess, webbrowser, urllib.parse, ctypes, socket, datetime, sys

def _windows_version():
    try:
        v = sys.getwindowsversion()
        return v.major, v.minor, v.build
    except Exception:
        return 0, 0, 0

def _is_win10_or_newer() -> bool:
    major, _, _ = _windows_version()
    return major >= 10

def _start_uri(uri: str) -> bool:
    try:
        result = subprocess.run(["cmd", "/c", "start", "", uri], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def _open_control_panel():
    try:
        subprocess.Popen(["control"])
    except Exception:
        pass

def _open_clipboard_viewer():
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    clipbrd = os.path.join(system_root, "System32", "clipbrd.exe")
    if os.path.exists(clipbrd):
        try:
            subprocess.Popen([clipbrd])
        except Exception:
            pass

def _empty_recycle_bin_shell(force: bool = True):
    try:
        flags = 0x00000001  # SHERB_NOCONFIRMATION
        if force:
            flags |= 0x00000002  # SHERB_NOPROGRESSUI
            flags |= 0x00000004  # SHERB_NOSOUND
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
    except Exception:
        pass

def _run_ps(ps: str):
    try:
        subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",ps], capture_output=True)
    except Exception:
        pass

def _press_vk(vk: int):
    try:
        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass

def _combo(vks):
    try:
        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002
        for vk in vks:
            user32.keybd_event(vk, 0, 0, 0)
        for vk in reversed(vks):
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass

def show_desktop(): _combo([0x5B, 0x44])              # Win + D
def run_dialog(): _combo([0x5B, 0x52])                # Win + R
def clipboard_history():
    if _is_win10_or_newer():
        _combo([0x5B, 0x56])         # Win + V
    else:
        _open_clipboard_viewer()
def close_active_window(): _combo([0x12, 0x73])       # Alt + F4
def minimize_window(): _combo([0x5B, 0x28])           # Win + Down
def maximize_window(): _combo([0x5B, 0x26])           # Win + Up
def snap_left(): _combo([0x5B, 0x25])                 # Win + Left
def snap_right(): _combo([0x5B, 0x27])                # Win + Right

def open_explorer():
    try: os.startfile("explorer")
    except Exception: pass

def open_downloads():
    try: os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))
    except Exception: pass

def open_documents():
    try: os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))
    except Exception: pass

def open_taskmgr():
    try: subprocess.Popen(["taskmgr"])
    except Exception: pass

def open_settings():
    if _is_win10_or_newer() and _start_uri("ms-settings:"):
        return
    _open_control_panel()

def open_security():
    if _is_win10_or_newer() and _start_uri("windowsdefender:"):
        return
    try:
        subprocess.Popen(["control", "/name", "Microsoft.WindowsDefender"])
        return
    except Exception:
        pass
    _open_control_panel()

def open_notepad():
    try: subprocess.Popen(["notepad"])
    except Exception: pass

def open_calc():
    try: subprocess.Popen(["calc"])
    except Exception: pass

def open_cmd():
    try: subprocess.Popen(["cmd"])
    except Exception: pass

def open_powershell():
    try: subprocess.Popen(["powershell","-NoProfile"])
    except Exception: pass

def open_control_panel():
    _open_control_panel()

def open_device_manager():
    try: subprocess.Popen(["devmgmt.msc"])
    except Exception: pass

def open_services():
    try: subprocess.Popen(["services.msc"])
    except Exception: pass

def open_recycle_bin():
    try: subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
    except Exception: pass

def empty_recycle_bin(force: bool = True):
    if _is_win10_or_newer():
        _run_ps("Clear-RecycleBin -Force" if force else "Clear-RecycleBin")
    else:
        _empty_recycle_bin_shell(force)

def lock_pc():
    try: ctypes.windll.user32.LockWorkStation()
    except Exception: pass

def sleep_pc():
    _run_ps("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def volume_up(steps: int = 5):
    for _ in range(max(1,int(steps))): _press_vk(0xAF)

def volume_down(steps: int = 5):
    for _ in range(max(1,int(steps))): _press_vk(0xAE)

def volume_mute(): _press_vk(0xAD)

def open_url(url: str):
    try: webbrowser.open(url)
    except Exception: pass

def web_search(query: str):
    open_url("https://duckduckgo.com/?q=" + urllib.parse.quote_plus(query))

def check_internet(host="8.8.8.8", port=53, timeout=1.5) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def screenshot_to_desktop(prefix: str = "kryakva_shot") -> str:
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(desktop, f"{prefix}_{ts}.png")
        img.save(path)
        return path
    except Exception:
        return ""
