from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import Qt
from Cope import debug, todo

EVAL = 0
PREF = 1

NOT_APPLICABLE = -2
NOT_ANSWERED   = 0
ANSWERED       = 1
SKIPPED        = 2

class Trait:
    # If this is false, it just strikes them out instead
    todo("This option doesn't actually work")
    HIDE_SKIPPED_PREF_QUESTIONS = False
    def __init__(self, trait, value=0, state=NOT_ANSWERED):
        self.trait = trait
        self.state = state
        self.value = value

    def asListItem(self, mode):
        item = QListWidgetItem(self.trait)
        # item.setTristate(True)
        self.updateListItem(item, mode)
        return item

    def updateListItem(self, item, mode):
        if (self.value != 0):
            assert self.state == ANSWERED, "Somewhere you're updating a Trait weight or modifier without setting the state"
        # if mode == EVAL:
            # item.setTristate(True)
        if self.state == ANSWERED:
            item.setCheckState(Qt.CheckState.Checked)
        elif self.state == SKIPPED and mode == EVAL:
            item.setCheckState(Qt.CheckState.PartiallyChecked)

        # If we're setting preferences and they skip a question, we're discounting it
        elif self.state == SKIPPED and mode == PREF:
            item.setCheckState(Qt.CheckState.Unchecked)
            font = item.font()
            font.setStrikeOut(True)
            item.setFont(font)
            if self.HIDE_SKIPPED_PREF_QUESTIONS:
                item.setHidden(True)
        else:
            pass
            # item.setCheckState(Qt.CheckState.Unchecked)

    def __str__(self):
        if self.state == NOT_APPLICABLE:
            state = 'not_applicable'
        elif self.state == NOT_ANSWERED:
            state = 'not_answered'
        elif self.state == ANSWERED:
            state = 'answered'
        elif self.state == SKIPPED:
            state = 'skipped'
        return f'Trait["{self.trait}": {self.value}, {state}]'

#* JSON Methods
    @staticmethod
    def fromJSON(json):
        return Trait(*json)

    def toJSON(self):
        return [self.trait, self.value, self.state]
