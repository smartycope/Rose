# This Python file uses the following encoding: utf-8
import os
import shutil
import sys
from os.path import basename, dirname, join
from pathlib import Path

import jstyleson as jsonc
try:
    from Cope import debug
except ImportError:
    debug = lambda *args, **_: print(*args)
from PyQt6 import uic
from PyQt6.QtCore import QEvent, QFile, QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox,
                             QFileDialog, QListView, QListWidget, QMainWindow,
                             QMessageBox, QSlider, QWidget)

from FileManager import FileManager
from QuestionList import QuestionList
from ResultsMenu import ResultsMenu
from Singleton import *
from Trait import *

class MainWindow(QMainWindow):
    def __init__(self):
        # Load the UI
        super(MainWindow, self).__init__()
        uic.loadUi(Singleton.ui / "form.ui", self)

        Singleton.mainWindow = self

        # Ensure that the saves folder exists, if not, create it
        Singleton.saves.mkdir(exist_ok=True)

        # Set the tooltips of the labels to be the same as the boxes they're next to
        self.thresholdLabel.setToolTip(self.thresholdBox.toolTip())
        self.maxUnknownsLabel.setToolTip(self.maxUnknownsBox.toolTip())
        self.dealbreakerLimitLabel.setToolTip(self.dealbreakerLimitBox.toolTip())

        # Save the options tab widget so we can reinsert it after calling tabs.clear()
        self._optionsWidget = self.Options

        self.blockDealbreakerMessage = False
        self._loadedYet = False

        self.fileManager = FileManager(Singleton.saves, self)

        # Just assume we're starting on the Options page
        self.bindSignals()

        # Set the correct mode
        self.switchMode(Singleton.startingMode, save=False, reload=True)

        if Singleton.debugging:
            pass
            # debug("This is only here for debugging", clr=3)
            # self.load(mode=PREF, file=Singleton.saves / 'testing.pref')
            # self.tabs.setCurrentIndex(1)

    def keyPressEvent(self, key):
        max = self.maxValue()
        min = self.minValue()

        if key.text() == 'y':
            self.responseSlider.setValue(max)
        elif key.text() == '0':
            # This is contested
            self.responseSlider.setValue(max)
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
        def accept():
            self.responseSlider.setValue(self.maxValue())
            self.next()
        def reject():
            self.responseSlider.setValue(self.minValue())
            self.next()
        def eh():
            self.responseSlider.setValue(0 if Singleton.mode == PREF else int(Singleton.MAX_VALUE / 2))
            self.next()
        self.minButton.clicked.connect(reject)
        self.maxButton.clicked.connect(accept)
        self.ehButton.clicked.connect(eh)

        self.responseSlider.sliderMoved.connect(self.uncheckDealbreakerBox)

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
        self.questionBox.returnPressed.connect(self.addAttribute)

        self.evalModeButton.pressed.connect(self.switchMode)
        self.preferenceModeButton.pressed.connect(self.switchMode)

        self.evalFileButton.pressed.connect(lambda: self.load(mode=EVAL))
        self.prefFileButton.pressed.connect(lambda: self.load(mode=PREF))

        self.fileManager.evalFileChanged.connect(lambda file: self.evalFileLabel.setText(os.path.basename(file)))
        self.fileManager.prefFileChanged.connect(lambda file: self.prefFileLabel.setText(os.path.basename(file)))

        self.dealbreakerBox.released.connect(self.warnDealbreaker)

        self.groupSelector.textActivated.connect(self.addGroup)

    def closeEvent(self, a0):
        self.save()
        return super().closeEvent(a0)

    def save(self, mode=None):
        if mode is None:
            mode = Singleton.mode

        j = {}
        for i in range(1, self.tabs.count()):
            j[self.tabs.tabText(i)] = self.tabs.widget(i).serialize()

        self.fileManager.save(j,
            mode=mode,
            tolerance=self.thresholdBox.value() / 100,
            maxUnknowns=self.maxUnknownsBox.value(),
            dealbreakerLimit=self.dealbreakerLimitBox.value() / 100
        )

    def load(self, mode=None, file=None, reload=True):
        if mode is None:
            mode = Singleton.mode

        json, tolerance, maxUnknowns, dealbreakerLimit = self.fileManager.load(mode=mode, file=file)
        if mode == PREF and json is not None:
            self.thresholdBox.setValue(int(tolerance * 100))
            self.maxUnknownsBox.setValue(int(maxUnknowns))
            self.dealbreakerLimitBox.setValue(int(dealbreakerLimit * 100))
        if json is not None:
            # Make sure we switch to the mode of the file we just loaded
            # For instance, if we open a pref file when in eval mode, then bad
            # things would happen
            self.switchMode(mode, save=False)
            # If we've already loaded, just add the data to the existing traits
            if not self._loadedYet or reload:
                self.initLists(json)
                self._loadedYet = True
            else:
                self.addModeDataToLists(mode, json)
            # Manually set the combo box to start out on Misc.
            # initLists() should fill it
            try:
                self.groupSelector.setCurrentIndex(self.groupSelector.findText('Misc'))
            except:
                # It's not that important
                pass

        # Update at the end
        self.updateQuestionGui()

    def uncheckDealbreakerBox(self):
        if Singleton.mode == PREF:
            debug('dealbreaker unchecked')
            self.dealbreakerBox.setChecked(False)

    def addModeDataToLists(self, mode, json):
        # Loop through the traits
        for i in range(1, self.tabs.count()):
            try:
                self.tabs.widget(i).addModeData(mode, json[self.tabs.tabText(i)])
            except KeyError:
                debug(f'Error: {self.tabs.tabText(i)} isnt in the json', clr=-1,
                    throwError=Singleton.debugging)

    def _initList(self, traits):
        l = QuestionList(traits)
        l.updateGUI.connect(self.updateQuestionGui)
        l.reachedEnd.connect(lambda: self.incrementTab(1))
        l.reachedBegin.connect(lambda: self.incrementTab(-1))
        l.questionAccepted.connect(self.acceptQuestion)
        # l.skipQuestion.connect(self.skipQuestion)
        return l

    def initLists(self, json):
        """ Initializes all the lists and fills them will all the questions """
        # Remove all the tabs except the Options tab
        self.tabs.clear()
        self.tabs.addTab(self._optionsWidget, "Options")
        # Fill the manual adding combo box
        self.groupSelector.clear()

        #* Fill the list boxes and add the tabs
        for catagory, traits in json.items():
            # Don't add another Options tab
            if catagory == "Options":
                continue
            self.groupSelector.addItem(catagory)
            self.tabs.addTab(self._initList(traits), catagory)

    def acceptQuestion(self):
        # Double check that the question exists
        if (item := self.currentList.currentItem()) is not None:
            # If the trait is already marked as a dealbreaker, then this will unset it
            # Also, if we're in eval mode, we don't care
            if Singleton.mode == EVAL or not self.dealbreakerBox:
                item.value = self.responseSlider.value()
            # Check that they haven't failed a dealbreaker question
            if Singleton.mode == EVAL:
                if not item.checkDealbreaker(self.dealbreakerLimitBox.value()):
                    self.breakDeal()

    def incrementTab(self, amt=1):
        self.tabs.setCurrentIndex(self.tabs.currentIndex() + amt)
        # If we're going back, go to the bottom question
        if amt < 0 and self.currentList is not None:
            self.currentList.setCurrentItem(self.currentList.item(self.currentList.count() - 1))

    def updateQuestionGui(self):
        """ Run whenever the question is changed and we need to update the
            right side GUI """
        # This line of code is *sick*
        if (l := self.currentList) is not None and \
           (item := l.currentItem()) is not None and \
           not item.isHidden():
            self.question.setText(item.trait)
            self.responseSlider.setValue(item.value)
            self.blockDealbreakerMessage = item.dealbreakerState
            self.dealbreakerBox.setChecked(item.dealbreakerState)

            # Update the progress bar manually
            answered = 0
            total = 0
            for trait in self.allTraits:
                if trait.prefState == SKIPPED:
                    # If it's not an applicable question, it counts as answered
                    # only in pref mode (it'll be hidden in eval mode)
                    if Singleton.mode == PREF:
                        total += 1
                        answered += 1
                else:
                    total += 1
                    if trait.state == ANSWERED:
                        answered += 1
            self.progressBar.setValue(round((answered / total) * 100))

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
            return 'Is it true that...'

    def warnDealbreaker(self):
        """ Run when the dealbreaker box state has changed """

        if self.currentList is None or self.currentList.currentItem() is None:
            return
        # Only ask if we're turning it on
        if not self.dealbreakerBox.isChecked():
            # Inform the current Trait it's not a breakbreaker anymore
            self.currentList.currentItem().value = self.responseSlider.value()
            return

        if not self.blockDealbreakerMessage:
            self.blockDealbreakerMessage = False
            # This looks daunting, it's actually pretty simple.
            # QMessageBox.question() just brings up a quick dialog box, and
            # returns whatever button was clicked. This then sets the
            # dealbreakerBox checked state to if they clicked apply
            okay = QMessageBox.question(self, "Dealbreaker Warning",
                    "Are you SURE you can't live with that?",
                    buttons=QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
                ) == QMessageBox.StandardButton.Apply

            if okay:
                self.dealbreakerBox.setChecked(True)
                if self.responseSlider.value() >= 0:
                    self.currentList.currentItem().value = self.maxValue() + Singleton.DEALBREAKER_BONUS
                else:
                    self.currentList.currentItem().value = self.minValue() - Singleton.DEALBREAKER_BONUS
                # Don't do this here! I don't remember why, but it's important.
                # self.currentList.acceptAnswer()
                self.currentList.currentItem().state = ANSWERED
                self.updateQuestionGui()
        else:
            self.currentList.resetAnswer()
            self.updateQuestionGui()

        self.blockDealbreakerMessage = False

    def breakDeal(self):
        """ Run when we've accepted an answer in EVAL mode and it doesn't pass our dealbreaker threshold """
        QMessageBox(QMessageBox.Icon.Critical, 'That was a Dealbreaker!', 'That was a dealbreaker. Would you like to change your standards?')

    def switchMode(self, to=None, save=True, reload=False):
        """ Switch between EVAL and PREF modes """
        if Singleton.mode == to and not reload:
            return
        # Switch to eval mode
        if (to is None and self.preferenceModeButton.isChecked()) or to == EVAL:
            debug(f'Switching to EVAL mode', active=Singleton.debugging)
            if save:
                self.save()
            Singleton.mode = EVAL
            self.setWindowTitle('Rose - Calibrating Preferences')
            self.preferenceModeButton.setChecked(False)
            self.evalModeButton.setChecked(True)
            # Add spaces so their centered correctly
            self.minButton.setText('No   ')
            self.ehButton.setText('Sorta')
            self.maxButton.setText('  Yes')
            self.responseSlider.setMaximum(Singleton.MAX_VALUE)
            self.responseSlider.setMinimum(0)
            self.responseSlider.setValue(round(Singleton.MAX_VALUE / 2))
            # self.responseSlider.setTickPosition(QSlider.TickPosition.NoTicks)
            self.responseSlider.setTickInterval(50)
            self.dealbreakerBox.hide()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(True)
            self.skipButton.setText('Not Applicable')

        # Switch to pref mode
        elif (to is None and self.evalModeButton.isChecked()) or to == PREF:
            debug(f'Switching to PREF mode', active=Singleton.debugging)
            if save:
                self.save()
            Singleton.mode = PREF
            self.setWindowTitle('Rose - Evaluating')
            self.preferenceModeButton.setChecked(True)
            self.evalModeButton.setChecked(False)
            # Add spaces so their centered correctly
            self.minButton.setText('I hate that        ')
            self.ehButton.setText("I don't really care")
            self.maxButton.setText('     Very Important')
            self.responseSlider.setMaximum(Singleton.MAX_VALUE)
            self.responseSlider.setMinimum(-Singleton.MAX_VALUE)
            self.responseSlider.setValue(0)
            # self.responseSlider.setTickPosition(QSlider.TickPosition.TicksAbove)
            self.responseSlider.setTickInterval(100)
            self.dealbreakerBox.show()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(False)
            self.skipButton.setText('Remove Question')

        # Update all the Traits to make sure they have to correct answered status for this mode
        for trait in self.allTraits:
            trait.update()

        # If we have a file for the current mode, load it
        if (file := self.fileManager.getSavedFilename(mode=Singleton.mode)) is not None:
            self.fileManager.load(file=file, mode=Singleton.mode)
        # If we don't have a file for the current mode, but we do have a file for the mode we just switched from,
        # convert the other mode's file into an equivalent current mode file, and load it
        elif (file := self.fileManager.getSavedFilename(mode=not Singleton.mode)) is not None:
            self.fileManager.load(file=self.fileManager._convertFileMode(file, toMode=Singleton.mode), mode=Singleton.mode)

    def calculate(self):
        """ The actual algorithm part -- calculate if they fit our criteria """
        # Save the current mode file first
        self.save()

        person = 0
        max = 0
        count = 0
        skipped = 0
        unanswered = 0

        for trait in self.allTraits:
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
        self.load(file=Singleton.COPIED_PREFERENCES_FILE, mode=PREF, reload=True)

    def addGroup(self, name):
        # If it already exists, ignore it
        if name in [self.tabs.tabText(i) for i in range(self.tabs.count())]:
            return
        self.tabs.addTab(self._initList([]), name)

    def addAttribute(self):
        """ Called when enter is pressed in questionBox """
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

        # Clear the box so it feels like something happened
        self.questionBox.clear()

    def maxValue(self):
        return Singleton.MAX_VALUE

    def minValue(self):
        return 0 if Singleton.mode == EVAL else -Singleton.MAX_VALUE

    @property
    def allTraits(self):
       return [self.tabs.widget(i).item(k) for i in range(1, self.tabs.count()) for k in range(self.tabs.widget(i).count())]

    @property
    def currentList(self):
        return self.tabs.currentWidget() if self.tabs.tabText(self.tabs.currentIndex()) != 'Options' else None

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    try:
        rtn = app.exec()
    except Exception as err:
        if Singleton.debugging:
            raise err
        else:
            window.save()
    sys.exit(rtn)
