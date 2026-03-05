from __future__ import annotations

from app.logging_config import setup_logging
from app.ui.duck_pet import DuckDesktopWidget


if __name__ == "__main__":
    setup_logging()
    DuckDesktopWidget().run()
