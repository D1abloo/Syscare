from __future__ import annotations

import sys

from . import __app_name__, __version__


HELP = f"""{__app_name__} {__version__}

Uso:
  syscare              Abre la interfaz grafica
  syscare --help       Muestra esta ayuda
  syscare --version    Muestra la version
"""


def main() -> None:
    if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
        print(HELP)
        return
    if any(arg == "--version" for arg in sys.argv[1:]):
        print(__version__)
        return
    from .app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
