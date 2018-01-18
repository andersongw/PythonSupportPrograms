# Last Edited 01/17/18
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


sleepData = collections.namedtuple('sleepData','date target actual begin end deep light awake wakeTime wakeLocation note wakeArtist wakeSong wakePhrase')
sleepDataDefault = sleepData(curDate(), 6,6, "11:30","6:00","4:00","3:00","0:00","6:00", "NJ","","","","")

## Setup UI

#
#   Sleep Record Data
#

##sleepData = collections.namedtuple('sleepData',
#   'date target actual deep light awake wakeTime wakeLocation note wakeArtist wakeSong wakePhrase')
##sleepDataDefault =
##  sleepData(curDate(), 6,6, "4:00","3:00","0:00","6:00", "NJ","","","","")

class sleepFrame(tk.Frame):
    def __init__(self,master = None, dbConn = None,outerTabs = None, initVals = sleepDataDefault):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.tabs = outerTabs

        self.dataFrame = formFrame(self,"Data Entry",0,0)
        self.date = dateFieldTop(self.dataFrame.frame,"Date",0,0)
        self.location = dataFieldTop(self.dataFrame.frame,"Waking Location",0,1,2)
        self.target = dataFieldTop(self.dataFrame.frame,"Target",1,0)
        self.actual = dataFieldTop(self.dataFrame.frame,"Actual",1,1)
        self.wake = dataFieldTop(self.dataFrame.frame,"Wake Time",1,2)
        self.sleepTime = statusLabelBoxTop(self.dataFrame.frame,"Fell Asleep","",1,3)
        self.beginTime = dataFieldTop(self.dataFrame.frame,"Begin",2,0)
        self.endTime = dataFieldTop(self.dataFrame.frame,"End",2,1)
        self.deep = dataFieldTop(self.dataFrame.frame,"Deep",2,2)
        self.light = dataFieldTop(self.dataFrame.frame,"Light",2,3)
        self.awake = dataFieldTop(self.dataFrame.frame,"Awake",2,4)
        self.note = dataFieldLeft(self.dataFrame.frame,"Note",3,0,4)
        self.artist = dataFieldLeft(self.dataFrame.frame,"Wake -- Artist",4,0,5)
        self.song = dataFieldLeft(self.dataFrame.frame,"Waking Lyrics -- Song",5,0,5)
        self.lyric = dataFieldLeft(self.dataFrame.frame,"Waking Lyrics -- Phrase",6,0,5)

        #self.saveBtn = actionBtn(self,"Save Sleep Data",lambda event:self.saveData,7,0)
        self.saveBtn = actionBtn(self.dataFrame.frame,"Save Sleep Data",lambda event:self.saveBtnFn(),7,0)
        self.clrBtn = actionBtn(self.dataFrame.frame,"Clear Data",lambda event:self.clearData(),7,1)
        self.saveFlag = dataCheckBox(self.dataFrame.frame,"Save Data",False,7,2)
        self.nextTab = actionBtn(self.dataFrame.frame,"Commute Tab",lambda event:self.jumpTab(),7,3)

        self.setData(initVals)
        self.showSleepTime()

        #self.viewFrame = formFrame(self,"Data View",8,0,7,5)
        self.viewFrame = formFrame(self,"Data View",1,0)
        self.viewStart = dateFieldLeft(self.viewFrame.frame,"View Startdate",0,0,1,twoWeeksBefore(curDate()))
        self.viewRefresh = actionBtn(self.viewFrame.frame,"Refresh",lambda event:self.refreshView(),0,1)
        colWide = 60
        self.viewCfg=[
            treeColTpl('target',colWide,'Target'),
            treeColTpl('actual',colWide,'Actual'),
            treeColTpl('bedtime',colWide,'Bedtime'),
            treeColTpl('waketime',colWide,'Wake-up'),
            treeColTpl('begintime',colWide,'Begin'),
            treeColTpl('endtime',colWide,'End'),
            treeColTpl('deep',colWide,'Deep'),
            treeColTpl('light',colWide,'Light'),
            treeColTpl('awake',colWide,'Awake')]
        self.viewSleep = treeView(self.viewFrame.frame,None,self.viewCfg,1,0,4)
        self.viewSleep.setIconWidth(dateColWidth)
        self.missingLabel=statusLabelBox(self.viewFrame.frame,"Missing Dates","0 of 0",0,5)
        self.missingDaysList=messageListbox(self.viewFrame.frame,1,5)
        self.initialView()    

        
        self.dataType = "Sleep"
        self.dataTable = "SleepData"
        self.dataCols = ["Date","Target","Actual","VivofitBegin","VivofitEnd","VivofitDeep","VivofitLight","VivofitAwake","WakeTime","WakeLocation","Note","WakeLyricsArtist","WakeLyricsSong","WakeLyricsPhrase"]

        self.wake.bindField("<FocusOut>",self.showSleepTime)
        self.actual.bindField("<FocusOut>",self.showSleepTime)
        self.viewStart.bindField("<FocusOut>",self.refreshView)
        self.missingDaysList.bindField("<Double-Button-1>",self.pickMissingDate)
        self.viewSleep.bindField("<Double-Button-1>",self.pickSleepDate)
        self.beginTime.bindField("<FocusOut>",self.fixPM)

    # Use this function to adjust a start time listed in 12-hr format (assumes I'll never go to sleep
    #   between 10 am and 1 pm 
    def fixPM(self,event=None):
        newTime = dt.datetime.strptime(self.beginTime.getVal(),"%H:%M")
        if newTime.hour > 9 and newTime.hour <13:
            newTime = newTime + dt.timedelta(hours=12)
        self.beginTime.setVal(newTime.strftime('%H:%M'))

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        
    def pickSleepDate(self,event=None):
        curLine=self.viewSleep.getSelection()[0]
        curDate = self.viewSleep.getText(curLine)
        curData=self.fetchSleepData(curDate)
        self.setData(curData)


    def pickMissingDate(self,event=None):
        try:
            curLine = self.missingDaysList.getSelection()
            self.date.setDateText(curLine)
            self.target.takeFocus()
        except:
            print("exception pickMissingDate (121)")
            
    def jumpTab(self):
        print(self.tabs.select(1))

    def refreshView(self,event=None):
        self.viewSleep.clearTree()
        self.missingDaysList.clearData()
        self.initialView()

    def getData(self):
        return sleepData(self.date.getVal(),
                float(self.target.getVal()),
                float(self.actual.getVal()),
                self.beginTime.getVal(),
                self.endTime.getVal(),
                self.deep.getVal(),
                self.light.getVal(),
                self.awake.getVal(),
                self.wake.getVal(),
                self.location.getVal(),
                self.note.getVal(),
                self.artist.getVal(),
                self.song.getVal(),
                self.lyric.getVal())

    def setData(self,newData):
        self.date.setDateText(newData.date)
        self.location.setVal(newData.wakeLocation)
        self.target.setVal(newData.target)
        self.actual.setVal(newData.actual)
        self.wake.setVal(newData.wakeTime)
        self.beginTime.setVal(newData.begin)
        self.endTime.setVal(newData.end)
        self.deep.setVal(newData.deep)
        self.light.setVal(newData.light)
        self.awake.setVal(newData.awake)
        self.note.setVal(newData.note),
        self.artist.setVal(newData.wakeArtist),
        self.song.setVal(newData.wakeSong)
        self.lyric.setVal(newData.wakePhrase)
        return

    def clearData(self):
        self.date.setDateText(curDate())
        self.location.setVal("")
        self.target.setVal("")
        self.actual.setVal("")
        self.wake.setVal("")
        self.deep.setVal("")
        self.light.setVal("")
        self.awake.setVal("")
        self.artist.setVal("")
        self.song.setVal("")
        self.lyric.setVal("")
        return

    def setDate(self,newDate):
        self.date.setDateText(newDate)

        newData = self.fetchSleepData(newDate)

        if newData == None:
            self.setData(sleepDataDefault)
            self.date.setDateText(newDate)
            return

        self.setData(newData)
        
        #tkmb.showinfo(message=self.fetchSleepData(newDate))
        # Need to decide what to do here when the date is changed;
        # What data to display; what warnings if no existing data

    def fetchSleepData(self,date):
        wkDate = stampFromDate(date)
        sqlStr = str.format("SELECT * FROM {} WHERE Date = (?)",self.dataTable)
        cur = self.dbConn.execute(sqlStr,(wkDate,))
        res = cur.fetchone()
        if res == None:
            return None

        return sleepData(res["Date"],
                         res["Target"],
                         res["Actual"],
                         res["VivofitBegin"],
                         res["VivofitEnd"],
                         res["VivofitDeep"],
                         res["VivofitLight"],
                         res["VivofitAwake"],
                         res["WakeTime"],
                         res["WakeLocation"],
                         res["Note"],
                         res["WakeLyricsArtist"],
                         res["WakeLyricsSong"],
                         res["WakeLyricsPhrase"])


    def showSleepTime(self,event=None):
        res = self.calcSleepTime(self.actual.getVal(),self.wake.getVal())
        self.sleepTime.setVal(res)

    def calcSleepTime(self,actual,wakeTime):
        timeAsleep = dt.timedelta(hours=float(actual))
        timeAwake = dt.datetime.strptime(wakeTime,"%H:%M")
        timeToSleep = timeAwake-timeAsleep
        return timeToSleep.strftime("%H:%M")

    def saveBtnFn(self,Event=None):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)
        #self.date.setVal(nextDay(self.date.getVal()))
        self.date.stepDate()
        self.target.takeFocus()


        
    def saveData(self):

        if not saveNotify(self.dataType,self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True

        saveSleep = self.getData()
        newSaveSleep = saveSleep._replace(date=self.date.getDateStamp())

        replaceSql(self.dbConn,self.dataTable,self.dataCols,newSaveSleep)

        self.dbConn.commit()
        self.refreshView()

        self.statusBox.addLine("Saved Sleep Data for {}".format(self.date.getDateText()))

        return True

    def initialView(self):
        res = self.dbConn.execute("SELECT * FROM SleepData WHERE Date>=? ORDER BY Date",[self.viewStart.getDateStamp()]).fetchall()
        self.displayDateSet = set()
        for ln in res:
            self.displayDateSet.add(ln["Date"])
            viewLine = (dateFromStamp(ln["Date"]),
                        ln["Target"],
                        ln["Actual"],
                        self.calcSleepTime(ln["Actual"],ln["WakeTime"]),
                        ln["WakeTime"],
                        ln["VivofitBegin"],
                        ln["VivofitEnd"],
                        ln["VivofitDeep"],
                        ln["VivofitLight"],
                        ln["VivofitAwake"])
            self.addSleepView(viewLine)
        allDateSet={stampFromDate(ln) for ln in daysSince(self.viewStart.getVal())}
        missingDates=sorted(list(allDateSet-self.displayDateSet))
        tmpStr=str.format("{} of {}",len(missingDates),len(allDateSet))
        self.missingLabel.setVal(tmpStr)
        for ln in missingDates:
            self.missingDaysList.addLine(dateFromStamp(ln))
##        if len(missingDates)>0:
##            self.missingDaysList.setSelection(0)
        

    def addSleepView(self,viewData):
        self.viewSleep.addLine("",viewData[0],viewData[1:])
    
