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

defcon = collections.namedtuple('defcon','date ext int note')
recData= collections.namedtuple('recData','date menFlag HRec SRec')

defconDefault = defcon(curDate(),4,4,"")
recDefault = recData(curDate(),False,"","")

#
#   Defcon Data
#

class defconData(tk.Frame):
    def __init__(self,master = None, dbConn = None, outerTabs = None, initVals = (defconDefault,recDefault)):
        tk.Frame.__init__(self,master)
        self.grid()
        self.date = dateFieldLeft(self,"Date",0,0,2)

        self.dayFrame = formFrame(self,"Daily",1,0,2)
        self.defconFrame = formFrame(self,"Defcon",1,2,2)
        self.missingFrame = formFrame(self,"Missing Dates",1,4,2)
        self.viewFrame = formFrame(self,"ViewDefcons",2,0,6)

        dcFrame = self.defconFrame.frame
        self.ext = dataFieldLeft(dcFrame,"External",3,0,2)
        self.int = dataFieldLeft(dcFrame,"Internal",4,0,2)
        self.note = dataTextBox(dcFrame,"Note",5,0,4,2,boxW=40)
        self.saveDefconBtn = actionBtn(dcFrame,"Save Defcon Only",lambda event:self.saveDefcon(),0,1,2)

        dyFrame = self.dayFrame.frame
        self.men = dataCheckBox(dyFrame,"MenFlag",False,0,0)
        self.menReportLast = statusLabelBox(dyFrame,"Last time","None",1)
        self.menReportNext = statusLabelBox(dyFrame,"Next time","None",2)
        self.hrec = dataFieldTop(dyFrame,"HRec",3)
        self.srec = dataFieldTop(dyFrame,"SRec",3,1)
        

        self.viewStart = dateFieldLeft(self.missingFrame.frame,"Start Date",0,0,2,initVal=deltaDate(-14))
        self.missingDates = messageListbox(self.missingFrame.frame,1,0,2)
                                         
        self.defconTreeCfg = [treeColTpl("Men",40,"Men"),
                              treeColTpl("Int",40,"Int"),
                              treeColTpl("Ext",40,"Ext"),
                              treeColTpl("Note",250,"Note")]
        self.defconTree = treeView(self.viewFrame.frame,"Defcon",self.defconTreeCfg,0)
        self.defconTree.setIconWidth(dateColWidth)

        recCol = 75
        self.recViewCfg=[
            treeColTpl("HRec",recCol,"HRec"),
            treeColTpl("SRec",recCol,"SRec")]
        self.recTree = treeView(self.viewFrame.frame,"Rec",self.recViewCfg,0,1)
        self.recTree.setIconWidth(dateColWidth)
    
        btnRow = 5
        self.saveTab = actionBtn(self,"Save Defcon Data",lambda event:self.saveBtnFn(),btnRow,0)
        self.clrBtn = actionBtn(self,"Clear Data",lambda event:self.clearData(),btnRow,1)
        self.saveFlag = dataCheckBox(self,"Save Data",False,btnRow,2)
        self.refreshViewBtn = actionBtn(self,"Refresh View",lambda event:self.popDates(),btnRow,3)
        self.bellaJump = actionBtn(self,"Arabella Data",lambda event:self.tabJump(-1),btnRow,4)
        self.weighJump = actionBtn(self,"Weight Watchers Data",lambda event:self.tabJump(1),btnRow,5)


        self.dbConn = dbConn
        self.tabs = outerTabs
        self.dataType = "Defcon"
        self.dataTable = "DefconData"
        self.dataCols = ["Date","ExternalDefcon","InternalDefcon","DefconNote"]
        self.recTable = "RecData"
        self.recCols = ["Date","MenFlag","HRec","SRec"]
 
        self.setData(initVals)
        self.popDates()
        self.popView()

    def popDates(self):
        """Not sure"""
        self.findLastMen()
##        self.missingDates.clearData()
##        workDate = self.viewStart.getVal()
##        res = orderedFetchSql(self.dbConn,self.dataTable,["sortableDate(Date)"],[sortableDate(workDate)],"sortableDate(Date)")
##        for ln in res:
##            self.missingDates.addLine(ln["Date"])

    def popView(self,event=None):
        """Populates the defconTree and recTree widgets.

           Called as an action from the RefreshView button, or as part of the initialization of the
           defconData class.
        """

        #  First -- populate the defcon tree
        res = self.dbConn.execute("SELECT * FROM DefconData WHERE sortableDate(Date)>=sortableDate(?) ORDER BY sortableDate(Date)",[self.viewStart.getVal()]).fetchall()
        self.displaySet = set()
        rec_iid = {}
        for ln in res:
            self.displaySet.add(ln["Date"])
            viewLine = ("",
                        ln["ExternalDefcon"],
                        ln["InternalDefcon"],
                        ln["DefconNote"])
            rec_iid=self.defconTree.addLine("",ln["Date"],viewLine)
        allDateSet = daysSince(self.viewStart.getVal())
        missingDays=sorted(list(allDateSet-self.displaySet))
        tmpStr=str.format("{} of {}",len(missingDays),len(allDateSet))
        for ln in missingDays:
            self.missingDates.addLine(ln)

        for ln in sorted(list(self.displaySet)):
            pass
            print(ln)

        # Second -- populate the rec tree
        res = self.dbConn.execute("SELECT * FROM RecData WHERE sortableDate(Date)>=sortableDate(?) ORDER BY sortableDate(Date)",[self.viewStart.getVal()]).fetchall()
        for ln in res:
            viewLine = (ln["HRec"],ln["SRec"])
            self.recTree.addLine("",ln["Date"],viewLine)
            
    def findLastMen(self):
        """Identify the last date for which a True menFlag was recorded, then update the display for when
        the next is expected.
        """
        #recentMen = self.dbConn.execute("SELECT sortableDate(Date) FROM RecData WHERE MenFlag = 1 ORDER BY sortableDate(Date) DESC").fetchall()
        lastMen = self.dbConn.execute("SELECT max(sortableDate(Date))as date FROM RecData WHERE MenFlag = 1").fetchone()
##        for ln in recentMen:
##            print(ln[:])
        lastDate = dt.datetime.strptime(lastMen["date"],"%Y-%m-%d")
        expectDate = lastDate+dt.timedelta(21) #assume next starts 21 days after the last ends
        nextMen = expectDate.strftime("%Y-%m-%d")
        self.menReportLast.setVal(lastMen["date"])
        self.menReportNext.setVal(nextMen)

    def tabJump(self,delta):
        self.tabs.select(4+delta)

    def getData(self):
        return (defcon(
                    self.date.getVal(),
                    int(self.ext.getVal()),
                    int(self.int.getVal()),
                    self.note.getVal()),
                recData(
                    self.date.getVal(),
                    bool(self.men.getVal()),
                    self.hrec.getVal(),
                    self.srec.getVal()))


    def saveBtnFn(self,event=None):
        self.saveFlag.setVal(True)
        self.saveData()
        self.saveFlag.setVal(False)

    def connectStatus(self,statusBox):
        self.statusBox = statusBox
        
                
    def saveData(self):

        if not saveNotify(self.dataType,self.saveFlag.getVal()):
            return False

        if not self.saveFlag.getVal():
            return True

        saveDefcon,saveRec = self.getData()
        insertSql(self.dbConn,self.dataTable,self.dataCols,saveDefcon)
        insertSql(self.dbConn,self.recTable,self.recCols,saveRec)
        
        self.statusBox.addLine("Saved Full Defcon Data for {}".format(self.date.getVal()))

        return True

    def saveDefcon(self):
        
        sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
        self.dbConn.execute(sqlStr,saveDefcon)
        self.dbConn.commit()

        self.statusBox.addLine("Saved Defcon Only Data for {}".format(self.date.getVal()))


        return True

    def setData(self,newData):
        newDefcon,newRec = newData
        self.date.setVal(newDefcon.date)
        self.men.setVal(newRec.menFlag)
        self.ext.setVal(newDefcon.ext)
        self.int.setVal(newDefcon.int)
        self.note.setVal(newDefcon.note)
        self.hrec.setVal(newRec.HRec)
        self.srec.setVal(newRec.SRec)

    def clearData(self):
        self.date.setVal("")
        self.men.setVal("")
        self.ext.setVal("")
        self.int.setVal("")
        self.note.setVal("")
        self.hrec.setVal("")
        self.srec.setVal("")
        self.int.toggleEnable()

    def setDate(self,newDate):
        self.date.setVal(newDate)
        #tkmb.showinfo(self,self.fetchDefconData(newDate))
        # Need to decide what to do here when the date is changed;
        # What data to display; what warnings if no existing data

    def fetchDefconData(self,date):
        cur = self.dbConn.execute("SELECT * FROM DefconData WHERE Date=(?) ORDER BY DefconID",(date,))
        res = cur.fetchone()
        if res != None:
            newDefcon = defcon(res["Date"],
                                   res["ExternalDefcon"],
                                   res["InternalDefcon"],                          
                                   res["DefconNote"])
        else:
            newDefcon = defconDefault

        cur = self.dbConn.execute("SELECT * FROM RecData WHERE Date=(?) ORDER BY DefconID",(date,))
        res = cur.fetchone()
        if res != None:
            newRec = recData(res["Date"],
                                   res["MenFlag"],
                                   res["HRec"],
                                   res["SRec"])
        return (newDefcon,newRec)
                     
