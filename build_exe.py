from __future__ import annotations

import subprocess
import sys


def build() -> None:
    """Build `dist/kryakva.exe` with PyInstaller."""
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "kryakva",
        "app/main.py",
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    build()
