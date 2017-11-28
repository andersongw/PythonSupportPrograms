# Last Edited 11/24/17
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
import csv

import pyperclip

from guiBlocks import *
from taskViewers import *
from noteDlg import *
import autoversion as av

execExts=(".py",".pyw",".exe")

av.dispRunDateTime()
el=av.editLog()
el.autoversionList(('autoversion.py','guiBlocks.py','taskViewers.py','todoMgr.pyw','noteDlg.py'))

blankTask = taskTuple(None,"", "", "", "", "", "", "", "", "", "", "", "")    


##noteTuple = collections.namedtuple('noteTuple',
##        "noteID taskID noteDate noteText archive fileID")
##blankNote=noteTuple(None,None,"","",False,None)
##
##fileTuple = collections.namedtuple('fileTuple',
##        "fileID filePath fileName saveTime")
##blankFile = (None,"","","")

##Issues to work on:
#   1.  Improved auto-priority function to speed up; don't commit database for every item
#          -- Related: how to handle priority for completed/archived tasks?  Maybe add a note with the date of the staus change and the priority at the time?
#                       maybe leave the priority fixed at the time of completion, but not include it in the auto increment operation
#   2.  Hash associated file to compare editions
#           Use hashed files and periodically walk the file structure to look for linked files that have moved.
#   3.  Filter tasks to find particular terms
#   4.  Flag project/task target dates that are sooner than any component sub-task target dates
#           ** Red font for target date text when it's earlier than all subtasks
#          When to check this?  Walk up the tree every time a subtask is added/changed?  Only on Refresh?  Store project
#   5.  Flag a task that's marked complete without all subtasks being complete
#           * Related: flag a task that's not marked complete when all subtasks are complete.
#               -- Maybe italicise text/use gray font while there are open subtasks, and use red font if marked complete prematurely
#   6.  Add a project category top level hierarachy (technical vs purchase).  Projects will still have no parents, but will not be top level iids
#           Alternate: use to filter task display
#   7.  Add a separate database to leave at work (for work-related embedded files)
#           Alternate: Encrypt the database on exit/decrypt on start?
#
#
#   8.  Add a new field to the TaskTuple -- ancestors:
#           A list containing the parent tasks for each task, all the way up to the top level project
#           For a project, it's an empty list
#           For each subtask of the project, it inherits the parent's list and appends the parent's TaskID
#   9.  Add a descendents field to TaskTuple:
#           List of sets; add a level to the list for each sub-division of tasks / add an element to the set for each subtask created
#           Necessary to implement 4. and 5.
#   10. Better way to indicate whether the task has changed since last update
#   11. Quick find for parent task -- generalized functionality for dropdown boxes that isn't working
#   12. Autocomplete subtasks when a task is marked complete (alt: block marking a task complete until all subtasks are complete)
#   13. Debug confirmFile function.  Not popping up the relink dialog.
#   14. Add new tasks directly to the pool of parent tasks without having to hit refresh
#   15. Implement restore file button
#   16. Modify note display to indicate whether a file is stored or just linked
#   17. Move tasks when a parent is reassigned (without having to refresh display; alt: refresh display)
#           -- Related: insert new tasks according to their priority
#           -- Related: shift subtasks when adjusting priority
#   18. Update the parents dropdown with every  refresh  (think this is complete; definitely updates with every new non-atomic task)
#
#   19. Add a reporting tab for attached files -- kind of have this with a cursory implementation
#           -- Maybe add an option to sort by priority vs. alphabetical
#   20. Debug adding a note to a new task; doesn't find the task until it's saved.
#           -- In addition to autosaving the task, maybe change the background of the note field until the task is saved.
#           -- Also, maybe copy the note field text prior to saving it, then repopulate the note text field with the text after saving the task
#   21. Whenever the tree display changes, maybe step through all IID, identify whether they show up, make any changes to what displays,
#       then when redisplaying the tree, include the prior information for whether or not they show up in the new view.  Should be a method
#       on the Treeview class?
#   22. Implement +/- keys for adjusting priority
#   23. Add a display field to the Parent Task display to show the TaskID
#       (To help disambiguate tasks with similar titles)
#   24. Port this list into the ToDo Manager to simplify tracking :)
#
#
#   Completed
#   Implement multiple font-based tags (italics/strikeout/bold)
#   Adjust priority to avoid collisions (auto-increase higher priority tasks when a new task is introduced/priority is reassigned)
#       (Duplicated below)
        #   Want to assign consecutive priorities for all tasks with a given parent
        #   Search for all tasks with the target task's parent (sort by priority)
        #   Until dialogs work properly, arbitrarily assign priority in the event of a collision
        #   Step through all tasks of lower priority than the target, assigning the priority as the position in the list
        #   Assign the target its specified priority
        #   Step through the rest of the tasks based on their position in the list + the target priority
        #   Run this algorithm any time the priority changes on any task
#   Autodistribute priority within tasks
#   Autoarchive subtasks when a task is marked Archived (alt as above) -- completed!
#
#
#
#




#################################################################################
#
##  Add/Edit Task
#
#################################################################################

class addTaskDlg(tk.Frame):
    def __init__(self,master = None, dbConn = None, taskView = None, noteView = None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.taskView = taskView
        self.noteView = noteView
        self.tsk = blankTask
        self.storedTask = None

        self.title = dataFieldLeft(self,"Task Title",0,0,3)
        self.parent = dataComboBox(self,"Parent Task",["New Project"],1,0,2)     
        self.priority = dataFieldLeft(self,"Priority",2,0)
        self.contact = dataFieldLeft(self,"Contact Person",2,1)
        self.flagDrop = dataComboBox(self,"Flag",["Work","Home"],2,2)          
        self.desc = dataTextBox(self,"Description",3,0,4)
        self.dateStart = dateFieldLeft(self,"Start Date",8,0)
        self.target = dateFieldLeft(self,"Target Date",8,1)
        self.complete = dataCheckBox(self,"Task Complete?",False,9,0)
        self.dateEnd = dateFieldLeft(self,"Completion Date",8,2)
        self.archive = dataCheckBox(self,"Archive Task?",False,9,1)
        self.atomic = dataCheckBox(self,"Atomic Task?",False,9,2)

        #self.saveBtn=actionBtn(self,"Save New Task",self.saveTask,10,0)
        #self.saveBtn=actionBtn(self,"Save New Task",self.saveTask,10,0)
        #self.clearTaskBtn = actionBtn(self,"Clear Task",self.clearTask,10,1)
        self.saveClearBtn = dblBtn(self,["Save New Task","Clear Task"],[self.saveTask,self.clearTask],10,0)
        self.copyPasteTaskBtn = dblBtn(self,["Store Task","Duplicate Task"],[self.storeTask,self.duplicateTask],11,0)
        self.storedTaskBox = dataFieldLeft(self,"Stored Task",11,1,2)
        self.duplicateTree = dataCheckBox(self,"Duplicate SubTasks?",True,12,1)
        self.filterDuplicates = dataCheckBox(self,"Include Completed/Archived Subtasks",True,12,2)
        
        self.export = buttonPrompt(self,"Export Subtasks","ExportFilename.csv",self.exportTasks,10,2)

        self.archiveBtn=actionBtn(self,"Archive Subtasks",self.archiveSubTasksFn,10,1)
                                    
        self.complete.setCommand(self.markComplete)
        self.title.bindField('<ButtonRelease-3>',rightClickPaste)
        self.contact.bindField('<ButtonRelease-3>',rightClickPaste)
        self.desc.bindField('<Control-ButtonRelease-3>',rightClickPasteTextBox)
        self.desc.bindField('<ButtonRelease-3>',textBoxInsertPaste)
        self.dateStart.bindField('<ButtonRelease-3>',self.datePaste)
        self.target.bindField('<ButtonRelease-3>',self.datePaste)
        self.priority.bindField('<MouseWheel>',self.scrollPriority)


##        self.saveBtn.bindField('<ButtonRelease-1>',self.saveTask)
##        self.saveBtn.bindField('<Control-ButtonRelease-1>',self.ctrlSaveTask)

        self.dataTable = "Tasks"
        self.dataCols=[
            "Title",
            "ParentTask",
            "Flag",
            "StartDate",
            "Description",
            "Priority",
            "Contact",
            "TargetDate",
            "EndDate",
            "Complete",
            "Archive",
            "Atomic"]
        #print("Running popTasks")
        self.popTasks()
        self.clearTask()

##    def testFn(self,event=None):
##        print(event.state)
##
##        print(checkCtrlClick(event))
##        print(checkAltClick(event))
##       

    def storeTask(self,event=None):
        if checkCtrlClick(event):
            self.storedTask = None
            self.storedTaskBox.setVal("")
            return
        self.storedTask = self.taskID
        self.storedTaskBox.setVal(self.title.getVal())

    def duplicateTask(self,event=None):
        old_new={}
        newParent = None
        inQueue = [self.storedTask]
        sqlStr = "INSERT INTO Tasks ({}) VALUES ({})".format(",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
        while len(inQueue)>0:
            curTask = inQueue.pop()
            curTuple = taskTupleFromSQL(self.dbConn.execute("SELECT * FROM Tasks WHERE TaskID = ?",[curTask]).fetchone())
            newTuple = curTuple._replace(parentID = newParent)
            if curTask not in old_new.keys():
                cur = self.dbConn.execute(sqlStr,newTuple[1:])
                old_new[curTask]=cur.lastrowid
                finalTask = newTuple._replace(taskID=cur.lastrowid)
                self.taskView.addNewTask(finalTask)
            subTasks = [taskTupleFromSQL(ln) for ln in self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask = ?",[curTask]).fetchall()]
            for tsk in subTasks:
                newTuple = tsk._replace(parentID = old_new[curTask])
                cur = self.dbConn.execute(sqlStr,newTuple[1:])
                old_new[tsk.taskID] = cur.lastrowid
                finalTask = newTuple._replace(taskID = cur.lastrowid)
                self.taskView.addNewTask(finalTask)      
            inQueue+=[tsk.taskID for tsk in subTasks]
        self.dbConn.commit()
        
            



##        descends = findDecendants(self.dbConn,self.storedTask)
##        for ln in descends.keys():
##            print(ln,descends[ln])
##
##        
##    # To start - just copy the current task as a new task
##        storedTask = fetchTask(self.dbConn,self.storedTask)
##        newTask = storedTask._replace(parentID=None)
##        print(newTask)
        

        

    # Handler to allow changing the priority field using the scroll wheel
    def scrollPriority(self,event=None):
        if event.delta>0:
            step = -1
        else:
            step = 1
        try:
            curVal = int(self.priority.getVal())
        except ValueError:
            curVal = 4

        self.priority.setVal(self.formatPriority(curVal+step))
            
    def formatPriority(self,newVal):
        return "{:02d}".format(newVal)

    def deconflictPriority(self):
##        dirList = dir(self)
##        for ln in dirList:
##            print(ln)
##        print(self.getCurParentID())
        curPriority = max(1,int(self.priority.getVal()))
        curParent = self.getCurParentID()
        if curParent is None:
            siblings = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask IS NULL ORDER BY Priority").fetchall()
        else:
            siblings = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask = ? ORDER BY Priority",[curParent]).fetchall()
        #siblings = self.dbConn.execute("SELECT * FROM Tasks WHERE ParentTask = ? ORDER BY Priority",[curParent]).fetchall()
        sibList = [taskTupleFromSQL(ln) for ln in siblings if ln["Title"] != self.title.getVal()]
        curPriority = min(curPriority,len(sibList)+1)

        #firstCut = min(curPriority,len(sibList))

        for curPos in range(curPriority-1):
            #print(curPos+1,sibList[curPos].title)
            curTask = sibList[curPos]._replace(priority = self.formatPriority(curPos+1))
            updateSql(self.dbConn,self.dataTable,self.dataCols,curTask[1:],"TaskID",[curTask.taskID])
            self.taskView.updateTask(curTask)

##        print(curPriority,self.title.getVal())
##        print("Rest of list here")

        for curPos in range(curPriority,len(sibList)+1):
            #print(curPos+1,sibList[curPos-1].title)
            curTask = sibList[curPos-1]._replace(priority = self.formatPriority(curPos+1))
            updateSql(self.dbConn,self.dataTable,self.dataCols,curTask[1:],"TaskID",[curTask.taskID])
            self.taskView.updateTask(curTask)
            
        
####        if curPriority>1:
####            for curPos in range(firstCut):
####                curTask = sibList[curPos]
####                print(curTask)
####                curTask = curTask._replace(priority=curPos+1)
####                updateSql(self.dbConn,self.dataTable,self.dataCols,curTask[1:],"TaskID",[curTask.taskID])
####                self.taskView.updateTask(curTask)
####
####        if curPriority<len(sibList):
####            for curPos in range(curPriority+1):
####                curTask = sibList[curPos]
####                print(curTask)
####                curTask = curTask._replace(priority = curPos+1)
####                updateSql(self.dbConn,self.dataTable,self.dataCols,curTask[1:],"TaskID",[curTask.taskID])
####                self.taskView.updateTask(curTask)
####        

    def archiveSubTasksFn(self,event=None):
        # Walk down the tree from the current task, and set the archive flags to True
        tsk = self.getData()
        allSubtasks = walkProjectList(self.dbConn,self.taskID,True)
        for tsk in allSubtasks:
            #print(tsk)
            newTsk=tsk._replace(archive=1)
            #print(newTsk)
            updateSql(self.dbConn,self.dataTable,self.dataCols,newTsk[1:],"TaskID",[newTsk.taskID])
            self.taskView.updateTask(newTsk)


    #   Generate a CSV file wilth all of the sub tasks under the current task
    def exportTasks(self):
        if self.taskID == None:
            tkmb.showerror(None,"No task selected")
            return
        allSubTasks = walkProjectList(self.dbConn,self.taskID)
        id_title = {tsk.taskID:tsk.title for tsk in allSubTasks}
        id_title[None]="Project"

        exportNameRaw = self.export.getVal()
        (fname,fext)=os.path.splitext(exportNameRaw)
        exportName = fname+".csv"

        exportFile = open(exportName,'w',newline='')
        exportWriter = csv.writer(exportFile)
        exportWriter.writerow(["Data Exported:",curDate()])        
        exportWriter.writerow(["Project:",id_title[self.taskID]])
        exportWriter.writerow(["Task","Parent","Description"])
        for ln in allSubTasks:
            exportWriter.writerow([id_title[ln.taskID],id_title[ln.parentID],ln.desc])
            
        exportFile.close()
        if tkmb.askyesno(None,"All subtasks exported to "+exportName+". Open File?",default=tkmb.NO):
            os.startfile(exportName)



    def markComplete(self):
        if self.complete.getVal():
            self.dateEnd.setVal(curDate())
        else:
            self.dateEnd.setVal("")

    def clearTask(self,event=None):
        self.taskID = None
        self.title.setVal("")
        self.dateStart.setVal(curDate())
        self.priority.setVal("04")
        self.desc.setVal("")
        self.contact.setVal("Self")
        self.target.setVal("ASAP") 
        self.complete.setVal(0)
        self.dateEnd.setVal("")
        self.archive.setVal(0)
        self.atomic.setVal(0)
        #self.saveBtn.recaption("Save New Task")
        self.saveClearBtn.recaption0("Save New Task")
        self.noteView.clearTask()

        
    def setData(self,newData):
        if newData.parentID == None:
            parentTitle = "New Project"
        else:
            parentTitle = self.taskDict[newData.parentID]

        self.taskID = newData.taskID
        self.title.setVal(newData.title)
        self.parent.setVal(parentTitle)
        self.flagDrop.setVal(newData.flag)
        self.priority.setVal(newData.priority)
        self.desc.setVal(newData.desc)
        self.contact.setVal(newData.contact)
        self.dateStart.setVal(newData.startDate)
        self.target.setVal(newData.targetDate)
        self.complete.setVal(newData.complete)
        self.dateEnd.setVal(newData.dateComplete)
        self.archive.setVal(newData.archive)
        self.atomic.setVal(newData.atomic)
        #self.saveBtn.recaption("Update Current Task")
        self.saveClearBtn.recaption0("Update Current Task")
        self.noteView.popNotes(self.taskID)


##    def title_parentID(self,title):
##        parents = self.dbConn.execute("SELECT TaskID,ParentTask FROM Tasks WHERE Title = ?",[title]).fetchall()
##        if parents == None:
##            tkmb.showerror(None,"No Task Found")
##            return None
##        elif len(parents)>1:
##            tkmb.showinfo(None,"Name collision; multiple titles.  Add code to select among candidates.  Returning first for now.")
##            #   Can add an iterating sequence of dialog boxes to choose from
##            #   Show title and associated parent task
##
##        return parents[0]["TaskID"]

    def getCurParentID(self):
        if self.parent.getVal()=='New Project':
            parent = None
        else:
            parentTask = self.parent.getVal()
            parents = self.dbConn.execute("SELECT TaskID,ParentTask FROM Tasks WHERE Title = ?",[parentTask]).fetchall()
            if len(parents)==0:
                tkmb.showerror(None,"No task with that title")
                parent = None
            elif len(parents)>1:
                tkmb.showinfo(None,"Name collision; multiple titles.  Add code to select among candidates.  Returning first for now.")

            parent = parents[0]["TaskID"]

        return parent
    

    def getData(self):
##        if self.parent.getVal()=='New Project':
##            parent = None
##        else:
##            parent = self.title_parentID(self.parent.getVal())
        parent = self.getCurParentID()

        return taskTuple(
            self.taskID,
            self.title.getVal(),
            parent,
            self.flagDrop.getVal(),
            self.dateStart.getVal(),
            self.desc.getVal(),
            self.priority.getVal(),
            self.contact.getVal(),
            self.target.getVal(),
            self.dateEnd.getVal(),
            self.complete.getVal(),
            self.archive.getVal(),
            self.atomic.getVal())

    def saveTask(self,event=None):
        tsk = self.getData()
        if tsk.taskID == None:#Create a new task
            self.taskID=insertSql(self.dbConn,self.dataTable,self.dataCols,tsk[1:])
            self.noteView.setTaskID(self.taskID)
##            if tsk.parentID != None:
##                self.taskID = self.dbConn.execute("SELECT TaskID FROM Tasks WHERE Title=? AND ParentTask = ?",[tsk.title,tsk.parentID]).fetchone()["TaskID"]
##            else:
##                self.taskID = self.dbConn.execute("SELECT TaskID FROM Tasks WHERE Title=? AND ParentTask IS NULL",[tsk.title]).fetchone()["TaskID"]

            newTsk=tsk._replace(taskID=self.taskID)
            self.taskView.addNewTask(newTsk)
            #Add to the parent dropdown
            if not (newTsk.complete or newTsk.archive or newTsk.atomic):
                self.taskList = self.addTaskToList(self.taskList,newTsk)
                self.parentTaskList = self.addTaskToList(self.parentTaskList,newTsk)
                self.parent.updateVals(self.parentTaskList)  # Why doesn't this update the parent list?
                #tkmb.showinfo(None,"Should update parent list")
        else:# Update the existing task
            if tsk.taskID == tsk.parentID:
                print("Self-parent collision.  Time paradox!")
                tsk._replace(parentID=None)
            updateSql(self.dbConn,self.dataTable,self.dataCols,tsk[1:],"TaskID",[tsk.taskID])
            self.taskView.updateTask(tsk)
            self.noteView.setTaskID(tsk.taskID)

        if checkCtrlClick(event):
            self.clearTask()

        self.deconflictPriority()



    def ctrlSaveTask(self,event=None):
        self.saveTask()
        self.clearTask()
        self.title.takeFocus()

    def addTaskToList(self,curList,newTask):
        tmpList=curList[1:]+[newTask.title]
        tmpList.sort()
        outList = [curList[0]]+tmpList
        return outList
        

    def popTasks(self):  #Gather the list of available tasks to use as parents
        #print("Enter popTasks")
        res = self.dbConn.execute("SELECT Title,TaskID,Complete,Archive,Atomic FROM Tasks ORDER BY Title").fetchall()
##        self.taskList = ["New Project"]+[ln["Title"] for ln in res]
##        self.taskDict = {ln["TaskID"]:ln["Title"] for ln in res}
        self.taskList=["New Project"]
        self.parentTaskList=["New Project"]
        self.taskDict={}
        for ln in res:
            lnTitle=ln["Title"]
            self.taskList.append(lnTitle)
            self.taskDict[ln["TaskID"]]=lnTitle
            if not (ln["Complete"] or ln["Archive"] or ln["Atomic"]):
                self.parentTaskList.append(lnTitle)
        self.taskDict[None]="New Project"
        self.parent.updateVals(self.parentTaskList)
        self.parent.setQuickFind()
        #tkmb.showinfo(None,"Should refresh the parent drop down")

##
##    def debug(self,event=None):
##        #self.taskView.receiveDebug()
##        print(len(self.desc.getVal()))
##
##    def ctrlDebug(self,event=None):
##        print("Ctrl click")

    def setEditField(self,activeField):
        if activeField == "":
            self.title.takeFocus()
        elif activeField == "startDate":
            self.dateStart.takeFocus()
        elif activeField == "desc":
            self.desc.takeFocus()
        elif activeField == "priority":
            self.priority.takeFocus()
        elif activeField == "contact":
            self.contact.takeFocus()
        elif activeField == "targetDate":
            self.target.takeFocus()
        elif activeField == "endDate":
            self.dateEnd.takeFocus()

    def setParentBox(self,newParentText):
        self.parent.setVal(newParentText)

    def datePaste(self,event = None):
        pasteData = pyperclip.paste()
        testDate = cleanDate(pasteData)

        checkDate = re.search("\d{2}/\d{2}/\d{2}",testDate)

        if checkDate == None:
            pasteData = curDate()
        else:
            pasteData = checkDate.group()

        event.widget.delete(0,tk.END)
        event.widget.insert(0,pasteData)
        event.widget.focus_force()

#
##  Global Support Functions
#    

def walkProjectList(dbConn,projTask,fullList = False):
    inQueue=[projTask]
    outQueue=[]
    projRes = dbConn.execute("SELECT * FROM Tasks WHERE TaskID = ?",[projTask]).fetchone()
    outTuples = [taskTupleFromSQL(projRes)]
    if fullList:
        sqlStr = "SELECT * FROM Tasks WHERE ParentTask = ?"
    else:
        sqlStr = "SELECT * FROM Tasks WHERE ParentTask = ? AND Complete = 0 AND Archive = 0"


    while len(inQueue)>0:
        workTask = inQueue.pop()
        outQueue.append(workTask)
        subTasks = [taskTupleFromSQL(ln) for ln in dbConn.execute(sqlStr,[workTask]).fetchall()]
        inQueue+=[task.taskID for task in subTasks]
        outTuples+=subTasks

    return outTuples

def findDecendants(conn,taskID):
    inQueue = [taskID]
    #outQueue = []
    sqlStr = "SELECT TaskID FROM Tasks WHERE ParentTask = ?"
    outDict = {}
    while len(inQueue)>0:
        curTask = inQueue.pop()
        #outQueue.append(curTask)
        subTasks = [ln["TaskID"] for ln in conn.execute(sqlStr,[curTask]).fetchall()]

        inQueue+=subTasks
        outDict[curTask]=subTasks
    return outDict
        
    


def fetchTask(conn,taskID):
    curTask = conn.execute("SELECT * FROM Tasks WHERE TaskID = ?",[taskID]).fetchone()
    return taskTupleFromSQL(curTask)



def flagSubTasks(dbConn,curTaskID,complete=None,archive=None):
    if complete==None and archive==None:
        return

        
    inQueue=[curTaskID]
    sqlStr = "SELECT TaskID FROM Tasks WHERE ParentTask = ?"
    while len(inQueue)>0:
        workTask = inQueue.pop()
        if complete!=None:
            dbConn.execute("UPDATE Tasks SET Complete = ? WHERE TaskID = ?",[complete,workTask])
        if archive!=None:
            dbConn.execute("UPDATE Tasks SET Archive = ? WHERE TaskID = ?",[complete,workTask])
        subTasks = [ln["TaskID"] for ln in dbConn.execute(sqlStr,[workTask]).fetchall()]
        inQueue+=[task.taskID for task in subTasks]

    
    
        


#
##  Main Code Body
#

                               
curDir = os.getcwd()
dbFile = "todoMgr.db"

if not os.path.isfile(dbFile):
    dbFile=tkfd.askopenfilename()
    curDir = os.path.dirname(dbFile)

shutil.copyfile(dbFile,"BK"+dbFile)
    
conn = sqlite3.connect(dbFile) 
conn.row_factory = sqlite3.Row
conn.create_function("sortableDate",1,sortableDate)

win = tk.Tk()

addTaskFrame = tk.LabelFrame(win,text="Task Entry/Edit")
addTaskFrame.grid(row=0,sticky=tk.NSEW)

noteFrame = tk.LabelFrame(win,text="Notes")
noteFrame.grid(row=1,columnspan=2,sticky=tk.NSEW)

notesView = addNotesDlg(noteFrame,conn)
notesView.grid()

treeFrame = tk.LabelFrame(win,text="Task View")
treeFrame.grid(row=2,columnspan=2,sticky = tk.NSEW)

tasksView = taskViewDlg(treeFrame,conn)
tasksView.grid()

taskDlg = addTaskDlg(addTaskFrame,conn,tasksView,notesView)
tasksView.setEditDlg(taskDlg)
taskDlg.grid()
notesView.setTaskEdit(taskDlg)

reportFrame = tk.LabelFrame(win,text="Reporting")
reportFrame.grid(row=0,column=1,sticky=tk.N,columnspan=4)

reportTabs = ttk.Notebook(reportFrame)
#superFrame = tk.Frame(reportFrame)
#superFrame.grid(columnspan=1)
#pickComplete = dataCheckBox(reportFrame,"Completed",False,3,0)
#pickArchive = dataCheckBox(reportFrame,"Archived",False,3,1)
pickArchiveComplete = dataDblCheckBox(reportFrame,["Completed","Archived"],[False,False],3,0)
pickFlag = dataComboBox(reportFrame,"Flag",["Home","Work"],2,0,2)
pickFlag.setVal("Work")


reportTabs.grid(sticky=tk.NSEW,row=0,column=0,columnspan=4)

upcomingTab = upcomingDlg(reportTabs,conn,tasksView,taskDlg)
recentTab = recentDlg(reportTabs,conn,tasksView,taskDlg)
attachTab = attachmentsDlg(reportTabs,conn,tasksView,taskDlg)

refreshReportsBtn=actionBtn(reportFrame,"Refresh Tabs",lambda event:refreshTabsFn([upcomingTab,recentTab,attachTab]),3,1)
pickFlag.bindField("<<ComboboxSelected>>",pushFlag)

reportTabs.grid(sticky=tk.NSEW,row=0,column=0,columnspan=4)

#upcomingTab = upcomingDlg(reportTabs,conn,tasksView,taskDlg)
#recentTab = recentDlg(reportTabs,conn,tasksView,taskDlg)


reportTabs.add(upcomingTab,text="Upcoming Tasks")
reportTabs.add(recentTab,text = "Recent Tasks")
reportTabs.add(attachTab,text="Attachments")

statusFrame = tk.LabelFrame(win,text="Status")
statusFrame.grid(row=1,column=2,sticky=tk.NS)

statusBox = messageListbox(statusFrame,boxWidth=30,boxHeight = 15)




actionBtn(win,"Exit",lambda event:win.destroy(),3,0,2)

win.mainloop()
conn.close()

                                  
