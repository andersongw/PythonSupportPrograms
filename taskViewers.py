import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as tkmb
from tkinter import filedialog as tkfd
from tkinter import font
import collections
import sqlite3
import re
import datetime as dt
import os.path
import shutil

import pyperclip
from guiBlocks import *


taskTuple = collections.namedtuple('taskTuple',
        "taskID title parentID flag startDate desc priority contact targetDate dateComplete complete archive atomic")    


#
##  Global Support Functions
#
        


def taskTupleFromSQL(sqlRow):
    return taskTuple._make(tuple(sqlRow))

def sqlFromTaskTuple(db,curTask):
    pass

def refreshTabsFn(tabsList):
    for workTab in tabsList:
        workTab.populateView()
        
def getProjects(conn,flag = None,complete = None, archive = None):
    sqlStr = "SELECT * FROM Tasks WHERE ParentTask IS NULL"
    sqlParam = []
    if flag != None:
        sqlStr+=" AND Flag = ?"
        sqlParam.append(flag)
    if complete != None:
        sqlStr+=" AND Complete = ?"
        sqlParam.append(complete)
    if archive != None:
        sqlStr+=" AND Archive = ?"
        sqlParam.append(archive)        
    return conn.execute(sqlStr,sqlParam).fetchall()
    
def pushFlag(event=None):
    upcomingTab.setFlag(pickFlag.getVal())
    recentTab.setFlag(pickFlag.getVal())
    refreshTabsFn()

def findProjectSQL(conn,workTaskID):
    curParent = workTaskID
    newParent = conn.execute("SELECT ParentTask FROM Tasks WHERE TaskID = ?",[curParent]).fetchone()["ParentTask"]
    while newParent !=None and newParent != curParent:
        #print(newParent)
        curParent=newParent
        newParent = conn.execute("SELECT ParentTask FROM Tasks WHERE TaskID = ?",[curParent]).fetchone()["ParentTask"]
    print("projectTask is: ",curParent)

def checkAtomicTask(conn,testTaskID):
    return (conn.execute("SELECT count(ParentTask) AS subTasks FROM Tasks WHERE ParentTask = ? GROUP BY ParentTask",[testTaskID]).fetchone()==None)

class attachmentsDlg(tk.Frame):
    def __init__(self,master=None, dbConn = None, taskTree = None, taskView = None):
        tk.Frame.__init__(self,master)
        self.dbConn = dbConn
        self.taskTree = taskTree
        self.taskView = taskView
        self.attachColCfg = []
        self.attachView = treeView(self,"Attached Files",self.attachColCfg,1,0)
        self.attachView.setIconWidth(500)
        self.attachView.setRowCount(5)
        self.attachView.bindField("<<TreeviewSelect>>",self.selectFile)

        self.taskDict = {ln["TaskID"]:taskTupleFromSQL(ln) for ln in self.dbConn.execute("SELECT * FROM Tasks").fetchall()}
        
        self.populateView()


    def populateView(self):
        self.iid_task = {}
        self.iid_note={}
        self.noteToTask={}
        self.iidProjects = []
        self.attachView.clearTree()
        #res = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask IS NULL").fetchall()
        res = getProjects(self.dbConn)#,complete=False,archive=False) -- caused lots of trouble; need to sort this out later
        for ln in res:
            #print(ln["Title"],ln["Complete"])
            iid = self.attachView.addLine("",ln["Title"],[])
            self.iidProjects.append(iid)
            taskID = ln["TaskID"]
            self.iid_task[iid]=taskID
            self.iid_task[taskID]=iid

        res = self.dbConn.execute("SELECT * FROM Notes NATURAL JOIN Files").fetchall()
        for ln in res:
            taskID = ln["TaskID"]
            curTask = taskID
            curPar=self.taskDict[curTask].parentID
            while curPar != None and curPar!=curTask:
                curTask = curPar
                try:
                    curPar = self.taskDict[curTask].parentID
                except KeyError:
                    pass

            try:
                iidParent = self.iid_task[curTask]
            except KeyError:
                pass

            
            iid = self.attachView.addLine(iidParent,ln["FileName"],[])
##            self.iid_task[iid]=taskID
##            self.iid_task[taskID]=iid
            self.iid_note[iid]=ln["NoteID"]
            self.noteToTask[ln["NoteID"]]=ln["TaskID"]

        for ln in self.iidProjects:
            if len(self.attachView.getChildren(ln))==0:
                self.attachView.hideItem(ln)
            else:
                self.attachView.closeLine(ln)
        
    def selectFile(self,event=None):
        selectIID = self.attachView.getSelection()[0]
        if selectIID in self.iidProjects:
            workTask = self.taskDict[self.iid_task[selectIID]]
        else:  
            workNote=self.iid_note[selectIID]
            if workNote!=None:
                workTask = self.taskDict[self.noteToTask[workNote]]
        self.taskTree.showTask(workTask)
        self.taskView.setData(workTask)
            
        

  
class recentDlg(tk.Frame):
    def __init__(self,master = None,dbConn = None, taskTree = None, taskView = None):
        tk.Frame.__init__(self,master)

        self.dbConn = dbConn
        self.taskTree = taskTree
        self.taskView = taskView

        self.useFlag = "Work"

        self.recentColCfg = [
            treeColTpl("taskTitle",200,"Title"),
            treeColTpl("taskStart",100,"Date Added"),
            treeColTpl("targetDate",100,"Target Date")]
        self.valueFields=["Title","StartDate","TargetDate"]
        self.recentView = treeView(self,"Recent Tasks",self.recentColCfg,1,0)
        self.recentView.setIconWidth(135)
        self.recentView.setRowCount(5)

        self.recentView.bindField("<<TreeviewSelect>>",self.selectTask)
        self.populateView()

    def setFlag(self,newFlag):
        self.useFlag = newFlag

    def populateView(self):
        self.iid_task={}
        self.recentView.clearTree()
        workDate = lastMonday()
        
        self.populateGroup("Recently Added","SELECT * FROM Tasks WHERE sortableDate(StartDate)>=sortableDate(?) AND Flag =?",[workDate,self.useFlag])
        self.populateGroup("Recently Completed","SELECT * FROM Tasks WHERE sortableDate(EndDate)>=sortableDate(?) AND Flag =?",[workDate,self.useFlag])

    def selectTask(self,event=None):
        selectIID = self.recentView.getSelection()[0]
        workTask = self.iid_task[selectIID]
        if workTask != None:
            self.taskTree.showTask(workTask)
            self.taskView.setData(workTask)
        

    def populateGroup(self,label,sqlStr,sqlValues):
        curIID = self.recentView.addLine("",label,[])
        self.iid_task[curIID] = None
        res = self.dbConn.execute(sqlStr,sqlValues).fetchall()
        for tsk in res:
            newIID = self.recentView.addLine(curIID,"",[tsk[col] for col in self.valueFields])
            self.iid_task[newIID]=taskTupleFromSQL(tsk)

        
class upcomingDlg(tk.Frame):
    def __init__(self,master = None,dbConn = None, taskTree = None, taskView = None):
        tk.Frame.__init__(self,master)

        self.dbConn = dbConn
        self.taskTree = taskTree
        self.taskView = taskView

        self.useFlag = "Work"

        self.upcomingColCfg = [
            treeColTpl("taskTitle",200,"Title"),
            treeColTpl("targetDate",100,"Target Date"),
            treeColTpl("priority",75,"Priority")]
        self.valueFields=["Title","TargetDate","Priority"]
                               
        self.upcomingView = treeView(self,"Upcoming Tasks",self.upcomingColCfg,1,0)
        self.upcomingView.setIconWidth(85)
        self.upcomingView.setRowCount(5)

        self.upcomingView.bindField("<<TreeviewSelect>>",self.selectTask)
        
        self.populateView()

    def setFlag(self,newFlag):
        self.useFlag = newFlag

    def populateView(self):
        self.iid_task={}
        self.upcomingView.clearTree()
        
        workDate=curDate()
        self.populateGroup("Overdue",
            "SELECT * FROM Tasks WHERE sortableDate(TargetDate)<sortableDate(?) AND Complete=0 AND Archive = 0 AND ParentTask IS NOT NULL AND Flag=? ORDER BY sortableDate(TargetDate)",[workDate,self.useFlag])

        self.populateGroup("Due Today",
            "SELECT * FROM Tasks WHERE sortableDate(TargetDate)=sortableDate(?) AND Complete = 0 AND ARCHIVE = 0 AND ParentTask IS NOT NULL AND Flag = ? ORDER BY sortableDate(TargetDate)",[workDate,self.useFlag]) 
        
        workDate=nextFriday(0)
        self.populateGroup("This Week",
            "SELECT * FROM Tasks WHERE sortableDate(TargetDate)>=sortableDate(?) AND TargetDate<=sortableDate(?) AND Complete=0 AND Archive = 0 AND ParentTask IS NOT NULL AND Flag= ? ORDER BY sortableDate(TargetDate)",[curDate(),workDate,self.useFlag])
        
        nextStart = workDate
        workDate = nextFriday(1)
        self.populateGroup("Next Week",
            "SELECT * FROM Tasks WHERE sortableDate(TargetDate)>sortableDate(?) AND TargetDate<=sortableDate(?) AND Complete=0 AND Archive = 0 AND ParentTask IS NOT NULL AND Flag= ? ORDER BY sortableDate(TargetDate)",[nextStart,workDate,self.useFlag])
        
        noFixed = "ASAP"
        self.populateGroup("No Fixed","SELECT * FROM Tasks WHERE sortableDate(TargetDate) = sortableDate(?) AND Complete=0 AND Archive = 0 AND ParentTask IS NOT NULL AND Flag=? ORDER BY Priority",[noFixed,self.useFlag])

    def selectTask(self,event=None):
        selectIID = self.upcomingView.getSelection()[0]
        workTask = self.iid_task[selectIID]
        if workTask != None:
            self.taskTree.showTask(workTask)
            self.taskView.setData(workTask)

    def populateGroup(self,label,sqlStr,sqlValues):
        curIID = self.upcomingView.addLine("",label,[])
        self.iid_task[curIID] = None
        res = self.dbConn.execute(sqlStr,sqlValues).fetchall()
        for tsk in res:
            if checkAtomicTask(self.dbConn,tsk["TaskID"]):
                newIID = self.upcomingView.addLine(curIID,"",[tsk[col] for col in self.valueFields])
                self.iid_task[newIID]=taskTupleFromSQL(tsk)

#
##  View Tasks
#

class taskViewDlg(tk.Frame):
    def __init__(self,master = None,dbConn = None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn

        self.dispProjCount = statusLabelBox(self,"Project Count","TBD",1,0) # Total number of uncompleted projects
        self.dispActiveCount = statusLabelBox(self,"Active Tasks","TBD",1,1) # Total number of uncompleted atomic tasks
        #self.dispTtlCount = statusLabelBox(self,"Total Tasks","TBD",1,2) # No idea what this was for; just commenting out for now
		
        self.hideComplete = dataCheckBox(self,"Hide Completed Tasks?",False,0,2)
        self.hideArchive = dataCheckBox(self,"Hide Archived Tasks?",True,0,3)
		
        self.hideComplete.setCommand(self.toggleHideTasks)
        self.hideArchive.setCommand(self.toggleHideTasks)

        colSetup=[
            treeColTpl("flag",50,"Flag"),
            treeColTpl("startDate",100,"Creation Date"),
            treeColTpl("desc",300,"Description"),
            treeColTpl("priority",100,"Priority"),
            treeColTpl("contact",100,"Contact Person"),
            treeColTpl("targetDate",100,"Target Date"),
            treeColTpl("endDate",100,"Completion Date")]
        self.taskView = treeView(self,"TaskView",colSetup,2,0,5)
        self.taskView.setIconWidth(300)

        self.refreshBtn = actionBtn(self,"Refresh View",lambda event:self.refreshView(),0,0)
        self.closeProjectsBtn = actionBtn(self,"Close Projects",lambda event:self.closeProjects(),0,1)


        self.populateTree()
        binList = [True,False]
        for complete in binList:
            for atomic in binList:
                archive=True
                tagName = self.getTagName(complete,archive,atomic)
                self.taskView.setGenericTag(tagName,strike=complete,bold=atomic,color='red')
                archive=False
                tagName = self.getTagName(complete,archive,atomic)
                self.taskView.setGenericTag(tagName,strike=complete,bold=atomic)
                    
                                                                                                
##        self.taskView.setGenericTag("complete",strike=True)
##        self.taskView.setGenericTag("atomic",bold=True,strike=True)
##        self.taskView.setGenericTag("archive",color='red')
##        self.taskView.setFontTag("complete",("Segoe UI",9,"overstrike"))
##        self.taskView.setFontTag("atomic",("Segoe UI",9,"bold"))
##        self.taskView.setFontTag("completeAtomic",("Segoe UI",9,"bold overstrike"))
##        self.taskView.setColorTag("archive",'red')
##        self.taskView.setMixedTag("all",("Segoe UI",9,"bold overstrike"),'red')
        # Need a more flexible way of specifying tags; esp composed tags
        # Such as "completed/atomic or archived/completed (or all three)
        #self.taskView.setFontTag("atomicComplete",
        
        #self.taskView.bindField("<<TreeviewSelect>>",self.onSelectOne)
        self.taskView.bindField("<Button-1>",self.clickLine)
        self.taskView.bindField("<Double-Button-1>",self.dblClickLine)
        self.taskView.bindField("<Button-3>",self.rtClickSelect)
        self.closeProjectsBtn.bindField("<Control-Button-1>",self.taskView.closeAllLines)

        self.dblClick = False
        self.lftClick = False
        self.rtClick = False
        self.closeProjects()

    def getTagName(self,complete=False,archive=False,atomic=False,task=None):
        tagName=""
        if task!=None:
            (complete,archive,atomic) = (task.complete,task.archive,task.atomic)
        if complete:
            tagName+="complete"
        if archive:
            tagName+="archive"
        if atomic:
            tagName+="atomic"
        if len(tagName)==0:
            tagName = "normal"
        return tagName
        


    def setEditDlg(self,editDlg=None):
        self.editDlg = editDlg

    def refreshView(self,collapse=True):
        self.taskView.clearTree()
        self.populateTree()
        self.editDlg.popTasks()
        if collapse:
            self.closeProjects()

    def taskTuple_Item(self,task):
        return (task.title,task[3:-2])

    def findSubtasks(self,taskID):
        ##Do I want to supplant this with the global version?  Not sure either way.
        if taskID != None:
            res = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask = ? ORDER BY Priority, Title",[taskID]).fetchall()
        else:
            res = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask IS NULL ORDER BY Priority, Title").fetchall()
            
        return [taskTupleFromSQL(ln) for ln in res]

    def hideLine(self,task):
        # Determine whether to display the item or not, depending on its status
        xComplete = self.hideComplete.getVal() and task.complete # True (hidden) if complete and hide
        xArchive = self.hideArchive.getVal() and task.archive # True (hidden) if archive and hide
        return xComplete or xArchive # True if either is hidden

    def genTags(self):
        pass


    def formTagName(self,complete,archive,atomic):
        pass
        
                     

    def updateCountDisplay(self):
        nProj = len(self.projectSet)
        nTask = len(self.taskSet-self.parentSet)
        self.dispProjCount.setVal(nProj)
        self.dispActiveCount.setVal(nTask)
        return (nProj,nTask)

    def popSets(self):
        fullDB = self.dbConn.execute("SELECT TaskID,ParentTask FROM Tasks WHERE Complete=0 AND Archive =0").fetchall()
        self.taskSet = {ln["TaskID"] for ln in fullDB}
        self.parentSet = {ln["ParentTask"] for ln in fullDB}
        self.projectSet = {ln["TaskID"] for ln in fullDB if ln["ParentTask"]==None}

    def populateTree(self):

        self.popSets()
        self.updateCountDisplay()
        
        inQueue=[None]
        outQueue=[]
        self.id_iid = {}
        self.iid_task = {}
        self.hiddenSet = set()
        while len(inQueue)>0:
            workTask = inQueue.pop()
            outQueue.append(workTask)
            subTasks = self.findSubtasks(workTask)
                
            if workTask == None:
                parentIID = ""
            else:
                parentIID = self.id_iid[workTask]


            for task in subTasks:
                newIID=self.addTaskLine(task,parentIID)
##                (txt,vals)=self.taskTuple_Item(task)
##                tag = self.task_tag(task)
##                
##                newIID=self.taskView.addLine(parentIID,txt,vals,tag)
##                self.id_iid[task.taskID]=newIID
##                self.iid_task[newIID]=task
                if self.hideLine(task):
                    self.taskView.hideItem(newIID)
                    self.hiddenSet.add(newIID)
                inQueue.append(task.taskID)

    def addTaskLine(self,task,parentIID):
        (txt,vals)=self.taskTuple_Item(task)
        tag = self.task_tag(task)
                
        newIID=self.taskView.addLine(parentIID,txt,vals,tag)
        self.id_iid[task.taskID]=newIID
        self.iid_task[newIID]=task

        return newIID


    def closeProjects(self):
        self.taskView.closeAllLines()
##        projects = self.taskView.getParents().values()
##        for iid in projects:
##            self.taskView.toggleLineOpen(iid)

    def toggleHideTasks(self):
        keyList = list(self.iid_task.keys())
        for ky in keyList:
            tsk=self.iid_task[ky]
            if self.hideLine(tsk):
                self.taskView.hideItem(ky)
                self.hiddenSet.add(ky)
            else:
                if ky in self.hiddenSet:
                    try:
                        parentIID = self.id_iid.get(tsk.parentID,None) ## Apparently a problem here
                        if parentIID is not None:
                            self.taskView.unhideItem(ky,parentIID)
                            self.hiddenSet.remove(ky)
                        else:
                            self.addTaskLine(tsk,"")
                    except KeyError:
                        print("Some kind of problem with that; can't unhide ",tsk.title,"; task parent is ",tsk.parentID)
        self.refreshView(False)

    def receiveDebug(self):
        projects = self.taskView.getParents()
        newIID = self.taskView.addLine("","Debug",[""])
        crossoff=self.taskView.getSelection()
        for iid in crossoff:
            self.taskView.tagItem(iid,"")
            lastIID = iid

        self.editDlg.setData(self.taskView.getText(lastIID))
        self.taskView.clearSelection()

    def showTask(self,task):
        taskIID = self.id_iid[task.taskID]
        self.taskView.showItem(taskIID)

    def onSelectOne(self,selIID,parentIID=None):
        #Populate the edit dialog with the details of the selected task/subtask
        #iid=event.widget.selection()[0]
        selTask = self.iid_task[selIID]

        if self.rtClick:
            self.editDlg.setParentBox(selTask.title)
            self.editDlg.clearTask()
            self.editDlg.title.takeFocus()
        else:
            if self.dblClick:
                selTask = selTask._replace(complete=1)
   
            self.editDlg.setData(selTask)
            self.editDlg.setEditField(self.setInputField)
        
            if self.dblClick:
                self.editDlg.markComplete()

        self.lftClick = False
        self.dblClick = False
        self.rtClick = False
        
    def clickLine(self,event=None):
        self.lftClick = True
        curx = event.x
        cury = event.y
        rowIID = event.widget.identify_row(cury)
        colID = event.widget.identify_column(curx)
        self.setInputField = event.widget.column(colID,"id")
        self.onSelectOne(rowIID)
        
    def dblClickLine(self,event=None):
        self.dblClick = True
        curx = event.x
        cury = event.y
        rowIID = event.widget.identify_row(cury)
        colID = event.widget.identify_column(curx)
        self.setInputField = event.widget.column(colID,"id")
        self.lftClick = True
        self.onSelectOne(rowIID)

    def rtClickSelect(self,event=None):
        cury = event.y
        rowIID = event.widget.identify_row(cury)
        self.rtClick = True
        self.taskView.setSelection(rowIID)
        parentIID = self.taskView.getCurParent(rowIID)
        self.onSelectOne(rowIID,parentIID)


    def addNewTask(self,task):
        self.taskSet.add(task.taskID)
        if task.parentID == None:
            parentIID = ""
            self.projectSet.add(task.taskID)
        else:
            parentIID = self.id_iid[task.parentID]
            self.parentSet.add(task.parentID)

            
        (txt,vals)=self.taskTuple_Item(task)
        tag = self.task_tag(task)
            
        newIID=self.taskView.addLine(parentIID,txt,vals,tag)
        self.id_iid[task.taskID]=newIID
        self.iid_task[newIID]=task
        if self.hideLine(task):
            self.taskView.field.detach(newIID)
            self.hiddenSet.add(newIID)
            self.taskSet.discard(task.taskID)

        self.updateCountDisplay()



    def task_tag(self,wkTask):
        tag = self.getTagName(task=wkTask)
        if wkTask.archive or wkTask.complete:
            self.taskSet.discard(wkTask.taskID)

        return tag

    def updateTask(self,task):

        taskIID = self.id_iid[task.taskID]
        (txt,vals)=self.taskTuple_Item(task)
        tag = self.task_tag(task)
        self.taskView.updateLine(taskIID,txt,vals,tag)
        self.iid_task[taskIID]=task
        if self.hideLine(task):
            self.taskView.field.detach(taskIID)
            self.hiddenSet.add(taskIID)

