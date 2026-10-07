"""Launch the read-only AIDA desktop shell with python -B -m src.ui."""

import sys


def main() -> int:
    try:
        import tkinter as tk
    except ImportError as error:
        print(f"AIDA UI requires Python with Tkinter/Tcl/Tk. Use a Python installation with Tcl/Tk support: {error}", file=sys.stderr)
        return 2
    from src.config import load_config
    try:
        config = load_config()
    except (OSError, ValueError) as error:
        print(f"AIDA UI configuration error: {error}", file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"AIDA UI cannot initialize Tcl/Tk. Check the Python Tcl/Tk installation and desktop session: {error}", file=sys.stderr)
        return 2
    from .app import Application
    from .service import RepositoryService
    try:
        Application(root, RepositoryService(config), config.developer_workspace)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
