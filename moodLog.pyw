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

import autoversion as av

av.dispRunDateTime()
av.autoversionList(("autoversion.py","guiBlocks.py","moodLog.pyw"))


class hScaleLeft(tk.Frame,baseDataControl):
    def __init__(self,master=None, label=None, rng=(1,5),initVal = 0, r=0, c=0, w=1, h=1, desc = None):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        (self.minVal,self.maxVal)=(min(rng),max(rng))

        self.data = tk.IntVar()
        self.data.set(initVal)
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Scale(master,variable=self.data,orient=tk.HORIZONTAL, from_=self.minVal, to = self.maxVal)
        self.field.grid(row = realRow, column = realCol+1, columnspan = realSpan-1,rowspan=realHeight)
        
        self.field.bind("<MouseWheel>",self.scrollBar)

    def scrollBar(self,event=None):
        curVal = self.data.get()
        if event.delta>0:
            self.data.set(min(self.maxVal,curVal+1))
        else:
            self.data.set(max(self.minVal,curVal-1))
        

    def setScaleLabels(self,newLabels):
        pass            

    def setRange(self,newRange):
        (self.minVal,self.maxVal)=(min(rng),max(rng))
        self.field["from_"]=self.minVal
        self.field["to"]=self.maxVal

    def setLow(self,newLow):
        self.minVal = newLow
        self.field["from_"]=newLow

    def setHigh(self,newHigh):
        self.maxVal = newHigh
        self.field["to"]=newHigh

class hScaleTop(hScaleLeft):
    def __init__(self,master=None, label=None, rng=(0,5),initVal = 0, r=0, c=0, w=1, h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        (self.minVal,self.maxVal)=(min(rng),max(rng))

        self.data = tk.IntVar()
        self.data.set(initVal)
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Scale(variable=self.data,orient=tk.HORIZONTAL, from_=self.minVal, to = self.maxVal)
        self.field.grid(row = realRow+1, column = realCol, rowspan = realHeight-1,columnspan=realSpan)
   

class vScaleTop(hScaleLeft):
    def __init__(self,master=None, label=None, rng=(0,5),initVal = 0, r=0, c=0, w=1, h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        (self.minVal,self.maxVal)=(min(rng),max(rng))

        self.data = tk.IntVar()
        self.data.set(initVal)
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Scale(variable=self.data,orient=tk.VERTICAL, from_=self.minVal, to = self.maxVal)
        self.field.grid(row = realRow, column = realCol+1, columnspan = realSpan-1,rowspan=realHeight)

class vScaleLeft(hScaleLeft):
    def __init__(self,master=None, label=None, rng=(0,5),initVal = 0, r=0, c=0, w=1, h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        (self.minVal,self.maxVal)=(min(rng),max(rng))

        self.data = tk.IntVar()
        self.data.set(initVal)
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Scale(variable=self.data,orient=tk.VERTICAL, from_=self.minVal, to = self.maxVal)
        self.field.grid(row = realRow+1, column = realCol, columnspan = realSpan,rowspan=realHeight-1)
    
class clockTime(tk.Frame):
    def __init__(self,master=None,r=0,c=0,w=1,h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        self.data = tk.StringVar()
        self.field = tk.Label(master,textvariable=self.data)
        self.field.grid(row = realRow,column=realCol,columnspan=realSpan,rowspan=realHeight)
        self.clockID = None
        self.runClock()

    def updateTime(self):
        self.data.set(dt.datetime.now().strftime("%H:%M"))

    def runClock(self):
        self.updateTime()
        self.clockID=self.after(60000,self.runClock)

    def toggleClock(self):
        if self.clockID==None:
            runClock()
        else:
            self.after_cancel(self.clockID)


class countdownTimer(tk.Frame):
    def __init__(self,master=None,timerVal = "15:00",r=0,c=0,w=1,h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        self.tmr=None
        self.timeInterval = 1 #second
        self.dtDelta = dt.timedelta(seconds = self.timeInterval)
        self.dtTimer = dt.timedelta()
        self.startTimer = timerVal
        self.tmrFrame = tk.Frame(master)
        self.tmrFrame.grid(row=realRow,column=realCol, columnspan=realSpan,rowspan = realHeight)
        self.runTmr = dataCheckBox(self.tmrFrame,"Run Timer",0,0,cmd=self.toggleTmr)
        self.tmrVal = dataFieldLeft(self.tmrFrame,"Timer Value",1,0,initVal=timerVal)
        self.parseTime = "(\d?\d)?:?(\d?\d)?:?(\d?\d)"
        


    def setTime(self):
        wkTime = self.tmrVal.getVal()
        timeLn = wkTime.count(":")
        if timeLn == 1:
            tmMatch = re.match("(?P<mn>\d?\d):(?P<sc>\d?\d)",wkTime)
            self.dtTimer = dt.timedelta(minutes = int(tmMatch.group("mn")), seconds = int(tmMatch.group("sc")))
        elif  timeLn == 2:
            tmMatch = re.match("(?P<hr>\d?\d):(?P<mn>\d?\d):(?P<sc>\d?\d)",wkTime)
            self.dtTimer = dt.timedelta(hours = int(tmMatch.group("hr")),minutes = int(tmMatch.group("mn")), seconds = int(tmMatch.group("sc")))
        self.startTimer = wkTime                 
        

    def toggleTmr(self):
        if self.runTmr.getVal():
            self.setTime()
            self.runTimer()
            self.tmrVal.toggleEnable(False)
        else:
            self.after_cancel(self.tmr)
            self.tmr=None
            self.tmrVal.toggleEnable(True)

##    def startTimer(self):
##        self.tmr=self.after(1000,self.runTimer)

    def runTimer(self):
        self.tmr=self.after(1000 * self.timeInterval,self.runTimer)
        self.dtTimer=self.dtTimer-self.dtDelta
        self.tmrVal.setVal(str(self.dtTimer))
        if self.dtTimer == dt.timedelta():
            self.timerEnd()
            

    def timerEnd(self):
        #print("End!")
        self.after_cancel(self.tmr)
        self.tmr=None
        self.tmrVal.setVal(self.startTimer)
        self.runTmr.setVal(False)
##        print("End Timer")
##        win.lift()
##        win.attributes('-topmost', 1)
##        win.attributes('-topmost', 0)
        

moodTuple=collections.namedtuple("moodTuple",'energy energyNote hunger hungerNote focus focusNote anger angerNote stamp')

class moodDlg(tk.Frame):
    def __init__(self,master=None,dbConn=None):
        tk.Frame.__init__(self,master)
        self.dbConn = dbConn
        self.grid()
        scaleFrame = formFrame(self,"Quantities",0,0)
        otherFrame = formFrame(self,"Controls",0,1)
        self.energy = hScaleLeft(scaleFrame.frame,"Energy",(1,5),3,0)
        self.hunger = hScaleLeft(scaleFrame.frame,"Hunger",(1,5),3,1)
        self.focus = hScaleLeft(scaleFrame.frame,"Focus",(1,5),3,2)
        self.anger = hScaleLeft(scaleFrame.frame,"Anger",(1,5),3,3)

        self.energyNote = dataTextBox(scaleFrame.frame,"",0,1)
        self.hungerNote = dataTextBox(scaleFrame.frame,"",1,1)
        self.focusNote = dataTextBox(scaleFrame.frame,"",2,1)
        self.angerNote = dataTextBox(scaleFrame.frame,"",3,1)

        self.energyNote.bindField("<KeyPress>",self.resetBackground)
        self.hungerNote.bindField("<KeyPress>",self.resetBackground)
        self.focusNote.bindField("<KeyPress>",self.resetBackground)
        self.angerNote.bindField("<KeyPress>",self.resetBackground)
        self.bgColor="#abf"
        

        self.clock = clockTime(otherFrame.frame,0)
        self.timer = countdownTimer(otherFrame.frame,r=1)
        self.logBtn = actionBtn(otherFrame.frame,"Record Snapshot",self.logSnap,2)
        self.msgBox = messageListbox(otherFrame.frame,3)
        
        self.dataTable = "InternalStates"
        self.dataCols = ["Energy","EnergyNote","Hunger","HungerNote","Focus","FocusNote","Anger","AngerNote","TimeStamp"]

    def getNoteText(self,widget):
        if widget.setBackground() == self.bgColor:
            return None
        return widget.getVal()
            

    def getData(self):
        return moodTuple(
            self.energy.getVal(),self.getNoteText(self.energyNote),
            self.hunger.getVal(),self.getNoteText(self.hungerNote),
            self.focus.getVal(),self.getNoteText(self.focusNote),
            self.anger.getVal(),self.getNoteText(self.angerNote),
            dt.datetime.now().isoformat())

    def logSnap(self,event=None):
        snap = self.getData()
        #print(snap)
        insertSql(self.dbConn,self.dataTable,self.dataCols,snap)
        self.msgBox.addLine(self.snapMessage(snap))

        bgColor="#abf"
        self.energyNote.setBackground(self.bgColor)
        self.hungerNote.setBackground(self.bgColor)
        self.focusNote.setBackground(self.bgColor)
        self.angerNote.setBackground(self.bgColor)

##        Didn't make any difference; may make this trigger on receiving focus
##        self.energyNote.selectAll()
##        self.hungerNote.selectAll()
##        self.focusNote.selectAll()
##        self.angerNote.selectAll()
        
    def snapMessage(self,snap):
        return str.format("Recorded {}{}{}{} at {}",
            snap.energy,
            snap.hunger,
            snap.focus,
            snap.anger,
            dt.datetime.now().strftime("%H:%M"))

    def resetBackground(self,event=None):
        event.widget["bg"]="SystemWindow"
        


"""
Quantities to monitor:
Aggression/Benevolence -- degree of inchoate rage
Depression
Energy/Exhaustion
Diligence/Focus
Hunger -- How hungry am I
Diet -- How well am I eating

Add a second tab with check boxes for what I'm working on (pull from toDo Manager
code) and probably how I'm wasting my time.  Not sure how I'll have to modify the
database to accomodate the new data

"""
dbFileDir = os.getcwd()
dbFile="moodDB.db"
conn = sqlite3.connect(os.path.join(dbFileDir, dbFile))
conn.row_factory = sqlite3.Row

win = tk.Tk()
watchMood = moodDlg(win,conn)


win.mainloop()

conn.close()
