from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt
from Cope import debug, todo
from Singleton import *
from typing import Union

# Depricated, if evalState it's skipped, if prefState it's setHidde
# NOT_APPLICABLE = -2
NOT_ANSWERED   = 0
ANSWERED       = 1
SKIPPED        = 2

todo('sort lists by state')

class Trait(QListWidgetItem):
    # If this is false, it just strikes them out instead
    HIDE_UNANSWERED_PREF_QUESTIONS = True


    def __init__(self, trait, pref=0, eval=0, evalState=NOT_ANSWERED, prefState=NOT_ANSWERED, parent=None):
        super().__init__(trait, parent=parent)
        self.trait = trait
        # self.state = state
        # self.value = value
        self.pref = pref
        self.eval = eval
        self.prefState = prefState
        self.evalState = evalState
        self.update()

    def update(self):
        def setStrikeout(to):
            font = self.font()
            font.setStrikeOut(to)
            self.setFont(font)

        if self.state == ANSWERED:
            self.setCheckState(Qt.CheckState.Checked)
            setStrikeout(False)
            self.setHidden(False)
        # This means it was deleted, but we might want it later
        elif Singleton.mode == PREF and self.prefState == SKIPPED:
            self.setCheckState(Qt.CheckState.Unchecked)
            setStrikeout(True)
            self.setHidden(False)
        # This means it was deleted
        elif (Singleton.mode == EVAL and self.prefState == SKIPPED) or \
             (Singleton.mode == EVAL and self.prefState == NOT_ANSWERED and self.HIDE_UNANSWERED_PREF_QUESTIONS):
            self.setCheckState(Qt.CheckState.Unchecked)
            setStrikeout(False)
            self.setHidden(True)
        # This means it was N/A'd
        elif Singleton.mode == EVAL and self.evalState == SKIPPED:
            self.setCheckState(Qt.CheckState.PartiallyChecked)
            setStrikeout(False)
            self.setHidden(False)
        elif self.state == NOT_ANSWERED:
            self.setCheckState(Qt.CheckState.Unchecked)
            setStrikeout(False)
            self.setHidden(False)

    def isDealbreaker(self):
        return self.pref > Singleton.MAX_VALUE or self.pref < -Singleton.MAX_VALUE

    def __str__(self):
        if self.state == NOT_APPLICABLE:
            state = 'not_applicable'
        elif self.state == NOT_ANSWERED:
            state = 'not_answered'
        elif self.state == ANSWERED:
            state = 'answered'
        elif self.state == SKIPPED:
            state = 'skipped'
        return f'Trait["{self.trait}": pref:{self.pref}, eval:{self.eval}, {state}]'

    @property
    def state(self):
        return self.prefState if Singleton.mode == PREF else self.evalState
    @state.setter
    def state(self, to):
        if Singleton.mode == PREF:
            self.prefState = to
        else:
            self.evalState = to
        self.update()

    @property
    def value(self):
       return self.pref if Singleton.mode == PREF else self.eval
    @value.setter
    def value(self, to):
        if Singleton.mode == PREF:
            self.pref = to
        else:
            self.eval = to

    @staticmethod
    def deserialize(json, mode=None):
        if mode is None:
            mode = Singleton.mode
        if mode == PREF:
            return Trait(trait=json[0], pref=json[1], prefState=json[2])
        else:
            return Trait(trait=json[0], eval=json[1], evalState=json[2])

    def serialize(self, mode=None):
        if mode is None:
            mode = Singleton.mode
        return [self.trait, self.pref if mode == PREF else self.eval, self.prefState if mode == PREF else self.evalState]
