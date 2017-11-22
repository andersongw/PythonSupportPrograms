# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 13:55:27 2017

@author: Greg
"""

import sqlite3
import tkinter as tk
import tkinter.filedialog as tkfd
import win32com.client as w32
import os
import os.path
import re
import datetime as dt
import collections
import openpyxl as xl



from guiBlocks import *
"""
Some useful links for the Outlook COM model:
    https://msdn.microsoft.com/en-us/VBA/Outlook-VBA/articles/namespace-addstore-method-outlook

for openpyxl:
    https://openpyxl.readthedocs.io/en/default/
    (although the Automate the Boring Stuff book is much more helpful)
"""
rePerson = re.compile(r"(?P<person>.*) (CIV|CTR) .*, (?P<code>[0-9]*)")
reName = re.compile(r"(?P<last>.*), (?P<first>\S*) ?(?P<mi>\S)?")
reEmail = re.compile(r".*RECIPIENTS/CN=(?P<email>\D*\d*)")

messageData = collections.namedtuple("messageData","date name email code attach, body")
nullMsg = messageData(None,None,None,None,[],None)
excelRow = collections.namedtuple("excelRow","date senderName senderAddress subject body numAttach recipList recipEmails attachList")
nullExcel = (None,None,None,None,None,0,[],[],[])

def parseName(rawName):
    """Break down the SenderName into a proper first/last"""
    # First check ot see if the person is a Navy/Govt employee with a decorated name
    tst = rePerson.match(rawName)
    code = None
    try:
        name = tst.group("person")
        code= tst.group("code")
    except AttributeError:
        name = rawName.title()  # If not, then title case the name to get rid of all caps
        
    #  Next, parse the name into first, last, mi
    tst = reName.match(name)
    try:
       first = tst.group("first")
       mi = tst.group("mi")
       last = tst.group("last")
       name  = ' '.join([first,mi,last])
    except AttributeError:
        pass
    except TypeError:  #Throws if mi is None; just join the first and last
        name  = ' '.join([first,last]) 
        
    return name,code

def parseEmail(rawAddress):
    tst = reEmail.match(rawAddress)
    try:
        email = tst.group("email").lower()+"@navy.mil"
    except AttributeError:
        email = rawAddress.lower()
        
    return email   

class excelLink():
    def __init__(self, excelFile):
        try:
            self.wkBook = xl.load_workbook(excelFile)
        except FileNotFoundError:
            newPath = locateFile(excelFile)
            if newPath != None:
                self.wkBook = xl.load_workbook(newPath)
            else:
                self.wkBook=None
        
    def checkFile(self):
        return self.wkBook != None
        
    def readExcelExport(self):
        wkSheet = self.wkBook.get_active_sheet()
        rows = wkSheet.rows
        rowList = [self.parseExcelRow(ln) for ln in rows]
        print(len(rowList))
        return rowList
        
    def parseExcelRow(self,wkRow):
        curRow = [ln.value for ln in wkRow]
        curLine = excelRow(*curRow)
        try:
            timestamp = curLine.date.timestamp()
        except ValueError:
            return nullExcel
        except AttributeError:
            return nullExcel
        
        person,code = parseName(curLine.senderName)
        email = parseEmail(curLine.senderAddress)
        try:
            attach = curLine.attachList.split(';')[:-1]
        except:
            attach=[]
            
        fixBody = curLine.body.replace('_x000D_',"")
        fixBody = re.sub('\n+','\n',fixBody)
        
        return messageData(timestamp,person,email,code,attach,fixBody)
        
        #"date name email code attach"
        
    

class outlookLink():
    def __init__(self):
        self.outlook = w32.Dispatch("Outlook.Application")
        self.ns = self.outlook.GetNamespace("MAPI")
        self.rePerson = re.compile(r"(?P<person>.*) (CIV|CTR) .*, (?P<code>[0-9]*)")
        self.reName = re.compile(r"(?P<last>.*), (?P<first>\S*) ?(?P<mi>\S)?")
        self.reEmail = re.compile(r".*RECIPIENTS/CN=(?P<email>\D*\d*)")
        self.folders = []
        self.messages = []
        self.curFolderSet = None
        self.curFolder = None


    def attachPST(self,pstFile):
        """Add a PST file to the Outlook object, and return a list of folders
        within the PST file."""
        print(pstFile)
        try:
            self.ns.AddStore(pstFile)
            self.curFolderSet = self.ns.Folders
            self.folders = [ln.Name for ln in self.curFolderSet]
            return self.folders
        except:
            print("Whelp -- bollocks on that.  Do find out more.")
            return []
        
    def fetchSubfolders(self,folderName):
        """Return a list of subfolders within a folder.  May need a way to go
        back up, but for now, just restart by searching for the pst again
        (maybe)."""
        try:
            self.curFolder = self.curFolderSet(folderName)
            self.curFolderSet = self.curFolder.Folders
            self.folders = [ln.Name for ln in self.curFolderSet]
            return self.folders
        except:
            print("No, really.  fuck this!")
            return []

    def fetchMessages(self,folderName):
        """Return a list of MailObjects given a folder name"""
        try:
            self.curFolder = self.curFolderSet(folderName)
            self.messages = self.curFolder.Items
            return self.messages
        except:
            print("Denied!")
            return []
            
    def getCurFolder(self):
        """Return the current working folder"""
        return self.curFolder.Name
    
    def getMsgCount(self):
        """Return the number of messages in the current working folder"""
        return len(self.messages)
    
    def getMsgInfo(self,msg):
        try:
            name = msg.SenderName
            addy = msg.SenderEmailAddress
            date = msg.ReceivedTime.timestamp()
            attachments = msg.Attachments
            body = msg.Body
        except:
            print("Nope")
            return nullMsg
        
        name,code = self.parseName(name)
        email = self.parseEmail(addy)
        attachList = [attach.DisplayName for attach in attachments]
        
        return messageData(date,name,email,code,attachList,body)
        
    def parseName(self,sender):
        """Break down the SenderName into a proper first/last"""
        # First check ot see if the person is a Navy/Govt employee with a decorated name
        tst = self.rePerson.match(sender)
        code = None
        try:
            name = tst.group("person")
            code= tst.group("code")
        except AttributeError:
            name = sender.title()  # If not, then title case the name to get rid of all caps
            
        #  Next, parse the name into first, last, mi
        tst = self.reName.match(name)
        try:
           first = tst.group("first")
           mi = tst.group("mi")
           last = tst.group("last")
           name  = ' '.join([first,mi,last])
        except AttributeError:
            pass
        except TypeError:  #Throws if mi is None; just join the first and last
            name  = ' '.join([first,last]) 
            
        return name,code
    
    def parseEmail(self,addy):
        tst = self.reEmail.match(addy)
        try:
            email = tst.group("email").lower()+"@navy.mil"
        except AttributeError:
            email = addy.lower()
            
        return email
            
     

class paperAbstractDlg(tk.Frame):
    def __init__(self,master,dbConn):
        tk.Frame.__init__(self,master)
        
        excelBase = "email export.xlsx"
        
        self.grid()
        self.dbConn = dbConn
        
        self.docDir = os.path.join(os.environ["USERPROFILE"],"documents")
        
        leftFrame = formFrame(self,"Paper Data",0,0)
        leftControls = leftFrame.frame
               
        symRow, titleRow, origNameRow, newNameRow, primRow, corRow, coRow, addCoRow, saveClrRow, bodyRow = range(10)

        self.symBox = dataComboBox(leftControls, "Symposium",[],symRow)
        self.titleBox = dataFieldLeft(leftControls,"Paper Title",titleRow)
        self.origFilenameBox = dataComboBox(leftControls,"Original Filename",["test1","test2"],origNameRow)
        self.dateRec = dataFieldLeft(leftControls,"Date Received",origNameRow,1)
        self.newFilenameBox = dataFieldLeft(leftControls,"New Filename",newNameRow)
        self.primaryAuthorBox = dataComboBox(leftControls,"Primary Author",["Test1","Test2"],primRow)
        self.corrAuthorBox = dataComboBox(leftControls,"Corresponding Author",["Test1","Test2"],corRow)
        self.coAuthorBox = dataComboBox(leftControls,"Co-Author",["Test1","Test2"],coRow)
        self.addCoauthorBtn = actionBtn(leftControls,"Add Coauthor",self.addCoauthFn,addCoRow)
        
        self.authLabel = statusLabelBox(leftControls,"Authors","",newNameRow,1)
        self.authorsBox = messageListbox(leftControls,primRow,1)
        self.saveClearBtn = dblBtn(leftControls,["Save Data","Clear Data"],[self.saveData,self.clearData],saveClrRow)
        
        self.bodyBox = dataTextBox(leftControls,"Message Body",bodyRow,0,2,boxH=5)
        
        rightFrame = formFrame(self,"Email Data",0,1)
        rightControls = rightFrame.frame
        
        pstRow, fldrRow, xlRow,countRow, treeRow = range(5)

        self.pstBox = dataFieldLeft(rightControls, "Outlook PST File",pstRow)
        self.pstBtn = actionBtn(rightControls, "Find PST File",self.pstFindFn,pstRow,1)
        self.folderBox = dataComboBox(rightControls, "Outlook Folder",["test","quiz"], fldrRow)
        self.folderBtns = dblBtn(rightControls,["Read SubFolders","Read Messages"],[self.readSubfldrsFn,self.readFolderFn],fldrRow,1)
        self.xlFileBox = dataFieldLeft(rightControls,"Excel Export File",xlRow,0)
        self.xlFileBtn =actionBtn(rightControls,"Find Excel File",self.findXlFn,xlRow,1)
        self.totalDocs = statusLabelBox(rightControls,"Total Submitted","",countRow,0)
        self.numProcess = statusLabelBox(rightControls,"Total Processed","",countRow,1)
        self.numRemain = statusLabelBox(rightControls,"Number Remaining","",countRow,2)
        
        self.emailTreeCfg = [
                treeColTpl("abstractFile",100,"Abstract File"),
                treeColTpl("subDate",75,"Date Recv"),
                treeColTpl("sender",125,"Sender"),
                treeColTpl("mailBody",125,"Message Body"),
                treeColTpl("title",175,"Paper Title"),
                treeColTpl("primAuth",125,"Primary Author")]
        self.emailView = treeView(rightControls,"Process emails",self.emailTreeCfg,treeRow,0,3)
        self.emailView.setIconWidth(5)
        self.emailView.bindField("<<TreeviewSelect>>",self.selectEmailFn)
        
        self.xlFileBox.setVal(excelBase)
        self.outlook = outlookLink()
        self.popSym()
        self.popAuthors()
        
    def popSym(self):
        res=self.dbConn.execute("SELECT SymposiumID, Name FROM Symposia ORDER BY EndDate DESC").fetchall()
        self.sym_id={ln["Name"]:ln["SymposiumID"] for ln in res}
        self.symBox.updateVals(list(self.sym_id.keys()))
        
    def popAuthors(self):
        res = self.dbConn.execute("SELECT * FROM People WHERE PersonID>0 ORDER BY LastName").fetchall()
        self.authList = [f"{ln['Title']} {ln['Firstname']} {ln['Lastname']}" for ln in res]
        ids = [ln["PersonID"] for ln in res]
        self.name_id = dict(zip(self.authList,ids))
        self.primaryAuthorBox.updateVals(self.authList)
        self.coAuthorBox.updateVals(self.authList)
        self.corrAuthorBox.updateVals(self.authList)
        
    def addCoauthFn(self,event=None):
        pass
    
    def saveData(self,event=None):
        pass
    
    def clearData(self,event = None):
        pass
    
    def findXlFn(self,event=None):
        self.excel = excelLink(self.xlFileBox.getVal())
        if not self.excel.checkFile():
            newFile = tkfd.askopenfilename()
            self.xlFileBox.setVal(newFile)
            self.excel = excelLink(newFile)
        self.iid_attachlist={}
        msgList = self.excel.readExcelExport()
        for msg in msgList:
            try:
                printDate = dt.date.fromtimestamp(msg.date).isoformat()
                addLine = [msg.attach,
                           printDate,
                           msg.name,msg.body]
            except:
                print("shit.")
                continue
            newIID = self.emailView.addLine("","",addLine)
            self.iid_attachlist[newIID]=msg.attach
            
        
    
    def pstFindFn(self,event = None):
        """Pulls up the File Selector dialog so the user can find the PST file
        of interest, then attaches it to the Outlook object and pulls the list
        of folders therein.  Finally, populates the Folders dropdown."""
        
        #docDir = os.path.join(os.environ["USERPROFILE"],"documents")
        #pstFile = tkfd.askopenfilename(initialdir=docDir,title="Select PST File")
        pstFile = tkfd.askopenfilename(title="Select PST File")
        self.pstBox.setVal(pstFile)
        
        folderList = self.outlook.attachPST(pstFile)
        self.folderBox.updateVals(folderList)
        

    def readSubfldrsFn(self,event=None):
        newFolderList = self.outlook.fetchSubfolders(self.folderBox.getVal())
        self.folderBox.updateVals(newFolderList)
        
        
    def readFolderFn(self,event=None):
        self.iid_attachlist={}
        msgList = self.outlook.fetchMessages(self.folderBox.getVal())
        for msg in msgList:
            msgData = self.outlook.getMsgInfo(msg)
            if msgData != nullMsg:
                printDate = dt.date.fromtimestamp(msgData.date).isoformat()
                addLine = [msgData.attach,
                           printDate,
                           msgData.name,
                           msgData.body]
            else:
                addLine=["Secure message"]
            newIID = self.emailView.addLine("","",addLine)
            self.iid_attachlist[newIID]=msgData.attach

            

    def selectEmailFn(self,event=None):
        selIID = self.emailView.getSelection()[0]
        emailData = self.emailView.getValues(selIID)
        attachList = self.iid_attachlist[selIID]
        self.origFilenameBox.updateVals(attachList)
        self.dateRec.setVal(emailData[1])
        self.bodyBox.setVal(emailData[3])
        
    
    