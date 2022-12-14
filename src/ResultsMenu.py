from PyQt6.QtWidgets import QDialogButtonBox, QDialog
from PyQt6.QtCore import QSize
from PyQt6 import uic
from pathlib import Path
from Singleton import Singleton

class ResultsMenu(QDialog):
    def __init__(self, perfectScore, score, answeredCount, skipCount, unanswered, tolerance, maxUnknowns):
        SIG_FIGS = None
        super(QDialog, self).__init__()
        uic.loadUi(Singleton.ui / "results.ui", self)

        if perfectScore == 0:
            return

        percentage = round((score/perfectScore) * 100, SIG_FIGS)

        self.matchBar.setValue(percentage)
        offset = 40
        self.friendZone.setMinimumSize(QSize(round(self.width() * tolerance) - offset, 0))

        mainText = f'Of the {answeredCount} questions answered, {skipCount} skipped, and {unanswered} unanswered, ' \
                   f'they got a score of {score} out of a maximum possible score of {perfectScore}. ' \
                   f'That\'s {percentage}%.\n' \
                   f'Given your tolerance of {round(tolerance * 100, SIG_FIGS)}%, you should{" not" if tolerance > score/perfectScore else ""} ' \
                   f'enter a relationship with them.'

        if maxUnknowns < unanswered:
            mainText = f'Of the {answeredCount + skipCount + unanswered} questions, you left {unanswered} unanswered.' \
                       f"That's more than your limit of {maxUnknowns}. You should probably get to know them a bit more first."

        self.resultsLabel.setText(mainText)
