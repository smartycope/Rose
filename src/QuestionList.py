from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QListWidget, QListView, QMessageBox, QAbstractButton
from PyQt6.QtCore import QEvent, QFile, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QWidget, QDialogButtonBox, QSlider

from Trait import *
from ResultsMenu import ResultsMenu

from Singleton import *


class QuestionList(QListWidget):
    ICON_SIZE = 10
    WORD_WRAP = True

    updateGUI = pyqtSignal()
    reachedEnd = pyqtSignal()
    reachedBegin = pyqtSignal()
    questionAccepted = pyqtSignal()
    skipQuestion = pyqtSignal()

    def __init__(self, traits=[], parent=None):
        super().__init__(parent)
        # Connect all the signals
        self.bindSignals()

        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setWordWrap(self.WORD_WRAP)
        self.setAlternatingRowColors(True)

        self._loadTraits(traits)

    def keyPressEvent(self, e):
        # Only do things for these keys, otherwise don't accept the input
        if e.text() in ('y', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'n', 's', 'b'):
            Singleton.mainWindow.keyPressEvent(e)
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.next()
        else:
            super().keyPressEvent(e)

    def bindSignals(self):
        # So you can use arrow keys
        self.itemSelectionChanged.connect(self.updateGUI.emit)

    def _loadTraits(self, traits):
        for trait in traits:
            self.addItem(Trait.deserialize(trait))

    def back(self):
        self.incrementQuestion(-1)

    def next(self):
        self.acceptAnswer()
        self.incrementQuestion()

    def addModeData(self, mode, data):
        # This is SO innefficent
        for jsn in data:
            for i in range(self.count()):
                if self.item(i).trait == data[0]:
                    if mode == PREF:
                        self.item(i).pref = data[1]
                        self.item(i).prefState = data[2]
                    else:
                        self.item(i).eval = data[1]
                        self.item(i).evalState = data[2]

    def incrementQuestion(self, amt=1) -> int:
        """ Used to change the current question
            Note: This is only meant to accept -1 or 1 for the amt """

        i = self.currentRow() + amt
        self.setCurrentRow(i)
        while (item := self.currentItem()) is not None and item.isHidden():
            i = self.currentRow() + amt
            self.setCurrentRow(i)

        #* Handle looping the tabs when we're at the end or beginning
        # If we're at the top and we hit back, go to the previous tab, if there is one
        if i < 0:
            self.reachedBegin.emit()
            return 0
        # If we're at the bottom and we hit next or skip, go to the next tab, if there is one
        elif i >= self.count():
            self.reachedEnd.emit()
            return self.count() - 1

        return i

    def skip(self):
        if (item := self.currentItem()) is not None:
            self.skipQuestion.emit()
            item.state = SKIPPED

        self.incrementQuestion()

    def acceptAnswer(self):
        """ Run when we want to "set" the current trait """
        if self.currentItem() is not None:
            self.currentItem().state = ANSWERED
            # debug('question accepted', active=Singleton.debugging)

        self.questionAccepted.emit()
        self.updateGUI.emit()

    def resetAnswer(self, state=NOT_ANSWERED):
        """ Resets the current trait to default values """
        self.currentItem().value = 0 if Singleton.mode == PREF else int(Singleton.MAX_VALUE / 2)

    def serialize(self):
        l = []
        for i in range(self.count()):
            l.append(self.item(i).serialize())
        return l

    def deserialize(self, obj):
        self.clear()
        for i in obj:
            self.addItem(Trait.deserialize(i))
