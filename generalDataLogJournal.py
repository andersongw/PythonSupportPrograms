import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmb
import tkinter.filedialog as tkfd
import sqlite3
import collections
import datetime as dt
import re
import os
import os.path

from guiBlocks import *
from generalDataLogFunctions import *

bookFormatDrop = ["None","Audiobook (Solo)","Audio (Shared)","Audio (Heather and Bella)","eBook (Nook)","eBook (Kindle)","Print"]

dayJournal = collections.namedtuple('dayJournal','date steps stepGoal stepDist dts occasional medical moviesTV project')
bookData = collections.namedtuple('bookData','date bookTitle bookFormat')

dayJournalDefault = dayJournal(curDate(),10000,10000,5.0,"DT","","","","")
bookDataDefault = bookData(curDate(),"","")

#
#   Daily Journal Data
#

class dayData(tk.Frame):
    def __init__(self,master = None, dbConn = None, outerTabs = None,initVals = (dayJournalDefault,bookDataDefault)):
        tk.Frame.__init__(self,master)
        self.grid()

        self.dbConn = dbConn
        self.tabs = outerTabs
        
        self.dataType = "Journal"
        self.dataTable = "DayJournal"
        self.dataCols = ["Date","Steps","StepGoal","StepDistance","DTS","OccasionalActions","MedLog","MoviesTV","ProjectWork"]
        self.bookTable = "BookTracking"
        self.bookCols = ["Date","BookTitle","BookFormat"]
        self.fetchBookTitles()

        self.date=dateFieldLeft(self,"Date",0)

        self.dataFrame = formFrame(self,"Journal Data",1,0,3,4)
        self.steps = dataFieldLeft(self.dataFrame.frame,"Step Count",1)
        self.stepGoal = dataFieldLeft(self.dataFrame.frame,"Step Goal",1,1)
        self.stepDist = dataFieldLeft(self.dataFrame.frame,"Step Distance",2,0)
        self.stepAvg = statusLabelBox(self.dataFrame.frame,"Avg stride","2.0",2,1)
        self.occasional = dataTextBox(self.dataFrame.frame,"Occasional Actions",3,0,2)
        self.medical = dataTextBox(self.dataFrame.frame,"Medical State",4,0,2)
        self.moviesTV = dataTextBox(self.dataFrame.frame,"Movies and TV",5,0,2)
        self.proj = dataTextBox(self.dataFrame.frame,"Projects",6,0,2)

        self.dtsFrame = formFrame(self,"DTS",1,3,1,2)
        self.flagD = dataCheckBox(self.dtsFrame.frame,"D",True,1,2)
        self.flagT = dataCheckBox(self.dtsFrame.frame,"T",True,2,2)
        self.flagS = dataCheckBox(self.dtsFrame.frame,"S",False,3,2)
        self.numS = dataFieldLeft(self.dtsFrame.frame,"",3,3)
        self.flagH = dataCheckBox(self.dtsFrame.frame,"H",False,4,2)
        self.numH = dataFieldLeft(self.dtsFrame.frame,"",4,3)
        self.flagNf = dataCheckBox(self.dtsFrame.frame,"f",False,1,3)
        self.flagNt = dataCheckBox(self.dtsFrame.frame,"t",False,2,3)

        self.reviewFrame = formFrame(self,"Mising Dates",3,3,1,3)
        self.viewStartDate = dateFieldLeft(self.reviewFrame.frame,"Start Date",initVal=twoWeeksBefore(curDate()))
        self.missingDates = messageListbox(self.reviewFrame.frame,1,0,3)
        self.missingDates.bindField("<ButtonRelease-1>",self.pickDate)

        self.refreshBtn = actionBtn(self,"Refresh Display",lambda event:self.refreshDispFn(),7,3)

        self.bookFrame = formFrame(self,None,1,4,3,4)

        self.bookFrame = formFrame(self,"Book Data",1,4,2,4)
        self.bookTitle = dataComboBox(self.bookFrame.frame,"Book Title",self.titleList,0)
        self.bookFormat = dataComboBox(self.bookFrame.frame,"Book Format",bookFormatDrop,1)
        self.bookSaveBtn = actionBtn(self.bookFrame.frame,"Save Book Only",lambda event:self.saveBook(),2)

        self.bookViewCfg = [treeColTpl("form",100,"Format")]
        self.bookView = treeView(self.bookFrame.frame,None,self.bookViewCfg,3)
        self.bookView.bindField("<Double-Button-1>",self.delBook)
        
        self.viewFrame = formFrame(self,"View",8,0,8)
        self.journalViewCfg = [
            treeColTpl("steps",60,"Step Goal"),
            treeColTpl("target",60,"Target"),
            treeColTpl("dist",60,"Distance"),
            treeColTpl("dts",50,"DTS"),
            treeColTpl("occasion",150,"Occasional Actions"),
            treeColTpl("med",150,"Medical"),
            treeColTpl("tv",150,"Television and Movies"),
            treeColTpl("proj",150,"Projects")]
        self.journalView = treeView(self.viewFrame.frame,None,self.journalViewCfg,8,0,7)
        self.journalView.setIconWidth(dateColWidth)
        self.journalView.setRowCount(5)
        self.journalView.bindField("<Double-Button-1>",self.pickDay)
            
        self.popView()


        self.saveBtn = actionBtn(self,"Save Journal",lambda event:self.saveJournal(),7)
        self.clrBtn = actionBtn(self,"Clear Data",lambda event:self.clearData(),7,1)
        self.saveFlag = dataCheckBox(self,"Save Data",False,7,2)


        self.commuteJump = actionBtn(self,"Commute Data",lambda event:self.tabJump(-1),7,4)
        self.bellaJump = actionBtn(self,"Arabella Data",lambda event:self.tabJump(1),7,5)

        self.steps.bindField("<FocusOut>",self.calcAvgStride)
        self.stepDist.bindField("<FocusOut>",self.calcAvgStride)

        self.setData(initVals)
        self.refreshDispFn()

    def popView(self,event=None):
        self.journalView.clearTree()
        self.displaySet = set()
        sqlStr = str.format("SELECT * FROM {} WHERE sortableDate(Date)>= sortableDate(?) ORDER BY sortableDate(Date)",self.dataTable)
        res = self.dbConn.execute(sqlStr,[self.viewStartDate.getVal()]).fetchall()
        for ln in res:
            self.displaySet.add(ln["Date"])
            self.journalView.addLine("",ln["Date"],ln[2:])

        allDateSet = daysSince(self.viewStartDate.getVal())
        missingDates = sorted(list(allDateSet-self.displaySet))
        tmpStr = str.format("{} of {}",len(missingDates),len(allDateSet))
        for ln in missingDates:
            self.missingDates.addLine(ln)

    def pickDay(self,event=None):
        selIID = self.journalView.getSelection()[0]
        popDate = self.journalView.getText(selIID)
        newData=self.fetchJournalData(popDate)
        self.setData(newData)
        
        

    def delBook(self,event = None):
        selIID = self.bookView.getSelection()[0]
        delFormat=self.bookView.getValues(selIID)[0]
        delTitle = self.bookView.getText(selIID)
        delDateIID = self.bookView.getCurParent(selIID)
        delDate = self.bookView.getText(delDateIID)
        delBook= bookData(delDate,delTitle,delFormat)

        bookSet = fetchSql(self.dbConn,self.bookTable,self.bookCols,delBook)
        if len(bookSet)>0:
            delSql(self.dbConn,self.bookTable,["BookID"],[bookSet[0]["BookID"]])

        self.bookView.clearTree()
        self.popRecentBooks()
        
        

    def refreshDispFn(self):
        self.missingDates.clearData()
        self.bookView.clearTree()
        self.popMissingDates()
        self.popRecentBooks()
        self.popView()

    def saveJournal(self):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)

    def popMissingDates(self):
        pass
##        res = self.dbConn.execute("SELECT Date FROM DayJournal WHERE sortableDate(Date)>sortableDate(?) ORDER BY sortableDate(Date)",[self.viewStartDate.getVal()]).fetchall()
##        for ln in res:
##            self.missingDates.addLine(ln["Date"])

    def pickDate(self,event=None):
        curLine = self.missingDates.getSelection()
        newData=self.fetchJournalData(curLine)
        self.setData(newData)

    def tabJump(self,delta):
        self.tabs.select(2+delta)

    def formatDTS(self):
        dts = ""
        flag = True
        if self.flagD.getVal():
            dts+="D"
            flag = False
        if self.flagT.getVal():
            dts+="T"
            flag = False
        if self.flagS.getVal():
            dts+="S"
            flag = False
        if self.numS.getVal()!="":
            dts+=self.numS.getVal()
            flag = False
        if self.flagH.getVal():
            dts+="H"+self.numH.getVal()
            flag = False
        if self.flagNf.getVal():
            dts+="f"
            flag = False
        if self.flagNt.getVal():
            dts+="t"
            flag = False
        if flag:
            dts="X"
        return dts

    def parseDTS(self,dts):#Replace with regex groups
        if dts.find("D")>-1:
            self.flagD.setVal(True)
        else:
            self.flagD.setVal(False)
            
        if dts.find("T")>-1:
            self.flagT.setVal(True)
        else:
            self.flagT.setVal(False)
            
        if dts.find("S")>-1:
            self.flagS.setVal(True)
            nextChar = dts[dts.find("S")+1]
            try:
                self.numS.setVal(int(nextChar))
            except ValueError:
                pass
        else:
            self.flagS.setVal(False)
            
        if dts.find("H")>-1:
            self.flagH.setVal(True)
            nextChar = dts[dts.find("H")+1]
            try:
                self.numH.setVal(int(nextChar))
            except ValueError:
                pass
        else:
            self.flagH.setVal(False)
            
        if dts.find("f")>-1:
            self.flagNf.setVal(True)
        else:
            self.flagNf.setVal(False)
            
        if dts.find("t")>-1:
            self.flagNt.setVal(True)
        else:
            self.flagNt.setVal(False)

    def fetchBookTitles(self):
        sqlStr = str.format("SELECT DISTINCT BookTitle FROM {} ORDER BY BookTitle",self.bookTable)
        res = self.dbConn.execute(sqlStr).fetchall()
        self.titleList = [book["BookTitle"] for book in res]
        
    def getData(self):
        outJournal = dayJournal(
            self.date.getVal(),
            self.steps.getVal(),
            self.stepGoal.getVal(),
            self.stepDist.getVal(),
            self.formatDTS(),
            self.occasional.getVal(),
            self.medical.getVal(),
            self.moviesTV.getVal(),
            self.proj.getVal())
        outBook = bookData(
            self.date.getVal(),
            self.bookTitle.getVal(),
            self.bookFormat.getVal())
        return (outJournal,outBook)

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        


    def saveData(self):

        if not saveNotify("Journal",self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True

        journalData,bookInfo = self.getData()

        replaceSql(self.dbConn,self.dataTable,self.dataCols,journalData)

        if self.bookFormat.getVal()!="None":
            insertSql(self.dbConn,self.bookTable,self.bookCols,bookInfo)

        self.refreshDispFn()
        self.statusBox.addLine("Saved Journal Data for {}".format(self.date.getVal()))

        return True

    def saveBook(self):
        bookSave=self.getData()[1]
        insertSql(self.dbConn,self.bookTable,self.bookCols,bookSave)
##        sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.bookTable,",".join(self.bookCols),"?"+",?"*(len(self.bookCols)-1))
##        self.dbConn.execute(sqlStr,self.getData()[1])        
##        self.dbConn.commit()
        self.addBookLine(bookSave)
        self.statusBox.addLine("Saved Book Data for {}".format(self.date.getVal()))


    def setData(self,newData):
        newJournal = newData[0]
        newBook = newData[1]

        if newJournal == None:
            newJournal = dayJournalDefault

        if newBook == None:
            newBook = bookDataDefault
        
        self.date.setVal(newJournal.date)
        self.steps.setVal(newJournal.steps)
        self.stepGoal.setVal(newJournal.stepGoal)
        self.stepDist.setVal(newJournal.stepDist)
        self.parseDTS(newJournal.dts)
        self.occasional.setVal(newJournal.occasional)
        self.medical.setVal(newJournal.medical)
        self.bookTitle.setVal(newBook.bookTitle)
        self.bookFormat.setVal(newBook.bookFormat)
        self.moviesTV.setVal(newJournal.moviesTV)
        self.proj.setVal(newJournal.project)

        self.calcAvgStride()
        
        return

    def calcAvgStride(self,event=None):
        steps = int(self.steps.getVal())
        dist = self.stepDist.getVal()
        if dist!=None and dist!="None":
            dist=float(dist)
            stride = str.format("{:1.2f} ft/step, {:d} steps/mile",(5280.*dist)/steps, int(steps/dist))
        else:
            stride = "None"
        self.stepAvg.setVal(stride)


    def clearData(self):
        self.date.setVal("")
        self.steps.setVal("")
        self.stepGoal.setVal("")
        self.stepDist.setVal("")
        self.parseDTS("")
        self.occasional.setVal("")
        self.medical.setVal("")
        self.bookTitle.setVal("")
        self.bookFormat.setVal("")
        self.moviesTV.setVal("")
        self.proj.setVal("")
        return

    def fetchJournalData(self,date):
        sqlStrDay = str.format("SELECT * FROM {} WHERE Date = (?)",self.dataTable)
        sqlStrBook = str.format("SELECT * FROM {} WHERE Date = (?)",self.bookTable)
        dayRes = self.dbConn.execute(sqlStrDay,(date,)).fetchone()
        bookRes = self.dbConn.execute(sqlStrBook,(date,)).fetchall()
        if dayRes != None:
            newJournal = dayJournal(
                dayRes["Date"],
                dayRes["Steps"],
                dayRes["StepGoal"],
                dayRes["StepDistance"],
                dayRes["DTS"],
                dayRes["OccasionalActions"],
                dayRes["MedLog"],
                dayRes["MoviesTV"],
                dayRes["ProjectWork"])
        else:
            newJournal=None
            
        if len(bookRes)>0:
            newBook = [bookData(
                            ln["Date"],
                            ln["BookTitle"],
                            ln["BookFormat"]) for ln in bookRes]
            
        else:
            newBook=[None]

        return (newJournal,newBook[0])

    def setDate(self,newDate):
        self.date.setVal(newDate)

        self.setData(self.fetchJournalData(newDate))

    def addBookLine(self,newBook):
        dateIID = self.bookView.getIID(newBook.date) #'date bookTitle bookFormat'        
        if dateIID == "":
            newIID = self.bookView.addLine(dateIID,newBook.date,[])#["",""])
            self.bookView.addLine(newIID,newBook.bookTitle,[newBook.bookFormat])
        else:
            self.bookView.addLine(dateIID,newBook.bookTitle,[newBook.bookFormat])

    def popRecentBooks(self):
        workDate=self.viewStartDate.getVal()
        sqlStrBook = str.format("SELECT * FROM {} WHERE sortableDate(Date)>= (sortableDate(?)) ORDER BY sortableDate(Date)",self.bookTable)
        bookRes = self.dbConn.execute(sqlStrBook,[workDate]).fetchall()

        if len(bookRes)>0:
            for ln in bookRes:
                self.addBookLine(bookData(
                            ln["Date"],
                            ln["BookTitle"],
                            ln["BookFormat"]))
                
