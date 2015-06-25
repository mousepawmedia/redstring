#!/usr/bin/python

###############################################################################
# Redstring 2.0
# by Jason C. McDonald
# MousePaw Labs
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import os
from gi.repository import Gtk, GObject
from multiprocessing.pool import ThreadPool
import os.path
import xml.etree.ElementTree as xml

#These are some global variables we use for compile progress iteration.
maximum = 1
stepAccum = 0

#These are for all pre-final combinations.
preMaximum = 1
preStepAccum = 0

killswitch = False

#Save path for project document.
project_path = ""

#Are there changes to the project pending?
changes_pending = False

#This is the global result array.
results = []


#Calculate the number of results.
def calculateCompile(buffers):
    global maximum
    global preMaximum

    #Start out with count 1 (so it doesn't mess up multiplcation...)
    count = 1
    preCount = 0

    #Multiply all the buffer counts by each other.
    for i in buffers:
        length = len(i)
        if(length > 1):
            count *= length
            preCount += count

    #Remove last iteration (those aren't pre-steps)
    preCount -= count

    if count is 0:
        count = 1

    if preCount is 0:
        preCount = 1

    #Write out to global variables.
    maximum = count
    preMaximum = preCount


###############################################################################
# Repeating Code
###############################################################################


def mainLoop():
    #Make sure the window title represents open file.
    setTitle(project_path)

    #Update maximums.
    buffers = importAllBuffers()
    calculateCompile(buffers)

    #Show maximum in status bar. (Use msgID 1)
    updateStatus(str(maximum) + " combinations.", 1)

    return True


###############################################################################
# Buffer Undo/Redo
###############################################################################

#Undo/Redo History Variables
historyIndex = 0
historyBuffers = []


def resetHistory():
    global historyIndex, historyBuffers

    historyIndex = 0
    historyBuffers = []
    beginEditBuffer()
    updateUndoRedoButtons()


#We need to wipe out everything after the current position if we Undo and edit.
def finalizeUndo():
    global historyIndex, historyBuffers

    if (historyIndex < len(historyBuffers) - 1):
        historyBuffers = historyBuffers[:historyIndex]


#When a buffer is edited, take a history snapshot.
def beginEditBuffer(widget=None):
    global historyIndex, historyBuffers

    #Import the buffers
    oldData = importAllBuffers()

    #If the widget is defined (actual edit), finalize earlier undos.
    if widget is not None:
        finalizeUndo()

    #If there are previous snapshots...
    if len(historyBuffers) > 0:
        #AND if the current data does not match the last snapshot.
        if oldData is not historyBuffers[len(historyBuffers) - 1]:
            #Take snapshot of buffers.
            historyBuffers.append(oldData)
            #Update snapshot number to latest.
            historyIndex = len(historyBuffers) - 1
    #If there were no previous snapshots...
    else:
        #Take the first snapshot.
        historyBuffers.append(oldData)
        #Update snapshot number to latest (0, really)
        historyIndex = len(historyBuffers) - 1


def endEditBuffer(widget):
    #We only need to update undo/redo depending on edits.
    updateUndoRedoButtons()


#Undo changes using snapshots.
def undo(self=None):
    global historyIndex, historyBuffers

    #If we haven't yet taken the latest snapshot...
    if (historyIndex == len(historyBuffers) - 1):
        #Take the snapshot.
        beginEditBuffer()

    #If the history index is greater than 0 (otherwise, we stay at 0)
    if (historyIndex > 0):
        #Back up one snapshot.
        historyIndex -= 1

    #Load selected snapshot into GUI.
    updateGUIBuffers(historyBuffers[historyIndex])

    #Update relevant buttons.
    updateUndoRedoButtons()


#Redo changes using snapshots.
def redo(self=None):
    global historyIndex, historyBuffers

    #If the history index is less than the max...
    if (historyIndex < len(historyBuffers) - 1):
        #There is something to restore. Step forward.
        historyIndex += 1

    #Load selected snapshot into GUI.
    updateGUIBuffers(historyBuffers[historyIndex])

    #Update relevant buttons.
    updateUndoRedoButtons()


#Returns True if we have something to undo, False otherwise.
def canUndo():
    global historyIndex, historyBuffers

    if (historyIndex == 0):
        return False
    else:
        return True


#Returns True if we have something to undo, False otherwise.
def canRedo():
    global historyIndex, historyBuffers

    if (historyIndex == len(historyBuffers) - 1):
        return False
    else:
        return True


def updateUndoRedoButtons():
    #Load the undo button.
    btnUndo = builder.get_object("btnUndo")
    miUndo = builder.get_object("miUndo")
    #Disable/Enable depending on whether we can undo.
    btnUndo.set_sensitive(canUndo())
    miUndo.set_sensitive(canUndo())

    #Load the redo button.
    btnRedo = builder.get_object("btnRedo")
    miRedo = builder.get_object("miRedo")
    #Disable/Enable depending on whether we can undo.
    btnRedo.set_sensitive(canRedo())
    miRedo.set_sensitive(canRedo())


###############################################################################
# Compiler GUI
###############################################################################


def updateProgressPre():
    global maximum

    #Update the label to show how many results we WILL have.
    lblProgress = builder.get_object("lblProgress")
    strProgress = "Ready to compile " + str(maximum) + " combinations."
    lblProgress.set_text(strProgress)

    #Reset the progress bars.
    barProgress = builder.get_object("barProgress")
    barProgressMaster = builder.get_object("barProgressMaster")
    barProgress.set_fraction(0)
    barProgressMaster.set_fraction(0)

    #Show only the Close and Run buttons.
    btnCancelCompile = builder.get_object("btnCancelCompile")
    btnCloseCompile = builder.get_object("btnCloseCompile")
    btnRunCompile = builder.get_object("btnRunCompile")
    btnViewResults = builder.get_object("btnViewResults")

    btnCancelCompile.hide()
    btnCloseCompile.show()
    btnRunCompile.show()
    btnViewResults.hide()


#Update progress screen.
def updateProgress():
    global stepAccum
    global maximum

    global preStepAccum
    global preMaximum

    #Get interface items.
    lblProgress = builder.get_object("lblProgress")
    barProgress = builder.get_object("barProgress")
    barProgressMaster = builder.get_object("barProgressMaster")

    superStep = stepAccum + preStepAccum
    superMaximum = maximum + preMaximum

    #If we're still on step 0, we're on pre-steps
    if (stepAccum is 0):
        strProgress = "Preparing to write. (Step " + str(preStepAccum) + \
            " of " + str(preMaximum) + ".)"
        lblProgress.set_text(strProgress)
        barProgress.pulse()

        #Calculate pre-step percentage
        prePercentage = float(preStepAccum) / float(preMaximum)

        #Update the progress bar.
        barProgress.set_fraction(prePercentage)

    #Otherwise, update progress.
    else:
        #Update the progress text label with index and maximum.
        strProgress = "Writing combination " + str(stepAccum) + \
            " of " + str(maximum) + "."
        lblProgress.set_text(strProgress)

        #Calculate step percentage
        percentage = float(stepAccum) / float(maximum)

        #Update the progress bar.
        barProgress.set_fraction(percentage)

    #Update the master progress bar.
    if (superMaximum == 0):
        superMaximum = 1

    superPercentage = float(superStep) / float(superMaximum)
    barProgressMaster.set_fraction(superPercentage)


#Update progress screen so it says it is done.
def updateProgressDone():
    #Update the progress text label.
    lblProgress = builder.get_object("lblProgress")
    strProgress = "Compile Done!"
    lblProgress.set_text(strProgress)

    #Update the progress bars.
    barProgress = builder.get_object("barProgress")
    barProgressMaster = builder.get_object("barProgressMaster")
    barProgress.set_fraction(1)
    barProgressMaster.set_fraction(1)

    #Show only the Close and View buttons.
    btnCancelCompile = builder.get_object("btnCancelCompile")
    btnCloseCompile = builder.get_object("btnCloseCompile")
    btnRunCompile = builder.get_object("btnRunCompile")
    btnViewResults = builder.get_object("btnViewResults")

    btnCancelCompile.hide()
    btnCloseCompile.show()
    btnRunCompile.hide()
    btnViewResults.show()


def showCompileWindow(self):
    #Show window
    compileWindow = builder.get_object("compilingWindow")
    compileWindow.show_all()

    #Import buffer list.
    buffers = importAllBuffers()

    #Figure out how many combinations we'll get. (Updates maximum)
    calculateCompile(buffers)

    #Show maximum on the compile window.
    updateProgressPre()


def closeCompileWindow(self, widget=None):
    #This should override the close function of the compile window.
    compileWindow = builder.get_object("compilingWindow")

    #We only want to hide it instead.
    compileWindow.hide()

    #Return true, because we handled the event, so Gtk need not to.
    return True


###############################################################################
# Compilation Functions
###############################################################################


def compileStep(model, cue, sub):
    model = model.replace(cue, sub)
    return model


def compileModel(model, buffers):
    global stepAccum
    global preStepAccum

    #Define list of output strings.
    subOutput = []
    pool = ThreadPool(processes=1)

    #Define cues.
    cues = ["{A}", "{B}", "{C}", "{D}", "{E}", "{F}", "{G}", "{H}"]

    #Park the model in the output array initially.
    subOutput = [model]

    #Set up templist for holding pre-revised output array on each iteration.
    templist = []

    #For each buffer (0-8)
    for i in range(0, 8):
        #We shouldn't loop through empty buffers.
        #It messes up our progress counts.
        if ((len(buffers[i]) is 1) and (buffers[i][0] is "") or
            (len(buffers[i]) is 0)):
                continue
        else:
            #Make a copy of the output array, and then clear output.
            templist = subOutput
            subOutput = []

            #For each string in buffers...
            for s in buffers[i]:
                #And for each item in the array.
                for m in templist:
                    #Grab one string from the array.
                    temp = m

                    #If we hit a killswitch, stop everything.
                    if killswitch:
                        return

                    #Run the compile step async.
                    async_result = pool.apply_async(compileStep, (temp,
                        cues[i], s))

                    #Update the progress screen.
                    updateProgress()

                    #Ask Gtk to update itself...but only once to avoid lag.
                    if Gtk.events_pending():
                        Gtk.main_iteration()

                    #Get those async results that were baking...
                    temp = async_result.get()

                    #If the string (temp) is done cooking (no cues)...
                    #...add one step.
                    if temp.find("{") is -1:
                        stepAccum += 1
                    #If the string is still cooking (has cues)...
                    #...add one pre step.
                    else:
                        preStepAccum += 1

                    #Add string to the output array.
                    subOutput += [temp]
    return subOutput


def runCompile(self):
    global stepAccum
    global preStepAccum
    global killswitch
    global results

    #Hide all buttons except cancel.
    btnCancelCompile = builder.get_object("btnCancelCompile")
    btnCloseCompile = builder.get_object("btnCloseCompile")
    btnRunCompile = builder.get_object("btnRunCompile")
    btnViewResults = builder.get_object("btnViewResults")

    btnCancelCompile.show()
    btnCloseCompile.hide()
    btnRunCompile.hide()
    btnViewResults.hide()

    #Reset step accumulators.
    preStepAccum = 0
    stepAccum = 0

    #Import buffer list.
    buffers = importAllBuffers()
    output = []

    #Run substitution on each model.
    for model in buffers[0]:
        batch = compileModel(model, buffers[1:])

        #If we triggered the killswitch, stop everything.
        #Otherwise, s'all good.
        if not killswitch:
            output += batch
        elif killswitch:
            output = []

    #If the killswitch was thrown, revert back to inital window state...
    #...and reset killswitch.
    if killswitch:
        updateProgressPre()
        killswitch = False
    #Otherwise, s'all good.
    else:
        updateProgressDone()
        #Store the results directly.
        results = output


def killCompile(self):
    #Throw the killswitch.
    global killswitch
    killswitch = True


#Import all the buffers from the GUI as parsed lists.
def importAllBuffers():
    #Import the text buffer from the GUI
    bufferA = builder.get_object("bufferColA")
    #Convert the text buffer to a string.
    txtColA = bufferA.get_text(bufferA.get_start_iter(),
         bufferA.get_end_iter(), True)
    #Parse the string into an array, splitting by new line.
    arrColA = txtColA.split("\n")

    bufferB = builder.get_object("bufferColB")
    txtColB = bufferB.get_text(bufferB.get_start_iter(),
         bufferB.get_end_iter(), True)
    arrColB = txtColB.split("\n")

    bufferC = builder.get_object("bufferColC")
    txtColC = bufferC.get_text(bufferC.get_start_iter(),
         bufferC.get_end_iter(), True)
    arrColC = txtColC.split("\n")

    bufferD = builder.get_object("bufferColD")
    txtColD = bufferD.get_text(bufferD.get_start_iter(),
         bufferD.get_end_iter(), True)
    arrColD = txtColD.split("\n")

    bufferE = builder.get_object("bufferColE")
    txtColE = bufferE.get_text(bufferE.get_start_iter(),
         bufferE.get_end_iter(), True)
    arrColE = txtColE.split("\n")

    bufferF = builder.get_object("bufferColF")
    txtColF = bufferF.get_text(bufferF.get_start_iter(),
         bufferF.get_end_iter(), True)
    arrColF = txtColF.split("\n")

    bufferG = builder.get_object("bufferColG")
    txtColG = bufferG.get_text(bufferG.get_start_iter(),
         bufferG.get_end_iter(), True)
    arrColG = txtColG.split("\n")

    bufferH = builder.get_object("bufferColH")
    txtColH = bufferH.get_text(bufferH.get_start_iter(),
         bufferH.get_end_iter(), True)
    arrColH = txtColH.split("\n")

    bufferModels = builder.get_object("bufferModels")
    txtModels = bufferModels.get_text(bufferModels.get_start_iter(),
         bufferModels.get_end_iter(), True)
    arrModels = txtModels.split("\n")

    #Return a list (array) of all the lists, in order. Models first!
    return[arrModels, arrColA, arrColB, arrColC, arrColD, arrColE, arrColF,
        arrColG, arrColH]


def updateGUIBuffers(buffers):
    #Convert the buffer array to a string.
    str1 = ""
    str2 = ""
    str3 = ""
    str4 = ""
    str5 = ""
    str6 = ""
    str7 = ""
    str8 = ""
    mdl = ""

    for i in range(1, 8):
        for s in buffers[i]:

            #If it is none, convert to an empty string
            if s is None:
                s = ""
            else:
                #Otherwise, add a newline to the end.
                s += "\n"

            if i is 1:
                str1 += s
            elif i is 2:
                str2 += s
            elif i is 3:
                str3 += s
            elif i is 4:
                str4 += s
            elif i is 5:
                str5 += s
            elif i is 6:
                str6 += s
            elif i is 7:
                str7 += s
            elif i is 8:
                str8 += s

    for m in buffers[0]:
        if m is None:
                m = ""
        else:
            #Otherwise, add a newline to the end.
            m += "\n"
        mdl += m

    #Import the text buffer from the GUI
    bufferA = builder.get_object("bufferColA")
    #Remove last character, being a trailing \n
    str1 = str1[0:-1]
    #Move the data to the buffer.
    bufferA.set_text(str1)

    bufferB = builder.get_object("bufferColB")
    #Remove last character, being a trailing \n
    str2 = str2[0:-1]
    bufferB.set_text(str2)

    bufferC = builder.get_object("bufferColC")
    str3 = str3[0:-1]
    bufferC.set_text(str3)

    bufferD = builder.get_object("bufferColD")
    str4 = str4[0:-1]
    bufferD.set_text(str4)

    bufferE = builder.get_object("bufferColE")
    str5 = str5[0:-1]
    bufferE.set_text(str5)

    bufferF = builder.get_object("bufferColF")
    str6 = str6[0:-1]
    bufferF.set_text(str6)

    bufferG = builder.get_object("bufferColG")
    str7 = str7[0:-1]
    bufferG.set_text(str7)

    bufferH = builder.get_object("bufferColH")
    str8 = str8[0:-1]
    bufferH.set_text(str8)

    bufferModels = builder.get_object("bufferModels")
    bufferModels.set_text(mdl)


def clearBuffers():
    #Create empty buffers.

    #Get GUI buffer object.
    bufferA = builder.get_object("bufferColA")
    #Empty the buffer.
    bufferA.set_text("")

    bufferB = builder.get_object("bufferColB")
    bufferB.set_text("")

    bufferC = builder.get_object("bufferColC")
    bufferC.set_text("")

    bufferD = builder.get_object("bufferColD")
    bufferD.set_text("")

    bufferE = builder.get_object("bufferColE")
    bufferE.set_text("")

    bufferF = builder.get_object("bufferColF")
    bufferF.set_text("")

    bufferG = builder.get_object("bufferColG")
    bufferG.set_text("")

    bufferH = builder.get_object("bufferColH")
    bufferH.set_text("")

    bufferModels = builder.get_object("bufferModels")
    bufferModels.set_text("")


###############################################################################
# Results Screen GUI
###############################################################################


def showResultsWindow(self):
    global results

    #Show window
    resultsWindow = builder.get_object("resultsWindow")
    resultsWindow.show_all()

    #Create results string.
    strResults = ""
    for s in results:
        temp = s + "\n"
        strResults += temp

    #Update contents
    bufferResults = builder.get_object("txtResults")
    bufferResults.get_buffer().set_text(strResults)


def copyResults(self, widget=None):
    bufferResults = builder.get_object("txtResults")
    #Select everything...
    bufferResults.emit("select-all", True)
    #And copy it to the system clipboard!
    bufferResults.emit("copy-clipboard")
    updateStatus("Copied to clipboard!")


def selectResults(self, widget=None):
    bufferResults = builder.get_object("txtResults")
    #Select everything.
    bufferResults.emit("select-all", True)


def exportResults(self, widget=None):
    bufferResults = builder.get_object("bufferResults")
    dlgFileChoose = builder.get_object("dlgFileChoose")
    dlgAsk = builder.get_object("dlgQuestion")
    lblAsk = builder.get_object("lblQuestion")

    txtFilter = Gtk.FileFilter()
    txtFilter.set_name("Text Files")
    txtFilter.add_pattern("*.txt")
    txtFilter.add_mime_type("text/plain")
    dlgFileChoose.add_filter(txtFilter)

    allFilter = Gtk.FileFilter()
    allFilter.set_name("All Files")
    allFilter.add_pattern("*")
    dlgFileChoose.add_filter(allFilter)

    #Run file chooser dialog.
    response = dlgFileChoose.run()

    #If cancelled.
    if response is 0:
        #Hide box and do nothing.
        dlgFileChoose.hide()

    #If a file path was provided.
    elif response is 1:
        #Get file name.
        filename = dlgFileChoose.get_filename()

        #Prepare for write.
        text = bufferResults.get_text(bufferResults.get_start_iter(),
            bufferResults.get_end_iter(), True)

        #Check if path exists. If it does...
        if os.path.exists(filename):
            #Confirm overwrite.
            lblAsk.set_text("Are you sure you want to overwrite "
                + filename + "?")
            confirm = dlgAsk.run()
            if confirm is 1:
                #If overwrite confirmed, write out.
                with open(filename, 'w') as f:
                    f.write(text)
                    updateStatus("Results exported.")
                f.close()
            #Hide confirm dialog.
            dlgAsk.hide()
        #If the file doesn't yet exist...
        else:
            #Create it.
            with open(filename, 'w') as f:
                f.write(text)
                updateStatus("Results exported.")
            f.close()

        #Hide file chooser box.
        dlgFileChoose.hide()

        #Aaaaand, we're done exporting! Hooray!


def closeResultsWindow(self, widget=None):
    #This should override the close function of the compile window.
    resultsWindow = builder.get_object("resultsWindow")

    #We only want to hide it instead.
    resultsWindow.hide()

    #Return true, because we handled the event, so Gtk need not to.
    return True


###############################################################################
# Project Save
###############################################################################


def changesPending():
    #Determine if changes are pending.
    global project_path

    #Compare parseProject() to file contents.
    guibuffers = importAllBuffers()
    filebuffers = loadBuffersFromProject(project_path)

    #Empty buffers for comparison.
    empty = [[''], [''], [''], [''], [''], [''], [''], [''], ['']]

    if (guibuffers == filebuffers):
        #We're good! No changes pending.
        r = False
    elif (project_path is "") and (guibuffers == empty):
        #Empty project, nothing to do.
        r = False
    else:
        #Changes are pending.
        r = True

    return r


def loadBuffersFromProject(project_path):
    buffers = []
    arr = []

    if project_path is '':
        #Empty project path. Just return empty buffers.
        return buffers

    if project_path is None:
        #Can't open a nonexistent path. Just return empty buffers.
        return buffers

    #If we can open the thing..
    with open(project_path, 'r') as f:
        #Run our parsing code. Note we don't bother with f.
        tree = xml.parse(project_path)
        red = tree.getroot()
        arr = []
        for m in red[8]:
            if (m.text is not None):
                arr.append(m.text)
        buffers.append(arr)

        for i in range(1, 8):
            arr = []
            for l in red[i - 1]:
                if (l.text is not None):
                    arr.append(l.text)
            buffers.append(arr)
    #Close the file anyway.
    f.close()
    return buffers


#Define a new project (xml)
def parseProject():
    buffers = importAllBuffers()

    #These should be saved as .RED files.
    red = xml.Element("red")

    #Define buffer subelements.
    #lint:disable
    b1 = xml.SubElement(red, "b1")
    b2 = xml.SubElement(red, "b2")
    b3 = xml.SubElement(red, "b3")
    b4 = xml.SubElement(red, "b4")
    b5 = xml.SubElement(red, "b5")
    b6 = xml.SubElement(red, "b6")
    b7 = xml.SubElement(red, "b7")
    b8 = xml.SubElement(red, "b8")
    mdl = xml.SubElement(red, "mdl")
    #lint:enable

    #Store the buffers in their respective nodes, using <s> tags.
    for i in range(1, 8):
        for item in buffers[i]:
            #To save time and space, we eval using b and the i (b1, b2, etc.)
            s = xml.SubElement(eval("b" + str(i)), "s")
            s.text = item

    #Store the models.
    for model in buffers[0]:
        m = xml.SubElement(mdl, "m")
        m.text = model

    #Create XML tree string to write out.
    fileOutput = xml.tostring(red, encoding='utf8', method='xml')
    return fileOutput


def chooseOpenPath():
    #Get a new save path (i.e. New, Save As...)

    dlgFileOpen = builder.get_object("dlgFileOpen")

    redFilter = Gtk.FileFilter()
    redFilter.set_name("Redstring Projects")
    redFilter.add_pattern("*.red")
    redFilter.add_mime_type("application/xml")
    dlgFileOpen.add_filter(redFilter)

    #Run file chooser dialog.
    response = dlgFileOpen.run()

    #Variable for return.
    path = ""

    #If cancelled.
    if response is 0:
        #Hide box and do nothing.
        dlgFileOpen.hide()

    #If a file path was provided.
    elif response is 1:
        #Get file name.
        filename = dlgFileOpen.get_filename()

        #Check if path exists. If it does...
        if os.path.exists(filename):
            #We're good! Use this path.
            path = filename
        #If the file doesn't exist...
        else:
            #Something's wrong, Dave. Return empty.
            path = ""

        #Hide file chooser box.
        dlgFileOpen.hide()

    return path


def chooseSavePath():
    #Get a new save path (i.e. New, Save As...)

    dlgFileChoose = builder.get_object("dlgFileChoose")
    dlgAsk = builder.get_object("dlgQuestion")
    lblAsk = builder.get_object("lblQuestion")

    redFilter = Gtk.FileFilter()
    redFilter.set_name("Redstring Projects")
    redFilter.add_pattern("*.red")
    redFilter.add_mime_type("application/xml")
    dlgFileChoose.add_filter(redFilter)

    allFilter = Gtk.FileFilter()
    allFilter.set_name("All Files")
    allFilter.add_pattern("*")
    dlgFileChoose.add_filter(allFilter)

    #Variable for return.
    path = ""

    while(path is ""):
        #Run file chooser dialog.
        response = dlgFileChoose.run()

        #If cancelled.
        if response is 0:
            #Hide box and do nothing.
            dlgFileChoose.hide()
            return

        #If a file path was provided.
        elif response is 1:
            #Get file name.
            filename = dlgFileChoose.get_filename()

            #Check if path exists. If it does...
            if os.path.exists(filename):
                #Confirm overwrite.
                lblAsk.set_text("Are you sure you want to overwrite "
                    + filename + "?")
                confirm = dlgAsk.run()

                if confirm is 1:
                    #Set return to string.
                    path = filename
                else:
                    #We will be rerunning. Ensure path is empty.
                    path = ""

                #Hide confirm dialog.
                dlgAsk.hide()

            #If the file doesn't yet exist...
            else:
                #Set return to string.
                path = filename

    #Hide file chooser box.
    dlgFileChoose.hide()

    return path


#SIDE NOTE: Close and new really do the same thing.
def newProject(self=None):
    #Get open path.
    global project_path

    pending = changesPending()
    if pending:
        #Prompt to save.
        #dlgAsk = builder.get_object("dlgQuestion")
        #lblAsk = builder.get_object("lblQuestion")
        #lblAsk.set_text("Do you want to save your changes?")
        #confirm = dlgAsk.run()

        confirm = displayDialog("Question", "Do you want to save your changes?",
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO)

        #Hide confirm dialog.
        #dlgAsk.hide()

        if confirm == Gtk.ResponseType.YES:
            #Save project.
            saved = saveProject()
            if saved is False:
                return

    #Clear project path.
    project_path = ""
    #Clear project data (buffers)
    clearBuffers()
    #Set window title.
    setTitle()
    #Reset undo history.
    resetHistory()


def openProject(self=None):
    #Get open path.
    global project_path
    empty = []

    pending = changesPending()
    if pending:
        #Prompt to save.
        #dlgAsk = builder.get_object("dlgQuestion")
        #lblAsk = builder.get_object("lblQuestion")

        confirm = displayDialog("Question", "Do you want to save your changes?",
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO)

        #Hide confirm dialog.
        #dlgAsk.hide()

        if confirm == Gtk.ResponseType.YES:
            #Save project.
            saved = saveProject()
            if saved is False:
                return

    #Ask for new path.
    path = chooseOpenPath()
    project_path = path
    #Set window title.
    setTitle(project_path)
    #Load buffers in from the project.
    buffers = loadBuffersFromProject(path)
    #If we didn't just get an empty buffer set...
    if (buffers != empty):
        #Update the GUI with new buffers.
        updateGUIBuffers(buffers)
        #Reset undo history.
        resetHistory()


def saveProject(self=None):
    global project_path

    #Return value (True if save is successful)
    r = False

    #If a path is not already defined...
    if project_path is "":
        project_path = chooseSavePath()

    #We make sure something was returned...
    if project_path is not "":
        #Prepare for write.
        fileOutput = parseProject()

        #Write out to file.
        with open(project_path, 'w') as f:
            f.write(fileOutput)
            updateStatus("Project saved!")
            #Set window title.
            setTitle(project_path)
            r = True
        #Close the file.
        f.close()

    return r


def saveProjectAs(self=None):
    global project_path

    #Return value (True if save is successful)
    r = False

    path = chooseSavePath()
    #We make sure something was returned...
    if project_path is not "":
        #Prepare for write.
        fileOutput = parseProject()
        #Write out to existing file.
        with open(project_path, 'w') as f:
            f.write(fileOutput)
            updateStatus("Project saved!")
            #S'all good. Save project path.
            project_path = path
            #Set window title.
            setTitle(project_path)
            r = True
        #Close the file.
        f.close()

    return r

#SIDE NOTE: Close and New really do the same thing. Look at New.


###############################################################################
# Status Bar
###############################################################################


def updateStatus(text="", msgID=0):
    #Update the status bar with the given message.
    statusBar = builder.get_object("statusbar")
    statusBar.push(msgID, text)

    #If the msgID is anything but 1 (compile estimation message)
    if msgID is not 1:
        #Clear the status bar after 3 seconds.
        GObject.timeout_add(3000, clearStatus, msgID)
        #threading.Timer(3.0, clearStatus, [msgID]).start()
    #Otherwise, never "clear" properly.


def clearStatus(msgID):
    statusBar = builder.get_object("statusbar")
    statusBar.pop(msgID)
    return False


###############################################################################
# Dialog Box
###############################################################################

def displayDialog(msg, subMsg="", messageType=Gtk.MessageType.INFO,
    buttonsType=Gtk.ButtonsType.OK, affirmIsDestruc=False):

    md = Gtk.MessageDialog(window,
        0,
        messageType,
        Gtk.ButtonsType.NONE,
        msg)
    if subMsg is not "":
        md.format_secondary_text(subMsg)

    #OVERRIDE BUTTON DEFAULTS TO BE GNOME HIG COMPLIANT.

    #Basic button types...
    if buttonsType is Gtk.ButtonsType.OK:
        md.add_button("OK", Gtk.ResponseType.OK)
    elif buttonsType is Gtk.ButtonsType.CLOSE:
        md.add_button("Close", Gtk.ResponseType.CLOSE)
    elif buttonsType is Gtk.ButtonsType.CANCEL:
        md.add_button("Cancel", Gtk.ResponseType.CANCEL)
    #YES/NO
    elif buttonsType is Gtk.ButtonsType.YES_NO and affirmIsDestruc is False:
        md.add_button("Yes", Gtk.ResponseType.YES)
        md.add_button("No", Gtk.ResponseType.NO)
    elif buttonsType is Gtk.ButtonsType.YES_NO and affirmIsDestruc is True:
        md.add_button("No", Gtk.ResponseType.NO)
        md.add_button("Yes", Gtk.ResponseType.YES)
    #OK/CANCEL
    elif buttonsType is Gtk.ButtonsType.OK_CANCEL and affirmIsDestruc is False:
        md.add_button("OK", Gtk.ResponseType.OK)
        md.add_button("Cancel", Gtk.ResponseType.CANCEL)
    elif buttonsType is Gtk.ButtonsType.OK_CANCEL and affirmIsDestruc is True:
        md.add_button("Cancel", Gtk.ResponseType.CANCEL)
        md.add_button("OK", Gtk.ResponseType.OK)

    response = md.run()
    md.destroy()

    return response


###############################################################################
# Other GUI Stuff
###############################################################################


def setTitle(text=""):
    window = builder.get_object("mainWindow")
    #Give title its default value.
    title = "Redstring 2.0"
    #If we got some text as an argument.
    if text is not "":
        #Add working path (or other message).
        title += " (" + str(text) + ")"
        #Set window title to title string.
        window.set_title(title)


def showAbout(widget):
    dlgAbout = builder.get_object("dlgAbout")
    response = dlgAbout.run()

    #Standard close response.
    if (response == -4) or (response == -6):
        dlgAbout.hide()


def hideAbout(self=None, widget=None):
    dlgAbout = builder.get_object("dlgAbout")
    dlgAbout.hide()
    return True


###############################################################################
# Main Program
###############################################################################

#Define handlers
handlers = {
    "onDeleteWindow": Gtk.main_quit,

    "showCompile": showCompileWindow,
    "runCompile": runCompile,
    "killCompile": killCompile,
    "closeCompile": closeCompileWindow,

    "showResults": showResultsWindow,
    "copyResults": copyResults,
    "selectResults": selectResults,
    "exportResults": exportResults,
    "closeResults": closeResultsWindow,

    "new-project": newProject,
    "open-project": openProject,
    "save-project": saveProject,
    "saveas-project": saveProjectAs,

    "begin-edit": beginEditBuffer,
    "end-edit": endEditBuffer,

    "undo-last": undo,
    "redo-last": redo,

    "hideAbout": hideAbout,
    "show-about": showAbout,
}


#Import interface from Glade.
builder = Gtk.Builder()
builder.add_from_file("redstring_interface.glade")
builder.connect_signals(handlers)
window = builder.get_object("mainWindow")

#Start up main loop.
GObject.timeout_add(3000, mainLoop)
resetHistory()

window.show_all()

Gtk.main()
