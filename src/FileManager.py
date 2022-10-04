import jstyleson as jsonc
import os
from PyQt6.QtWidgets import QApplication, QListWidget, QListView, QMessageBox, QAbstractButton
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QWidget, QDialogButtonBox, QSlider
from os.path import dirname, join, basename
import shutil
from Cope import debug, todo
from Singleton import *
from Trait import NOT_ANSWERED, ANSWERED, SKIPPED

class FileManager:
    def __init__(self, saveFolder, parent=None):
        self.prefFile = None
        self.prefJson = None
        self.evalFile = None
        self.evalJson = None
        self.saves = saveFolder
        self.parent = parent

    def getFile(self, save=True, mode=None):
        """ Promts the user for a filepath """
        if mode is None:
            mode = Singleton.mode

        fileType = '*.pref' if mode == PREF else '*.eval'

        if save:
            todo('figure out how to have default suggested filenames')
            file = QFileDialog.getSaveFileName(self.parent,
                    caption=f'Save your personal preferences file'
                            if mode == PREF else
                            'Save your responses about the person you\'re considering',
                    filter=fileType,
                    initialFilter=fileType
                )[0]
        else:
            file = QFileDialog.getOpenFileName(self.parent,
                caption=f'Open your personal preferences file'
                        if mode == PREF else
                        'Open a file you saved on someone',
                filter=fileType,
                initialFilter=fileType
            )[0]

        if file != '' and file is not None:
            if not file.endswith(fileType[1:]):
                file = file + fileType[1:]
            # self.setFile(mode, file)

        return file

        # if Singleton.mode == PREF:
        #     name = f'{self.name}{"p" if self.name == "" else "P"}references.json'
        # elif Singleton.mode == EVAL:
        #     name = f'{self.name}{"a" if self.name == "" else "A"}ttributes.json'

    def setFile(self, mode, file, json):
        """ Sets a given file to be the cannonical file that we're using for the given mode, and sets the labels appropriately
            Also sets the cannonical json to be used by the calculate function and checking for dealbreakers """
        # if file is None:
        #     file = self.getFile(save=False, mode=mode)

        if mode == EVAL:
            self.evalFile = file
            self.evalJson = json
            # It's easiest just to do this here
            self.parent.evalFileLabel.setText(os.path.basename(file))
        elif mode == PREF:
            self.prefFile = file
            self.prefJson = json
            self.parent.prefFileLabel.setText(os.path.basename(file))

        # This isn't up to date until loadFile, so don't call it here
        # self.fillLists()

    def getSavedFilename(self, mode=None):
        """ Returns the applicable filename if we've already selected one, otherwise None """
        if mode is None:
            mode = Singleton.mode
        if mode == EVAL and self.evalFile is not None and self.evalFile != '':
            return self.evalFile
        elif mode == PREF and self.prefFile is not None and self.prefFile != '':
            return self.prefFile
        else:
            return None

    def save(self, json, mode, tolerance, maxUnknowns, dealbreakerLimit):
        # If we've already asked, don't ask again
        if (file := self.getSavedFilename(mode)) is None:
            return

        with open(file, 'w') as f:
            # Don't forget to update the cannonical saved jsons (for dealbreaker checking and the final calculation, which both require weights and modifiers)
            if mode == PREF:
                self.prefJson = json
                jsonc.dump({
                    "__type__": 'PREF',
                    "Tolerance": tolerance,
                    "Attributes": json,
                    "Settings": {
                        "max unknowns": maxUnknowns,
                        "dealbreaker limit": dealbreakerLimit,
                    }
                }, f, indent=4)
                print(f'Saved {file}!')

            elif mode == EVAL:
                self.evalJson = json
                jsonc.dump({
                    '__type__': 'EVAL',
                    'Attributes': json
                }, f, indent=4)
                print(f'Saved {file}!')
            else:
                debug('unreachable state reached!', clr=-1)

    def load(self, mode=None, file=None):
        if mode is None:
            mode = Singleton.mode

        if file is None:
            file = self.getFile(save=False, mode=mode)
            if file == '' or file is None:
                debug(clr=-1)
                return (None,)*4

        # Dont touch the boilerplate file!
        if file == Singleton.DEFAULT_PREFERENCES_FILE:
            copy = Singleton.saves / (Singleton.DEFAULT_PREFERENCES_FILE.stem + '-copy.pref')
            shutil.copy(Singleton.DEFAULT_PREFERENCES_FILE, copy)
            file = copy

        with open(file, 'r') as f:
            if mode == PREF:
                try:
                    j = jsonc.load(f)
                    # We selected an eval file instead of a pref file
                    if j['__type__'] != 'PREF':
                        QMessageBox.critical(self.parent, 'Wrong File Selected', 'It looks like you selected a file on a specific person, not a preferences file.')
                        todo('add optional autoconversion here')
                        return (None,)*4

                    tolerance = float(j["Tolerance"])
                    maxUnknowns = float(j["Settings"]["max unknowns"])
                    dealbreakerLimit = float(j["Settings"]["dealbreaker limit"])
                    json = j['Attributes']
                    self.setFile(PREF, file, json)
                # The file is invalid
                except Exception as err:
                    debug(err, throw=True)
                    if Singleton.debugging:
                            raise err
                    QMessageBox.critical(self.parent, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return (None,)*4
            elif mode == EVAL:
                try:
                    j = jsonc.load(f)

                    # We've selected a pref file instead of an eval file
                    if j['__type__'] != 'EVAL':
                        QMessageBox.critical(self.parent, 'Wrong File Selected', 'It looks like you selected a preferences file, not a file on a specific person.')
                        todo('add optional autoconversion here')
                        return (None,)*4

                    tolerance = None
                    maxUnknowns = None
                    dealbreakerLimit = None
                    json = j['Attributes']
                    self.setFile(EVAL, file, json)
                # The file is invalid
                except Exception as err:
                        debug(err, stackTrace=True)
                        if Singleton.debugging:
                            raise err
                        QMessageBox.critical(self.parent, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                        return (None,)*4

        return json, tolerance, maxUnknowns, dealbreakerLimit

    def _convertFileMode(self, file, toMode):
        """ Take the given file, and converts it from the mode it's currently in to 'to'
            Losses all the state and value data, just keeps the questions
            If going from pref -> eval, it also drops the skipped questions, but not vice versa """
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
                    # This is bad practice. Right here I *should* take parameters for these instead. But I'm lazy
                    toJson["Tolerance"] = self.parent.thresholdBox.value()
                    toJson["Settings"]["max unknowns"] = self.parent.maxUnknownsBox.value()
                    toJson["Settings"]["dealbreaker limit"] = self.parent.dealbreakerLimitBox.value()
                    toJson['Attributes'] = stripData(fromJson['Attributes'], PREF)
                    # nameAddOn = ' - preferences'
                # The file is invalid
                except Exception as err:
                    debug(err, stackTrace=True)
                    QMessageBox.critical(self.parent, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return file

            # We're going from pref -> eval
            elif toMode == EVAL:
                try:
                    toJson['__type__'] = 'EVAL'
                    toJson['Attributes'] = stripData(fromJson['Attributes'], EVAL)
                    # nameAddOn = ' - evaluation'
                # The file is invalid
                except Exception as err:
                    debug(err, stackTrace=True)
                    QMessageBox.critical(self.parent, 'Invalid File', 'It looks like the file you selected has an invalid format.')
                    return file
            else:
                debug('Impossible state reached', color=-1)

        newFilename = join(dirname(file), basename(file).split('.')[0] + '.' + ('pref' if toMode == PREF else 'eval'))
        with open(newFilename, 'w+') as toFile:
            # debug(toJson, f'writing to file {newFilename}')
            jsonc.dump(toJson, toFile, indent=4)

        return newFilename
