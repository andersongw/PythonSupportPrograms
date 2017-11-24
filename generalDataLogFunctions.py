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

def curDate():
    return dt.date.today().strftime("%m/%d/%y")

#
#   Global support functions
#

def saveNotify(dataType,saveFlag):
    
    if saveFlag:
        retVal = tkmb.askokcancel(message = str.format("Saving {} data",dataType))
    else:
        retVal = tkmb.askokcancel(message = str.format("Skipping {} data",dataType))
        
    return retVal

def saveFn():
    statusBox.addLine("This Save button is no longer active.")
    
##    if not sleepTab.saveData():
##        return
##    if not commuteTab.saveData():
##        return
##    if not journalTab.saveData():
##        return
##    if not arabellaTab.saveData():
##        return
##    if not defconTab.saveData():
##        return
##    if not wwScaleTab.saveData():
##        return
##    if not fatTab.saveData():
##        return


def dateUpdate(dateField,event):
    dateField.exitDateField(event)
    newData=dateField.getVal()
    workDay.setVal(dt.datetime.strptime(newData,"%m/%d/%y").strftime("%A"))
    sleepTab.setDate(newData)
    commuteTab.setDate(newData)
    journalTab.setDate(newData)
    arabellaTab.setDate(newData)
    defconTab.setDate(newData)
    wwScaleTab.setDate(newData)
    fatTab.setDate(newData)

def makeUpdateStr(dbTable,setCols,whereCond):
    return str.format("UPDATE {} SET {} WHERE {}",dbTable,",".join([col+"=? " for col in setCols]),whereCond)

def cleanTime(timeStr):
    timeRe = re.compile(r"(?P<H>[012]?\d):?(?P<M>\d{2})")
    H,M = (int(n) for n in timeRe.match(timeStr).group('H','M'))
    return str.format("{:02d}:{:02d}",H,M)

