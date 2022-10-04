from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QListWidget, QListView, QMessageBox, QAbstractButton
from PyQt6.QtCore import QEvent, QFile, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QWidget, QDialogButtonBox, QSlider
# from PyQt6 import
from Cope import debug, todo, depricated

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
    resetQuestion = pyqtSignal()

    def __init__(self, catagory, traits=[], parent=None):
        super().__init__(parent)
        # Connect all the signals
        self.bindSignals()

        # So it handles clicking on an item slightly differently
        self.itemClicked.connect(self.onTraitClicked)
        # Set the icon sizes
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        # If we're doing word wrap or not
        self.setWordWrap(self.WORD_WRAP)
        todo('Set the keys to be handled by the window instead')
        # Set the keys to be handled by the window instead
        # self.keyPressEvent = parent.keyPressEvent

        self._loadTraits(traits)

    def keyPressEvent(self, e):
        # Only do things for these keys, otherwise don't accept the input
        if e.text() in ('y', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'n', 's', 'b'):
            Singleton.mainWindow.keyPressEvent(e)
        # if e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
        #     super().keyPressEvent(e)
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

    # Used to change the current question
    def incrementQuestion(self, amt=1) -> int:
        """ Note: This is only meant to accept -1 or 1 for the amt """
        # i = self.index + amt
        # self.setCurrentIndex(self.currentIndex() + amt)
        # self.setCurrentItem(self.item(self.currentIndex() + amt))
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
        if self.currentItem().state != ANSWERED:
            self.currentItem().state = SKIPPED

        # If you go back to a question you've already answered and hit skip, then it resets the question
        if self.currentItem().state == ANSWERED:
            self.resetAnswer(state=SKIPPED)

        self.incrementQuestion()

    def onTraitClicked(self, _=False):
        """ Called when you jump to a new question by clicking on it """
        # self.switchTrait(self.currentRow(), self.currentIndex(), False)
        pass

    # Run when we want to "set" the current trait
    def acceptAnswer(self):
        if self.currentItem() is not None:# and self.currentItem().state != ANSWERED:
            self.currentItem().state = ANSWERED
            debug('question accepted')

        self.questionAccepted.emit()
        self.updateGUI.emit()

    def resetAnswer(self, state=NOT_ANSWERED):
        """ Resets the current trait to default values """
        if self.currentItem().state == ANSWERED:
            self.resetQuestion.emit()

        self.currentItem().value = 0

    def serialize(self):
        l = []
        for i in range(self.count()):
            l.append(self.item(i).serialize())
        return l

    def deserialize(self, obj):
        self.clear()
        for i in obj:
            self.addItem(Trait.deserialize(i))
