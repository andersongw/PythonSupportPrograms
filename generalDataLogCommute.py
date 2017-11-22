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

commuteDropdownList=["None","Toll","Inbound Fuel","Outbound Fuel",
 "Inbound Patco Fare", "Outbound Patco Fare",
 "Inbound Patco+Septa","Septa","NJT","Parking","TIPS Reimburse"]

commute = collections.namedtuple('commuteData','date note cost step')
commuteDefault=[
    commute(curDate(),"Toll",5.00,1),
    commute(curDate(),"Inbound Fuel",0.75,2),
    commute(curDate(),"Outbound Fuel",0.75,3)]


#
#   Commute Data
#


class commuteData(tk.Frame):
    def __init__(self,master = None, dbConn = None, outerTabs = None,initVals = commuteDefault):
        tk.Frame.__init__(self,master)
        self.dbConn = dbConn
        self.tabs = outerTabs
        self.grid()
        self.date = dateFieldLeft(self,"Date")
        self.totalCost = statusLabelBox(self,"Total Cost","6.50",0,1,1)
        self.drops=[]
        self.costs=[]
        self.includes=[]
        dropVals = self.fetchCommuteDrops()
        self.lineCount = 9
        
        self.autoDrive = actionBtn(self,"Drove",lambda event:self.autoDriveFn(),1,0)
        self.autoDriveTwo = actionBtn(self,"Drove Twice",lambda event:self.autoDriveTwoFn(),1,1)
        self.autoPatco = actionBtn(self,"Patco",lambda event:self.autoPatcoFn(),2,0)
        self.autoBike = actionBtn(self,"Bike",lambda event:self.autoBikeFn(),2,1)
        self.autoBike = actionBtn(self,"Bus + Patco",lambda event:self.autoBusPatcoFn(),3,0)
        self.addSepta = dataCheckBox(self,"Add Septa",False,3,1,1,self.toggleSepta)
        self.lastAuto = "Drive"
        
        startLine = 4
        for n in range(startLine,self.lineCount+startLine):
            self.drops+= [dataComboBox(self,"Note " + str(n-startLine+1)+": ",dropVals,n)]
            self.costs+=[dataFieldLeft(self,"Cost",n,1)]
            self.includes+=[dataCheckBox(self,"",True,n,2)]

        self.viewFrame = formFrame(self,None,1,3,3,11)
        self.viewStart = dateFieldLeft(self.viewFrame.frame,"Start Date",0,0,1,twoWeeksBefore(curDate()))
        self.viewBtn = actionBtn(self.viewFrame.frame,"Reset View",lambda event:self.fillView(),0,1)

        viewCfg = [
            treeColTpl("type",150,"Expense Type"),
            treeColTpl("cost",50,"Cost")]
        
        self.commuteView = treeView(self.viewFrame.frame,"Recent Commutes",viewCfg,1,0,2)
        self.commuteView.setIconWidth(100)
        self.commuteView.bindField("<<TreeviewSelect>>",self.selectLine)
        self.commuteView.setFontTag("TotalCommute",("Segoe UI",9,"bold"))

        self.missingLabel = statusLabelBox(self.viewFrame.frame,"Missing Dates","0 of 0",0,3)
        self.missingDaysList = messageListbox(self.viewFrame.frame,1,3)

        btnRow = startLine+self.lineCount
        self.saveBtn = actionBtn(self,"Save Commute Data",lambda event:self.saveBtnFn(),btnRow,0)
        self.saveFlag = dataCheckBox(self,"Save Data",False,btnRow,2)
        self.clearBtn = actionBtn(self,"Reset Data",lambda event:self.clearData(),btnRow,1)
        self.jumpSleep = actionBtn(self,"Sleep Data",lambda event:self.jumpTab(-1),btnRow,3)
        self.jumpJournal = actionBtn(self,"Journal Data",lambda event:self.jumpTab(1),btnRow,4)

        self.dataType = "Commute"
        self.dataTable = "CommuteData"
        self.dataCols = ["Date","CommuteNote","CommuteCost","CommuteStep"]

        for box in self.costs:
            box.bindField("<FocusOut>",self.calcTotalCost)
        
        self.setData(initVals)
        self.calcTotalCost()

        self.fillView()

     
    def autoDriveFn(self):
        self.clearData()
        self.drops[0].setVal("Toll")
        self.costs[0].setVal("5.00")

        self.drops[1].setVal("Inbound Fuel")
        self.costs[1].setVal("0.75")

        self.drops[2].setVal("Outbound Fuel")
        self.costs[2].setVal("0.75")

        self.calcTotalCost()
        self.lastAuto = "Drive"
        
    def autoDriveTwoFn(self):
        self.clearData()
        self.drops[0].setVal("Toll")
        self.costs[0].setVal("5.00")

        self.drops[1].setVal("Inbound Fuel")
        self.costs[1].setVal("0.75")

        self.drops[2].setVal("Outbound Fuel")
        self.costs[2].setVal("0.75")

        self.drops[3].setVal("Toll")
        self.costs[3].setVal("5.00")

        self.drops[4].setVal("Inbound Fuel")
        self.costs[4].setVal("0.75")

        self.drops[5].setVal("Outbound Fuel")
        self.costs[5].setVal("0.75")

        self.calcTotalCost()
        self.lastAuto = "Drive"
        
    def autoPatcoFn(self):
        self.clearData()
        self.drops[0].setVal("Parking")
        self.costs[0].setVal("1.00")

        self.drops[1].setVal("Inbound Fuel")
        self.costs[1].setVal("0.15")

        if self.addSepta.getVal():
            self.drops[2].setVal("Inbound Patco + Septa")
            self.costs[2].setVal("5.70")

            self.drops[5].setVal("TIPS Reimburse")
            self.costs[5].setVal("-8.30")

        else:
            self.drops[2].setVal("Inbound Patco Fare")
            self.costs[2].setVal("2.60")

            self.drops[5].setVal("TIPS Reimburse")
            self.costs[5].setVal("-5.20")

        self.drops[3].setVal("Outbound Patco Fare")
        self.costs[3].setVal("2.60")

        self.drops[4].setVal("Outbound Fuel")
        self.costs[4].setVal("0.15")

        self.calcTotalCost()
        self.lastAuto="Patco"

    def autoBikeFn(self):
        self.clearData()

        if self.addSepta.getVal():
            self.drops[0].setVal("Inbound Patco + Septa")
            self.costs[0].setVal("5.70")

            self.drops[2].setVal("TIPS Reimburse")
            self.costs[2].setVal("-8.30")

        else:
            self.drops[0].setVal("Inbound Patco Fare")
            self.costs[0].setVal("2.60")

            self.drops[2].setVal("TIPS Reimburse")
            self.costs[2].setVal("-5.20")

        self.drops[1].setVal("Outbound Patco Fare")
        self.costs[1].setVal("2.60")

        self.calcTotalCost()
        self.lastAuto="Bike"
        
    def autoBusPatcoFn(self):
        self.clearData()
        self.drops[0].setVal("Inbound NJT Bus")
        self.costs[0].setVal("1.60")

        if self.addSepta.getVal():
            self.drops[1].setVal("Inbound Patco + Septa")
            self.costs[1].setVal("5.70")

            self.drops[4].setVal("TIPS Reimburse")
            self.costs[4].setVal("-11.5")

        else:
            self.drops[1].setVal("Inbound Patco Fare")
            self.costs[1].setVal("2.60")

            self.drops[4].setVal("TIPS Reimbursel")
            self.costs[4].setVal("-8.40")

        self.drops[2].setVal("Outbound Patco Fare")
        self.costs[2].setVal("2.60")

        self.drops[3].setVal("Outbound NJT Bus")
        self.costs[3].setVal("1.60")

        self.calcTotalCost()
        self.lastAuto="Bus"

    def toggleSepta(self):
        if self.lastAuto == "Patco":
            self.autoPatcoFn()
        elif self.lastAuto == "Bus":
            self.autoBusPatcoFn()
        elif self.lastAuto == "Bike":
            self.autoBikeFn()

    def jumpTab(self,delta):
        self.tabs.select(1+delta)

    def saveBtnFn(self,Event=None):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)
        self.fillView()

    def selectLine(self,event):
        selIID = self.commuteView.getSelection()
        lineParent = self.commuteView.getCurParent(selIID)
        if lineParent == "":
            workDate = self.commuteView.getText(selIID)
        else:
            workDate = self.commuteView.getText(lineParent)

        workCommute = self.fetchCommuteData(workDate)
        self.clearData()
        self.setData(workCommute)


    def setData(self,newData):
        self.date.setVal(newData[0].date)
        commuteLen = len(newData)
        for step in range(commuteLen):
            self.drops[step].setVal(newData[step].note,ignore=False)
            self.costs[step].setVal(newData[step].cost)

        for step in range(commuteLen,self.lineCount):
            self.drops[step].setVal("None")

    def getData(self):
        out=[]
        step=0
        for n in range(self.lineCount):
            if self.drops[n].getVal()=="None":
                break
            if self.includes[n].getVal():
                out+=[commute(self.date.getVal(),self.drops[n].getVal(),float(self.costs[n].getVal()),step)]
                step+=1

        return out


    def calcTotalCost(self,event=None):
        ttl = 0.0
        for box in self.costs:
            if not box.getVal() == "":
                ttl+=float(box.getVal())
        self.totalCost.setVal(formatCost(ttl))
            

    def clearData(self):
        for n in range(self.lineCount):
            self.drops[n].setVal("None")
            self.costs[n].setVal("")
            self.includes[n].setVal(True)
            
    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        

    def saveData(self):

        if not saveNotify("Commute",self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True
                
        sqlStr = str.format("DELETE FROM {} WHERE Date = ?",self.dataTable)
        self.dbConn.execute(sqlStr,[self.date.getVal()])

        commuteList = self.getData()

        self.populateView(commuteList)
        
        for ln in commuteList:
            insertSql(self.dbConn,self.dataTable,self.dataCols,ln)            
##            sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
##            self.dbConn.execute(sqlStr,ln)

        self.dbConn.commit()
        self.statusBox.addLine("Saved Commute Data for {}".format(self.date.getVal()))


        return True

    def fetchCommuteDrops(self):
        return [txt[0] for txt in self.dbConn.execute("SELECT ControlText FROM ControlText WHERE ControlType = 'Commute'")]

    def fetchCommuteData(self,date):
        cur = self.dbConn.execute("SELECT * FROM CommuteData WHERE Date=(?) ORDER BY CommuteStep",(date,))
        res = cur.fetchall()
        if res != []:
            commutes = []
            for ln in res:
                commutes+=[commute(ln["Date"],
                                   ln["CommuteNote"],
                                   ln["CommuteCost"],
                                   ln["CommuteStep"])]
            return commutes
        return []

    def populateView(self,commuteList,weekIID=""):
        if len(commuteList)==0:
            return
        iidDate = self.commuteView.addLine(weekIID,commuteList[0].date,["",""])
        ttlCost = 0.0
        for ln in commuteList:
            self.commuteView.addLine(iidDate,str(ln.step),[ln.note,formatCost(ln.cost)])
            ttlCost+=ln.cost
        self.commuteView.updateLine(iidDate,commuteList[0].date,["Day Total",formatCost(ttlCost)],"TotalCommute")

    def fillView(self):
        self.commuteView.clearTree()
        res = self.dbConn.execute('SELECT DISTINCT Date  FROM CommuteData WHERE sortableDate(Date)>=sortableDate(?) ORDER BY sortableDate(Date)',[self.viewStart.getVal()]).fetchall()
        allDates = weekdaysSince(self.viewStart.getVal())
        dateSet=set()
        groupIID=""
        for ln in res:
            workDate=ln["Date"]
            if isMonday(workDate):
                fri = fromDatetime(toDatetime(workDate)+dt.timedelta(4))
                wkCost=self.getTtlCost(workDate,fri)
                groupIID = self.commuteView.addLine("","Week Total",[workDate+" -- "+fri,""],"TotalCommute")
                actualTtlIID = self.commuteView.addLine(groupIID,"Actual",["",formatCost(wkCost)],"TotalCommute")
                savingsIID=self.commuteView.addLine(groupIID,"Savings",["Baseline = $32.50",formatCost(32.50-wkCost)],"TotalCommute")
                
            cur = self.fetchCommuteData(workDate)
            self.populateView(cur,groupIID)
            dateSet.add(workDate)

        missingDates = sorted(list(allDates-dateSet))
        self.missingDaysList.clearData()
        for ln in missingDates:
            self.missingDaysList.addLine(ln)
        tmpStr=str.format("{} of {}",len(missingDates),len(allDates))
        self.missingLabel.setVal(tmpStr)
        # be sure this includes the current date -- for this and other quick ref widgets

    def getTtlCost(self,startDay,endDay):
        res = self.dbConn.execute("SELECT total(CommuteCost) FROM CommuteData WHERE sortableDate(Date)>=sortableDate(?) AND sortableDate(Date)<=sortableDate(?)",[startDay,endDay]).fetchone()
        return(res[0])

    def setDate(self,newDate):
        self.date.setVal(newDate)
        newData = self.fetchCommuteData(newDate)
        for n in range(self.lineCount):
            self.drops[n].setVal("None")
            self.costs[n].setVal("")

        if len(newData)==0:
            self.setData(commuteDefault)
            self.date.setVal(newDate)
        else:
            self.setData(newData)
        #tkmb.showinfo(message=self.fetchCommuteData(newDate))
        # Need to decide what to do here when the date is changed;
        # What data to display; what warnings if no existing data
        
