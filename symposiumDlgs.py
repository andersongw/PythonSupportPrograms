import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmb
import tkinter.filedialog as tkfd
import sqlite3
import collections
import datetime
import re
import os.path

import pyperclip

from guiBlocks import *


#
##  Global functions
#

##def testRead(fileName,dbConn):
##    inFile = open(fileName,'rb')
##    fileBytes = inFile.read()
##    tkmb.showinfo(message="Read file")
##    inFile.close()
##
##    dbConn.execute("INSERT into AbstractFiless (Paper,FileObject) VALUES (1,?)",[bytes(fileBytes)])
##    dbConn.commit()
##
##def testWrite(newFilename,dbConn):
##
##    cur = dbConn.execute("SELECT FileObject FROM AbstractFiless  WHERE Paper=1")
##    res = cur.fetchone()
##    if res != None:
##        newBytes = res["FileObject"]
##
##    outFile = open(newFilename,'xb',0)
##    outBytes=outFile.write(newBytes)
##    outFile.close()


##def popAuthors(dbConn):
##    cur = dbConn.execute("SELECT * FROM People ORDER BY Lastname")
##    res = cur.fetchall()
##
##    return [formatNameSQL(ln) for ln in res]
##

def fetchCommittee(conn):
    res = conn.execute("SELECT DISTINCT Reviewer,LastName FROM Abstracts JOIN People on Reviewer = PersonID ORDER BY LastName").fetchall()
    if len(res)>0:
        return [ln["Reviewer"] for ln in res]
    else:
         return [1]

def makeInsertSQL(tableStr,colsList):
    return str.format("INSERT INTO {} ({}) VALUES ({})",
                      tableStr,
                      ",".join(colsList),
                      "?"+",?"*(len(colsList)-1))


def formatNameSQL(sqlRow):
    return str.format("{} {} {}",sqlRow["Title"],sqlRow["Firstname"],sqlRow["Lastname"])





#
# Classes for datasets
#

personData = collections.namedtuple('personData',
            'title first middle last suffix phone phoneExt email affiliation')
personDefault = personData("Mr.","Doug","","Murphy","","2158978762","","email@host.com","NSWCPD, Code 321")

personName = collections.namedtuple('personName','title first last')

paperData = collections.namedtuple('paperData','symposium title primeAuthor coauthors correspond')
paperDefault = paperData(1,"Test Paper",1,[],1)

abstractData = collections.namedtuple('abstractData',
             'paper dateRec dateAcq reviewer dateRev notes accept dateNot')
abstractDefault = abstractData(1, "11/1/16", "11/1/16",  1,   "11/1/16", "", True, "")

AbstractFilesData = collections.namedtuple('AbstractFilesData',"paper originalName issName")
AbstractFilesDefault = AbstractFilesData('0','noName','noName')


#
##  Person Code
#


class personDlg(tk.Frame):
    def __init__(self, master = None, dbConn = None, initVals = personDefault):
        """Initalize the personDlg"""
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.fetchTitles()
        self.fetchAffiliations()
        self.fullName = dataFieldLeft(self,"Full Name")
        self.title = dataComboTop(self,"Title",self.titleList,1,0)
        self.first = dataFieldTop(self,"First",1,1)
        self.middle = dataFieldTop(self,"Middle",1,2)
        self.last = dataFieldTop(self,"Last",1,3)
        self.suffix = dataFieldTop(self,"Suffix",1,4)
        self.phone = dataFieldLeft(self,"Phone",2,0)
        self.ext = dataFieldLeft(self,"Ext.",2,1)
        self.email = dataFieldLeft(self,"Email",3,0,2)
        self.affiliation = dataComboBox(self,"Affiliation",self.affilList,4,0,2)
        self.saveBtn = actionBtn(self,"Save Data",self.saveData,5,1)
        self.clrBtn = actionBtn(self,"Clear Data",self.clearData,5)
        self.setData(initVals)

        self.dataTable = "People"
        self.dataCols = ["Title","Firstname","Middle","Lastname","Suffix","Phone","phoneExt","Email","Affiliation"]

        self.cName = re.compile(r"(?P<title>Dr\.|Mr?s?\.)?\s?(?P<first>\w+)\s?(?P<middle>\w+\.?)?\s(?P<last>\w+)")
        self.cPhone = re.compile(r"\(?(?:\d{3})\)?[-.]?(?:\d{3})[-.]?(?:\d{4})")
        self.cEmail = re.compile(r"[A-Za-z0-9._+]+@[A-Za-z0-9._]+")

        self.fullName.bindField('<FocusOut>',self.parseName)
        self.fullName.bindField('<ButtonRelease-3>',rightClickPaste)
        self.title.bindField('<ButtonRelease-3>',rightClickPaste)
        #self.title.bindField('<FocusOut>',self.checkTitle)
        self.first.bindField('<ButtonRelease-3>',rightClickPaste)
        self.middle.bindField('<ButtonRelease-3>',rightClickPaste)
        self.last.bindField('<ButtonRelease-3>',rightClickPaste)
        self.suffix.bindField('<ButtonRelease-3>',rightClickPaste)
        self.phone.bindField('<ButtonRelease-3>',rightClickPaste)
        self.ext.bindField('<ButtonRelease-3>',rightClickPaste) 
        self.email.bindField('<ButtonRelease-3>',rightClickPaste)
        self.affiliation.bindField('<ButtonRelease-3>',rightClickPaste)        

    def fetchTitles(self):
        """Get personal titles (Mr. Dr., Ms., etc.) as previously stored in the database."""
        cur = self.dbConn.execute("SELECT DISTINCT Title FROM People ORDER BY Title")
        self.titleList = [ln["Title"] for ln in cur.fetchall()]

    def fetchAffiliations(self):
        """Get the list of author affiliations as previously stored in the database."""
        cur = self.dbConn.execute("SELECT DISTINCT Affiliation FROM People ORDER BY Affiliation")
        self.affilList = [ln["Affiliation"] for ln in cur.fetchall()]

    def checkAffiliation(self,event=None):
        """Add a new affiliation to the list if it's not been seen before."""
        if self.affiliation.getVal() not in self.affilList:
            self.affilList.append(self.affiliation.getVal())
            self.affilList.sort()
            self.affiliation.updateVals(self.affilList)

    def checkTitle(self,event=None):
        """Add a new title to the list if it's not been seen before."""
        if self.title.getVal() not in self.titleList:
            self.titleList.append(self.title.getVal())
            self.titleList.sort()
            self.title.updateVals(self.titleList)
        
    def parseName(self,event=None):
        """Break a name down into its component parts, including the phone 
        number, email address, and name."""
        txt = event.widget.get()

        resPhone = self.cPhone.search(txt)
        resEmail = self.cEmail.search(txt)
        resName = self.cName.search(txt)
        
        if resPhone!=None:
            self.phone.setVal(resPhone.group())

        if resEmail!=None:
            self.email.setVal(resEmail.group())

        if resName!=None:
            if resName.group('title')==None:
                self.title.setVal("Mr.")
            else:
                self.title.setVal(resName.group('title'))
            self.first.setVal(resName.group('first'))
            if resName.group('middle')==None:
                self.middle.setVal("")
            else:
                self.middle.setVal(resName.group('middle'))
            self.last.setVal(resName.group('last'))

    def formatName(self):
        """Produce a formatted name in the style <Title> <First> <Last>"""
        return self.title.getVal() + " " + self.first.getVal() + " " + self.last.getVal()
    
    def getData(self):
        """Return a personData namedtuple corresponding to the data in the controls"""
        return personData(
            self.title.getVal(),
            self.first.getVal(),
            self.middle.getVal(),
            self.last.getVal(),
            self.suffix.getVal(),
            self.phone.getVal(),
            self.ext.getVal(),
            self.email.getVal(),
            self.affiliation.getVal())

    def setData(self,newData):
        """Set the data in the controls to correspond to a new personData namedtuple"""
        self.title.setVal(newData.title),
        self.first.setVal(newData.first),
        self.middle.setVal(newData.middle),
        self.last.setVal(newData.last),
        self.suffix.setVal(newData.suffix),
        self.phone.setVal(newData.phone),
        self.ext.setVal(newData.phoneExt),
        self.email.setVal(newData.email),
        self.affiliation.setVal(newData.affiliation)
        self.fullName.setVal(self.formatName())
    
    def clearData(self):
        """Clear the data in the controls"""
        self.title.setVal(""),
        self.first.setVal(""),
        self.middle.setVal(""),
        self.last.setVal(""),
        self.suffix.setVal(""),
        self.phone.setVal(""),
        self.ext.setVal(""),
        self.email.setVal(""),
        self.affiliation.setVal("")
        self.fullName.setVal("")

    def saveData(self):
        """Write the data in the controls to the database"""
        self.checkTitle()
        self.checkAffiliation()

        checkCur = self.dbConn.execute(
            "SELECT * FROM People WHERE Firstname = ? AND Lastname=?",
            [self.first.getVal(),self.last.getVal()])
        res = checkCur.fetchall()
        if len(res)==0: 
            sqlStr = str.format("INSERT INTO {} ({}) VALUES ({})",
                                self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
            cur = self.dbConn.execute(sqlStr,self.getData())
            self.dbConn.commit()
        else:
            for person in res:
                print(str.format("{} {} works for {}",
                                 person["Firstname"],person["Lastname"],person["affiliation"]))

        self.first.setVal(""),
        self.middle.setVal(""),
        self.last.setVal(""),
        self.suffix.setVal(""),
        self.phone.setVal(""),
        self.ext.setVal(""),
        self.email.setVal("")

#
## Paper Code
#

class paperDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None,initVals = paperDefault):
        tk.Frame.__init__(self,master)
        
        self.grid()
        symRow = 0
        tpcRow = 1
        coRow = 2
        btnRow = 9
        
        
        self.dbConn = dbConn
        self.popSym()
        self.symposiumBox = dataComboBox(self,"Symposium",self.symList,symRow,0)
        
        self.popAuthors()
        self.primeAuthor = dataComboBox(self,"Primary Author",self.authorList,tpcRow,2)
        self.coAuthor = dataComboBox(self,"Co-Author",self.authorList,tpcRow,3)
        self.authorBox = messageListbox(self,coRow,0,2)
        self.correspond = dataComboBox(self,"Corresponding Author",self.authorList,coRow,2)
        self.addCoauthorBtn = actionBtn(self,"Add Co-author",self.addCoauthorFn,coRow,3)

        self.popPapers()
        self.title = dataComboBox(self,"Paper Title",self.paperList,tpcRow,0)
        
        self.quickTime = 0
        self.quickLetters = ""

        self.saveBtn = actionBtn(self,"Save Data",self.saveData,btnRow,1)
        self.clrBtn = actionBtn(self,"Clear Data",self.clearData,btnRow)

        self.dataTable = "Papers"
        self.dataCols = ["SymposiumID","Title","PrimaryAuthor","CorrespondingAuthor"]
        self.coauthorTable = "CoAuthors"
        self.coauthorCols = ["Paper","Author"]
        
        self.addPrimeAuthorFn()
        self.primeAuthor.bindField("<FocusOut>",self.addPrimeAuthorFn)
        self.authorBox.bindField("<Double-Button-1>",self.delCoAuthor)
        self.title.bindField('<ButtonRelease-3>',rightClickPaste)
        #self.title.bindField('<FocusOut>',self.checkPaper)
        self.title.bindField('<<ComboboxSelected>>',self.checkPaper)
        self.primeAuthor.bindField("<FocusIn>",self.updateAuthors)
        self.primeAuthor.bindField("<KeyRelease>",self.quickFindAuthor)
        self.coAuthor.bindField("<KeyRelease>",self.quickFindAuthor)
        self.correspond.bindField("<KeyRelease>",self.quickFindAuthor)

    def quickFindAuthor(self,event=None):
        """Function to facilitate a quickfind by typing the first few letters
        of an author's name in the person box"""
        w=event.widget
        if event.keycode<65 or event.keycode>90:
            self.quickLetters = ""
            self.quickTime = event.time
            return
        if (event.time - self.quickTime) <500:
            self.quickLetters=self.quickLetters+event.char
        else:
            self.quickLetters = event.char
        for test in self.quickAuthors:
            if test>=self.quickLetters:
                w.current(self.quickAuthors.index(test))
                break
        self.quickTime = event.time

    def updateAuthors(self,event=None):
        """Associate the authors with the current paper"""
        self.popAuthors()
        self.primeAuthor.updateVals(self.authorList)
        self.coAuthor.updateVals(self.authorList)
        self.correspond.updateVals(self.authorList)

    def checkPaper(self,event=None):
        """Confirm that the paper is not already in the current set of papers"""
        if self.title.getVal() not in self.paperList:
            self.paperList.append(self.title.getVal())
            self.paperList.sort()
            self.title.updateVals(self.paperList)
            return

        ##  This section of code should probably go into setData. . .
        self.authorBox.clearData()

        cur = self.dbConn.execute("SELECT People.* FROM Papers JOIN People on Papers.PrimaryAuthor = People.PersonID WHERE Papers.Title = ?",[self.title.getVal()])
        res = cur.fetchone()
        if res ==None:
            self.primeAuthor.setVal("No Author Found; Check database")
            return
        self.primeAuthor.setVal(formatNameSQL(res))
        self.addPrimeAuthorFn()

        cur = self.dbConn.execute("SELECT People.* FROM Papers JOIN People on Papers.CorrespondingAuthor = People.PersonID WHERE Papers.Title = ?",[self.title.getVal()])
        res = cur.fetchone()
        if res == None:
            self.correspond.setVal(self.primeAuthor.getVal())
        else:
            self.correspond.setVal(formatNameSQL(res))

        cur = self.dbConn.execute("SELECT People.* FROM Papers JOIN People JOIN CoAuthors ON Papers.paperID = CoAuthors.PaperID AND People.PersonID = CoAuthors.Author WHERE Papers.Title = ?",[self.title.getVal()])
        res = cur.fetchall()
        if res == None:
            return
        for ln in res:
            curAuthor = str.format(formatNameSQL(ln))
            self.authorBox.addLine(curAuthor)
            self.coAuthor.setVal(curAuthor)

    def setData(self,newData):
        """Ostensibly to set the data in the controls to match the paper in a
        new paperData namedtuple (Never implemented)"""
        pass
    
    def getData(self):
        """Return a paperData namedtuple for the data in the controls"""
        symp = self.symposiumBox.getData()
        boxData = self.authorBox.getData()
        authorID = self.authorLookup[boxData[0]]
        correspondID = self.authorLookup[self.authorList[self.correspond.getIndex()]]
        authorList=[self.authorLookup[auth] for auth in boxData[1:]]
        return paperData(symp,self.title.getVal(),authorID,authorList,correspondID)
            

    def saveData(self):
        """Write the data in the current controls to the database"""
        newPaper = self.getData()

        cur = self.dbConn.execute("SELECT PaperID FROM Papers WHERE Title = ?",[self.title.getVal()])
        res = cur.fetchone()
        if not res==None:
            self.dbConn.execute("DELETE FROM CoAuthors WHERE Paper = ?",[res["PaperID"]])
            self.dbConn.execute("DELETE FROM Papers WHERE Title = ?",[self.title.getVal()])

        sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.dataTable,",".join(self.dataCols),"?"+",?"*(len(self.dataCols)-1))
        newCur = self.dbConn.execute(sqlStr,[newPaper.symposium, newPaper.title,newPaper.primeAuthor,newPaper.correspond])

        newRow = newCur.lastrowid
        if len(newPaper.coauthors)>0:
            for coauth in newPaper.coauthors:
                sqlStr = str.format("INSERT into {} ({}) VALUES ({})",self.coauthorTable,",".join(self.coauthorCols),"?"+",?"*(len(self.coauthorCols)-1))
                newCur = self.dbConn.execute(sqlStr,[newRow,coauth])

        self.dbConn.commit()
        self.clearData()
        

    def clearData(self):
        """Reset the data in the controls"""
        self.title.setVal("")
        self.authorBox.clearData()
        self.addPrimeAuthorFn()

    def popSym(self):
        """Populate the list of symposia currently archived in the database"""
        res=self.dbConn.execute("SELECT * FROM Symposia ORDER BY StartDate").fetchall()
        self.symList = [ln["Name"] for ln in res]
        self.symID_Title = {ln["SymposiumID"]:ln["Name"] for ln in res}
        for ln in res:
            self.symID_Title[ln["Name"]] = ln["SymposiumID"]
            
            

    def popAuthors(self):
        """Load people from database to provide candidates for authors and coauthors"""
#        cur = self.dbConn.execute("SELECT * FROM People WHERE PersonID>0 ORDER BY Lastname")
#        res = cur.fetchall()
        res = self.dbConn.execute("SELECT * FROM People WHERE PersonID>0 ORDER BY Lastname").fetchall()

        self.authorList = [formatNameSQL(ln) for ln in res]
        self.quickAuthors = [ln["Lastname"].lower() for ln in res]
        vals = [ln["PersonID"] for ln in res]
        
        self.authorLookup = dict(zip(self.authorList,vals))

    def popPapers(self):
        """Load the papers from the database"""
        curSymposium = self.symposiumBox.getVal()
        print(curSymposium)
        res = self.dbConn.execute("SELECT * FROM Papers WHERE PaperID>0 ORDER BY Title").fetchall()
        self.paperList = [ln["Title"] for ln in res]

    def addPrimeAuthorFn(self,event=None):
        curAuthor = self.primeAuthor.getVal()
        self.authorBox.dropLine(0)
        self.authorBox.insertLine(0,curAuthor)
        
    def addCoauthorFn(self):
        curAuthor = self.coAuthor.getVal()
        self.authorBox.addLine(curAuthor)

    def delCoAuthor(self,event):
        curIndex = self.authorBox.getSelectionIndex()
        if curIndex == (0,):
            tkmb.showerror(None,"Cannot delete primary author")
        else:
            self.authorBox.dropLine(curIndex)



#
##  Abstract Code
#

class abstractDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None,initVals = abstractDefault):
        tk.Frame.__init__(self,master)
        self.grid()
        self.altVectors=["Webform","Email"]
        self.dbConn = dbConn
        self.popPapers()
        self.popFilenames()
        self.fileBox = dataComboBox(self,"Abstract File",self.AbstractFiless,0,0)
        self.titleBox = dataComboBox(self,"Paper Title",self.paperList,0,1)
        self.infoBox = messageListbox(self,1,0,2)
        self.newName = dataFieldLeft(self,"Revised Filename",0,3)
        self.dateRec = dataFieldLeft(self,"Date Received",1,3)
        self.saveBtn = actionBtn(self,"Save Data",self.saveData,2,3)
        self.paperCount = statusLabelBox(self,"Papers",len(self.paperList),4,3)
        self.fileCount = statusLabelBox(self,"Files",len(self.AbstractFiless),4,4)
        self.abstractText = dataTextBox(self,"Abstract Text",5,0,6,2)

        self.titleBox.bindField("<<ComboboxSelected>>",self.lookupPaper)
        self.fileBox.bindField("<<ComboboxSelected>>",self.lookupPaper)
        self.abstractText.bindField('<ButtonRelease-3>',rightClickPasteTextBox)

        self.dataTable = "Abstracts"
        self.dataCols = ["Paper","DateReceived"]
        self.fileTable = "AbstractFiles"
        self.fileCols = ["Paper","FileObject","OriginalFilename","ISSFilename"]

        self.lookupPaper()

    def popPapers(self):
        # generate the list of papers for the paper title combobox
        res = self.dbConn.execute("SELECT * FROM Papers WHERE PaperID>0 ORDER BY Title").fetchall()
        allPapers = [ln["Title"] for ln in res]

        res = self.dbConn.execute("SELECT Title FROM Papers NATURAL JOIN AbstractFiles").fetchall()
        procPapers = {ln["Title"] for ln in res}

        self.paperList = [paper for paper in allPapers if paper not in procPapers]

    def popFilenames(self):
        # Generate the list of filenames for the filename combobox
        self.abstractsDir = os.getcwd()
        if not os.path.isdir(self.abstractsDir):
            self.abstractsDir=tkfd.askdirectory()
        
        fileList = self.altVectors+os.listdir(self.abstractsDir)
        res = self.dbConn.execute("SELECT OriginalFilename,ISSFilename FROM AbstractFiles").fetchall()

        allFiles = {file for file in fileList}
        oldNames = {ln["OriginalFilename"] for ln in res}
        newNames = {ln["ISSFilename"] for ln in res}
         
        self.AbstractFiless = [file for file in allFiles if file not in (oldNames and newNames)]
        self.AbstractFiless.sort()

    def updateComboBoxes(self,event=None):
        self.popPapers()
        self.popFilenames()
        self.titleBox.updateVals(self.paperList)
        self.fileBox.updateVals(self.AbstractFiless)

    def setNewName(self):
        # Generate the new filename based on the paper number (PaperID) and author name
        self.newName.field.delete(0,tk.END)
        paperNum = self.getPaperNumSQL()
        lastName = self.getPaperAuthorSQL().last
        oldName,ext = os.path.splitext(self.fileBox.getVal())
        newName = str.format("{:02d} - {}{}",paperNum,lastName,ext)
        self.newName.setVal(newName)
        
    def lookupPaper(self,event=None):
        # Populates the infobox with the original filename, paper title, and primary Author
        self.setNewName()
        self.infoBox.clearData()
        self.infoBox.addLine(self.fileBox.getVal())
        self.infoBox.addLine(self.titleBox.getVal())
        self.infoBox.addLine(self.getPaperAuthorSQL())

    def getPaperNumSQL(self):
        # Lookup the PaperID from the Title
        if self.titleBox.getVal()=="":
            return 0
        res = self.dbConn.execute("SELECT PaperID from Papers WHERE Title = ?",[self.titleBox.getVal()]).fetchone()
        if res == None:
            tkmb.showerror(None,"No paper found; check database")
            return 0
        return res["PaperID"]

    def getPaperAuthorSQL(self):
        # Look up the paper author based on the title
        # Joins the People table to the Papers table on PersonID
        if self.titleBox.getVal() == "":
            return personName("Mr.","Doug","Murphy")
        res = self.dbConn.execute("SELECT People.* from Papers JOIN People ON Papers.PrimaryAuthor = People.PersonID WHERE Papers.Title=?",[self.titleBox.getVal()]).fetchone()
        if res == None:
            tkmb.showerror(None,"No such person; check database")
            return personName("Mr.","Doug","Murphy")
        return personName(res["Title"],res["Firstname"],res["Lastname"])

    def saveData(self):
        # Add record to the Abstract table
        # But not all fields will be completed now.
        # Only Paper and Date Received

        

        paperNum = self.getPaperNumSQL()
        dateRec = self.dateRec.getVal()
        insertStr = makeInsertSQL(self.dataTable,self.dataCols)
        
        self.dbConn.execute(insertStr,[paperNum,dateRec])

        # Also populate AbstractFiless table
        # All columns: Paper, FileObject, OriginalFilename, and ISSFilename

        origName = self.fileBox.getVal()
        newName = self.newName.getVal()

        openName = os.path.join(self.abstractsDir,origName)

        if origName in self.altVectors:
            txtFile = open(openName,"w")
            txtFile.write(str.format("Author Name: {}\n",self.getPaperAuthorSQL()))
            txtFile.write(str.format("Paper Title: {}\n",self.titleBox.getVal()))
            txtFile.write(str.format("Abstract Text\n{}",self.abstractText.getVal()))
            txtFile.close()
            newName = newName+".txt"

        inFile = open(openName,'rb')
        fileBytes = inFile.read()
        inFile.close()

        insertStr = makeInsertSQL(self.fileTable,self.fileCols)
        self.dbConn.execute(insertStr,[paperNum,fileBytes,origName,newName])
        self.dbConn.commit()

        # Finally, rename the file, and update the combobox lists
        # to remove the paper just processed

        os.rename(openName,os.path.join(self.abstractsDir,newName))

        if origName not in self.altVectors:
            self.AbstractFiless.remove(origName)
        self.paperList.remove(self.titleBox.getVal())

        self.titleBox.updateVals(self.paperList)
        self.titleBox.setVal(self.paperList[0])
        self.fileBox.updateVals(self.AbstractFiless)
        self.fileBox.setVal(self.AbstractFiless[0])

        self.paperCount.setVal(len(self.paperList))
        self.fileCount.setVal(len(self.AbstractFiless))
        self.lookupPaper()

    def clearData(self):
        pass    

    def setData(self,newData):
        pass

    def getData(self):
        pass

#
##  Assemble Committee Dialog
#

class buildCommitteeDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.popPeople()
        self.allPeople = dataComboBox(self,"People",self.allPeopleList,0,0,2)
        self.committeeDisp = messageListbox(self,1,0,3)
        self.addPerson = actionBtn(self,"Add to committee",self.addToCommittee,0,2)

        self.committeeDisp.bindField("<Double-Button-1>",self.delCommittee)
        self.allPeople.setQuickFind(self.lastNames)

        for person in [self.lookupAuthor[id] for id in fetchCommittee(self.dbConn)]:
            self.committeeDisp.addLine(person)

        self.allPeople.updateVals(self.allPeopleList)
        self.allPeople.setVal(self.allPeopleList[0])
            


    def popPeople(self):
        res = self.dbConn.execute("SELECT * FROM People WHERE PersonID>0 ORDER BY Lastname").fetchall()
        self.allPeopleList = [formatNameSQL(ln) for ln in res]
        self.lastNames = [ln["Lastname"].lower() for ln in res]
        self.lookupAuthorID = {formatNameSQL(ln):ln["PersonID"] for ln in res}
        self.lookupAuthor = {ln["PersonID"]:formatNameSQL(ln) for ln in res}


    def addToCommittee(self):
        person = self.allPeople.getVal()
        self.committeeDisp.addLine(person)
        
##        self.allPeopleList.remove(person)
        self.allPeople.updateVals(self.allPeopleList)
        self.allPeople.setVal(self.allPeopleList[0])
        
    def delCommittee(self,event=None):
        curIndex = self.committeeDisp.getSelectionIndex()
        self.committeeDisp.dropLine(curIndex)      
        
        

    def getData(self):
        return list({self.lookupAuthorID[name] for name in self.committeeDisp.getData()})


#
## Assign Abstracts Dialog
#


class assignCommitteeDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None):
        tk.Frame.__init__(self,master)
        self.dbConn = dbConn
        self.popPeople()
        self.popPapers()
        self.id_committeeName={id:self.id_name[id] for id in fetchCommittee(self.dbConn)}
        #self.committeeList=[(id,self.id_name[id] for id in fetchCommittee(self.dbConn)]

        leftPane = tk.Frame(self)
        leftPane.grid(row=0,column=0,sticky=tk.N)
        self.committee = dataComboBox(leftPane,"Committee Members",list(self.id_committeeName.values()),0,0,2)
        self.paperCount = statusLabelBox(leftPane,"Papers remaining",len(self.unassignedPapers),1,0)
        self.paperBox = dataComboBox(leftPane,"Unassigned Papers",self.unassignedPapers,2,0,2)
        self.assignBtn = actionBtn(leftPane,"Assign paper to reviewer",self.assignPaper,3,0)
        self.assignRest = actionBtn(leftPane,"Assign remaining papers randomly",self.randomAssign,4,0)
        self.saveBtn = actionBtn(leftPane,"Save Assignments",self.saveData,5,0)
        self.status = statusLabelBox(leftPane,"Status: ","Idle",6,0)

        colCfg = [
            treeColTpl("title",300,"Title")]
            
        rightPane=tk.Frame(self)
        rightPane.grid(row=0,column=1)
        self.assignView = treeView(rightPane,"Abstract Assignments",colCfg)

        self.initializeAssignView()
        
        
    def popPapers(self):
        res=self.dbConn.execute("SELECT Title, PrimaryAuthor, PaperID, ISSFilename, Reviewer FROM Papers NATURAL JOIN AbstractFiles NATURAL JOIN Abstracts WHERE PaperID>0 ORDER BY Title").fetchall()
        self.paperList = []
        self.unassignedPapers = []
        self.title_paperID = {}
        self.paperID_title = {}
        self.title_issFile = {}
        self.title_authorID = {}
        self.reviewerID_paperIDs = {}
        
        for ln in res:
            title = ln["Title"]
            paperID = ln["PaperID"]
            reviewer = ln["Reviewer"]
            
            self.paperList.append(title)
            self.paperID_title[paperID] = title
            self.title_paperID[title] = paperID
            self.title_issFile[title] = ln["ISSFilename"]
            self.title_authorID[title] = ln["PrimaryAuthor"]
            
            if reviewer == None:
                self.unassignedPapers.append(title)
                continue
                
            if reviewer in self.reviewerID_paperIDs:
                self.reviewerID_paperIDs[reviewer].append(paperID)
            else:
                self.reviewerID_paperIDs[reviewer] = [paperID]     
       


    def popPeople(self):
        res = self.dbConn.execute("SELECT * FROM People WHERE PersonID>0 ORDER BY Lastname").fetchall()
        self.allPeopleList = [formatNameSQL(ln) for ln in res]
        self.lastNames = [ln["Lastname"].lower() for ln in res]
        self.name_id = {formatNameSQL(ln):ln["PersonID"] for ln in res}
        self.id_name = {ln["PersonID"]:formatNameSQL(ln) for ln in res}
        

##    def genCommitteeList(self,idList):
##        #self.committeeList = [self.id_name[id] for id in idList]
##        if len(#self.committeeList)>0:
##            self.committee.updateVals(#self.committeeList)
##
##        self.iidCommittee = self.assignView.getParents()
##        for person in #self.committeeList:
##            if person not in self.iidCommittee:
##                self.iidCommittee[person]=self.assignView.addLine("",person,["",""])

    def initializeAssignView(self):
    #Here we read the papers as they're assigned to each committee member
    # Take the list of reviewers, sort and reverse the list.
    # Pop through, and select each reviewer's papers, then assign each to that reviewer
    # Don't forget to remove each paper from self.paperList as it's assigned
        try:
            self.iid_committeeName = {}
            for person in self.id_committeeName.values():
                iidReviewer = self.assignView.addLine("",person,[])
                self.iid_committeeName[person] = iidReviewer
                workID = self.name_id[person]
                for paperID in self.reviewerID_paperIDs[workID]:
                    paper = self.paperID_title[paperID]
                    self.assignView.addLine(iidReviewer,self.title_issFile.get(paper,paper),[paper])
        except KeyError:
            print(workID)

            
    def findAssignedPapers(self,reviewerID):
        res=self.dbConn.execute("SELECT Paper FROM Abstracts WHERE Reviewer = ?",[reviewerID]).fetchall()
        

    def assignPaper(self):
        reviewer = self.committee.getVal()
        iidReviewer = self.iid_committeeName[reviewer]
        paper = self.paperBox.getVal()
        self.assignView.addLine(iidReviewer,self.title_issFile.get(paper,paper),[paper])

        self.paperList.remove(paper)
        self.paperBox.updateVals(self.paperList)
        self.paperCount.setVal(len(self.paperList))
        if len(self.paperList)>0:
            self.paperBox.setVal(self.paperList[0])
        else:
            self.paperBox.setVal("HI!")


    def randomAssign(self):
        committee = self.assignView.getParents()
##        committeePool = [name for name in committee.keys()]
        papersGone = False
        while not papersGone:
            committeePool = [name for name in self.assignView.getParents().keys()]
            while len(committeePool)>0:
                reviewer = random.choice(committeePool)
                paper = random.choice(self.paperList)
                committeePool.remove(reviewer)
                self.paperList.remove(paper)
                self.assignView.addLine(committee[reviewer],self.title_issFile.get(paper,paper),[paper])
                papersGone=(len(self.paperList)<1)
                if papersGone:
                    break

        self.paperBox.updateVals(self.paperList)
        self.paperCount.setVal(len(self.paperList))
        if len(self.paperList)>0:
            self.paperBox.setVal(self.paperList[0])
        else:
            self.paperBox.setVal("HI!")
                 

    def saveData(self):
        self.status.setVal("Saving")
        committee = self.assignView.getParents()
        names = [name for name in committee.keys()]
        
        baseExcelFile = os.path.join(curDir,"ISS 2017 Review Template.xlsx")
        if not os.path.isfile(baseExcelFile):
            tkmb.showerror(None,"Do something about this!")
            

        for name in names:
            os.chdir(curDir)
            nameIndex = self.allPeopleList.index(name)
            lastname = self.lastNames[nameIndex]
            excelName = lastname + ".xlsx"

            if not os.path.isdir(lastname):
                os.mkdir(lastname)
            os.chdir(lastname)
            if not os.path.isfile(excelName):
                shutil.copy(baseExcelFile,excelName)

            wb = xl.load_workbook(excelName)
            ws = wb.active

            ws.cell(row=1,column=2).value = name
            workRow = 4
        

            assignments = self.assignView.getChildren(committee[name])
            papers = [paper for paper in assignments.keys()]
            for paper in papers:
                assignTitle = self.assignView.getValues(assignments[paper])[0]
                primAuth = self.id_name[self.title_authorID[assignTitle]]
                paperID = self.title_paperID[assignTitle]
                self.dbConn.execute("UPDATE Abstracts SET Reviewer = ? WHERE Paper = ?",[self.name_id[name],paperID])
                ws.cell(row = workRow,column = 2).value = paper
                ws.cell(row = workRow,column = 3).value = assignTitle
                ws.cell(row = workRow,column = 4).value = primAuth
                workRow+=1
                self.saveAbstractFiles(paperID)

            wb.save(excelName)



        self.dbConn.commit()
        self.status.setVal("Idle")

    def saveAbstractFiles(self,paperID):
        res=self.dbConn.execute("SELECT * FROM AbstractFiles WHERE Paper = ?",[paperID]).fetchone()
        if res == None:
            return

        newBytes = res["FileObject"]
        newName = res["ISSFileName"]      
        outFile = open(newName,'xb',0)
        outBytes = outFile.write(newBytes)
        outFile.close()
                     
                
class aggregateReviewResultsDlg(tk.Frame):
    def __init__(self,master=None,dbConn = None):
        tk.Frame.__init__(self,master)
        self.dbConn = dbConn

        self.lftPane = tk.Frame(self)
        self.lftPane.grid(row=0,column=0)
        self.aggregateFilename = dataFieldLeft(self.lftPane,"Aggregate Filename")
        self.startCollection = actionBtn(self.lftPane,"Combine Review Files",self.combineFiles,1,1)

        self.collectFilelistBtn = actionBtn(self.lftPane,"Collect File List",self.getFileList,1,0)
        self.fileCount = statusLabelBox(self.lftPane,"Review Files: ","0",2,0)
        self.reviewFiles = messageListbox(self.lftPane,3,0)

        self.rtPane = tk.Frame(self)
        self.rtPane.grid(row=0,column=2)
        self.importReviewsBtn = actionBtn(self.rtPane,"Import Reviews",self.importReviews,1,0)
        self.saveReviewsBtn = actionBtn(self.rtPane,"Save Reviews",self.saveData,2,0)
        self.exportForNotify = actionBtn(self.rtPane,"Export for Notification",self.exportNotify,3,0)
        
        self.reviewColCfg=[
            treeColTpl("Rec",150,"Recommendation"),
            treeColTpl("Dec",120,"Decision")]
        self.viewReviews = treeView(self.rtPane,"Abstract Reviews",self.reviewColCfg,0,1,1,4)

        self.aggregateFilename.setVal("All Reviews ISS 2017.xlsx")


    def importReviews(self):
        collectFile = self.aggregateFilename.getVal()
        if not os.path.isfile(collectFile):
            collectFile = tkfd.askopenfilename()

        self.aggFile = xl.load_workbook(collectFile)
        ws = self.aggFile.active
        decide=("Reject","Accept")

        parentDict={}

        for wkRow in range(2,ws.max_row):
            fname = ws.cell(row=wkRow, column=3).value
            reviewer = ws.cell(row=wkRow, column=2).value
            rec = ws.cell(row=wkRow, column=6).value
            decision = decide[ws.cell(row=wkRow, column=7).value]

            if reviewer not in parentDict:
                parentDict[reviewer] = self.viewReviews.addLine("",reviewer,[])

            self.viewReviews.addLine(parentDict[reviewer],fname,[rec,decision])
            

    def saveData(self):
        dataTable = "Abstracts"
        dataCols = ["ReviewerRec","Accepted"]
        keyCol = "AbstractID"

        # Use ISSFilename and AbstractFiles table to look up AbstractID
        reviewers = self.viewReviews.getParents()
        for rev in reviewers.keys():
            papers=self.viewReviews.getChildren(reviewers[rev])
            for fname in papers.keys():
                abstractID = self.dbConn.execute(
                    "SELECT AbstractID FROM Abstracts NATURAL JOIN AbstractFiles WHERE ISSFilename = ?",[fname]).fetchone()["AbstractID"]
                vals=self.viewReviews.getValues(papers[fname])
                updateData = (vals[0],vals[1].find("Accept")>-1)
                updateSql(self.dbConn,dataTable,dataCols,updateData,keyCol,abstractID)
                
        
        

    def exportNotify(self):
        collectFile = self.aggregateFilename.getVal()
        if not os.path.isfile(collectFile):
            collectFile = tkfd.askopenfilename()
            
        wb = xl.load_workbook(collectFile)
        wsBlocks = wb["EmailComponents"]
        wsEmails = wb["Emails"]

        subj = wsBlocks["A1"].value
        body1 = wsBlocks["A2"].value
        body2 = wsBlocks["A3"].value
        reject = wsBlocks["A4"].value
        accept = wsBlocks["A5"].value     
        sig = wsBlocks["A6"].value


        (idCol,primeCol,corrCol,emailCol,subjCol,bodyCol,attachCol) = tuple(range(1,8))
        workRow = 1

        abstracts = self.dbConn.execute(
                    "SELECT PaperID, People.Title AS Title,FirstName,LastName,Papers.Title AS paperTitle, Accepted FROM People JOIN Papers ON PersonID=PrimaryAuthor NATURAL JOIN Abstracts ORDER BY PaperID").fetchall()
        for abstract in abstracts:
            workRow +=1
            paperID = abstract["PaperID"]
            corrAuthSQL = self.dbConn.execute("SELECT People.Title,FirstName,LastName,Email FROM People JOIN Papers ON PersonID=CorrespondingAuthor WHERE PaperID = ?",[paperID]).fetchone()

            primAuth = formatNameSQL(abstract) 
            corrAuth = formatNameSQL(corrAuthSQL)

            bodyTxt = str.format("Dear {} {},\n",abstract["Title"],abstract["LastName"])
            bodyTxt += body1 + abstract["paperTitle"] + body2 + "\n\n"

            if abstract["Accepted"]:
                bodyTxt += accept + "\n"
            else:
                bodyTxt += reject + "\n"

            bodyTxt += sig

            wsEmails.cell(row = workRow,column = idCol).value = paperID
            wsEmails.cell(row = workRow,column = primeCol).value = primAuth
            wsEmails.cell(row = workRow,column = corrCol).value = corrAuth
            wsEmails.cell(row = workRow,column = emailCol).value = corrAuthSQL["Email"]
            wsEmails.cell(row = workRow,column = subjCol).value = subj
            wsEmails.cell(row = workRow,column = bodyCol).value = bodyTxt

            
        wb.save(collectFile)

            

            


    def getFileList(self):
        self.fileList = tkfd.askopenfilenames()
        self.fileCount.setVal(len(self.fileList))
        nameList = [os.path.basename(f).lower() for f in self.fileList]
        nameList.sort()
        for name in nameList:
            self.reviewFiles.addLine(name)

#
##
#

    def combineFiles(self):

        if len(self.reviewFiles.getData())==0:
            self.getFileList()

        collectFile = self.aggregateFilename.getVal()
        if not os.path.isfile(collectFile):
            collectFile = tkfd.askopenfilename()

        self.aggFile = xl.load_workbook(collectFile)
        ws = self.aggFile.active

        workRow = 2
        for wkFile in self.fileList:
            newReviewer,newReview = self.readExcelReview(wkFile)
            lastName = newReviewer.split()[-1]

            for wkRow in newReview:
                ws.cell(row = workRow,column = 2).value = newReviewer
                workCol = 3
                ctxt=""
                for wkCell in wkRow:
                    if workCol == 7:
                        workCol=9
                    ws.cell(row=workRow,column=workCol).value = wkCell.value
##                    print(wkCell.comment)
##                    if wkCell.comment != None:
##                        oldComment = wkCell.comment
##                        ctxt = oldComment.text
##                        cauth = oldComment.author
##                        newComment = xlc.Comment(ctxt,cauth)
##                        ws.cell(row=workRow,column=workCol).comment = newComment
                    workCol+=1
                ws.cell(row=workRow,column=workCol).value = ctxt

                workRow+=1

        self.aggFile.save(collectFile)

#
##
#
            

    def readExcelReview(self,filename):
        wb = xl.load_workbook(filename)
        ws = wb.active

        reviewer = ws["B1"].value
        reviewRows = tuple(ws.rows)[3:]
        reviews = []
        
        for r in reviewRows:
            reviews.append(r[1:])
                           
        return (reviewer,reviews)
        

#
## Assign Keywords
#

class kwDlg(tk.Frame):
    def __init__(self,master=None, dbConn = None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.dbConn = dbConn
        self.popPapers()
        self.popKeywords()

        self.paperTitle = dataComboBox(self,"Paper Title",self.paperList,1,0,3)
        self.dropPaperBtn = actionBtn(self,"Remove Paper",self.dropPaperFn,2,2)
        self.pickKeywords = dataComboBox(self,"Keywords",self.keywordList,2,0)
        self.assignKeyword = actionBtn(self,"Assign Keyword",self.addKeyword,3,0)
        self.btnSaveClear = dblBtn(self,["Save Data","Clear Data"],[self.saveFn,self.clearFn],4,0)
        statusLabelBox(self,None,"Keywords",2,1)
        self.keywordBox = messageListbox(self,3,1)
        self.paperCount = statusLabelBox(self,"Papers remaining",len(self.paperList))

        self.paperTitle.bindField('<<ComboboxSelected>>',self.fetchKeywords)
        self.pickKeywords.bindField('<ButtonRelease-3>',rightClickPaste)
        self.pickKeywords.bindField('<<ComboboxSelected>>',self.checkKeyword)
        self.pickKeywords.bindField('<FocusOut>',self.checkKeyword)
        self.keywordBox.bindField('<Double-Button-1>',self.delLine)
        

    def popPapers(self):
        res=self.dbConn.execute("SELECT PaperID,Title FROM Papers NATURAL JOIN Abstracts WHERE Accepted = 1 ORDER BY Title").fetchall()
        self.paperDict={paperID:title for paperID,title in res}
        self.paperDict.update({title:paperID for paperID,title in res})
        self.paperList=[ln["Title"] for ln in res]

    def popKeywords(self):
        res=self.dbConn.execute("SELECT * FROM Keywords ORDER BY Keyword").fetchall()
        self.keywordDict={kwID:kw for kwID,kw in res}
        self.keywordDict.update({kw:kwID for kwID,kw  in res})
        self.keywordList=[ln["Keyword"] for ln in res]

    def fetchKeywords(self,event=None):
        self.clearFn()
        workID = self.paperDict[self.paperTitle.getVal()]
        res = fetchSql(self.dbConn,"PaperKeywords NATURAL JOIN Keywords",["PaperID"],[workID])
        if len(res)==0:
            return
        for ln in res:
            self.keywordBox.addLine(ln["Keyword"])

    def checkKeyword(self,event=None):
        if not self.pickKeywords.getVal() in self.keywordList:
            kw=self.pickKeywords.getVal()
            #insertSql(self.dbConn,"Keywords",["Keyword"],[self.pickKeywords.getVal()])
            try:
                self.dbConn.execute("INSERT OR REPLACE INTO Keywords (Keyword) VALUES (?)",[kw])
                self.dbConn.commit()
            except sqlite3.IntegrityError:
                print("Could not add ",kw)
            self.popKeywords()
            self.pickKeywords.updateVals(self.keywordList)
    
    def delLine(self,event=None):
        curIndex = self.keywordBox.getSelectionIndex()
        self.keywordBox.dropLine(curIndex)
                            
    def addKeyword(self,event=None):
        self.checkKeyword()
        newKeyword = self.pickKeywords.getVal()
        if newKeyword not in self.keywordBox.getData():
            self.keywordBox.addLine(self.pickKeywords.getVal())

    def saveFn(self,event=None):
        kwList = self.keywordBox.getData()
        if len(kwList)==0:
            return
        workPaper=self.paperTitle.getVal()
        print(workPaper)
        paperID = self.paperDict[workPaper]
        delSql(self.dbConn,"PaperKeywords",["PaperID"],[paperID])
        for ln in self.keywordBox.getData():
            kwID = self.keywordDict[ln]
            insertSql(self.dbConn,"PaperKeywords",["PaperID","KeywordID"],[paperID,kwID])
        self.dropPaperFn()

        checkRes = fetchSql(self.dbConn,"PaperKeywords NATURAL JOIN Keywords",["PaperID"],[paperID])
        for ln in checkRes:
            print(ln[:])
            
    def dropPaperFn(self,event=None):
        workPaper=self.paperTitle.getVal()
        try:
            self.paperList.remove(workPaper)
        except ValueError:
            pass
        if len(self.paperList)>0:
            self.paperTitle.setVal(self.paperList[0])
            self.paperTitle.updateVals(self.paperList)
            self.fetchKeywords()
        else:
            self.paperTitle.setVal("")
        self.paperCount.setVal(len(self.paperList))
         

    def clearFn(self,event=None):
        self.keywordBox.clearData()


        
        
        
            


    

        
   
        
