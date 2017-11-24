# Last Edited 11/23/17
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

bellaCareClasses=["None","A few hours or less","Most of the day","Evening","Overnight","Note"]
bellaSleepClasses=["None","Stayed in Bed (We woke her)","Late Morning (Post-0700)","Mid Morning (0500-0700)","Early Morning (pre-0500)","Single Bed"]

bellaData = collections.namedtuple('bellaData','date wakeTime wakeNote')
bellaCareData = collections.namedtuple('bellaCareData','date careTime careNote')

bellaDataDefault = bellaData(curDate(),"Stayed in bed","Woke her when I left for work at 7:00")
bellaCareDefault = bellaCareData(curDate(),"A few hours","None")

#
#   Arabella Record Data
#

class bellaDataFrm(tk.Frame):
    def __init__(self,master = None, dbConn = None, outerTabs = None, initVals = (bellaDataDefault,bellaCareDefault)):
        tk.Frame.__init__(self,master)
        self.careClasses=bellaCareClasses 
        self.wakeClasses=bellaSleepClasses
        self.grid()
        self.date = dateFieldLeft(self,"Date",0,0,2)

        self.wakeFrame = formFrame(self,"Wake Data",1,0,3)
        self.recentFrame = formFrame(self,"Recent Dates",2,0,3,3)
        self.careFrame = formFrame(self,"Care Data",1,3,3,2)
        
        self.wakeTime = dataComboBox(self.wakeFrame.frame,"Wake Time Category",self.wakeClasses,0,0,1)
        self.wakeNote = dataTextBox(self.wakeFrame.frame,"Wake Time Note",1,0,3,boxW=40)
        
        self.careTime = dataComboBox(self.careFrame.frame,"Care Time Category",self.careClasses,0)
        self.careNote = dataTextBox(self.careFrame.frame,"Care Note",1,0,3,boxW=40)
        self.saveCareOnly = actionBtn(self.careFrame.frame,"Save Care Only",lambda event:self.saveCare(),2)
        
        self.startDate = dateFieldLeft(self.recentFrame.frame,"Start Date",0,initVal=deltaDate(-14))
        #self.dateView = messageListbox(self.recentFrame.frame,1,0,2)
        
        self.refreshView = actionBtn(self,"Refresh View",lambda event:self.popWakeView(),0,4)
        #self.dateView.bindField("<ButtonRelease-1>",self.pickDate)

        #self.careFrame = formFrame(self,None,1,5,1,5)
        self.careViewCfg = [
            treeColTpl("time",100,"Time"),
            treeColTpl("note",100,"Note")]
        self.careView = treeView(self.careFrame.frame,"Bella Care",self.careViewCfg,3,0,1,4)
        self.careView.setIconWidth(dateColWidth)
        self.careView.bindField("<<TreeviewSelect>>",self.pickCare)
        self.careView.bindField("<Double-Button-1>",self.delCare)
        
        self.wakeViewCfg = [
            treeColTpl("wakeCat",150,"Wake Category"),
            treeColTpl("wakeNote",250,"Wake Note")]
        self.wakeView = treeView(self.recentFrame.frame,"Wake Data",self.wakeViewCfg,1,0,2)
        self.wakeView.setIconWidth(dateColWidth)
        self.wakeView.bindField("<<TreeviewSelect>>",self.pickDate)


        buttonRow = 9
        self.saveBellaBtn = actionBtn(self,"Save Arabella Data",lambda event:self.saveBella(),buttonRow,0)
        self.clrBtn = actionBtn(self,"Clear Data",lambda event:self.clearData(),buttonRow,1)
        self.saveFlag = dataCheckBox(self,"Save Data",False,buttonRow,2)
        self.refreshView = actionBtn(self,"Refresh View",lambda event:self.popWakeView(),buttonRow,3)

        
        self.journalJump = actionBtn(self,"Journal Data",lambda event:self.jumpTabs(-1),buttonRow,4)
        self.defconJump = actionBtn(self,"Defcon Data",lambda event:self.jumpTabs(1),buttonRow,5)

        self.dbConn = dbConn
        self.tabs = outerTabs
        self.dataType = "Arabella"
        self.dataTable = "BellaData"
        self.dataCols = ["Date","WakeTime","SleepNote"]
        self.careTable = "BellaCareTracking"
        self.careCols = ["Date","CareTime","CareNote"]


        self.popWakeView()
        self.setData(initVals)

    def pickDate(self,Event=None):
        curLine = self.wakeView.getSelection()[0]
        curDate = self.wakeView.getText(curLine)
        (wakeData,careData)=self.fetchArabellaData(curDate)
        self.setWake(wakeData)
        print(careData)
        #should also set the current line in careView to the appropriate date

    def pickCare(self,event=None):
        selIID = self.careView.getSelection()[0]
        selCare = self.careView.getValues(selIID)
        careData = self.careView.getValues(selIID)
        if len(careData)<2:
            print("Date line",careData)
            return
        
        careTime,careTxt = careData
        self.careTime.setVal(careTime)
        self.careNote.setVal(careTxt)
        dateIID = self.careView.getCurParent(selIID)
        curDate = self.careView.getText(dateIID)
        self.date.setVal(curDate)
        (wakeData,careData)=self.fetchArabellaData(curDate)
        self.setWake(wakeData)
        
        
        
        
        # should pick the date, fetch the appropriate care data and populate the gui
        # should also call up the appropriate date in the wake view.
        # Maybe use ctrl-click to delete the line, to eliminate duplicates (similar to the book view
        
    def delCare(self,event=None):
        # First, identify the record to be deleted
        # Second, find the 
        selIID = self.careView.getSelection()[0]
        careData = self.careView.getValues(selIID)
        if len(careData)<2:
            return
        curID = self.careView.getDataID(selIID)
        print(curID)
        sqlStr = "DELETE FROM {} WHERE {} = ?".format(self.careTable,"BellaCareID")
        self.dbConn.execute(sqlStr,[curID])
        self.dbConn.commit()
        self.popWakeView()
        
        

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        
    def popWakeView(self):
        self.wakeView.clearTree()
        tmpStr=str.format("SELECT * FROM {} WHERE sortableDate(Date)>=? ORDER BY sortableDate(Date)",self.dataTable)
        res=self.dbConn.execute(tmpStr,[sortableDate(self.startDate.getVal())]).fetchall()
        for ln in res:
            self.wakeView.addLine("",ln["Date"],[ln["WakeTime"],ln["SleepNote"]])

        self.careView.clearTree()
        tmpStr=str.format("SELECT * FROM {} WHERE sortableDate(Date)>=? ORDER BY sortableDate(Date)",self.careTable)
        res=self.dbConn.execute(tmpStr,[sortableDate(self.startDate.getVal())]).fetchall()
        for ln in res:
            wkID = ln["BellaCareID"]
            wkDate = ln["Date"]
            lineIID=self.careView.getIID(ln["Date"])
            if lineIID == "":
                lineIID=self.careView.addLine(lineIID,ln["Date"],[])
            self.careView.addLineID(lineIID,"",[ln["CareTime"],ln["CareNote"]],dataID=ln["BellaCareID"])
            

                                

    def saveBella(self,event=None):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)
        

    def jumpTabs(self,delta):
        self.tabs.select(3+delta)

    def getData(self):
        
        newWake = bellaData(
           self.date.getVal(),
           self.wakeTime.getVal(),
           self.wakeNote.getVal())
        newCare = bellaCareData(
           self.date.getVal(),
           self.careTime.getVal(),
           self.careNote.getVal())
        return (newWake,newCare)

    def saveData(self):
        if not saveNotify("Arabella",self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True        
        
        saveWake,saveCare = self.getData()

        replaceSql(self.dbConn,self.dataTable,self.dataCols,saveWake)
        if self.careTime.getVal()!="None":
            insertSql(self.dbConn,self.careTable,self.careCols,saveCare)
            self.popWakeView()

        self.statusBox.addLine("Saved Bella Data for {}".format(self.date.getVal()))
        
        return True

    def saveCare(self,event=None):
        if self.careTime.getVal()=="None":
            return
##        sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.careTable,",".join(self.careCols),"?"+",?"*(len(self.careCols)-1))
##        self.dbConn.execute(sqlStr,saveCare)
        wake,care= self.getData()
        insertSql(self.dbConn,self.careTable,self.careCols,care)
        self.addCareToView(care)
        self.statusBox.addLine("Saved Care Only Data for {}".format(self.date.getVal()))
        

    def setWake(self,newWake):
        self.date.setVal(newWake.date)
        self.wakeTime.setVal(newWake.wakeTime)
        self.wakeNote.setVal(newWake.wakeNote)        

    def setData(self,newData):
        newWake,newCare = newData
        self.date.setVal(newWake.date)
        self.careTime.setVal(newCare.careTime)
        self.careNote.setVal(newCare.careNote)
        self.wakeTime.setVal(newWake.wakeTime)
        self.wakeNote.setVal(newWake.wakeNote)
        return
    
    def clearData(self):
        self.date.setVal("")
        self.careTime.setVal("")
        self.careNote.setVal("")
        self.wakeTime.setVal("")
        self.wakeNote.setVal("")
        return

    def setDate(self,newDate):
        self.date.setVal(newDate)
        #tkmb.showinfo(self,self.fetchArabellaData(newDate))
        # Need to decide what to do here when the date is changed;
        # What data to display; what warnings if no existing data

    def fetchArabellaData(self,date):
        cur = self.dbConn.execute("SELECT * FROM BellaData WHERE Date=(?)",(date,))
        res = cur.fetchone()
        if res != None:
            newBella = bellaData(res["Date"],
                                   res["WakeTime"],
                                   res["SleepNote"])
        else:
            newBella = bellaDataDefault
            
        cur = self.dbConn.execute("SELECT * FROM BellaCareTracking WHERE Date=(?)",(date,))
        res = cur.fetchone()
        if res != None:
            newCare = bellaCareData(res["Date"],
                                    res["CareTime"],
                                    res["CareNote"])
        else:
            newCare = bellaCareDefault
            
        return (newBella,newCare)

    def addCareToView(self,newCare):
        # Interesting -- this version of the careView lists the caretaker as the text, with the duration
        # and the note text as the values.  This is not preserved when the view is populated.
        # I honestly don't know which protocol I prefer.  It should be consistent, at least, however
        dateIID = self.careView.getIID(newCare.date)
        parseNote = re.match(r"(?P<caretaker>.*) ?\((?P<note>.*)\)",newCare.careNote)        
        if dateIID == "":
            newIID = self.careView.addLine(dateIID,newCare.date,["",""])
            self.careView.addLine(newIID,parseNote.group("caretaker"),(newCare[1],parseNote.group("note")))
        else:
            self.careView.addLine(dateIID,parseNote.group("caretaker"),(newCare[1],parseNote.group("note")))

