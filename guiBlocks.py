# Last Edited 11/23/17
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog as tksd
import tkinter.messagebox as tkmb
import collections
import sqlite3
import os
import os.path
import re
import datetime as dt
import calendar as cal
import hashlib


import pyperclip

"""
functions:
    rightClickPaste(event)
    rightClickPasteTextBox(event)
    insertSql(db,table,cols,data)
    updateSql(db,table,cols,data,keyCol,keyVal)

blocks:
    formFrame(master=None,label=None,r=0,c=0,w=1,h=1
    dataCheckBox(master = None, label = "Default",initVal = True,r=0,c=0,w=1,cmd=None)
    messageListBox(master = None, r=0,c=0,w=1,h=4)
    dataComboBox(master = None,label="Default",dispVals=["Val 1","Val 2"], r=0,c=0,w=1)
    dataComboTop
    statusLabelBox
    dataFieldTop(master=None,label="Default",r=0,c=0,w=1,initVal="")
    dataFieldLeft(master=None,label="Default",r=0,c=0,w=1,initVal="")
    dataTextBox(master = None, label = "Default", r=0,c=0,w=1,boxW=20, boxH=3,initVal = "", boxFont = ("Helvetica","8"))
    radioGroup
    actionBtn(master = None,label = "Default",action = None,r=0,c=0,w=1,h=1)
    treeColTpl = collections.namedtuple("treeColTpl","colName colWidth colHead")
    treeView(master=None,label="Default",colConfig=[treeColTpl("Default",50,"Default")],r=0,c=0,w=1,h=1)

 
""" 

class dataDialog(tksd.Dialog):
##    def __init__(self,master):
##        self.mainFrame = tk.Frame(self)
##        self.mainFrame.pack()
##        self.result = None
##        print("This ran")
##        tksd.Dialog.__init__(self,master)
    def body(self,master):
        self.mainFrame = tk.Frame(self)
        self.mainFrame.pack()
        self.result = None
        # when creating new dialogs, subclass from this class, and place all new controls
        # in the self.mainFrame frame
        # also -- assign the output from the dialog to self.result
        

#
##  Support functions of general applicability
#
stdDateRegex = re.compile("(?P<mn>\d{1,2})[\. /-](?P<dy>\d{1,2})[\. /-](?P<yr>\d{2})")
isoStampRegex = re.compile("20(?P<yr>\d{2})-(?P<mn>\d{2})-(?P<dy>\d{2})T(?P<hr>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2}\.\d*)")

baseDatePatterns=[
        #(?P<mn>)(?P<dy>)(?P<yr>)
        "(?P<mn>\d{1,2})[\. /-](?P<dy>\d{1,2})",
        "(?P<yr>\d{2})(?P<mn>\d{2})(?P<dy>\d{2})",
        "(?P<mn>\d{1,2})[\. /-](?P<dy>\d{1,2})[\. /-](?P<yr>\d{4}|\d{2})",
        "(?P<dy>\d{2})[\. /-](?P<mn>(jan[a-z]*)|(feb[a-z]*)|(mar[a-z]*)|(apr[a-z]*)|(may[a-z]*)|(jun[a-z]*)|(jul[a-z]*)|(aug[a-z]*)|(sep[a-z]*)|(oct[a-z]*)|(nov[a-z]*)|(dec[a-z]*))[\. /-](?P<yr>\d{4}|\d{2})",
	"20(?P<yr>\d{2})-(?P<mn>\d{2})-(?P<dy>\d{2})T(?P<hr>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2}\.\d*)"
		]
# In treeViews, this is the width that should be used in setIconWidth to leave adequate room for
# a MM/DD/YY formatted date
dateColWidth = 75

def checkCtrlClick(event):
    """Returns True if a click event includes a Ctrl-key flag."""
    return event.state & 0x4 == 0x4

def checkAltClick(event):
    """Returns True if a click event includes an Alt-key flag."""
    return event.state & 0x20000 == 0x20000

def checkWeblink(testStr):
    """Returns True if a string is formatted as a url."""
    return re.match("https?://",testStr)!=None

blkSize = 65536

def getFileHash(fname):
    """Returns the md5 hash (string) for the specified file (including path)."""
    curHash = hashlib.md5()
    try:
        with open(fname,"rb") as afile:
            buf = afile.read(blkSize)
            while len(buf)>0:
                curHash.update(buf)
                buf = afile.read(blkSize)
    except FileNotFoundError:
        return None
    except  PermissionError:
        return None
    return curHash.hexdigest()

def getBlobHash(blob):
    """Returns the md5 hash (string) for the specified binary blob."""
    curHash = hashlib.md5()
    curHash.update(blob)
    return curHash.hexdigest()

def locateFile(fileName,fileHash = None, testDirs = None, findFirst = True):
    profDir=os.environ["USERPROFILE"]
    if testDirs == None:
        testDirs = ["Desktop","Documents"]
    foundList = []
    foundFile = False
    checkCount = 0
    for wkDir in testDirs:
        print(wkDir)
        tree = os.walk(os.path.join(profDir,wkDir))
        for rt,dirs,files in tree:
            checkCount+=1
            if fileName in files:
                foundFile = os.path.join(rt,fileName)
                if findFirst:
                    return foundFile
                foundFile = True
                foundList.append(os.path.join(rt,fileName))
            if checkCount%100 == 0:
                print(checkCount)
    if foundFile:
        return foundList
    return None
                

def getFileData(fname):
    """Returns a tuple consisting of the file's extension, modification time (formatted according to ISO 8601), and size (in bytes)."""
    ext = os.path.splitext(fname)[1]
    try:
        fileStat = os.stat(fname)
        fileTime = dt.datetime.fromtimestamp(fileStat.st_mtime).isoformat()
    except FileNotFoundError:
        return [ext,None]
    return (ext,fileTime,fileStat.st_size)

def getFileStats(fileName):
    """Returns a tuple of the file's modification time (formatted according to ISO 8601) and size (in bytes)."""
    try:
        fileStat = os.stat(fileName)
        fileTime = dt.datetime.fromtimestamp(fileStat.st_mtime).isoformat()
        fileSize = fileStat.st_size
    except FileNotFoundError:
        return (None,None)
    return (fileTime,fileSize)

#   Do I want to incorporate a ctrl/alt filter to add additional functionality on the insert?
def rightClickPaste(event):
    """Replaces the text in a non-TextBox widget with the text on the clipboard.  Also sets the focus to that widget."""
    event.widget.delete(0,tk.END)
    event.widget.insert(0,pyperclip.paste())
    event.widget.focus_force()

def rightClickPasteTextBox(event):
    """Replaces the text in a TextBox widget with the text on the clipboard.  Also sets the focus to that widget."""
    event.widget.delete('1.0',tk.END)
    event.widget.insert('1.0',pyperclip.paste())
    event.widget.focus_force()

# Do I want to trigger this handler from a regular right click with a Ctrl-modifier filter?
def textBoxInsertPaste(event):
    """Inserts the text from the clipboard into the textbox at the cursor location"""
    event.widget.insert(tk.CURRENT,pyperclip.paste())
    event.widget.focus_force()

def insertSql(db,table,cols,data):#cols and data must be iterables (lists,tuples, etc.)
    """Inserts and commits a single record to the database; returns the rowID of the record that was just added.

    Input parameters are: the connection to the database of interest, the table where the data will be inserted,
    the columns corresponding to the data, and the data itself.
    (Note that both the columns and data must be iterables (and obviously must be the same length.)
    """
    sql = str.format("INSERT INTO {} ({}) VALUES ({})", table, ",".join(cols), "?"+",?"*(len(cols)-1))
    cur = db.execute(sql,data)
    rowID = cur.lastrowid
    db.commit()
    return rowID

def replaceSql(db,table,cols,data):#cols and data must be iterables (lists,tuples, etc.)
    """Replaces (and commits) an existing record with new data.  Returns None.

    Input parameters are: the connection to the database of interest, the table holding the data to be replaced,
    the columns corresponding to the data, and the data itself.
    (Note that the 
    """
    sql = str.format("REPLACE INTO {} ({}) VALUES ({})", table, ",".join(cols), "?"+",?"*(len(cols)-1))
    db.execute(sql,data)
    db.commit()

def fetchSql(db,table,keyCols,keyData):#keyCols and keyData must be iterables (lists,tuples, etc.)
    sql = str.format("SELECT * FROM {} WHERE {} = ?",table,' = ? AND '.join(keyCols))
    res = db.execute(sql,keyData).fetchall()
    return res

def orderedFetchSql(db,table,keyCols,keyData,orderKey):#cols and data must be iterables (lists,tuples, etc.)
    sql = str.format("SELECT * FROM {} WHERE {} = ? ORDER BY {}",table,' = ? AND '.join(keyCols),orderKey)
    res = db.execute(sql,keyData).fetchall()
    return res

def delSql(db,table,keyCols,keyData):
    sql = str.format("DELETE FROM {} WHERE {} = ?",table,' = ? AND '.join(keyCols))
    res = db.execute(sql,keyData)
    db.commit()

def updateSql(db,table,cols,data,keyCol,keyVal):#cols and data must be iterables (lists,tuples, etc.) keyVal must be the same kind of iterable as data
    sql = str.format("UPDATE {} SET {} = ? WHERE {} = ?",table," = ?, ".join(cols), keyCol,keyVal)
    db.execute(sql,list(data)+list(keyVal))
    db.commit()

def copySql(db,table,idCol,rowID):
    sql = str.format("SELECT * FROM {} WHERE {} = ?",table,idCol)
    res = db.execute(sql,[rowID]).fetchone()
    print(res[:])
    if res !=None:
        cols = res.keys()
        cols.remove(idCol)
        return insertSql(db,table,cols,[res[col] for col in cols])
    return None

def insertFileSql(db,table,fileName,fileNameCol,fileDataCol,otherCols,otherData):
    justFileName = os.path.basename(fileName)
    inFile = open(fileName,'rb')
    inBytes = inFile.read()
    inFile.close()

    sql = str.format("INSERT INTO {} ({},{},{}) VALUES (?,?,{})",
                         table,
                         fileNameCol,
                         fileDataCol,
                         ",".join(otherCols),
                         "?"+",?"*(len(otherCols)-1))
    db.execute(sql,[justFileName,inBytes]+otherData)
    db.commit()

def retrieveFileSql(db,table,fileNameCol,fileDataCol,keyCol,keyData):
    sql = str.format("SELECT {},{} FROM {} WHERE {} = ?",
                     fileNameCol,
                     fileDataCol,
                     keyCol)
    res = db.execute(sql,[keyData]).fetchall()

    retList = []
    if res !=None:
        for ln in res:
            outFile = open(res[fileNameCol],'wb',0)
            outBytes = outFile.write(res[fileDataCol])
            outFile.close()
            retList.append(res[fileNameCol],len(outBytes))
    return retList

def checkDate(dateTxt):
    datePatterns=baseDatePatterns[:]

    while len(datePatterns)>0:
        checkPatt = datePatterns.pop()
        foundDate = re.search(checkPatt,dateTxt.lower())
        if foundDate != None:
            break
    else:
        return False
    return True
	
def cleanDate(dateTxt):
    months=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
    datePatterns=baseDatePatterns[:]
    
    while len(datePatterns)>0:
        checkPatt = datePatterns.pop()
        foundDate = re.search(checkPatt,dateTxt.lower())
        if foundDate != None:
            break
    else:
        return dateTxt

    res=foundDate.groupdict()

    if res["mn"] in months:
        res["mn"]=months.index(res["mn"])+1

    return str.format("{:02d}/{:02d}/{:02d}",int(res["mn"]),int(res["dy"]),int(res.get("yr",str(dt.date.today().year))[-2:]))

def nextDay(dayStr):
    """Returns the date for the day following the supplied date"""
    dayFormat = "%m/%d/%y"
    try:
        origDate = dt.datetime.strptime(cleanDate(dayStr),dayFormat)

    except ValueError:
        return curDate()

    return (origDate + dt.timedelta(1)).strftime(dayFormat)

def isValidDate(workDate):
    """Returns True if the supplied date is formatted in a way the application identifies as a date."""
    return stdDateRegex.match(cleanDate(workDate))!=None

def sortableDate(workDate):
    """Returns a date formatted as YYYY-MM-DD, which allows the data to be sorted by date."""
    try:
        parseDate = stdDateRegex.match(workDate).groupdict()
    except AttributeError:
        return workDate

    return str.format("20{}-{}-{}",parseDate['yr'],parseDate['mn'],parseDate['dy'])

def sortableTimestamp(workStamp):
    """Reformats a mm/dd/yy hh:mm:ss time stamp (recorded in database) to a sortable format (
    """
    sortedStamp = dt.datetime.strptime(workStamp,"%m/%d/%y %H:%M:%S")
    return sortedStamp.strftime("%y/%m/%d %H:%M:%S")

def daysSince(dateText):
    workDate = dt.datetime.strptime(cleanDate(dateText),"%m/%d/%y")
    delta = dt.datetime.today()-workDate+dt.timedelta(1)
    daySet={(workDate+dt.timedelta(dy)).strftime("%m/%d/%y") for dy in range(delta.days)}
    return daySet

def toDatetime(dateStr):
    return dt.datetime.strptime(cleanDate(dateStr),"%m/%d/%y")

def fromDatetime(workDate):
    return workDate.strftime("%m/%d/%y")

def weekdaysSince(dateText):
    workDate = toDatetime(dateText)
    delta = dt.datetime.today()-workDate
    daySet={(workDate+dt.timedelta(dy)).strftime("%m/%d/%y") for dy in range(delta.days) if (workDate+dt.timedelta(dy)).weekday()<5}
    return daySet

def isMonday(dateText):
    workDate = dt.datetime.strptime(cleanDate(dateText),"%m/%d/%y")
    return workDate.weekday()==0

def weekdayList(dateText):
   workDate = dt.datetime.strptime(cleanDate(dateText),"%m/%d/%y")
   deltaMonday = workDate.weekday()
   weekList = [(workDate+dt.timedelta(dy)).strftime("%m/%d/%y") for dy in range(-deltaMonday,5-deltaMonday)]
   return weekList

def curDay():
    return dt.date.today().strftime("%A")

def twoWeeksBefore(workDate):
	cleanDate=dt.datetime.strptime(workDate.replace('-','/'),"%m/%d/%y")
	newDate = cleanDate - dt.timedelta(14)
	return newDate.strftime("%m/%d/%y")

   
def monthDelta(oldDate,dMonth):
    """Advances the date supplied by the specified number if months.

    Input parameters:
    oldDate: the original date to be modified
    dMonth: the number of months to be modified (can be negative)
    """
    m = oldDate.month-1
    d = oldDate.day
    y = oldDate.year

    (dy,dm)=divmod(m+dMonth,12)

    newM = dm+1
    newY = y+dy

    try:
        newDate = dt.date(newY,newM,d)

    except ValueError:
        dum,lastDay = cal.monthrange(newY,newM)
        newDate=dt.date(newY,newM,lastDay)
        
    return newDate

def curDate():
    """Returns the current date formatted according to mm/dd/yy"""
    return dt.date.today().strftime("%m/%d/%y")

def curTime():
    """Returns the current time formatted according to hh:mm (24 hr format"""
    return dt.datetime.now().strftime("%H:%M")

def curDateTime():
    """Returns the current date and time formatted according to mm/dd/yy hh:mm (24 hr format)"""
    return dt.datetime.now().strftime("%m/%d/%y %H:%M")

def dispISOStamp(stamp):
    """Format a time stamp according to ISO 8601"""
    res=isoStampRegex.match(stamp)
    if res == None:
        return stamp
    parts = res.groupdict()
    return str.format("{}/{}/{} {}:{}",parts['mn'],parts['dy'],parts['yr'],parts['hr'],parts['min'])
    	
def deltaDate(dayDiff=7):
    return (dt.date.today()+dt.timedelta(dayDiff)).strftime("%m/%d/%y")

def nextFriday(weeksAway=0):
    friday=4-dt.date.today().weekday()
    return deltaDate(7*weeksAway+friday)

def lastMonday(weeksAgo=0):
    monday = 0 - dt.date.today().weekday()
    return deltaDate(monday - 7*weeksAgo)

def formatCost(cost):
    return str.format("${:4.2f}",cost)


timePatterns = [""]
def parseTime(timeStr):
    pass

                
    

##def setGenericTag(self, tagName, bold=False,strike=False, italic = False, under = False, size = 9, family = "Segoe UI", color = 'black'):
##    fontList = []
##    if bold:
##        fontList += ["bold"]
##    if strike:
##        fontStyle += ["overstrike"]
##    if under:
##        fontStyle += ["underline"]
##    if italic:
##        fontStyle += ["italic"]
##
##    fontStyle = " ".join(fontList)
##    self.field.tag_configure(tagName,font=(family,size,fontStyle),foreground=color)
##    

#################################################################
#
##Classes pertaining to setting up the TKinter building blocks
#
#################################################################

###############
#
##  Frame control
#
###############

##  Add Multi-action buttons.
##      Bundle a check box/Radio button in with an action button
##      Setting/Clearing the check box changes the label and callback for the action button
##      Replace the checkbox with another action button to make an N-way multi action


class formFrame(tk.Frame):
    def __init__(self,master=None,label=None,r=0,c=0,w=1,h=1):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2*h
        if label == None:
            self.frame=tk.Frame(master,bd=2)
        else:
            self.frame=tk.LabelFrame(master,text=label,bd=4)
        self.frame.grid(row=realRow,column=realCol,columnspan=realSpan,rowspan=realHeight,sticky=tk.NSEW)

class baseDataControl():
    def __init__(self):
        self.enable = True
        self.data = tk.StringVar()
        self.field = tk.Entry()
        self.field.grid()

    def getVal(self):
        return self.data.get()

    def setVal(self,newData):
        self.data.set(newData)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def toggleEnable(self,enable=None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()


###############
#
##   Check box control
#
###############

## Implementation of dataCheckBox based on composition from 
##class dataCheckBox(tk.Frame,baseDataControl):
##    def __init__(self,master = None, label = "Default",initVal = True,r=0,c=0,w=1,cmd=None):
##        tk.Frame.__init__(self,master)
##        baseDataControl.__init__(self)
##        
##        realRow = 2 * r
##        realCol = 2 * c
##        realSpan = 2 * w
##
##        self.data = tk.IntVar()
##        self.data.set(initVal)
##        self.field = tk.Checkbutton(master,text=label,variable = self.data,anchor=tk.W,command=cmd)
##        self.field.grid(row = realRow,column = realCol, columnspan = realSpan,sticky=tk.NSEW)
##
##    def setCommand(self,cmd):
##        self.field.config(command=cmd)
        
class dataDblCheckBox(tk.Frame):
    def __init__(self,master = None, labels = ["Left Check","Right Check"],initVal=[True,True],r=0, c=0,w=1,cmd = [None,None]):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w

        self.enable0 = True
        self.enable1 = True

        self.data0 = tk.IntVar()
        self.data1 = tk.IntVar()

        self.data0.set(initVal[0])
        self.data1.set(initVal[1])

        self.field0 = tk.Checkbutton(master,text=labels[0],variable=self.data0, anchor = tk.W, command = cmd[0])
        self.field0.grid(row = realRow, column = realCol, columnspan = w, sticky = tk.NSEW)
        
        self.field1 = tk.Checkbutton(master,text=labels[1],variable=self.data1, anchor = tk.W, command = cmd[1])
        self.field1.grid(row = realRow, column = realCol+w, columnspan = w, sticky = tk.NSEW)

    def getVal(self):
        return (self.data0.get(),self.data1.get())

    def setVal(self,newVal):
        self.data0.set(newVal[0])
        self.data1.set(newVal[1])
        

class dataCheckBox(tk.Frame):
    def __init__(self,master = None, label = "Default",initVal = True,r=0,c=0,w=1,cmd=None):
        tk.Frame.__init__(self,master)
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w

        self.enable = True
        self.data = tk.IntVar()
        self.data.set(initVal)
        self.field = tk.Checkbutton(master,text=label,variable = self.data,anchor=tk.W,command=cmd)
        self.field.grid(row = realRow,column = realCol, columnspan = realSpan,sticky=tk.NSEW)

    def getVal(self):
        return (self.data.get())

    def setVal(self,newVal):
        self.data.set(newVal)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def setCommand(self,cmd):
        self.field.config(command=cmd)

    def takeFocus(self):
        self.field.focus_set()


###############        
#
##   Listbox control
#
###############

class messageListbox(tk.Frame):
    def __init__(self,master = None, r=0,c=0,w=1,h=4,boxHeight=8,boxWidth=20):
        tk.Frame.__init__(self,master)
        realRow = 2 * r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h

        self.enable = True

        self.data = tk.StringVar()

        self.disp = tk.Listbox(master,listvariable = self.data, height = boxHeight, width = boxWidth)
        self.disp.grid(row = realRow, column = realCol, columnspan = realSpan, rowspan = realHeight,sticky=tk.NSEW)
        

    def getData(self):
        return self.disp.get(0,tk.END)

    def getLine(self,lineNum):
        return self.disp.get(lineNum).strip()

    def setData(self,allData):
        self.data.set(allData)

    def insertLine(self,lineNum,newLine):
        self.disp.insert(lineNum,newLine)
        self.disp.see(lineNum)

    def addLine(self,newLine):
        self.disp.insert(tk.END,newLine)
        self.disp.see(tk.END)

    def dropLine(self,lineNum):
        self.disp.delete(lineNum)

    def clearData(self):
        self.disp.delete(0,tk.END)

    def setSelection(self,selLine):
        self.disp.selection_set(selLine)

    def getSelection(self):
        return self.disp.selection_get()
    
    def getSelectionIndex(self):
        return self.disp.curselection()

    def findClickLine(self,event):
        return self.disp.get(self.disp.nearest(event.y))

    def findClickLineIndex(self,event):
        return self.disp.nearest(event.y)

    def bindField(self,event,func):
        self.disp.bind(event,func)

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()

###############
#
##   Combo box control (dropdown)
#
###############

class dataComboBox():
    def __init__(self,master = None,label="Default",dispVals=["Val 1","Val 2"], r=0,c=0,w=1):
        realRow = 2*r
        realCol = 2*c
        realSpan = 2*w

        self.enable = True
        
        self.data = tk.StringVar()
        if len(dispVals)>0:
            self.data.set(dispVals[0])
        self.useVals = dispVals
        self.keyTime = 0
        
        tk.Label(master,text=label).grid(row=realRow,column = realCol,sticky=tk.S,rowspan=2)
        self.field = ttk.Combobox(master,values=dispVals,textvariable=self.data)
        self.field.grid(row=realRow,column=realCol+1,columnspan=realSpan-1,sticky=tk.W+tk.S+tk.E,rowspan=2)

    def getVal(self):
        return self.data.get().strip()

    def setVal(self,newData,ignore=True):
        if newData in self.useVals:
            self.data.set(newData)
            self.field.set(newData)
        # don't remember what I wanted it to do in case the new value isn't part of the existing dropdown list
        elif not ignore:    
            self.data.set(newData)
            self.field.set(newData)
        # normally, ignore data that isn't part of the dropdown list
        # if ignore=False, go ahead and store the new data anyway


    def getIndex(self):
        return self.field.current()
            
    def updateVals(self,newVals):
        self.useVals = newVals
        self.field.config(values=newVals)
        try:
            self.setVal(newVals[0])
        except IndexError:
            pass
    

    def getDropList(self):
        return self.useVals

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def setQuickFind(self, vals = None):
        """Call this function to initiate a quick-lookup feature, where the selection
        jumps to the nearest match to the characters just typed.  If this function is called
        with a listof values arguments, it uses these values in a 1:1 correspondence to the values
        in the drop down.  Otherwise it defaults to the list of values in the drop down."""
        if vals == None:
            self.quickLookupList = list(self.field["values"])
        else:
            self.quickLookupList = vals
        self.quick_vals={k:v for k,v in zip(self.quickLookupList,self.field["values"])}
        self.quickLookupList.sort()
        self.field.bind("<KeyRelease>",self.quickFind)


    def quickFind(self,event):
        print("Quick Find Called")
        if event.keycode <65 or event.keycode >90:
            self.quickLetters = ""
            self.keyTime = event.time
            return
        if (event.time-self.keyTime)<500:
            self.findKey = self.findKey + event.char
        else:
            self.findKey = event.char
        for test in self.quickLookupList:
            print(self.findKey,test)
            if test>=self.findKey:
                #foundIndex = self.quickLookupList.index(test)
                #self.field.current(foundIndex)
                self.quick_vals[test]
                break
        self.keyTime = event.time

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()

class dataComboTop():
    def __init__(self,master = None,label="Default",dispVals=["Val 1","Val 2"], r=0,c=0,w=1):
        realRow = 2*r
        realCol = 2*c
        realSpan = 2*w
        
        self.enable = True
        self.data = tk.StringVar()
        self.data.set(dispVals[0])
        self.useVals = dispVals
        
        tk.Label(master,text=label).grid(row=realRow,column = realCol)
        self.field = ttk.Combobox(master,values=dispVals,textvariable=self.data)
        self.field.grid(row=realRow+1,column=realCol,columnspan=realSpan)

    def getVal(self):
        return self.data.get().strip()

    def setVal(self,newData):
        if newData in self.useVals:
            self.data.set(newData)
            self.field.set(newData)
            
    def updateVals(self,newVals):
        if len(newVals)>0:
            self.field.set(newVals[0])
        else:
            self.field.set("")
        self.field.config(values=newVals)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def setQuickFind(self, vals = None):
        print("Enter setQuickFind")
        if vals == None:
            self.quickLookupList = list(self.field["values"])
        else:
            self.quickLookupList = vals
        self.quickLookupList.sort()
        self.bindField("<KeyRelease>",self.quickFind)
        print("Set up quickFind")

    def quickFind(self,event):
        print("Running quick find")
        if event.keycode <65 or event.keycode >90:
            self.quickLetters = ""
            self.keyTime = event.time
            return
        if (event.time-self.keyTime)<500:
            self.findKey = self.findKey + event.char
        else:
            self.findKey = event.char
        for test in self.quickLookupList:
            if test>=self.findKey:
                self.field.current(self.field["values"].index(test))
                break
        self.keyTime = event.time

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()

###############
#
##  Status Label control
#
###############

class statusLabelBox(tk.Frame):
    def __init__(self,master = None,label=None,initVal = "Idle",r=0,c=0,w=1):
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        self.data = tk.StringVar()
        self.data.set(initVal)
        if not label == None:
            tk.Label(master,text=label).grid(row=realRow,column=realCol)
            realCol+=1
        self.field = tk.Label(master,textvariable=self.data,anchor=tk.W)
        self.field.grid(row = realRow,column=realCol,columnspan = realSpan,sticky=tk.NSEW)

    def getVal(self):
        return (self.data.get()).strip()

    def setVal(self,newVal):
        self.data.set(newVal)

    def takeFocus(self):
        self.field.focus_set()

class statusLabelBoxTop(tk.Frame):
    def __init__(self,master = None,label=None,initVal = "Idle",r=0,c=0,w=1):
        realRow = 2*r
        realCol = 2 * c
        realSpan = 2 * w
        self.data = tk.StringVar()
        self.data.set(initVal)
        if not label == None:
            tk.Label(master,text=label).grid(row=realRow,column=realCol)
            realRow+=1
        self.field = tk.Label(master,textvariable=self.data)
        self.field.grid(row = realRow,column=realCol,columnspan = realSpan,sticky=tk.NSEW)

    def getVal(self):
        return (self.data.get()).strip()

    def setVal(self,newVal):
        self.data.set(newVal)


    def takeFocus(self):
        self.field.focus_set()

###############
#
##   Edit box box controls
#
###############

class dataFieldTop():
    def __init__(self,master=None,label="Default",r=0,c=0,w=1,initVal=""):
        realRow=2*r
        realCol=2*c
        realSpan=2*w
        self.data = tk.StringVar()
        self.data.set(initVal)
        self.enable = True
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Entry(master,textvariable=self.data,justify=tk.CENTER)
        self.field.grid(row=realRow+1,column=realCol,columnspan=realSpan,sticky=tk.E+tk.W)

    def getVal(self):
        return self.data.get().strip()

    def setVal(self,newVal):
        self.data.set(newVal)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()
        self.field.select_range(0, tk.END)

    def setValidate(self,validWhen,validFunc):
        validCommand = self.field.register(validFunc)
        self.field["validate"] = validWhen
        self.field["validatecommand"]=validCommand
        

class dataFieldLeft():
    def __init__(self,master=None,label="Default",r=0,c=0,w=1,initVal=""):
        realRow=2*r
        realCol=2*c
        realSpan=2*w
        self.enable = True
        self.data = tk.StringVar()
        self.data.set(initVal)
        tk.Label(master,text=label).grid(row=realRow,column=realCol)
        self.field=tk.Entry(master,textvariable=self.data,justify=tk.LEFT)
        self.field.grid(row=realRow,column=realCol+1,columnspan=realSpan-1,sticky=tk.W+tk.E)

    def getVal(self):
        return self.data.get().strip()

    def setVal(self,newVal):
        self.data.set(newVal)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
            
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()
        self.field.select_range(0, tk.END)

    def setValidate(self,validWhen,validFunc):
        validCommand = self.field.register(validFunc)
        self.field["validate"] = validWhen
        self.field["validatecommand"]=validCommand

class dateFieldLeft(dataFieldLeft):
    def __init__(self,master=None,label="Default",r=0,c=0,w=1,initVal=""):
        dataFieldLeft.__init__(self,master,label,r,c,w,initVal)
        self.dateInit()

    def dateInit(self):
        self.acceptDate = {"ASAP","asap"}
        self.autoFormatStr="%m/%d/%y"

        self.field.bind("<MouseWheel>",self.stepDate)
        self.field.bind("<FocusOut>",self.exitDateField)

        
    def setAutoFormat(self,newFormatStr):
        self.autoFormatStr = newFormatStr

    def addAcceptDate(self,goodDate):
        self.acceptDate.add(goodDate)

    def dropAcceptDate(self,badDate):
        self.acceptDate.discard(badDate)

    def exitDateField(self,event=None):
        
        orig = self.data.get()
        if orig in self.acceptDate:
            return

        if checkDate(orig):
            self.data.set(cleanDate(orig))
            return

        self.field.bell()
        self.field.focus_set()

            

    def stepDate(self,event):
        try:
            origDate = dt.datetime.strptime(cleanDate(self.data.get()),"%m/%d/%y")

        except ValueError:
            self.data.set(curDate())
            return 

        if event.delta>0:
            step = -1
        else:
            step = 1

        if event.state & 0x004 == 4:
            newDate = monthDelta(origDate,step)
        else:
            newDate = origDate+dt.timedelta(step)

        self.data.set(newDate.strftime(self.autoFormatStr))
            
class dateFieldTop(dateFieldLeft):
    def __init__(self,master=None,label="Default",r=0,c=0,w=1,initVal=""):
        dataFieldTop.__init__(self,master,label,r,c,w,initVal)
        self.dateInit()

###############
#
##  dataTextBox
#
###############

class dataTextBox():
    def __init__(self, master = None, label = "Default", r=0,c=0,w=1,h=1,boxW=20, boxH=3,initVal = "", boxFont = ("Helvetica","8")):
        realRow=2*r
        realCol=2*c
        realSpan=2*w-1
        realHeight = 2*h
        self.enable = True
        self.data = initVal
        tk.Label(master,text=label,anchor=tk.NW).grid(row=realRow,column=realCol)
        self.field = tk.Text(master, height=boxH, width=boxW, wrap=tk.WORD, font=boxFont)
        self.field.grid(row=realRow,column=realCol+1,columnspan=realSpan,rowspan=realHeight,sticky=tk.W+tk.E)
        self.field.bind("<Control-Tab>",self.onTab)

    def getVal(self):
        self.data = self.field.get('1.0','end')
        return self.data

    def setVal(self,newData):
        self.data = newData
        self.field.delete('1.0','end')
        self.field.insert('1.0',newData)

    def bindField(self,event,func):
        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

    def toggleEnable(self,enable = None):
        if enable == None:
            self.enable = not self.enable

        if self.enable:
            self.field["state"]=tk.NORMAL
        else:
            self.field["state"]='disabled'

    def takeFocus(self):
        self.field.focus_set()


    def setBackground(self,newColor=None):
        if newColor == None:
            return self.field["bg"]
        self.field["bg"]=newColor

    def selectAll(self):
        self.field.tag_add(tk.SEL,"1.0",tk.END)

    def onTab(self,event=None):
       event.widget.tk_focusNext().focus()
       return("break")
        

###############
#
##   Radio button control
#
###############

class radioGroup(tk.Frame):
    def __init__(self,master=None,labelList=["Value 1","Value 2"],r=0,c=0,w=1):
        tk.Frame.__init__(self,master)
        self.data=tk.StringVar()
        self.data.set(labelList[0])
        realRow=2*r
        realCol=2*c
        realSpan=2*w
        self.grid()
        radioRow=0
        for labelVal in labelList:
            tk.Radiobutton(self,text=labelVal,value=labelVal,variable=self.data).grid(row=radioRow,sticky=tk.W)
            radioRow=radioRow+1

    def getVal(self):
        return self.data.get()

    def setVal(self,newVal):
        self.data.set(newVal)

##    def bindField(self,event,func):
##        self.field.bind(event,func)

    def bindData(self,func):
        self.data.trace("w",lambda name,index,mode:func(self.data))

###############
#
##   Button control
#
###############

class actionBtn(tk.Frame):
    def __init__(self,master = None,label = "Default",action = None,r=0,c=0,w=1,h=1,ctrlAction=None):
        tk.Frame.__init__(self,master)
        realRow= 2 * r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        self.btn = tk.Button(master,text = label)
        self.btn.grid(row = realRow, column = realCol, columnspan = realSpan, rowspan = realHeight, sticky = tk.NSEW)
        self.btn.bind("<ButtonRelease-1>",action)
        self.btn.bind("<Control-ButtonRelease-1>",ctrlAction)

## May not need the separate function; may just be able to query the event
        # to see if the ctrl key is pressed
    def setActionFn(self,newFn):
        self.btn.bind("<ButtonRelease-1>",newFn)

    def setCtrlActionFn(self,newFn):
        self.btn.bind("<Control-ButtonRelease-1>",newFn)
    
    def recaption(self,newCaption):
       self.btn["text"]=newCaption

    def takeFocus(self):
        self.btn.focus_set()

    def bindField(self,event,func):
        self.btn.bind(event,func)

###############
#
##   Double utton control
#
###############


class dblBtn(tk.Frame):
    def __init__(self,master = None,labels = ["Default1","Default2"],actions = [None,None],r=0,c=0,w=1,h=1,ctrlActions=[None,None]):
        tk.Frame.__init__(self,master)
        realRow= 2 * r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        self.btn1 = tk.Button(master,text = labels[0], command = None)
        self.btn1.grid(row = realRow, column = realCol, columnspan = w, rowspan = realHeight, sticky = tk.NSEW)
        self.btn2 = tk.Button(master,text = labels[1], command = None)
        self.btn2.grid(row = realRow, column = realCol+w, columnspan = w, rowspan = realHeight, sticky = tk.NSEW)

        self.btn1.bind("<ButtonRelease-1>",actions[0])
        self.btn1.bind("<Control-ButtonRelease-1>",ctrlActions[0])
        self.btn2.bind("<ButtonRelease-1>",actions[1])
        self.btn2.bind("<Control-ButtonRelease-1>",ctrlActions[1])
        
    def recaption(self,newCaption):
       self.btn1["text"]=newCaption[0]
       self.btn2["text"]=newCaption[1]

    def recaption0(self,newCaption):
       self.btn1["text"]=newCaption
       
    def recaption1(self,newCaption):
       self.btn2["text"]=newCaption

    def setActionFn(self,newFn):
        self.btn1["command"]= newFn[0]
        self.btn2["command"]= newFn[1]
        
    def setActionFn0(self,newFn):
        self.btn1["command"]= newFn

    def setActionFn1(self,newFn):
        self.btn2["command"]= newFn
       
    def takeFocus(self):
        self.btn1.focus_set()

    def bindField0(self,event,func):
        self.btn1.bind(event,func)

    def bindField1(self,event,func):
        self.btn2.bind(event,func)
  
class buttonPrompt(tk.Frame):
    def __init__(self, master = None, label="Default", initVal = "default", action = None, r=0,c=0,w=1,h=1):
        tk.Frame.__init__(self,master)
        realRow= 2 * r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h
        self.data = tk.StringVar()
        self.data.set(initVal)
        self.btn = tk.Button(master, text = label, command = action)
        self.btn.grid(row = realRow, column = realCol, columnspan= w, rowspan = realHeight,sticky = tk.NSEW)
        self.field=tk.Entry(master,textvariable=self.data,justify=tk.CENTER)
        self.field.grid(row=realRow,column=realCol+w,columnspan=w,sticky=tk.E+tk.W)

    def getVal(self):
        return self.data.get()

    def setVal(self,newVal):
        self.data.set(newVal)

    def recaption(self,newCaption):
        self.btn["text"]=newCaption

    def bindField(self,event,func):
        self.field.bind(even,func)

        
###############
#
##  Treeview
#
###############

treeColTpl = collections.namedtuple("treeColTpl","colName colWidth colHead")

class treeView(tk.Frame):
    def __init__(self,master=None,label="Default",colConfig=[treeColTpl("Default",50,"Default")],r=0,c=0,w=1,h=1):
        tk.Frame.__init__(self,master)
        realRow= 2 * r
        realCol = 2 * c
        realSpan = 2 * w
        realHeight = 2 * h

        tk.Label(master,text=label,anchor=tk.NW).grid(row=realRow,column=realCol)
        treeFrame = tk.Frame(master)
        treeFrame.grid(row = realRow+1, column=realCol,columnspan = realSpan, rowspan = realHeight)
     
        self.field = ttk.Treeview(treeFrame)
        self.field.grid(row=0,column=0,sticky=tk.NSEW)
        self.configCol(colConfig)
        ysb = ttk.Scrollbar(treeFrame, orient='vertical', command=self.field.yview)
        xsb = ttk.Scrollbar(treeFrame, orient='horizontal', command=self.field.xview)
        self.field.configure(yscroll=ysb.set, xscroll = xsb.set)
        xsb.grid(row = 1,column=0,sticky="ew")
        ysb.grid(row = 0,column=1,sticky = 'ns')

        self.txt_iid={}
        self.dataID_iid={}
        
    def configCol(self,colConfList):
        colList=[col.colName for col in colConfList]
        self.field["columns"]=colList
        for col in colConfList:
            self.field.column(col.colName,width=col.colWidth)
            self.field.heading(col.colName,text=col.colHead)

    def setRowCount(self,rowCount):
        self.field.configure(height=rowCount)

    def bindField(self,event,func):
        self.field.bind(event,func)
            
    def setIconWidth(self,iconWidth):
        self.field.column('#0',width = iconWidth)

    def insertLine(self, parentIID,index,lineText,lineData,lineTag=''):
        newIID = self.field.insert(parentIID,index,text=lineText,values=lineData)
        self.txt_iid[lineText] = newIID
        return newIID

    def insertLineID(self,parentIID,index,lineText,lineData,dataID=None,lineTag=''):
        newIID = self.field.insert(parentIID,index,text=lineText,values=lineData)
        self.txt_iid[lineText] = newIID
        self.dataID_iid[newIID]=dataID
        self.dataID_iid[dataID]=newIID
        return newIID
        

    def addLine(self,parentIID, lineText, lineData,lineTag=''):
        newIID = self.field.insert(parentIID,'end',text=lineText,values=lineData,open=True,tags=lineTag)
        self.txt_iid[lineText] = newIID
        return newIID

    def addLineID(self,parentIID, lineText, lineData,dataID=None,lineTag=''):
        newIID = self.field.insert(parentIID,'end',text=lineText,values=lineData,open=True,tags=lineTag)
        self.txt_iid[lineText] = newIID
        self.dataID_iid[newIID]=dataID
        self.dataID_iid[dataID]=newIID
        return newIID

    def updateLine(self,iid, lineText,lineData=[],lineTag=''):
        self.field.item(iid,text=lineText,values=lineData,tags=lineTag)

    def openLine(self,iid):
        self.field.item(iid,open=True)

    def closeLine(self,iid):
        self.field.item(iid,open=False)

    def toggleLineOpen(self,iid):
        cur=self.field.item(iid,'open')
        self.field.item(iid,open=not cur)

    def closeAllLines(self):
        for ln in self.txt_iid.values():
            self.field.item(ln,open=False)
        
        
    def showTree(self,treeState="Both"):
        if treeState=="Both":
            self.field["show"]="tree headings"
        elif treeState:
            self.field["show"]="tree"
        else:
            self.field["show"]="headings"

    def getParents(self):
        parents = self.field.get_children()
        return {self.field.item(iid,"text"):iid for iid in parents}

    def getCurParent(self,iid):
        return self.field.parent(iid)

    def getChildren(self,parent):
        children = self.field.get_children(parent)
        return {self.field.item(iid,"text"):iid for iid in children}
        
    def getValues(self,iid):
        return self.field.item(iid,"values")

    def getText(self,iid):
        return self.field.item(iid,'text')

    def getIID(self,itemText):
        return self.txt_iid.get(itemText,"")

    def getDataID(self,iid):
        return self.dataID_iid.get(iid,-1)

    def getDataIDFromTxt(self,itemText):
        tmpIID = self.getIID(itemText)
        return self.dataID_iid.get(tmpIID,-1)

    def getIIDFromDataID(self,dataID):
        return self.dataID_iid.get(dataID,"")

    def clearTree(self):
        iidList = self.field.get_children()
        for ln in iidList:
            self.field.delete(ln)
        self.txt_iid = {}
        self.dataID_iid={}

    def getItemTags(self,iid):
        return self.field.item(iid,'tags')
    
    def setFontTag(self,tagName,fontStyle):
        # Default Font Style is ("Segoe UI",9,<insert attributes here>))
        self.field.tag_configure(tagName,font=fontStyle)

    def setColorTag(self,tagName,fontColor='black'):
        self.field.tag_configure(tagName,foreground=fontColor)

    def setMixedTag(self,tagName,fontStyle,fontColor):
        self.field.tag_configure(tagName,foreground=fontColor,font=fontStyle)

    def setGenericTag(self, tagName, bold=False,strike=False, italic = False, under = False, size = 9, family = "Segoe UI", color = 'black'):
        fontList = []
        if bold:
            fontList += ["bold"]
        if strike:
            fontList += ["overstrike"]
        if under:
            fontList += ["underline"]
        if italic:
            fontList += ["italic"]

        fontStyle = " ".join(fontList)
        self.field.tag_configure(tagName,font=(family,size,fontStyle),foreground=color)
            

    def tagItem(self,iid,newTag):
        self.field.item(iid,tags=newTag)

    def setSelection(self,iid):
        self.field.selection_set(iid)

    def addSelection(self,iid):
        self.field.selection_add(iid)

    def getSelection(self):
        return self.field.selection()

    def clearSelection(self):
        cur = self.field.selection()
        for iid in cur:
            self.field.selection_remove(iid)

    def hideItem(self,iid):
        self.field.detach(iid)

    def unhideItem(self,iid,parent):
        self.field.move(iid,parent,'end')

    def showItem(self,iid):
        self.field.see(iid)

  



    
        

    
    
            


    
        
        
        












            
