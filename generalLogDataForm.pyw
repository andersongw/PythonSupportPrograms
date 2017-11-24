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
from generalDataLogSleep import *
from generalDataLogCommute import *
from generalDataLogJournal import *
from generalDataLogArabella import *
from generalDataLogDefcon import *
from generalDataLogWeight import *
from generalDataLogOmcron import *

import autoversion as av


av.dispRunDateTime()
##av.autoversionList((
##    "autoversion.py",
##    "guiBlocks.py",
##    "generalLogDataForm.pyw",
##    "generalDataLogFunctions.py",
##    "generalDataLogSleep.py",
##    "generalDataLogCommute.py",
##    "generalDataLogJournal.py",
##    "generalDataLogArabella.py",
##    "generalDataLogDefcon.py",
##    "generalDataLogWeight.py",
##    "generalDataLogOmcron.py"))
el=av.editLog()
el.autoversionList((
    "autoversion.py",
    "guiBlocks.py",
    "generalLogDataForm.pyw",
    "generalDataLogFunctions.py",
    "generalDataLogSleep.py",
    "generalDataLogCommute.py",
    "generalDataLogJournal.py",
    "generalDataLogArabella.py",
    "generalDataLogDefcon.py",
    "generalDataLogWeight.py",
    "generalDataLogOmcron.py"))


dbFileDir=os.getcwd()
dbFile="GeneralDataLog.db"

#
#   Month Display Class
#

class monthGrid(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dayWidth= 45
        self.dayBorderX = 2
        self.dayHeight = 45
        self.dayBorderY = 2
        self.dayGridX = 2*self.dayBorderX + self.dayWidth
        self.dayGridY = 2*self.dayBorderY + self.dayHeight
        self.curDay = [0,0]
        self.firstGrid = "2016/"
        
        self.canvas = tk.Canvas(self,height=self.dayGridY*6+5,width=self.dayGridX*7+5)
        
        for row in range(1,6):
            for col in range(7):
                self.canvas.create_rectangle(
                    self.dayGridX * col + self.dayBorderX,
                    self.dayGridY * row + self.dayBorderY,
                    self.dayGridX * (col+1) - self.dayBorderX,
                    self.dayGridY * (row+1) - self.dayBorderY)
        for col in range(7):
            self.canvas.create_text(
                (col + 0.5) * (2 * self.dayBorderX + self.dayWidth),
                self.dayHeight,
                text=("Sun","Mon","Tues","Wed","Thur","Fri","Sat")[col])

        self.canvas.grid()

    def renum(self,date):
        pass

def dateScroll(dateField,event):
    dateField.stepDate(event)
    workDate = dt.datetime.strptime(dateField.getVal(),"%m/%d/%y")
    workDay.setVal(workDate.strftime("%A"))
    

#
#   Begin Main Program
#

win = tk.Tk()


fullNameDB = os.path.join(dbFileDir, dbFile)

if not os.path.isfile(fullNameDB):
    fullNameDB = tkfd.askopenfilename()
conn = sqlite3.connect(fullNameDB)
conn.row_factory = sqlite3.Row
conn.create_function("sortableDate",1,sortableDate)

dateFrame = tk.Frame(win)
dateFrame.grid(row=0,sticky=tk.W)
workDate = dateFieldLeft(dateFrame,"Date:  ")
workDate.setVal(curDate())
workDay = statusLabelBox(dateFrame,"",curDay(),0,1)
#saveBtn = actionBtn(dateFrame,"Save",lambda event:saveFn(),0,4,2)
saveBtn = actionBtn(dateFrame,"Save",lambda event:statusBox.addLine("This button no longer implemented"),0,4,2)
exitBtn = actionBtn(dateFrame,"Exit",lambda event:win.destroy(),0,6)


workDate.bindField('<FocusOut>',lambda event:dateUpdate(workDate,event))
workDate.bindField('<KeyRelease-Up>',lambda event:dateChange(event,1))
workDate.bindField('<KeyRelease-Down>',lambda event:dateChange(event,-1))
workDate.bindField('<MouseWheel>',lambda event:dateScroll(workDate,event))

inputFrame = tk.LabelFrame(win,text = "Input Data")
inputFrame.grid(row=1,sticky=tk.W)

tabs = ttk.Notebook(inputFrame)
tabs.grid(sticky = tk.NSEW)

sleepTab = sleepFrame(tabs,conn,tabs)
commuteTab = commuteData(tabs,conn,tabs)
journalTab = dayData(tabs,conn,tabs)
arabellaTab = bellaDataFrm(tabs,conn,tabs)
defconTab = defconData(tabs,conn,tabs)
wwScaleTab = wwScaleData(tabs,conn,tabs)
fatTab = fatAnalyzerData(tabs,conn)

tabs.add(sleepTab,text = "Sleep Tracking")
tabs.add(commuteTab,text = "Commute")
tabs.add(journalTab,text = "Day Journal")
tabs.add(arabellaTab,text = "Arabella")
tabs.add(defconTab,text = "Defcon")
tabs.add(wwScaleTab,text = "Weight Watchers Scale")
tabs.add(fatTab,text = "Omcron Bodyfat Analyzer")
tabs.enable_traversal()
tabs.curTab = 0
##tabs.bind("<<NotebookTabChanged>>",lambda event:tabChange(event,tabs,newTree))

statusFrame = tk.LabelFrame(win,text="Status")
statusFrame.grid(row=1,column=1,sticky=tk.NS)

statusBox=messageListbox(statusFrame,w=2,boxWidth = 30,boxHeight=40)

sleepTab.connectStatus(statusBox)
commuteTab.connectStatus(statusBox)
journalTab.connectStatus(statusBox)
arabellaTab.connectStatus(statusBox)
defconTab.connectStatus(statusBox)
wwScaleTab.connectStatus(statusBox)
fatTab.connectStatus(statusBox)

                                 
win.mainloop()

conn.close()
