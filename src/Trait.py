from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt
from Singleton import *
from typing import Union

# Depricated, if evalState it's skipped, if prefState it's setHidden
# NOT_APPLICABLE = -2
NOT_ANSWERED   = 0
ANSWERED       = 1
SKIPPED        = 2

# Dealbreaker types
# These are specifically picked so they can be multiplied by
# Singleton.dealbreakerBonus and added to prefValue
MUST = 1
MUST_NOT = -1
NOT = 0

class Trait(QListWidgetItem):
    """ A specific attribute. Holds both pref and eval values and states.
        The properties state and value both fetch the current mode from Singleton
        and return the appropriate state. Value also incorperates dealbreaker, and
        will return appropriately adjusted values if it's a dealbreaker or not """
    # If this is false, it just strikes them out instead -- though it hasn't been tested
    HIDE_UNANSWERED_PREF_QUESTIONS = True

    def __init__(self, trait, pref=0, eval=0, evalState=NOT_ANSWERED, prefState=NOT_ANSWERED, dealbreaker=NOT, parent=None):
        super().__init__(trait, parent=parent)
        self.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemNeverHasChildren | Qt.ItemFlag.ItemIsEnabled)
        self.setText(trait)
        self.pref = pref
        self.eval = eval
        self.prefState = prefState
        self.evalState = evalState
        self.dealbreakerState = dealbreaker
        self.update()

    def checkDealbreaker(self, tolerance):
        """ Tolerance is between 0 and 100, NOT 0 and 1
            returns True if it passes """
        if self.dealbreakerState == MUST:
            #* Whether this is > or >= is actually kinda important
            return self.eval >= tolerance
        elif self.dealbreakerState == MUST_NOT:
            return self.eval <= tolerance
        else:
            return True

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
            self.setCheckState(Qt.CheckState.PartiallyChecked)
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
        if Singleton.mode == PREF:
            return self.prefState
        else:
            return self.evalState
    @state.setter
    def state(self, to):
        if Singleton.mode == PREF:
            self.prefState = to
        else:
            self.evalState = to
        self.update()

    @property
    def value(self):
        # Dealbreaker state enum values are picked specifically so you can do this
        if Singleton.mode == PREF:
            return (self.pref + (Singleton.DEALBREAKER_BONUS * self.dealbreakerState))
        else:
            return self.eval
    @value.setter
    def value(self, to):
        if Singleton.mode == PREF:
            if to > Singleton.MAX_VALUE:
                self.dealbreakerState = MUST
            elif to < -Singleton.MAX_VALUE:
                self.dealbreakerState = MUST_NOT
            else:
                self.dealbreakerState = NOT

            self.pref = to
        else:
            self.eval = to

    @property
    def trait(self):
       return self.text()
    @trait.setter
    def trait(self, to):
       self.setText(to)

    @staticmethod
    def deserialize(json, mode=None):
        if mode is None:
            mode = Singleton.mode
        if mode == PREF:
            if json[1] > Singleton.MAX_VALUE:
                dealbreakerState = MUST
            elif json[1] < -Singleton.MAX_VALUE:
                dealbreakerState = MUST_NOT
            else:
                dealbreakerState = NOT

            return Trait(trait=json[0], pref=json[1], prefState=json[2], dealbreaker=dealbreakerState)
        else:
            return Trait(trait=json[0], eval=json[1], evalState=json[2])

    def serialize(self, mode=None):
        if mode is None:
            mode = Singleton.mode
        return [self.trait, self.value, self.prefState if mode == PREF else self.evalState]
