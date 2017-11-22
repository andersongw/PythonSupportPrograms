#pullProject.pyw
import tkinter as tk
import datetime as dt
import sqlite3


def sortableTimeStamp(workStamp):
    sortedStamp = dt.datetime.strptime(workStamp,"%m/%d/%y %H:%M:%S")
    return sortedStamp.strftime("%y/%m/%d %H:%M:%S")

def pullFile(conn,fname):
    saveBytes = conn.execute("SELECT FileData from (SELECT FileData, filename, max(sortableTimestamp(Timestamp)) FROM FileRevisions GROUP BY Filename) WHERE filename=?",[fname]).fetchone()
    newFile = open(fname,'wb')
    byteCount = newFile.write(saveBytes[0])
    newFile.close()

conn = sqlite3.connect("VersionControl.db")
conn.create_function("sortableTimeStamp",1,sortableTimeStamp)

pullFile(conn,"autoversion.py")
pullFile(conn,"guiBlocks.py")

import autoversion as av
from guiBlocks import *

av.autoversionFile("pullProject.pyw")

class pullProjectDlg(tk.Frame):
    def __init__(self,master = None,dbConn = None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.projList = self.popProjects()

        self.actions = dblBtn(self,["List Files","Pull Files"],[self.listFn,self.pullFn],r=0)
        self.projects = dataComboBox(self,"Projects",self.projList,r=1)
        self.fileBox = messageListbox(self,r=2)

    def listFn(self,event=None):
        self.fileBox.clearData()
        res = self.dbConn.execute("SELECT Filename FROM Projects NATURAL JOIN ProjectFiles NATURAL JOIN StoredFiles WHERE Title = ?",[self.projects.getVal()]).fetchall()
        for ln in res:
            self.fileBox.addLine(ln)
        
    def pullFn(self,event=None):
        self.fileBox.clearData()
        projID = self.dbConn.execute("SELECT ProjectID FROM Projects WHERE Title=?",[self.projects.getVal()]).fetchone()[0]
        res = self.dbConn.execute("SELECT Filename FROM Projects NATURAL JOIN ProjectFiles NATURAL JOIN StoredFiles WHERE ProjectID = ?",[projID]).fetchall()
        for ln in res:
            self.fileBox.addLine("Pulling {}".format(ln))
            pullFile(self.dbConn,ln[0])

    def popProjects(self):
        res = self.dbConn.execute("SELECT Title FROM Projects ORDER BY Title").fetchall()
        return [ln[0] for ln in res]



win = tk.Tk()

pullDlg = pullProjectDlg(win,conn)
win.mainloop()
conn.close

        
