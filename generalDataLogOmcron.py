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

analyzer = collections.namedtuple('analyzer','date activity heightIn weightLb age gender fat BMI')

analyzerDefault = analyzer(curDate(),"Athletic",70,220,45,"Male",21.0,25)

#
#   Omcron Body Composition Analyzer Data
#


class fatAnalyzerData(tk.Frame):
    def __init__(self,master=None, dbConn = None, initVals=analyzerDefault):
        tk.Frame.__init__(self,master)
        self.grid()
        self.date = dateFieldTop(self,"Date")
        self.active = radioGroup(self,["Athletic","Normal"],1)
        self.height = dataFieldTop(self,"Height (inches)",2)
        self.weight = dataFieldTop(self,"Weight (lbs)",2,1)
        self.age = dataFieldTop(self,"Age",2,2)
        self.gender = radioGroup(self,["Male","Female"],3)
        self.fatPercent = dataFieldTop(self,"Percent body fat",4)
        self.bmi = dataFieldTop(self,"Body Mass Index",4,1)
        self.clrBtn = actionBtn(self,"Clear Data",lambda event:self.clearData(),5)
        self.saveFlag = dataCheckBox(self,"Save Data",False,5,1)

        self.dbConn = dbConn
        self.dataType = "Commute"
        self.dataTable = "AnalyzerData"
        self.dataCols = ["Date","ActivityLevel","UserHeightInch","UserWeightLb","UserAge","UserGender","BodyFatMeasure","BMI"]
        
        self.setData(initVals)

    def getData(self):
        return analyzer(
            self.date.getVal(),
            self.active.getVal(),
            float(self.height.getVal()),
            float(self.weight.getVal()),
            float(self.age.getVal()),
            self.gender.getVal(),
            float(self.fatPercent.getVal()),
            float(self.bmi.getVal()))

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        

    def saveData(self):
        
        if not saveNotify("Omcron",self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True

        sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
        self.dbConn.execute(sqlStr,self.getData())
        self.dbConn.commit()

        self.statusBox.addLine("Saved Omcron Data for {}".format(self.date.getVal()))


        return True
        
    def setData(self,newData):
        self.date.setVal(newData.date)
        self.active.setVal(newData.activity)
        self.height.setVal(newData.heightIn)
        self.weight.setVal(newData.weightLb)
        self.age.setVal(newData.age)
        self.gender.setVal(newData.gender)
        self.fatPercent.setVal(newData.fat)
        self.bmi.setVal(newData.BMI)

    def clearData(self):
        self.date.setVal("")
        self.active.setVal("")
        self.height.setVal("")
        self.weight.setVal("")
        self.age.setVal("")
        self.gender.setVal("")
        self.fatPercent.setVal("")
        self.bmi.setVal("")

    def setDate(self,newDate):
        self.date.setVal(newDate)
