from __future__ import annotations

import logging
import sys
from tkinter import messagebox

from app.logging_config import setup_logging
from app.source_guard import SourceGuardError, ensure_github_source
from app.ui.duck_pet import DuckDesktopWidget


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        ensure_github_source()
    except SourceGuardError as error:
        logger.error("%s", error)
        try:
            messagebox.showerror("Kryakva Source Guard", str(error))
        except Exception:
            pass
        sys.exit(1)

    DuckDesktopWidget().run()
