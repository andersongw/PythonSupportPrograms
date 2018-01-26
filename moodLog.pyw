# Last Edited 01/22/18
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

el = av.editLog()
el.autoversionList((
		"autoversion.py",
		"guiBlocks.py",
		"moodLog.pyw"))


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
