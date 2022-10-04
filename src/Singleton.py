from pathlib import Path
from Cope import todo

EVAL = 0
PREF = 1

class _Singleton():
    debugging = __debug__ and True
    testing   = debugging and True

    dir = Path(__file__).resolve().parent.parent
    ui = dir / "ui"
    src = dir / "src"
    saves = dir / "saves"
    assets = dir / 'assets/'

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

Singleton = _Singleton()



# -- Note: consider changing the scoring in the program to be added logirithmically, so the closer it comes to 100 the more it's actually worth, but still judged the same way.
# -- Also, maybe if they negatively fulfill the value half the negative

todo('consider a switch to a "strongly agree", "agree", "slightly agree", etc. system instead of a slider')
todo('fix tab and shift+tab')
