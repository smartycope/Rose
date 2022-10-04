# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
from Cope import debug, todo, unreachableState

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QListWidget, QListView, QMessageBox, QAbstractButton
from PyQt6.QtCore import QEvent, QFile, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QWidget, QDialogButtonBox, QSlider

import jstyleson as jsonc
from os.path import dirname, join, basename
import shutil

from Trait import *
from ResultsMenu import ResultsMenu

from Singleton import *
from QuestionList import QuestionList
from FileManager import FileManager

# Ways to change the question:
# click "next"
# click "back"
# click "skip"
# click on a question
# arrow keys (eventually)


class MainWindow(QMainWindow):
    def __init__(self):
        # Load the UI
        super(MainWindow, self).__init__()
        uic.loadUi(Singleton.ui / "form.ui", self)

        Singleton.mainWindow = self

        # Set the tooltips of the labels to be the same as the boxes they're next to
        self.thresholdLabel.setToolTip(self.thresholdBox.toolTip())
        self.maxUnknownsLabel.setToolTip(self.maxUnknownsBox.toolTip())
        self.dealbreakerLimitLabel.setToolTip(self.dealbreakerLimitBox.toolTip())

        # Save the options tab widget so we can reinsert it after calling tabs.clear()
        self._optionsWidget = self.Options

        # Just assume we're starting on the Options page
        self.bindSignals()

        # self.index = 0
        self._questionsAnswered = 0
        self.blockDealbreakerMessage = False

        self.files = FileManager(Singleton.saves, self)

        # Set the correct mode
        self.switchMode(Singleton.startingMode, save=False)

        if Singleton.debugging:
            debug("This is only here for debugging", clr=3)
            self.load(mode=PREF, file='/home/leonard/hello/python/Rose/saves/boilerplate-copy.pref')
            # self.tabs.setCurrentIndex(1)

    def keyPressEvent(self, key):
        # debug('key pressed')
        max = 100
        min = 0 if Singleton.mode == EVAL else -100

        if key.text() == 'y':
            self.responseSlider.setValue(max)
        elif key.text() == '0':
            self.responseSlider.setValue(min)
        elif key.text() == '1':
            self.responseSlider.setValue(10 if Singleton.mode == EVAL else -80)
        elif key.text() == '2':
            self.responseSlider.setValue(20 if Singleton.mode == EVAL else -60)
        elif key.text() == '3':
            self.responseSlider.setValue(30 if Singleton.mode == EVAL else -40)
        elif key.text() == '4':
            self.responseSlider.setValue(40 if Singleton.mode == EVAL else -20)
        elif key.text() == '5':
            self.responseSlider.setValue(50 if Singleton.mode == EVAL else 0)
        elif key.text() == '6':
            self.responseSlider.setValue(60 if Singleton.mode == EVAL else 20)
        elif key.text() == '7':
            self.responseSlider.setValue(70 if Singleton.mode == EVAL else 40)
        elif key.text() == '8':
            self.responseSlider.setValue(80 if Singleton.mode == EVAL else 60)
        elif key.text() == '9':
            self.responseSlider.setValue(90 if Singleton.mode == EVAL else 80)
        elif key.text() == 'i' and Singleton.mode == PREF:
            self.responseSlider.setValue(max)
        elif key.text() == 'h' and Singleton.mode == PREF:
            self.responseSlider.setValue(min)
        elif key.text() == 'n':
            #* This is contested
            self.responseSlider.setValue(min)
            # self.nextButton.clicked.emit()
        elif key.text() == 's':
            self.skipButton.clicked.emit()
        elif key.text() == 'b':
            self.backButton.clicked.emit()
        # elif key.key() == Qt.Key.Key_Return:
            # if key.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # self.backButton.clicked.emit()
            # else:
                # self.nextButton.clicked.emit()
        # elif key.key() == Qt.Key.Key_Up:
            # self.backButton.clicked.emit()
        # elif key.key() == Qt.Key.Key_Down:
            # self.nextButton.clicked.emit()
        elif key.key() == Qt.Key.Key_Tab:
            debug('tab pressed!')
            if key.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.tabs.setCurrentIndex(self.tabs.currentIndex() - 1)
            else:
                self.tabs.setCurrentIndex(self.tabs.currentIndex() + 1)
        elif key.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if key.text() == 's':
                self.save()
            elif key.text() == 'o':
                self.load()
        else:
            super().keyPressEvent(key)

    def bindSignals(self):
        self.backButton.clicked.connect(self.back)
        self.nextButton.clicked.connect(self.next)
        self.skipButton.clicked.connect(self.skip)

        def seperateButtons(button):
            if button.text() == 'Save':
                self.save()
            elif button.text() == 'Open':
                self.load()
            elif button.text() == 'Restore Defaults':
                self.restoreDefaults()
            else:
                debug(button.text(), 'Button has this text somehow', throwError=True)
        self.fileButtonBox.clicked.connect(seperateButtons)

        self.calculateButton.clicked.connect(self.calculate)
        # self.questionBox.editingFinished.connect(self.addAttribute)
        self.questionBox.returnPressed.connect(self.addAttribute)

        self.evalModeButton.pressed.connect(self.switchMode)
        self.preferenceModeButton.pressed.connect(self.switchMode)

        self.evalFileButton.pressed.connect(lambda: self.load(mode=EVAL))
        self.prefFileButton.pressed.connect(lambda: self.load(mode=PREF))

        # self.dealbreakerBox.stateChanged.connect(self.warnDealbreaker)
        self.dealbreakerBox.toggled.connect(self.warnDealbreaker)

        self.groupSelector.textActivated.connect(self.addGroup)

        # self.nameEdit.textChanged.connect(lambda: Singleton.modeLabel.setText(self.getModeLabelText()))

    def closeEvent(self, a0):
        self.save()
        return super().closeEvent(a0)

    def save(self, mode=None):
        if mode is None:
            mode = Singleton.mode

        # If we've already asked, don't ask again
        if (file := self.files.getSavedFilename(mode)) is None:
        #     # If there's no file provided or if there's nothing to save, nevermind
        #     if len(self.traitJson.keys()) > 1:
        #         file = self.getFile(save=True)
        #         if file == '' or file is None:
                    return
            # else:
                # return

        j = {}
        with open(file, 'w+') as savefile:
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == 'Options':
                    continue
                j[self.tabs.tabText(i)] = self.tabs.widget(i).serialize()

        self.files.save(j,
            mode=mode,
            tolerance=self.thresholdBox.value() / 100,
            maxUnknowns=self.maxUnknownsBox.value(),
            dealbreakerLimit=self.dealbreakerLimitBox.value() / 100
        )

    def load(self, mode=None, file=None):
        if mode is None:
            mode = Singleton.mode

        json, tolerance, maxUnknowns, dealbreakerLimit = self.files.load(mode=mode, file=file)
        if mode == PREF and json is not None:
            self.thresholdBox.setValue(int(tolerance * 100))
            self.maxUnknownsBox.setValue(int(maxUnknowns))
            self.dealbreakerLimitBox.setValue(int(dealbreakerLimit * 100))
        if json is not None:
            self.initLists(json)
            # Manually set the combo box to start out on Misc.
            # initLists() should fill it
            try:
                self.groupSelector.setCurrentIndex(self.groupSelector.findText('Misc'))
            except:
                # It's not that important
                pass

    def initLists(self, json):
        """ Initializes all the lists and fills them will all the questions """
        debug('init lists called')
        # Remove all the tabs except the Options tab
        # for i in range(self.tabs.count()):
        #     if self.tabs.tabText(i) != "Options":
        #         self.tabs.removeTab(i)
        self.tabs.clear()
        self.tabs.addTab(self._optionsWidget, "Options")
        #* Fill the manual adding combo box
        self.groupSelector.clear()

        #* Fill the list boxes and add the tabs
        for catagory, traits in json.items():
            # Don't add another Options tab
            if catagory == "Options":
                continue
            self.groupSelector.addItem(catagory)
            l = QuestionList(catagory, traits)
            l.updateGUI.connect(self.updateQuestionGui)
            l.reachedEnd.connect(lambda: self.incrementTab(1))
            l.reachedBegin.connect(lambda: self.incrementTab(-1))
            l.questionAccepted.connect(self.acceptQuestion)
            l.resetQuestion.connect(self.resetQuestion)
            self.tabs.addTab(l, catagory)
            # self.tabs.insertTab(0, list, catagory)

    def resetQuestion(self):
        self._questionsAnswered -= 1

    def acceptQuestion(self):
        self._questionsAnswered += 1
        self.progressBar.setValue(round((self._questionsAnswered / self.getTotalTraits()) * 100))
        self.currentList.currentItem().value = self.responseSlider.value()
        # Check that they haven't failed a dealbreaker question
        if Singleton.mode == EVAL:
            if self.currentList.currentItem().pref > Singleton.MAX_VALUE and self.currentList.currentItem().eval < self.dealbreakerLimitBox.value():
                self.breakDeal()

    def incrementTab(self, amt=1):
        self.tabs.setCurrentIndex(self.tabs.currentIndex() + amt)
        # If we're going back, go to the bottom question
        if amt < 0 and self.currentList is not None:
            self.currentList.setCurrentItem(self.currentList.item(self.currentList.count() - 1))

    @todo
    def applyTolerance(self, amt, tolerances):
        # This has to be in order
        for tolerance in sorted(tolerances.values(), reverse=True):
            if amt >= tolerance:
                return invertDict(tolerances)[tolerance]
        raise UserWarning("You've somehow scored less than is possible.")

    def updateQuestionGui(self):
        """ Run whenever the question is changed and we need to update the right side GUI """
        # This line of code is *sick*
        if (l := self.currentList) is not None and (item := l.currentItem()) is not None:
            self.question.setText(item.trait)
            self.responseSlider.setValue(item.value)
            self.blockDealbreakerMessage = item.isDealbreaker()
            self.dealbreakerBox.setChecked(item.isDealbreaker())

    def back(self):
        """ When the back button is pressed """
        if self.currentList != None:
            self.currentList.back()

    def next(self):
        """ When the next button is pressed """
        if self.currentList != None:
            self.currentList.next()

    def skip(self):
        """ When the skip button is pressed """
        if self.currentList != None:
            self.currentList.skip()

    def getModeLabelText(self):
        """ Returns the text we want to put at the top of the left GUI """
        if Singleton.mode == PREF:
            return "How important is it to you that..."
        elif Singleton.mode == EVAL:
            return ''
            # return f'Regarding {self.name}...' if self.name != '' else ''

    def getTotalTraits(self):
        net = 0
        # Start at 1 to avoid the Options menu
        for i in range(1, self.tabs.count()):
            net += self.tabs.widget(i).count()
        return net

    def warnDealbreaker(self, state):
        """ Run when the dealbreaker box is selected in PREF mode """
        if self.currentList is None or self.currentList.currentItem() is None:
            return
        if not state:
            self.currentList.resetQuestion.emit()
            return

        if not self.blockDealbreakerMessage:
            self.blockDealbreakerMessage = False
            # This looks daunting, it's actually pretty simple. QMessageBox.question() just brings up a quick dialog box,
            # and returns whatever button was clicked. This then sets the dealbreakerBox checked state to if they clicked apply
            okay = QMessageBox.question(self, "Dealbreaker Warning", "Are you SURE you can't live with that?",
                    buttons=QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
                ) == QMessageBox.StandardButton.Apply

            self.dealbreakerBox.setChecked(okay)
            if okay:
                t = self.currentList.currentItem()
                self.currentList.acceptAnswer()
                # t.value = (Singleton.MAX_VALUE + 1) * (1 if self.responseSlider.value() >= 0 else -2)
                if self.responseSlider.value() > 0:
                    t.value = Singleton.MAX_VALUE + 1
                    debug(t.value)
                else:
                    t.value = -Singleton.MAX_VALUE - 1
                    debug(t.value)
                self.updateQuestionGui()
        else:
            self.currentList.resetAnswer()
            self.updateQuestionGui()

        self.blockDealbreakerMessage = False

    def breakDeal(self):
        """ Run when we've accepted an answer in EVAL mode and it doesn't pass our dealbreaker threshold """
        QMessageBox(QMessageBox.Icon.Critical, 'That was a Dealbreaker!', 'That was a dealbreaker. Would you like to change your standards?')

    def switchMode(self, to=None, save=True):
        """ Switch between EVAL and PREF modes """
        # Switch to eval mode
        if (to is None and self.preferenceModeButton.isChecked()) or to == EVAL:
            debug(f'Switching to EVAL mode', active=Singleton.debugging)
            Singleton.mode = EVAL
            if save:
                self.save(mode=PREF)
            self.preferenceModeButton.setChecked(False)
            self.evalModeButton.setChecked(True)
            self.maxLabel.setText('Yes')
            self.minLabel.setText('No')
            self.responseSlider.setMaximum(Singleton.MAX_VALUE)
            self.responseSlider.setMinimum(0)
            self.responseSlider.setValue(round(Singleton.MAX_VALUE / 2))
            self.responseSlider.setTickPosition(QSlider.TickPosition.NoTicks)
            self.dealbreakerBox.hide()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(True)
            self.skipButton.setText('Not Applicable')

        # Switch to pref mode
        elif (to is None and self.evalModeButton.isChecked()) or to == PREF:
            debug(f'Switching to PREF mode', active=Singleton.debugging)
            Singleton.mode = PREF
            if save:
                self.save(mode=EVAL)
            self.preferenceModeButton.setChecked(True)
            self.evalModeButton.setChecked(False)
            self.maxLabel.setText('Very Important')
            self.minLabel.setText('I hate that')
            self.responseSlider.setMaximum(Singleton.MAX_VALUE)
            self.responseSlider.setMinimum(-Singleton.MAX_VALUE)
            self.responseSlider.setValue(0)
            self.responseSlider.setTickPosition(QSlider.TickPosition.TicksAbove)
            self.dealbreakerBox.show()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(False)
            self.skipButton.setText('Remove Question')

        # Update all the Traits to make sure they have to correct answered status for this mode
        # Start at 1 to avoid the Options menu
        for i in range(1, self.tabs.count()):
            for k in range((list := self.tabs.widget(i)).count()):
                list.item(k).update()

        # If we have a file for the current mode, load it
        if (file := self.files.getSavedFilename(mode=Singleton.mode)) is not None:
            self.files.load(file=file, mode=Singleton.mode)
        # If we don't have a file for the current mode, but we do have a file for the mode we just switched from,
        # convert the other mode's file into an equivalent current mode file, and load it
        elif (file := self.files.getSavedFilename(mode=not Singleton.mode)) is not None:
            self.files.load(file=self.files._convertFileMode(file, toMode=Singleton.mode), mode=Singleton.mode)

    def calculate(self):
        """ The actual algorithm part -- calculate if they fit our criteria """
        # Save the current mode file first
        self.save()
        # This shouldn't be necissary, because the only way to change the other mode is to be in that mode,
        # and switchMode() saves the file
        # self.save(not Singleton.mode)

        person = 0
        max = 0
        count = 0
        skipped = 0
        unanswered = 0

        # Loop through the catagories
        # for prefTraits, evalTraits in zip(self.selectedPrefJson.values(), self.selectedEvalJson.values()):
        # Loop through the traits
        for i in range(1, self.tabs.count()):
            for k in range((list := self.tabs.widget(i)).count()):
                trait = list.item(k)
                # If they skipped or didn't answer a preferences question, we just assume it wasn't applicable to them
                if trait.prefState == ANSWERED:
                    if trait.evalState == ANSWERED:
                        person += (trait.eval / 100) * trait.pref
                        max    += trait.pref
                        count  += 1
                    elif trait.evalState == SKIPPED:
                        skipped += 1
                    else:
                        unanswered += 1
        ResultsMenu(max, person, count, skipped, unanswered, self.thresholdBox.value() / 100, self.maxUnknownsBox.value()).exec()

    def restoreDefaults(self):
        # Just so we never end up writing over the default preferences file
        shutil.copy(Singleton.DEFAULT_PREFERENCES_FILE, Singleton.COPIED_PREFERENCES_FILE)
        self.load(file=Singleton.COPIED_PREFERENCES_FILE, mode=PREF)

    def addGroup(self, name):
        # If it already exists, ignore it
        if name in [self.tabs.tabText(i) for i in self.tabs.count()]:
            return
        self.tabs.addTab(QuestionsList(name), name)
        # self.traitJson[name] = []

    # Called when enter is pressed in questionBox
    def addAttribute(self):
        text = self.questionBox.text()
        if self.groupSelector.currentText() == '' or text == '':
            return

        # Just find the tab with the current text of the combo box, and insert the question text into that tab's list
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.groupSelector.currentText():
                self.tabs.widget(i).addItem(Trait(trait=text))
                debug(f"Added {text} to {self.tabs.tabText(i)}!")
                # There better only be 1
                break
        # And don't forget to add it to our internal map of lists and our interal json
        # self.selectedPrefJson[self.groupSelector.currentText()].append(Trait(text).toJSON())
        # self.selectedEvalJson[self.groupSelector.currentText()].append(Trait(text).toJSON())

        # Clear the box so it feels like something happened
        self.questionBox.clear()

        # Reload the lists so the question shows up
        # self.loadFile()
        # self.initLists()

    @property
    def currentList(self):
        # return self.traitJson[self.tabs.tabText(self.tabs.currentIndex())]
        return self.tabs.currentWidget() if self.tabs.tabText(self.tabs.currentIndex()) != 'Options' else None

if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
