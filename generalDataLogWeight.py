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

wwScale = collections.namedtuple('wwScale','date weight fatLb fat water bone')

wwScaleDefault = wwScale(curDate(),220,65,30,50,7.7)

#
#   Weight Watchers Body Composition Scale Data
#

class wwScaleData(tk.Frame):
    def __init__(self,master=None, dbConn = None, outerTabs = None, initVals=wwScaleDefault):
        tk.Frame.__init__(self,master)
        self.grid()

        self.dataFrame = formFrame(self,"Data Entry",0,0)
        self.date = dateFieldTop(self.dataFrame.frame,"Date")
        self.weight = dataFieldTop(self.dataFrame.frame,"Weight",1)
        self.fatLb = dataFieldTop(self.dataFrame.frame,"Fat Weight",2,0)
        self.fat = dataFieldTop(self.dataFrame.frame,"Percent Fat",2,1)
        self.water = dataFieldTop(self.dataFrame.frame,"Percent Water",3,0)
        self.bone = dataFieldTop(self.dataFrame.frame,"Percent Bone",3,1)
        
        self.weight.bindField("<MouseWheel>",lambda event: self.rollEdit(event,self.weight))
        self.fatLb.bindField("<MouseWheel>",lambda event: self.rollEdit(event,self.fatLb))
        self.fat.bindField("<MouseWheel>",lambda event: self.rollEdit(event,self.fat))
        self.water.bindField("<MouseWheel>",lambda event: self.rollEdit(event,self.water))       
        self.bone.bindField("<MouseWheel>",lambda event: self.rollEdit(event,self.bone))
        
        self.clrBtn = actionBtn(self.dataFrame.frame,"Clear Data",lambda event:self.clearData(),4,2)
        self.saveFlag = dataCheckBox(self.dataFrame.frame,"Save Data",False,4,1)
        self.saveBtn = actionBtn(self.dataFrame.frame,"Save Weight Data",self.saveBtnFn,4,0)
        self.prevTab = actionBtn(self.dataFrame.frame,"Defcon Data",lambda event:self.jumpTab(-1),4,3)
        self.nextTab = actionBtn(self.dataFrame.frame,"Omcron Data",lambda event:self.jumpTab(+1),4,4)

        self.viewFrame = formFrame(self,"Data View",1,0)

        self.viewStart = dateFieldLeft(self.viewFrame.frame,"View Startdate",0,0,1,twoWeeksBefore(curDate()))
        self.viewRefresh = actionBtn(self.viewFrame.frame,"Refresh",lambda event:self.popView(),0,1)
        colWide = 100
        self.viewMin = statusLabelBox(self.viewFrame.frame,"Min Weight:","{} on {}",1,0)
        self.viewMax = statusLabelBox(self.viewFrame.frame,"Max Weight:","{} on {}",1,1)
        self.viewCfg=[
            treeColTpl('weight',colWide,'Weight'),
            treeColTpl('fat',colWide,'Fat Weight'),
            treeColTpl('percent',colWide,'Fat Percent'),
            treeColTpl('lean',colWide,'Lean Weight'),
            treeColTpl('water',colWide,'Percent Water'),
            treeColTpl('bone',colWide,'Percent Bone'),
            treeColTpl('athletic',colWide,'Target (15% Fat)'),
            treeColTpl('normal',colWide,'Target (20%)')]
        self.viewWeight = treeView(self.viewFrame.frame,None,self.viewCfg,2,0,4)
        self.viewWeight.setIconWidth(colWide)
##        self.missingLabel=statusLabelBox(self.viewFrame.frame,"Missing Dates","0 of 0",0,5)
##        self.missingDaysList=messageListbox(self.viewFrame.frame,1,5)
   
        self.tabs = outerTabs

        self.dbConn = dbConn
        self.dataType = "Weight Watchers Scale"
        self.dataTable = "WeightWatchersScale"
        self.dataCols = ["WeighDate","Weight","BodyFatWeight","BodyFatPercent","WaterPercent","BonePercent"]

        self.setData(initVals)
        self.popView()
        
    def showRange(self):
        sqlStr = "SELECT WeighDate,max(Weight) as lb FROM {} WHERE sortableDate(WeighDate)>sortableDate(?)".format(self.dataTable)
        maxVal = self.dbConn.execute(sqlStr,[self.viewStart.getVal()]).fetchone()
        sqlStr = "SELECT WeighDate,min(Weight) as lb FROM {} WHERE sortableDate(WeighDate)>sortableDate(?)".format(self.dataTable)
        minVal = self.dbConn.execute(sqlStr,[self.viewStart.getVal()]).fetchone()

        self.viewMin.setVal("{} on {}".format(minVal["lb"],minVal["WeighDate"]))
        self.viewMax.setVal("{} on {}".format(maxVal["lb"],maxVal["WeighDate"]))
        
        



    def jumpTab(self,delta):
        self.tabs.select(5+delta)

    def popView(self,event=None):
        self.viewWeight.clearTree()
        res = self.dbConn.execute("SELECT * FROM WeightWatchersScale WHERE sortableDate(WeighDate)>sortableDate(?) ORDER BY sortableDate(WeighDate)",[self.viewStart.getVal()]).fetchall()
        for ln in res:
            val=wwScale._make(ln[1:])
            lean=str.format("{:4.1f}",val.weight-val.fatLb)
            ath = str.format("{:4.1f}",(val.weight-val.fatLb)/(1-0.15))
            norm = str.format("{:4.1f}",(val.weight-val.fatLb)/(1-0.2))
            self.viewWeight.addLine("",ln["WeighDate"],[val.weight, val.fatLb,val.fat,lean,val.water,val.bone,ath,norm])
        self.showRange()


    def getData(self):
        return wwScale(
            self.date.getVal(),
            float(self.weight.getVal()),
            float(self.fatLb.getVal()),
            float(self.fat.getVal()),
            float(self.water.getVal()),
            float(self.bone.getVal()))
        
    def rollEdit(self,event,dataBox):
        
        if event.state & 0x004 == 4:
            baseStep = 1
        else:
            baseStep = 0.1
        
        if event.delta<0:
            step = -baseStep
        else:
            step = baseStep
            
        curVal = float(dataBox.getVal())
        dataBox.setVal("{:3.1f}".format(curVal+step))
        

    def saveBtnFn(self,event=None):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)
        self.date.setVal(nextDay(self.date.getVal()))

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        
        

    def saveData(self):

        if not saveNotify("Weight Watchers Scale",self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True

        saveWeight = self.getData()
        replaceSql(self.dbConn,self.dataTable,self.dataCols,saveWeight)
        self.dbConn.commit()
        self.popView()

##        sqlStr = str.format("DELETE FROM {} WHERE WeighDate = ?",self.dataTable)
##        self.dbConn.execute(sqlStr,(self.date.getVal(),))
##
##        sqlStr = makeInsertStr(self.dataTable,self.dataCols)
##        #sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
##        self.dbConn.execute(sqlStr,self.getData())
##        
##        self.dbConn.commit()

        self.statusBox.addLine("Saved Weight Data for {}".format(self.date.getVal()))


        return True

    def setData(self,newData):
        if newData == None:
            newData = wwScaleDefault
        self.date.setVal(newData.date)
        self.weight.setVal(str(newData.weight))
        self.fatLb.setVal(str(newData.fatLb))
        self.fat.setVal(str(newData.fat))
        self.water.setVal(str(newData.water))
        self.bone.setVal(str(newData.bone))
        return

    def clearData(self):
        self.date.setVal("")
        self.weight.setVal("")
        self.fatLb.setVal("")
        self.fat.setVal("")
        self.water.setVal("")
        self.bone.setVal("")
        return

    def setDate(self,newDate):
        self.date.setVal(newDate)
        self.setData(self.fetchWWScaleData(newDate))
        #tkmb.showinfo(self,self.fetchWWScaleData(newDate))
        # Need to decide what to do here when the date is changed;
        # What data to display; what warnings if no existing data


    def fetchWWScaleData(self,date):
        cur = self.dbConn.execute("SELECT * FROM WeightWatchersScale WHERE WeighDate = (?)",(date,))
        res = cur.fetchone()
        if res != None:
            return wwScale(res["WeighDate"],
                                res["Weight"],
                                res["BodyFatWeight"],
                                res["BodyFatPercent"],                         
                                res["WaterPercent"],
                                res["BonePercent"])
        return None


    
     


