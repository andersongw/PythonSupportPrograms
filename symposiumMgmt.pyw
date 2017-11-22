import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmb
import tkinter.filedialog as tkfd
import sqlite3
import collections
import datetime
import re
import os.path
import shutil
import random

import pyperclip
import openpyxl as xl
import openpyxl.comments as xlc

from guiBlocks import *
from symposiumDlgs import *
from paperAbstractSymposiumDlg import *
import autoversion as av

av.dispRunDateTime()
#av.autoversionList(("autoversion.py","guiBlocks.py","symposiumDlgs.py","symposiumMgmt.pyw","paperAbstractSymposiumDlg.py"))
log = av.editLog()
log.autoversionList(("autoversion.py","guiBlocks.py","symposiumDlgs.py","symposiumMgmt.pyw","paperAbstractSymposiumDlg.py"))

# Need new tab for draft paper assignment
#   * Should pull from Assign Abstracts pretty heavily
#   * Check the original reviewer worksheets
#   * Look at how the abstracts we distributed
#   * Need to know which papers have not been received and contact authors

# Will need another tab for Merge comments
#   * May or may not mirror the merge reviews tab
#   * 

#
##  Collect Reviews
#

#
## Manage Final Papers
#

finalTuple = collections.namedtuple("finalTuple",
                            "finalID paperID drop exten recv dateRecv recvFile issFile")

class manageFinalDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None):
        tk.Frame.__init__(self,master)

        self.dbConn = dbConn
        self.dropCount = 0
        self.paperCount = 0
        self.recvCount = 0

        #self.popReviewers()
        self.popFinalFiles()

        self.paperListBox = messageListbox(self,0,0,4,10)
        self.popPaperBox()
        
        self.paperTitle = dataFieldLeft(self,"Paper Title",1,4,2)
        self.dropCheck = dataCheckBox(self,"Dropped Paper",False,2,4)
        self.extenCheck = dataCheckBox(self,"Requested Extension",False,2,5)
        self.recvCheck = dataCheckBox(self,"Received Paper",False,3,4)
        self.recvDate = dataFieldLeft(self,"Date Received",3,5)
        self.finalFilename = dataComboBox(self,"Original Filename",self.finalFileList,4,4,2)
        self.newFilename = dataFieldLeft(self,"New Filename",5,4,2)
        self.newTitle = dataFieldLeft(self,"New Paper Title",7,4,2)
        

        self.remain = statusLabelBox(self,"Papers Remaining",self.paperCount,12,0)
        self.dropNum = statusLabelBox(self,"Papers Dropped",self.dropCount,13,0)
        self.recvNum = statusLabelBox(self,"Papers Received",self.recvCount,14,0)
        
        self.btnSave = actionBtn(self,"Save Data",self.saveFn,11,0)
        self.btnClear = actionBtn(self,"Clear Data",self.clearFn,11,1)
        self.refreshViewBtn = actionBtn(self,"Refresh",self.refreshFn,11,2)

        self.paperListBox.bindField("<ButtonRelease-1>",self.selectPaper)
        self.paperListBox.bindField("<ButtonRelease-3>",self.delPaper)
        self.finalFilename.bindField("<ButtonRelease-3>",self.delFilename)

        self.dataTable = "Finals"
        self.dataCols = [""]

    def selectPaper(self,event=None):
        curTitle = self.paperListBox.getSelection()
        self.paperTitle.setVal(curTitle)
        res = fetchSql(self.dbConn,"Abstracts NATURAL JOIN Papers JOIN People AS Author ON PrimaryAuthor=personID",["Papers.Title"],[curTitle])[0]
        self.newTitle.setVal(curTitle)
        newName = str.format("d{:02d} - {}",res["PaperID"],res["Lastname"])
        self.newFilename.setVal(newName)

    def delPaper(self,event=None):
        self.paperListBox.dropLine(self.paperListBox.findClickLineIndex(event))
        

    def delFilename(self,event=None):
        curList = self.finalFilename.getDropList()
        curFile = self.finalFilename.getVal()
        curList.remove(curFile)
        self.finalFilename.updateVals(curList)
        self.finalFilename.setVal(curList[0])
      

    def getData(self):
        return finalTuple(
            None,
            self.title_PaperID[self.paperTitle.getVal()],
            self.dropCheck.getVal(),
            self.extenCheck.getVal(),
            self.recvCheck.getVal(),
            self.recvDate.getVal(),
            self.finalFilename.getVal(),
            self.newFilename.getVal())

##    def popReviewers(self,event=None):
##        res = self.dbConn.execute("SELECT DISTINCT People.Title,FirstName,LastName,PersonID FROM Abstracts JOIN People ON Reviewer=PersonID ORDER BY LastName").fetchall()
##        self.reviewerDict = {ln["PersonID"]:formatNameSQL(ln) for ln in res}
##        self.reviewerDict.update({formatNameSQL(ln):ln["PersonID"] for ln in res})
##        self.reviewerList = [formatNameSQL(ln) for ln in res]

    def popFinalFiles(self,event=None):
        print("looking for final papers")
        workDir = os.getcwd()
        self.finalFileList=os.listdir(workDir)

    def popPaperBox(self,event=None):
        self.title_PaperID={}
        res = self.dbConn.execute("SELECT PaperID, Title FROM Abstracts NATURAL JOIN Papers WHERE Accepted = 1 ORDER BY Title").fetchall()
        for ln in res:
            (wkTitle,wkID)=(ln["Title"],ln["PaperID"])
            self.paperListBox.addLine(wkTitle)
            self.title_PaperID[wkTitle]=wkID
            self.title_PaperID[wkID]=wkTitle
            

        self.dropCount = len(res)
        self.paperCount = 0
        self.recvCount = 0
                
        #"draftID paperID drop exten recv dateRecv recvFile issFile reviewer")
        
    def saveFn(self,event=None):
        # Set all columns in the Drafts table
        # Store file data in DraftFiles table

        listBoxIdx = self.paperListBox.getSelectionIndex()
        fileList=self.finalFilename.getDropList()
        fileList.remove(self.finalFilename.getVal())

        self.paperListBox.dropLine(listBoxIdx[0])
        self.finalFilename.updateVals(fileList)
        
        workData = self.getData()
##        newID = insertSql(self.dbConn,"Drafts",
##                    ["PaperID","Dropped","Extension","Recv","DateRecv","ReviewerID"],
##                    [workData.paperID, workData.drop, workData.exten, workData.recv, workData.dateRecv, workData.reviewer])
##
##        inFile = open(self.draftFilename.getVal(),"rb")
##        inBytes = inFile.read()
##        inFile.close()
##
##        insertSql(self.dbConn,"DraftFile",
##                  ["DraftID","OriginalFilename","ISSFilename","FileObject"],
##                  [newID,workData.recvFile,workData.issFile,inBytes])

        self.paperCount-=1
        if workData.drop:
            self.dropCount+=1

        if workData.recv:
            self.recvCount+=1

        self.remain.setVal(self.paperCount)
        self.dropNum.setVal(self.dropCount)
        self.recvNum.setVal(self.recvCount)
                  

    def clearFn(self,event=None):
        self.refreshFn()
        self.dropCheck.setVal(False)
        self.extenCheck.setVal(False)
        self.recvCheck.setVal(False)
        self.finalFilename.setVal("")
        self.newFilename.setVal("")
                            
        

    def refreshFn(self,event=None):
        self.popPaperBox()
        #self.popTree()     



class manageFinalDlgAlt(tk.Frame):
    def __init__(self,master=None,dbConn=None):
        tk.Frame.__init__(self,master)
        self.dbConn=dbConn

        baseRow = 2
        self.paperListBox = messageListbox(self,baseRow,0,4,10)
        self.listPapers()

        self.paperDropdown = dataComboBox(self,"Paper Title",["a","b"],0,6)
        self.popPaperDrop()

        self.workDir = dataFieldLeft(self,"Working Directory",0,0,4)
        self.workDir.setVal(os.getcwd())
        self.reloadDir = actionBtn(self,"Refresh File List",self.listPapers,0,5)
        
        self.curPaper = statusLabelBox(self,"Current Paper","Unselected",1,0)
        self.statusAuthor=statusLabelBox(self,"Author","Unselected",1,5)
        self.checkDraft = dataCheckBox(self,"Draft",False,baseRow,5)
        self.checkFinal = dataCheckBox(self,"Final",False,baseRow+1,5)
        self.checkCopyright = dataCheckBox(self,"Copyright Form",False,baseRow+2,5)
        self.checkPresent = dataCheckBox(self,"Presentation",False,baseRow+3,5)
        self.checkDrop = dataCheckBox(self,"Paper Withdrawn",False,baseRow+4,5)

        workDate = curDate()

        self.recvDraft = dateFieldLeft(self,"Received",baseRow,6,initVal=workDate)
        self.recvFinal = dateFieldLeft(self,"Received",baseRow+1,6,initVal=workDate)
        self.recvCopyright = dateFieldLeft(self,"Received",baseRow+2,6,initVal=workDate)
        self.recvPresent = dateFieldLeft(self,"Received",baseRow+3,6,initVal=workDate)
        self.dropDate = dateFieldLeft(self,"Dropped",baseRow+4,6,initVal=workDate)
        

    def listPapers(self,event=None):
        allFiles = os.listdir()
        for ln in allFiles:
            self.paperListBox.addLine(ln)

    def popPaperDrop(self,event=None):
        res = self.dbConn.execute("SELECT PaperID,Papers.Title,LastName FROM Papers NATURAL JOIN Abstracts JOIN People ON PrimaryAuthor=PersonID WHERE Accepted=1 ORDER BY Papers.Title").fetchall()
        self.title_id = {ln["Title"]:ln["PaperID"] for ln in res}
        self.author_id = {ln["LastName"]:ln["PaperID"] for ln in res}
        
            
        
        

#
## Manage Moderators/Tracks
#

trackTuple = collections.namedtuple("trackTuple",
                            "trackID trackNum title room startTime endTime moderator")

class manageTracksDlg(tk.Frame):
    def __init__(self,master=None,dbConn=None):
        tk.Frame.__init__(self,master)
        self.dbConn=dbConn

        self.trackFrame = formFrame(self,"Track Management",0,0)
        
        self.trackNumBox = dataFieldLeft(self.trackFrame.frame,"Track Number",0,0)
        self.trackTitleBox = dataFieldLeft(self.trackFrame.frame,"Track Title",1,0)
        self.roomBox = dataComboBox(self.trackFrame.frame,"Track Room",["Zellerbach","Prince","Montgomery"],2,0)
        self.moderatorBox = dataComboBox(self.trackFrame.frame,"Moderator",["Person a","Person b"],3,0,2)
        self.startTimeBox = dataFieldLeft(self.trackFrame.frame,"Start Time",4,0)
        self.endTimeBox = dataFieldLeft(self.trackFrame.frame,"End Time",4,1)
        self.saveBtn = actionBtn(self.trackFrame.frame,"Save Data",self.saveFn,5,0)
        self.clearBtn = actionBtn(self.trackFrame.frame,"Clear Data",self.clearFn,5,1)

        self.paperFrame = formFrame(self,"Papers",0,1)

        self.workTrack = dataComboBox(self.paperFrame.frame,"Current Track",["Track 1","Track 2"],0,0,2)
        self.paperDrop = dataComboBox(self.paperFrame.frame,"Papers",["Paper 1","Paper 2"],1,0,2)
        self.paperPresenter = dataComboBox(self.paperFrame.frame,"Presenter",["Name 1","Name 2"],2,0,2)
        self.startTime = dataFieldLeft(self.paperFrame.frame,"Start Time",3,0)
        self.addPaperBtn = actionBtn(self.paperFrame.frame,"Add Paper",self.addPaperFn,3,1)

        self.agendaFrame = formFrame(self,"Agenda",0,2)

        self.agendaViewCfg = [
            treeColTpl("time",75,"Start Time"),
            treeColTpl("title",200,"Title"),
            treeColTpl("speakr",200,"Presenter")]
        self.agendaView = treeView(self.agendaFrame.frame,"",self.agendaViewCfg,0,0)
        self.agendaView.setIconWidth(75)
        
        

    def saveFn(self,event = None):
        pass

    def clearFn(self,event=None):
        pass

    def addPaperFn(self,event=None):
        pass

        

#
## Manage Drafts
#

draftTuple = collections.namedtuple("draftTuple",
                            "draftID paperID drop exten recv dateRecv recvFile issFile reviewer")

class manageDraftsDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None):
        tk.Frame.__init__(self,master)

        self.dbConn = dbConn
        self.dropCount = 0
        self.paperCount = 0
        self.recvCount = 0

        self.popReviewers()
        self.popDraftFiles()

        self.paperListBox = messageListbox(self,0,0,4,10)
        self.popPaperBox()
        
        self.reviewer = dataComboBox(self,"Reviewer",self.reviewerList,0,4,2)
        self.paperTitle = dataFieldLeft(self,"Paper Title",1,4,2)
        self.dropCheck = dataCheckBox(self,"Dropped Paper",False,2,4)
        self.extenCheck = dataCheckBox(self,"Requested Extension",False,2,5)
        self.recvCheck = dataCheckBox(self,"Received Paper",False,3,4)
        self.recvDate = dataFieldLeft(self,"Date Received",3,5)
        self.draftFilename = dataComboBox(self,"Original Filename",self.draftFileList,4,4,2)
        self.newFilename = dataFieldLeft(self,"New Filename",5,4,2)
        self.draftReviewer = dataComboBox(self,"Draft Reviewer",self.reviewerList,6,4,2)
        self.newTitle = dataFieldLeft(self,"New Paper Title",7,4,2)

        self.remain = statusLabelBox(self,"Papers Remaining",self.paperCount,11,0)
        self.dropNum = statusLabelBox(self,"Papers Dropped",self.dropCount,11,1)
        self.recvNum = statusLabelBox(self,"Papers Received",self.recvCount,11,2)
        
        self.btnSaveClear = dblBtn(self,["Save Data","Clear Data"],[self.saveFn,self.clearFn],8,4)
        self.refreshViewBtn = actionBtn(self,"Refresh",self.refreshFn,8,5)

        self.paperListBox.bindField("<ButtonRelease-1>",self.selectPaper)
        self.paperListBox.bindField("<ButtonRelease-3>",self.delPaper)
        self.draftFilename.bindField("<ButtonRelease-3>",self.delFilename)

    def selectPaper(self,event=None):
        curTitle = self.paperListBox.getSelection()
        self.paperTitle.setVal(curTitle)
        res = fetchSql(self.dbConn,"Abstracts NATURAL JOIN Papers JOIN People AS Author ON PrimaryAuthor=personID",["Papers.Title"],[curTitle])[0]
        self.reviewer.setVal(self.reviewerDict[res["Reviewer"]])
        self.draftReviewer.setVal(self.reviewerDict[res["Reviewer"]])
        self.newTitle.setVal(curTitle)
        newName = str.format("d{:02d} - {}",res["PaperID"],res["Lastname"])
        self.newFilename.setVal(newName)

    def delPaper(self,event=None):
        self.paperListBox.dropLine(self.paperListBox.findClickLineIndex(event))
        

    def delFilename(self,event=None):
        curList = self.draftFilename.getDropList()
        curFile = self.draftFilename.getVal()
        curList.remove(curFile)
        self.draftFilename.updateVals(curList)
        self.draftFilename.setVal(curList[0])
      

    def getData(self):
        return draftTuple(
            None,
            self.title_PaperID[self.paperTitle.getVal()],
            self.dropCheck.getVal(),
            self.extenCheck.getVal(),
            self.recvCheck.getVal(),
            self.recvDate.getVal(),
            self.draftFilename.getVal(),
            self.newFilename.getVal(),
            self.reviewerDict[self.reviewer.getVal()])

    def popReviewers(self,event=None):
        res = self.dbConn.execute("SELECT DISTINCT People.Title,FirstName,LastName,PersonID FROM Abstracts JOIN People ON Reviewer=PersonID ORDER BY LastName").fetchall()
        self.reviewerDict = {ln["PersonID"]:formatNameSQL(ln) for ln in res}
        self.reviewerDict.update({formatNameSQL(ln):ln["PersonID"] for ln in res})
        self.reviewerList = [formatNameSQL(ln) for ln in res]

    def popDraftFiles(self,event=None):
        print("looking for drafts")
        workDir = os.getcwd()
        self.draftFileList=os.listdir(workDir)

    def popPaperBox(self,event=None):
        self.title_PaperID={}
        res = self.dbConn.execute("SELECT PaperID, Title FROM Abstracts NATURAL JOIN Papers WHERE Accepted = 1 ORDER BY Title").fetchall()
        for ln in res:
            (wkTitle,wkID)=(ln["Title"],ln["PaperID"])
            self.paperListBox.addLine(wkTitle)
            self.title_PaperID[wkTitle]=wkID
            self.title_PaperID[wkID]=wkTitle
            

        self.dropCount = len(res)
        self.paperCount = 0
        self.recvCount = 0
                
        #"draftID paperID drop exten recv dateRecv recvFile issFile reviewer")
        
    def saveFn(self,event=None):
        # Set all columns in the Drafts table
        # Store file data in DraftFiles table

        listBoxIdx = self.paperListBox.getSelectionIndex()
        fileList=self.draftFilename.getDropList()
        fileList.remove(self.draftFilename.getVal())

        self.paperListBox.dropLine(listBoxIdx[0])
        self.draftFilename.updateVals(fileList)
        
        workData = self.getData()
##        newID = insertSql(self.dbConn,"Drafts",
##                    ["PaperID","Dropped","Extension","Recv","DateRecv","ReviewerID"],
##                    [workData.paperID, workData.drop, workData.exten, workData.recv, workData.dateRecv, workData.reviewer])
##
##        inFile = open(self.draftFilename.getVal(),"rb")
##        inBytes = inFile.read()
##        inFile.close()
##
##        insertSql(self.dbConn,"DraftFile",
##                  ["DraftID","OriginalFilename","ISSFilename","FileObject"],
##                  [newID,workData.recvFile,workData.issFile,inBytes])

        self.paperCount-=1
        if workData.drop:
            self.dropCount+=1

        if workData.recv:
            self.recvCount+=1

        self.remain.setVal(self.paperCount)
        self.dropNum.setVal(self.dropCount)
        self.recvNum.setVal(self.recvCount)
                  

    def clearFn(self,event=None):
        self.refreshFn()
        self.reviewer.setVal("")
        self.dropCheck.setVal(False)
        self.extenCheck.setVal(False)
        self.recvCheck.setVal(False)
        self.draftFilename.setVal("")
        self.newFilename.setVal("")
                            
        

    def refreshFn(self,event=None):
        self.popPaperBox()
        #self.popTree()     

##  Main App
#

def exitFn(event=None):
    win.destroy()
    
def tabChange(event):
    w=event.widget
    curTab = w.index("current")
    if curTab == 0: #Add person
        pass
    elif curTab == 1:   #Add paper
        addPaper.updateAuthors()
    elif curTab == 2:   #Add Abstract
        addAbstract.updateComboBoxes()
    elif curTab == 3:   #Populate Committee
        pass
    elif curTab == 4:   #Assign to Committee
        curCommittee = buildCommittee.getData()
        #assignAbstracts.genCommitteeList(curCommittee)
        #Don't think I need this function anymore.  Especially if I'm abandoning the Populate Committee tab
    elif curTab == 5:   #Aggregate Results
        pass
    elif curTab == 6:   # Assign Keywords
        pass

        

curDir = os.getcwd()
dbFile = "SymposiumManagement.db"


if not os.path.isfile(os.path.join(curDir,dbFile)):
    print("No database found")
    dbFile=tkfd.askopenfilename()
    curDir = os.path.dirname(dbFile)
    print(curDir)

    
conn = sqlite3.connect(dbFile) 
conn.row_factory = sqlite3.Row

##test = conn.execute("SELECT * FROM People WHERE PersonID = 0").fetchone()
##print(formatNameSQL(test))

win = tk.Tk()

tabFrame = tk.Frame(win)
tabFrame.grid(row=0,column=0)
tabs = ttk.Notebook(tabFrame)
tabs.grid(sticky=tk.NSEW)

addPerson = personDlg(tabs,conn)
addPaperAbstract = paperAbstractDlg(tabs,conn)
addPaper = paperDlg(tabs,conn)
addAbstract = abstractDlg(tabs,conn)
buildCommittee = buildCommitteeDlg(tabs,conn)
assignAbstracts = assignCommitteeDlg(tabs,conn)
mergeReviews = aggregateReviewResultsDlg(tabs,conn)
addKeywords = kwDlg(tabs,conn)
handleDrafts = manageDraftsDlg(tabs,conn)
handleFinals = manageFinalDlg(tabs,conn)
handleTracks = manageTracksDlg(tabs,conn)


tabs.add(addPerson,text="Person")
tabs.add(addPaper,text="Papers")
tabs.add(addPaperAbstract,text = "Paper/Abstract")
tabs.add(addAbstract,text="Abstract")
tabs.add(buildCommittee,text="Assemble Committee")
tabs.add(assignAbstracts,text="Assign Abstracts")
tabs.add(mergeReviews,text="Merge Reviews")
tabs.add(addKeywords,text="Keywords")
tabs.add(handleDrafts,text="Manage Drafts")
tabs.add(handleFinals,text="Manage Finals")
tabs.add(handleTracks,text="Manage Tracks")
tabs.enable_traversal()

tabs.bind("<<NotebookTabChanged>>",tabChange)

exitBtn = actionBtn(win,"Exit",exitFn,3)


win.mainloop()


conn.close()
