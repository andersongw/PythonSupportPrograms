# Last Edited 01/17/18
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
import fnmatch


import pyperclip

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
        




    
        

    
    
            


    
        
        
        












            
