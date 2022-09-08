# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
from Cope import debug, todo, unreachableState

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QListWidget, QListView, QMessageBox, QAbstractButton
from PyQt5.QtCore import QEvent, QFile, Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QWidget, QDialogButtonBox, QSlider

import jstyleson as jsonc
from os.path import dirname, join, basename; DIR = dirname(__file__)
import shutil

from Trait import *
from ResultsMenu import ResultsMenu

__DEBUG__ = True

# -- Note: consider changing the scoring in the program to be added logirithmically, so the closer it comes to 100 the more it's actually worth, but still judged the same way.
# -- Also, maybe if they negatively fulfill the value half the negative

todo('consider a switch to a "strongly agree", "agree", "slightly agree", etc. system instead of a slider')
todo('fix tab and shift+tab')

DEFAULT_SAVES_PATH = DIR
DEFAULT_PREFERENCES_FILE = join(DIR, 'boilerplatePreferences.jsonc')
COPIED_PREFERENCES_FILE = join(dirname(DEFAULT_PREFERENCES_FILE), 'UserPreferences.jsonc')
PARTLY_VALUE = 0.6
ROUND_TO = 1
STARTING_MODE = PREF


# Ways to change the question:
# click "next"
# click "back"
# click "skip"
# click on a question
# arrow keys (eventually)


class MainWindow(QMainWindow):
    ICON_SIZE = 10
    WORD_WRAP = False
    def __init__(self):
        # Load the UI
        super(MainWindow, self).__init__()
        uic.loadUi(Path(__file__).resolve().parent / "form.ui", self)
        self.centralWidget().setLayout(self.mainLayout)

        # Set the tooltips of the labels to be the same as the boxes they're next to
        self.thresholdLabel.setToolTip(self.thresholdBox.toolTip())
        self.maxUnknownsLabel.setToolTip(self.maxUnknownsBox.toolTip())
        self.dealbreakerLimitLabel.setToolTip(self.dealbreakerLimitBox.toolTip())

        # Just assume we're starting on the Options page
        self.tabs.currentWidget().setLayout(self.optionsLayout)
        self.bindSignals()

        self.index = 0
        self.numFinished = 0
        self.blockDealbreakerMessage = False

        self.selectedPrefFile = None
        self.selectedPrefJson = {}
        self.selectedEvalFile = None
        self.selectedEvalJson = {}

        # Set the correct mode
        self.switchMode(STARTING_MODE, save=False)

        if __DEBUG__:
            debug("This is only here for debugging", clr=3)
            self.loadFile(mode=PREF, file='/home/leonard/hello/python/Rose/UserPreferences.jsonc')
            self.loadFile(mode=EVAL, file='/home/leonard/hello/python/Rose/UserPreferences - evaluation.jsonc')
            # self.loadFile(mode=EVAL, file=self._convertFileMode('/home/leonard/hello/python/Rose/UserPreferences.jsonc', EVAL))

    def keyPressEvent(self, key):
        max = 100
        min = 0 if self.mode == EVAL else -100

        if key.text() == 'y':
            self.responseSlider.setValue(max)
        elif key.text() == '0':
            self.responseSlider.setValue(min)
        elif key.text() == '1':
            self.responseSlider.setValue(10 if self.mode == EVAL else -80)
        elif key.text() == '2':
            self.responseSlider.setValue(20 if self.mode == EVAL else -60)
        elif key.text() == '3':
            self.responseSlider.setValue(30 if self.mode == EVAL else -40)
        elif key.text() == '4':
            self.responseSlider.setValue(40 if self.mode == EVAL else -20)
        elif key.text() == '5':
            self.responseSlider.setValue(50 if self.mode == EVAL else 0)
        elif key.text() == '6':
            self.responseSlider.setValue(60 if self.mode == EVAL else 20)
        elif key.text() == '7':
            self.responseSlider.setValue(70 if self.mode == EVAL else 40)
        elif key.text() == '8':
            self.responseSlider.setValue(80 if self.mode == EVAL else 60)
        elif key.text() == '9':
            self.responseSlider.setValue(90 if self.mode == EVAL else 80)
        elif key.text() == 'i' and self.mode == PREF:
            self.responseSlider.setValue(max)
        elif key.text() == 'h' and self.mode == PREF:
            self.responseSlider.setValue(min)
        elif key.text() == 'n':
            #* This is contested
            self.responseSlider.setValue(min)
            # self.nextButton.clicked.emit()
        elif key.text() == 's':
            self.skipButton.clicked.emit()
        elif key.text() == 'b':
            self.backButton.clicked.emit()
        elif key.key() == Qt.Key.Key_Return:
            if key.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.backButton.clicked.emit()
            else:
                self.nextButton.clicked.emit()
        elif key.key() == Qt.Key.Key_Up:
            self.backButton.clicked.emit()
        elif key.key() == Qt.Key.Key_Down:
            self.nextButton.clicked.emit()
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
                self.loadFile()

    def bindSignals(self):
        self.backButton.clicked.connect(self.back)
        self.nextButton.clicked.connect(self.next)
        self.skipButton.clicked.connect(self.skip)

        def seperateButtons(button):
            if button.text() == 'Save':
                self.save()
            elif button.text() == 'Open':
                self.loadFile()
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

        self.evalFileButton.pressed.connect(lambda: self.loadFile(mode=EVAL))
        self.prefFileButton.pressed.connect(lambda: self.loadFile(mode=PREF))

        # self.dealbreakerBox.stateChanged.connect(self.warnDealbreaker)
        self.dealbreakerBox.toggled.connect(self.warnDealbreaker)

        self.groupSelector.textActivated.connect(self.addGroup)

        # self.nameEdit.textChanged.connect(lambda: self.modeLabel.setText(self.getModeLabelText()))

    def closeEvent(self, a0):
        self.save()
        return super().closeEvent(a0)

    # Generate and configure a new list widget
    def _getNewListWidget(self):
        list = QListWidget()
        # Connect all the signals
        # So you can use arrow keys
        # list.itemSelectionChanged.connect(self.onItemSelectionChanged)
        # So it handles clicking on an item slightly differently
        list.itemClicked.connect(self.onTraitClicked)
        # Set the icon sizes
        list.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        # If we're doing word wrap or not
        list.setWordWrap(self.WORD_WRAP)
        # Set the keys to be handled by the window instead
        list.keyPressEvent = self.keyPressEvent
        return list

    # Initializes all the lists and fills them will all the questions
    def fillLists(self):
        # Remove all the tabs except the Options tab
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) != "Options":
                self.tabs.removeTab(i)

        #* Fill the list boxes and add the tabs
        for catagory, traits in self.traitJson.items():
            # Don't add another Options tab
            if catagory == "Options":
                continue
            list = self._getNewListWidget()
            for trait in traits:
                if catagory == "Absolutes(>80)":
                    debug(trait, 'adding trait')
                list.addItem(Trait(*trait).asListItem(self.mode))
            self.tabs.insertTab(0, list, catagory)

    def applyTolerance(self, amt, tolerances):
        # This has to be in order
        for tolerance in sorted(tolerances.values(), reverse=True):
            if amt >= tolerance:
                return invertDict(tolerances)[tolerance]
        raise UserWarning("You've somehow scored less than is possible.")

    # Run whenever the question is changed and we need to update the right side GUI
    def updateQuestionGui(self):
        if self.currentTab != 'Options':
            self.question.setText(self.currentTrait.trait)
            self.responseSlider.setValue(self.currentTrait.value)
            self.blockDealbreakerMessage = self.currentTrait.value > 100
            self.dealbreakerBox.setChecked(self.blockDealbreakerMessage)

    # Used to change the current question
    def incrementIndex(self, amt=1) -> ('new index', 'new tab index'):
        if self.currentTab != 'Options':
            i = self.index + amt
            tab = self.tabs.currentIndex()

            #* Handle looping the tabs when we're at the end or beginning
            # If we're at the top and we hit back, go to the previous tab, if there is one
            if i < 0:
                if tab > 0:
                    # Not the current list, the length of the list we're switching to
                    newListLen = len(self.traitJson[self.tabs.tabText(self.tabs.currentIndex() - 1)])
                    return newListLen - 1, tab - 1
                else:
                    return 0, tab
            # If we're at the bottom and we hit next or skip, go to the next tab, if there is one
            elif i >= len(self.currentList):
                if tab < self.tabs.count() - 1: # - 1 becuase of the Options tab
                    return 0, tab + 1
                else:
                    return len(self.currentList) - 1, tab

            return i, tab

    # Called when you jump to a new question by clicking on it
    def onTraitClicked(self, _=False):
        self.switchTrait(self.currentListWidget.currentRow(), self.tabs.currentIndex(), False)

    # The function that's called *any* time the displayed trait changes
    # The only thing allowed to modify self.index or switch the current tab
    def switchTrait(self, index, tabIndex, acceptCurrent):
        # This order is *very* important
        if acceptCurrent:
            # This is here, because updateTraitStatus gets the current list item widget from the
            # list widget directly, and not from self.index, so when you click on an item it updates
            # the new one you clicked on, not the old one that needs updated.
            # Basically, we want to update the trait we are one before we move to the next one
            self.acceptAnswer()
            self.updateTraitStatus()

        self.index = index
        self.tabs.setCurrentIndex(tabIndex)

        # Some weird bug when trying to hit next when on the last question in the last list
        if type(self.currentListWidget) is QListWidget:
            self.currentListWidget.setCurrentRow(self.index)
        self.updateQuestionGui()

    # When the back button is pressed
    def back(self):
        if self.currentTab != 'Options':
            self.switchTrait(*self.incrementIndex(-1), False)

    # When the next button is pressed
    def next(self):
        if self.currentTab != 'Options':
            self.switchTrait(*self.incrementIndex(), True)

    # When the skip button is pressed
    def skip(self):
        if self.currentTab != 'Options':
            if self.currentTrait.state != ANSWERED:
                Trait(*self.currentList[self.index]).state = SKIPPED

            # If you go back to a question you've already answered and hit skip, then it resets the question
            if self.currentTrait.state == ANSWERED:
                self.resetAnswer(state=SKIPPED)

            self.updateTraitStatus()
            self.switchTrait(*self.incrementIndex(), False)
            # See comment in self.switchTrait as to why this is here

    # Returns the text we want to put at the top of the left GUI
    def getModeLabelText(self):
        if self.mode == PREF:
            return "How important is it to you that..."
        elif self.mode == EVAL:
            return ''
            # return f'Regarding {self.name}...' if self.name != '' else ''

    def getTotalTraits(self):
        net = 0
        for traits in self.traitJson.values():
            net += len(traits)
        return net

    # Updates the progress bar
    def updateProgressBar(self):
        self.progressBar.setValue(round((self.numFinished / self.getTotalTraits()) * 100))

    # The *only* thing allowed to update the current trait checkbox icon
    def updateTraitStatus(self):
        if self.currentListWidget.currentItem() is not None:
            self.currentTrait.updateListItem(self.currentListWidget.currentItem(), self.mode)

    # Run when we want to "set" the current trait
    def acceptAnswer(self):
        # Current State
        if self.currentList[self.index][2] != ANSWERED:
            self.numFinished += 1
            self.updateProgressBar()
        # Current State
        self.currentList[self.index][2] = ANSWERED

        # Current Value
        self.currentList[self.index][1] = self.responseSlider.value()

        # Check that they haven't failed a dealbreaker question
        if self.mode == EVAL:
            for i in self.selectedPrefJson[self.currentTab]:
                if i[0] == self.currentTrait.trait:
                    pref = i[1]
                    break
            for i in self.selectedEvalJson[self.currentTab]:
                if i[0] == self.currentTrait.trait:
                    eval = i[1]
                    break

            if pref > 100 and eval < self.dealbreakerLimitBox.value():
                self.breakDeal()

    # Resets the current trait to default values
    def resetAnswer(self, state=NOT_ANSWERED):
        if self.currentList[self.index][2] == ANSWERED:
            # Decrement the progress bar
            self.numFinished -= 1
            self.updateProgressBar()

        # Current Value
        self.currentList[self.index][1] = 0

        self.updateTraitStatus()

        # Current State
        self.currentList[self.index][2] = state

    # Run when the dealbreaker box is selected in PREF mode
    def warnDealbreaker(self, state):
        debug(state)
        debug(self.blockDealbreakerMessage)
        if state and not self.blockDealbreakerMessage:
            self.blockDealbreakerMessage = False
            # This looks daunting, it's actually pretty simple. QMessageBox.question() just brings up a quick dialog box,
            # and returns whatever button was clicked. This then sets the dealbreakerBox checked state to if they clicked apply
            okay = QMessageBox.question(self, "Dealbreaker Warning", "Are you SURE you can't live with that?",
                    buttons=QMessageBox.StandardButtons(
                        QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
                    )
                ) == QMessageBox.StandardButton.Apply

            self.dealbreakerBox.setChecked(okay)
            if okay:
                t = self.currentTrait
                t.value = 101
                self.currentTrait = t
                self.updateQuestionGui()
        elif not self.blockDealbreakerMessage:
            debug()
            self.resetAnswer()
            self.updateQuestionGui()

        self.blockDealbreakerMessage = False

    # Run when we've accepted an answer in EVAL mode and it doesn't pass our dealbreaker threshold
    def breakDeal(self):
        QMessageBox(QMessageBox.Icon.Critical, 'That was a Dealbreaker!', 'That was a dealbreaker. Would you like to change your standards?')

    # Switch between EVAL and PREF modes
    def switchMode(self, to=None, save=True):
        # Switch to eval mode
        if (to is None and self.preferenceModeButton.isChecked()) or to == EVAL:
            debug(f'Switching to EVAL mode', active=__DEBUG__)
            self.mode = EVAL
            if save:
                self.save(mode=PREF)
            self.preferenceModeButton.setChecked(False)
            self.evalModeButton.setChecked(True)
            self.maxLabel.setText('Yes')
            self.minLabel.setText('No')
            self.responseSlider.setMaximum(100)
            self.responseSlider.setMinimum(0)
            self.responseSlider.setValue(50)
            self.responseSlider.setTickPosition(QSlider.TickPosition.NoTicks)
            self.dealbreakerBox.hide()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(True)
            self.skipButton.setText('Not Applicable')

        # Switch to pref mode
        elif (to is None and self.evalModeButton.isChecked()) or to == PREF:
            debug(f'Switching to PREF mode', active=__DEBUG__)
            self.mode = PREF
            if save:
                self.save(mode=EVAL)
            self.preferenceModeButton.setChecked(True)
            self.evalModeButton.setChecked(False)
            self.maxLabel.setText('Very Important')
            self.minLabel.setText('I hate that')
            self.responseSlider.setMaximum(100)
            self.responseSlider.setMinimum(-100)
            self.responseSlider.setValue(0)
            self.responseSlider.setTickPosition(QSlider.TickPosition.TicksAbove)
            self.dealbreakerBox.show()
            self.modeLabel.setText(self.getModeLabelText())
            self.calculateButton.setVisible(False)
            self.skipButton.setText('Remove Question')

        # self.fillLists()

        # If we have a file for the current mode, load it
        if (file := self.getSavedFilename(mode=self.mode)) is not None:
            self.loadFile(file=file, mode=self.mode)
        # If we don't have a file for the current mode, but we do have a file for the mode we just switched from,
        # convert the other mode's file into an equivalent current mode file, and load it
        elif (file := self.getSavedFilename(mode=not self.mode)) is not None:
            self.loadFile(file=self._convertFileMode(file, toMode=self.mode), mode=self.mode)

    # Take the given file, and converts it from the mode it's currently in to 'to'
    # Losses all the state and value data, just keeps the questions
    # If going from pref -> eval, it also drops the skipped questions, but not vice versa
    def _convertFileMode(self, file, toMode):
        def stripData(attr, toMode):
            newAttr = {}
            for catagory in attr:
                newAttr[catagory] = []
                for trait, value, state in attr[catagory]:
                    #? This is contested - should you automatically remove unanswered preferences questions or not?
                    if state != SKIPPED and toMode == EVAL and (True or state != NOT_ANSWERED):
                        newAttr[catagory].append([trait, 0, 0])
            return newAttr

        with open(file, 'r') as f:
            fromJson = jsonc.load(f)
            toJson = {}

            # If no conversion is required
            if (fromJson['__type__'] == 'PREF' and toMode == PREF) or (fromJson['__type__'] == 'EVAL' and toMode == EVAL):
                return file

            # We're going from eval -> pref
            elif toMode == PREF:
                # Automatically come up with the name of the file we're creating
                try:
                    toJson['__type__'] = 'PREF'
                    toJson["Tolerance"] = self.thresholdBox.value()
                    toJson["Settings"]["max unknowns"] = self.maxUnknownsBox.value()
                    toJson["Settings"]["dealbreaker limit"] = self.dealbreakerLimitBox.value()
                    toJson['Attributes'] = stripData(fromJson['Attributes'], PREF)
                    nameAddOn = ' - preferences'
                # The file is invalid
                except Exception as err:
                    debug(err, stackTrace=True)
                    QMessageBox.critical(self, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return file

            # We're going from pref -> eval
            elif toMode == EVAL:
                try:
                    toJson['__type__'] = 'EVAL'
                    toJson['Attributes'] = stripData(fromJson['Attributes'], EVAL)
                    nameAddOn = ' - evaluation'
                # The file is invalid
                except Exception as err:
                    debug(err, stackTrace=True)
                    QMessageBox.critical(self, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return file
            else:
                debug('Impossible state reached', color=-1)

        newFilename = join(dirname(file), basename(file).split('.')[0] + nameAddOn + '.' + basename(file).split('.')[1])
        with open(newFilename, 'w+') as toFile:
            debug(toJson, f'writing to file {newFilename}')
            jsonc.dump(toJson, toFile, indent=4)

        return newFilename

    # The actual algorithm part -- calculate if they fit our criteria
    def calculate(self):
        # Save the current mode file first
        self.save()
        # This shouldn't be necissary, because the only way to change the other mode is to be in that mode,
        # and switchMode() saves the file
        # self.save(not self.mode)

        person = 0
        max = 0
        count = 0
        skipped = 0
        unanswered = 0

        # Loop through the catagories
        for prefTraits, evalTraits in zip(self.selectedPrefJson.values(), self.selectedEvalJson.values()):
            # Loop through the traits
            for prefTrait, evalTrait in zip(prefTraits, evalTraits):
                pref = Trait.fromJSON(prefTrait)
                eval = Trait.fromJSON(evalTrait)
                # If they skipped or didn't answer a preferences question, we just assume it wasn't applicable to them
                if pref.state == ANSWERED:
                    if eval.state == ANSWERED:
                        person += (eval.value / 100) * pref.value
                        max    += pref.value
                        count  += 1
                    elif eval.state == SKIPPED:
                        skipped += 1
                    else:
                        unanswered += 1
        ResultsMenu(max, person, count, skipped, unanswered, self.thresholdBox.value() / 100, self.maxUnknownsBox.value()).exec()

    # Promts the user for a filepath
    def getFile(self, save=True, mode=None):
        if mode is None:
            mode = self.mode

        if save:
            todo('figure out how to have default suggested filenames')
            file = QFileDialog.getSaveFileName(self,
                    caption=f'Save your personal preferences file'
                            if mode == PREF else
                            'Save your responses about the person you\'re considering',
                    filter="*.json, *.jsonc",
                    initialFilter="*.json, *.jsonc"
                )[0]
        else:
            file = QFileDialog.getOpenFileName(self,
                caption=f'Open your personal preferences file'
                        if mode == PREF else
                        'Open a file you saved on someone',
                filter="*.json *.jsonc",
                initialFilter="*.json *.jsonc"
            )[0]

        if file != '' and file is not None:
            if not file.endswith(('.json', '.jsonc')):
                file = file + '.json'
            # self.setFile(mode, file)

        return file

        # if self.mode == PREF:
        #     name = f'{self.name}{"p" if self.name == "" else "P"}references.json'
        # elif self.mode == EVAL:
        #     name = f'{self.name}{"a" if self.name == "" else "A"}ttributes.json'

    # Sets a given file to be the cannonical file that we're using for the given mode, and sets the labels appropriately
    # Also sets the cannonical json to be used by the calculate function and checking for dealbreakers
    def setFile(self, mode, file, json):
        # if file is None:
        #     file = self.getFile(save=False, mode=mode)

        if mode == EVAL:
            self.selectedEvalFile = file
            self.selectedEvalJson = json
            self.evalFileLabel.setText(os.path.basename(file))
        elif mode == PREF:
            self.selectedPrefFile = file
            self.selectedPrefJson = json
            self.prefFileLabel.setText(os.path.basename(file))

        # This isn't up to date until loadFile, so don't call it here
        # self.fillLists()

    # Returns the applicable filename if we've already selected one, otherwise None
    def getSavedFilename(self, mode=None):
        if mode is None:
            mode = self.mode
        if mode == EVAL and self.selectedEvalFile is not None and self.selectedEvalFile != '':
            return self.selectedEvalFile
        elif mode == PREF and self.selectedPrefFile is not None and self.selectedPrefFile != '':
            return self.selectedPrefFile
        else:
            return None

    def save(self, mode=None):
        if mode is None:
            mode = self.mode

        # If we've already asked, don't ask again
        if (file := self.getSavedFilename(mode)) is None:
            # If there's no file provided or if there's nothing to save, nevermind
            if len(self.traitJson.keys()) > 1:
                file = self.getFile(save=True)
                if file == '' or file is None:
                    return
            else:
                return

        j = {}
        with open(file, 'w+') as savefile:
            for catagory, traits in self.traitJson.items():
                if catagory == "Options":
                    continue
                group = []
                for trait in traits:
                    group.append(Trait(*trait).toJSON())
                j[catagory] = group

            # Don't forget to update the cannonical saved jsons (for dealbreaker checking and the final calculation, which both require weights and modifiers)
            if mode == PREF:
                self.selectedPrefJson = j
                jsonc.dump({
                    "__type__": 'PREF',
                    "Tolerance": self.thresholdBox.value() / 100,
                    "Attributes": j,
                    "Settings": {
                        "max unknowns": self.maxUnknownsBox.value(),
                        "dealbreaker limit": self.dealbreakerLimitBox.value() / 100,
                    }
                }, savefile, indent=4)
                print(f'Saved {file}!')

            elif mode == EVAL:
                self.selectedEvalJson = j
                jsonc.dump({
                    '__type__': 'EVAL',
                    'Attributes': j
                }, savefile, indent=4)
                print(f'Saved {file}!')
            else:
                debug('unreachable state reached!', clr=-1)

    def loadFile(self, mode=None, file=None):
        if mode is None:
            mode = self.mode

        if file is None:
            file = self.getFile(save=False)
            if file == '' or file is None:
                debug(clr=-1)
                return

        with open(file, 'r') as f:
            if mode == PREF:
                try:
                    j = jsonc.load(f)
                    # We selected an eval file instead of a pref file
                    if j['__type__'] != 'PREF':
                        QMessageBox.critical(self, 'Wrong File Selected', 'It looks like you selected a file on a specific person, not a preferences file.')
                        todo('add optional autoconversion here')
                        return

                    self.thresholdBox.setValue(int(j["Tolerance"] * 100))
                    self.maxUnknownsBox.setValue(int(j["Settings"]["max unknowns"]))
                    self.dealbreakerLimitBox.setValue(int(j["Settings"]["dealbreaker limit"] * 100))
                    self.fillLists()
                    self.setFile(PREF, file, j['Attributes'])
                # The file is invalid
                except Exception as err:
                    debug(err, throw=True)
                    if __DEBUG__:
                            raise err
                    QMessageBox.critical(self, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return
            elif mode == EVAL:
                try:
                    j = jsonc.load(f)

                    # We've selected a pref file instead of an eval file
                    if j['__type__'] != 'EVAL':
                        QMessageBox.critical(self, 'Wrong File Selected', 'It looks like you selected a preferences file, not a file on a specific person.')
                        todo('add optional autoconversion here')
                        return

                    self.fillLists()
                    self.setFile(EVAL, file, j['Attributes'])
                # The file is invalid
                except Exception as err:
                        debug(err, stackTrace=True)
                        if __DEBUG__:
                            raise err
                        QMessageBox.critical(self, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                        return

        #* Fill the manual adding combo box
        self.groupSelector.clear()
        for catagory in self.traitJson.keys():
            self.groupSelector.addItem(catagory)
        # Manually set the combo box to start out on Misc.
        try:
            self.groupSelector.setCurrentIndex(self.groupSelector.findText('Misc'))
        except:
            pass

    def restoreDefaults(self):
        # Just so we never end up writing over the default preferences file
        shutil.copy(DEFAULT_PREFERENCES_FILE, COPIED_PREFERENCES_FILE)
        self.loadFile(file=COPIED_PREFERENCES_FILE, mode=PREF)

    @property
    def traitJson(self):
        if self.mode == EVAL:
            return self.selectedEvalJson
        elif self.mode == PREF:
            return self.selectedPrefJson
        else:
            unreachableState()

    @property
    def currentList(self):
       return self.traitJson[self.tabs.tabText(self.tabs.currentIndex())]

    @property
    def currentListWidget(self):
       return self.tabs.currentWidget()

    @property
    def currentTab(self):
       return self.tabs.tabText(self.tabs.currentIndex())

    @property
    def currentTrait(self):
        # This *should* always be true, but just in case...
        if len(self.traitJson[self.tabs.tabText(self.tabs.currentIndex())]) > self.index:
            return Trait(*self.traitJson[self.tabs.tabText(self.tabs.currentIndex())][self.index])
        else:
            debug('self.index is greater than the number of items in the current catagory of self.traitJson', clr=-1)
            debug(self.index)
            debug(self.traitJson[self.tabs.tabText(self.tabs.currentIndex())], 'current catagory')
    @currentTrait.setter
    def currentTrait(self, to):
        # This *should* always be true, but just in case...
        if len(self.traitJson[self.tabs.tabText(self.tabs.currentIndex())]) > self.index:
            self.traitJson[self.tabs.tabText(self.tabs.currentIndex())][self.index] = to.toJSON()
        else:
            debug('self.index is greater than the number of items in the current catagory of self.traitJson', clr=-1)

    def addGroup(self, name):
        # If it already exists, ignore it
        if name in self.traitJson.keys():
            return
        self.tabs.addTab(self._getNewListWidget(), name)
        self.traitJson[name] = []

    # Called when enter is pressed in questionBox
    def addAttribute(self):
        text = self.questionBox.text()
        if self.groupSelector.currentText() == '' or text == '':
            return

        # Just find the tab with the current text of the combo box, and insert the question text into that tab's list
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.groupSelector.currentText():
                self.tabs.widget(i).addItem(text)
                debug(f"Added {text} to {self.tabs.tabText(i)}!")
                break
        # And don't forget to add it to our internal map of lists and our interal json
        self.selectedPrefJson[self.groupSelector.currentText()].append(Trait(text).toJSON())
        self.selectedEvalJson[self.groupSelector.currentText()].append(Trait(text).toJSON())

        # Clear the box so it feels like something happened
        self.questionBox.clear()

        # Reload the lists so the question shows up
        # self.loadFile()
        self.fillLists()


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
