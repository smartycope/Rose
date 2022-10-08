from pathlib import Path
from PyQt6.QtCore import QStandardPaths

EVAL = 0
PREF = 1

class _Singleton():
    debugging = __debug__ and False
    testing   = debugging and True

    dir = Path(__file__).resolve().parent.parent
    ui = dir / "ui"
    src = dir / "src"
    assets = dir / 'assets/'
    saves = Path(QStandardPaths.standardLocations(QStandardPaths.StandardLocation.DocumentsLocation)[0]).resolve() / 'Rose Saves'

    DEFAULT_SAVES_PATH = saves
    DEFAULT_PREFERENCES_FILE = dir / 'boilerplate.pref'
    COPIED_PREFERENCES_FILE = saves / 'defaults.pref'
    PARTLY_VALUE = 0.6
    ROUND_TO = 1
    startingMode = PREF

    mode = startingMode

    # Yes, this is kinda hacky
    mainWindow = None

    MAX_VALUE = 100

    DEALBREAKER_BONUS = 1

Singleton = _Singleton()
