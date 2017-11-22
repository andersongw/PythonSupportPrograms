import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as tkmb
from tkinter import filedialog as tkfd
from tkinter import font
import collections
import sqlite3
import re
import datetime as dt
import os.path
import shutil
import csv

import pyperclip

from guiBlocks import *

execExts=(".py",".pyw",".exe")

noteTuple = collections.namedtuple('noteTuple',
        "noteID taskID noteDate noteText archive fileID")
blankNote=noteTuple(None,None,"","",False,None)

fileTuple = collections.namedtuple('fileTuple',
        "fileID filePath fileName saveTime fileSize fileHash")
blankFile = (None,"","","","","")

#################################################################################
#
## addNotesDlg: add and manage notes associated with an individual task
#
#################################################################################


class addNotesDlg(tk.Frame):
    def __init__(self,master = None, dbConn = None):
        tk.Frame.__init__(self,master)
        self.grid()
		
        self.dbConn = dbConn
        self.taskID = None
        self.noteID = None
        self.fileID = None
        self.curNote = blankNote
        self.curFile = blankFile
        self.fileStamp = ""
        self.iid_noteID={} ## Do I want to consider using a single dict for both?  NoteID is always an integer and IIDs are always strings, so there's no chance of a collision.
        self.noteID_iid={}

        self.noteDate = dateFieldLeft(self,"Date",0,initVal=curDate())
        self.noteTxt = dataTextBox(self,"Note",1,0,3,2,boxW=40)
        
        self.addNoteBtns = dblBtn(self,["Add Note","Clear Note"],[self.addNoteFn,self.clearNote],1,3)
        
        self.archiveNote = dataCheckBox(self,"Archive Note",False,2,3)
        self.notePathname = statusLabelBox(self,"File Path",os.getcwd(),0,4,3)
        self.noteFilename = dataFieldLeft(self,"File",1,4,3,initVal="None")

        self.addFileBtns=dblBtn(self,["Add File","Open File"],[self.addFileFn,self.openFileFn],2,4)

        #self.verifyFileLinks = dataCheckBox(self,"Verify File Links",True,0,3)
        self.verifyFileLinks = dataCheckBox(self,"Verify File Links",False,2,6) # disable by default until the relink-dialog works properly
        self.storeFileBtns = dblBtn(self,["Store File","Restore File"],[self.storeFileFn,self.restoreFileFn],2,5)
		
        self.noteTreeCfg = [
            treeColTpl("txt",500,"Text"),
            treeColTpl("file",450,"FileName"),
            treeColTpl("time",150,"TimeStamp")]
            
        self.noteView = treeView(self,"Notes",self.noteTreeCfg,3,0,7)

        self.noteView.setIconWidth(dateColWidth)
        self.noteView.setRowCount(4)
        self.noteView.bindField("<<TreeviewSelect>>",self.onSelectOne)

        self.noteFilename.bindField('<ButtonRelease-3>',rightClickPaste)
        self.noteTxt.bindField('<ButtonRelease-3>',rightClickPasteTextBox)

        self.noteTable = "Notes"
        self.noteCols = [
            "NoteID",
            "TaskID",
            "NoteDate",
            "NoteText",
            "ArchiveNote",
            "FileID"]

        self.fileTable = "Files"
        self.fileCols = [
            "FileID",
            "FilePath",
            "FileName",#FileData column should be here, but that won't correspond with the usual calls to the insert/select commands
            "SaveTime",
            "FileSize",
            "FileHash"]

    # Set/reset the task associated with the current note			
    def setTaskID(self,newTaskID):
        #print(newTaskID)
        self.taskID = newTaskID

    def setTaskEdit(self,newTaskDlg):
        self.taskDlg = newTaskDlg

    # Handler for choosing a note out of the treeView
    def onSelectOne(self,event=None):
        workIID = self.noteView.getSelection()[0]
        self.noteID = self.iid_noteID[workIID]
        self.curNote = self.fetchNoteData(self.noteID)
        self.setNoteData(self.curNote)

        self.addNoteBtns.recaption0("Update Note")

        
    # Handler for the "Add File" button to associate a file with a note.
    def addFileFn(self,event=None):
        self.fileStamp = dt.datetime.now().isoformat()
        startName = self.noteFilename.getVal()

        

        # First, check whether the specified file is a web link; if so, see if it exists in the database
        #  if exists: get the fileID from the latest timestamp, if not save it as-is and set the fileID
        #  Do I want to reset the timestamp?  If so, do I need to find all of the notes that reference this note and point them to a new note?
        #  Or do I copy the existing note to a new record and update the original stamp?
        # If it;s a link, set size to 0 and hash to ""
        if checkWeblink(startName):
            res = self.dbConn.execute("SELECT FileID FROM(SELECT FileID, FileName, max(SaveTime) FROM Files GROUP BY FileName) WHERE FileName = ?",[startName]).fetchone()
            if res != None:
                self.fileID = res["FileID"]
                copySql(self.dbConn,self.fileTable,"FileID",self.fileID)
                self.dbConn.execute("UPDATE Files SET SaveTime = ? WHERE FileID = ?",[self.fileStamp,self.fileID])
            else:
                self.fileID = insertSql(self.dbConn,self.fileTable,self.fileCols[1:],[None,startName,self.fileStamp,0,""])
            self.curFile = self.getFileData()
            return
            
        #Second, open a file chooser dialog box and get choose a file
        startPath,startFile = os.path.split(startName)
        oldPath = self.notePathname.getVal()
        if os.path.exists(startName):
            addFilename = tkfd.askopenfilename(initialdir=startPath,initialfile=startFile)
        elif os.path.exists(startPath):
            addFilename = tkfd.askopenfilename(initialdir=startPath)
        elif os.path.exists(oldPath):
            addFilename = tkfd.askopenfilename(initialdir=oldPath)
        else:
            addFilename = tkfd.askopenfilename()

        # If the dialog was closed without a selection, returns the empty string; return without changing anything
        if addFilename == "":
            self.curFile = blankFile
            return
        
        filePath,fileName = os.path.split(addFilename)

        self.notePathname.setVal(filePath)
        self.noteFilename.setVal(fileName)

        fileStat = os.stat(addFilename)
        fileSize = fileStat.st_size
        fileHash = getFileHash(addFilename)

        # Look for an existing file in the database; if it's already in the database,
        #  associate the note with the latest timestamped version for the same directory and name

        res = self.dbConn.execute("SELECT FileID FROM(SELECT FileID, FilePath, FileName, max(SaveTime) FROM Files GROUP BY FilePath,FileName) WHERE FilePath = ? AND FileName = ?",[filePath,fileName]).fetchone()
        if res !=None:
            self.fileID = res["FileID"]
            copySql(self.dbConn,self.fileTable,"FileID",self.fileID)
            self.dbConn.execute("UPDATE Files SET SaveTime = ? WHERE FileID = ?",[self.fileStamp,self.fileID])
        else:
            self.fileID = insertSql(self.dbConn,self.fileTable,self.fileCols[1:],[filePath,fileName,self.fileStamp,fileSize,fileHash])

        self.curFile = self.getFileData()
        
        #   Maybe amend the database to include the file size on disk to
        #       facilitate quick checks between the database version and the disk version

##    def checkFileExists(self,ftupl):
##        return os.path.exists(os.path.join(ftupl.filePath,ftupl.fileName))

    def storeFileFn(self,event=None):
        # 1: confirm that self.curFile corresponds to the identified path; if not, execute addFileFn - this should cover all the required checks
        # 2: ensure that the requested file to be stored isn;t a weblink -- may implement that later, but that seems hazardous.  For now, exit with a message
        # 3: update the fileData column based on the current fileID


        #Why is there an error that self.curFile isn't a fileTuple (it's a regular tuple)
        # Was a new note on an existing task
        if not (self.curFile.fileName == self.noteFilename.getVal() and self.curFile.filePath == self.notePathname.getVal()):
            self.addFileFn()
            
        self.curFile._replace(saveTime = dt.datetime.now().isoformat())
        workFile = os.path.join(self.curFile.filePath,self.curFile.fileName)

        inFile = open(workFile,'rb')
        inBytes = inFile.read()
        inFile.close()

        oldBytes = fetchSql(self.dbConn,self.fileTable,["FileID"],[self.curFile.fileID])[0]["FileData"]
        if oldBytes == inBytes:
            tkmb.showinfo(None,"File hasn't changed; leaving the existing file alone")
            return

        copySql(self.dbConn,self.fileTable,"FileID",self.curFile.fileID)
        updateSql(self.dbConn,self.fileTable,["FileData","SaveTime"],[inBytes,self.curFile.saveTime],"FileID",[self.curFile.fileID])
        
#   Old logic follows
        #1: confirm the file exists; if not, display message and exit
        #2: read file
        #3: find the file in the database with latest timestamp; if not present, skip to step ?
        #4: compare read data against stored data; if same, display message and exit
        #5: save new data in database; if file didn't already exist, include standard fields as well
##        workPath = self.notePathname.getVal()
##        workFile = self.noteFilename.getVal()
##        fullName = os.path.join(workPath,workFile)
##        if not os.path.exists(os.path.join(:
##            tkmb.showerror(None,"No file at this location")
##            return


        

    def restoreFileFn(self,event=None):
        pass
 
    #  Handler for the "Open File" button to open the file associated with the note
    def openFileFn(self,event=None):
        workPath = self.notePathname.getVal()
        workName = self.noteFilename.getVal()
        if checkWeblink(workName):
            os.startfile(workName)
            return

            
        #[fileDir,fileName]=os.path.split(workName)
        if not os.path.exists(workPath):
            tkmb.showerror(None,"No such directory")
            return

        fullFile = os.path.join(workPath,workName)
        if not os.path.exists(fullFile):
            tkmb.showerror(None,"No such file")
            return

        if os.path.splitext(workName)[1] in execExts:
            os.startfile(workPath)
            return

        if checkCtrlClick(event):
            os.startfile(workPath)
            return
            
        try:
            os.startfile(fullFile)

        except OSError:
            os.startfile(workPath)    


    def getNoteData(self):
        self.curNote = noteTuple(
            self.noteID,
            self.taskID,
            self.noteDate.getVal(),
            self.noteTxt.getVal(),
            self.archiveNote.getVal(),
            self.fileID)
        return self.curNote

    def confirmFile(self,workPath,workFile):
        #print(workPath,workFile)
        # If the file is in the expected location, move on.
        # If not, does the user care?  If not, move on.
        if os.path.exists(os.path.join(workPath,workFile)):
            return (workPath,workFile)

        # If the file turns out not to be there, find out if the directory exists
        #   * If not, ask the user whether to re-create the directory or look for the new location
        #   * if recreate -- recreate it; then restore the saved file into it (not implemented yet)
        #   * if find new one, use askdirectory dialog to find it:
        #       * when found, replace the missing directory in all file records
        #       * confirm that file exists in the found directory.
        #           * If so, move on
        #           * If not, ask whether to restore file or find file

        if not os.path.exists(workPath):
            sol = tkmb.askyesnocancel("Directory not found","Would you like to find it (Yes), recreate it (no), or neither (Cancel)")
            if sol == None:
                return (workPath,workFile)
            if not sol:
                tkmb.showinfo(None,"Not implemented")
                return (workPath,workFile)
            oldPath = workPath
            workPath = tkfd.askdirectory()

        if not os.path.exists(os.path.join(workPath,workFile)):
            errStr = str.format("The file {} could not be located in {}",workFile,workPath)
            tkmb.showerror(None,errStr)
            return (workPath,workFile)
            
        if tkmb.askquestion("File found","File successfully located; remap all links to new directory?")==u'no':
            return (workPath,workFile)

        updateSql(self.dbConn,self.fileTable,["FilePath"],[workPath],"FilePath",[oldPath])
        return (workPath,workFile)
    
    # This is old code that I was proud of but no longer need; keeping it a while
##        res = fetchSql(self.dbConn,self.fileTable,["FilePath"],[oldPath])
##        for ln in res:
##            print(ln[:])

##        #fileDir,fileName = os.path.split(workFile)
##        if os.path.exists(workPath):
##            return tkfd.askopenfilename()
##        drv,relPath = os.path.splitdrive(workPath)
##        pathList = workPath.split(r"/")
##        while not os.path.exists("/".join(pathList)):
##            del pathList[-1]
##            specFile = tkfd.askopenfilename(initialdir="/".join(pathList))
##            return os.path.split(specFile)
##        


    def fetchFileData(self,workFileID):
        if workFileID!=None:
            res = fetchSql(self.dbConn,self.fileTable,["FileID"],[workFileID])[0]
            workPath = res["FilePath"]
            workName = res["FileName"]
            workTime = res["SaveTime"]
            workSize = res["FileSize"]
            workHash = res["FileHash"]
            self.notePathname.setVal(workPath)
            self.noteFilename.setVal(workName)
            if self.verifyFileLinks.getVal() and not checkWeblink(workName):
                workPath,workName = self.confirmFile(workPath,workName)
        else:
            workPath = ""
            workName = ""
            workTime = ""
            workSize = ""
            workHash = ""
        return fileTuple(
                    workFileID,
                    workPath,
                    workName,
                    workTime,
                    workSize,
                    workHash)

    def fetchNoteData(self,workID):
        res = fetchSql(self.dbConn,self.noteTable,["NoteID"],[workID])[0]
        return noteTuple(
                    workID,
                    self.taskID,
                    res["NoteDate"],
                    res["NoteText"],
                    res["ArchiveNote"],
                    res["FileID"])
        

    def setNoteData(self,newData):
        #self.taskID -- don't know what I want to do with this field; there shouldn't be a case where newData points to a task other than the current
        self.noteTxt.setVal(newData.noteText)
        self.archiveNote.setVal(newData.archive)
        self.noteDate.setVal(newData.noteDate)
        self.fileID = newData.fileID
        self.curFile=self.fetchFileData(self.fileID)
        
        self.notePathname.setVal(self.curFile.filePath)
        self.noteFilename.setVal(self.curFile.fileName)
        self.fileStamp = self.curFile.saveTime


    def getFileData(self):
        return fileTuple(
            self.fileID,
            self.notePathname.getVal(),
            self.noteFilename.getVal(),
            self.fileStamp,
            0,"")#Don't know how to use the file size or hash yet.  Half-assed inplementation, I know, but I'm kind of stuck for the moment      

    def addNoteFn(self,event=None):
        if self.taskID == None:
            #tkmb.showerror(None,"No associated task")
            saveTask=tkmb.askyesno(None,"No associated task; save current task?")
            #print(self.taskDlg.tsk.taskID)
            
            return
        workNote = self.getNoteData()[1:]

        workName = self.noteFilename.getVal()
        if checkWeblink(workName):
            dispName = workName
        else:
            dispName = os.path.basename(workName)
        
        if self.noteID == None:
            self.noteID = insertSql(self.dbConn,self.noteTable,self.noteCols[1:],workNote)
            self.curNote = noteTuple._make((self.noteID,)+workNote)
            newIID = self.noteView.addLine("","",[self.noteTxt.getVal(),dispName,dispISOStamp(self.fileStamp)])
            self.addNoteBtns.recaption0("Update Note")
            self.noteID_iid[self.noteID]=newIID
            self.iid_noteID[newIID]=self.curNote.noteID
            return

        if self.curNote.noteID != None:
            updateSql(self.dbConn, self.noteTable,self.noteCols[1:],workNote,"NoteID",[self.curNote.noteID])
            curIID = self.noteID_iid[self.curNote.noteID]
            self.noteView.updateLine(curIID,"",[self.noteTxt.getVal(),dispName,dispISOStamp(self.fileStamp)])
            return


    def clearNote(self,event=None):
        self.curNote=blankNote
        self.curFile=blankFile
        self.noteID = None
        self.fileID = None
        self.fileStamp = ""
        self.noteDate.setVal(curDate())
        self.noteTxt.setVal("")
        self.archiveNote.setVal(False)
        self.notePathname.setVal("")
        self.noteFilename.setVal("")
        self.addNoteBtns.recaption0("Add Note")

    def clearTask(self,event=None):
        self.taskID = None
        self.clearNote()
        self.noteView.clearTree()
        self.noteID_iid={}
        self.iid_noteID={}
        

    def popNotes(self,newTaskID):
        #Find all notes associated with the current task
        self.taskID = newTaskID
        self.clearNote()
        self.noteView.clearTree()
        taskNotes = fetchSql(self.dbConn,self.noteTable, ["TaskID"],[self.taskID])
        if len(taskNotes)==0:
            return

        for ln in taskNotes:
            newFile=self.fetchFileData(ln["FileID"])
            #print(ln["NoteDate"])
            newIID = self.noteView.addLine("",ln["NoteDate"],[ln["NoteText"],newFile.fileName,dispISOStamp(newFile.saveTime)])
            self.noteID_iid[ln["NoteID"]]=newIID
            self.iid_noteID[newIID]=ln["NoteID"]
        		
