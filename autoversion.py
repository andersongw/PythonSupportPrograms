import sqlite3
import os.path
import datetime as dt2


from guiBlocks import *

vcdb = "VersionControl.db"
cvdb = "CurrentVersion.db"

def dispRunDateTime():
    print(curDateTime())
    
class editLog():
    def __init__(self):
        if os.path.isfile(vcdb):
            print("Version Control Found")
            self.vcConn = sqlite3.connect(vcdb)
        else:
            print("Something's wrong; cannot find Version Control database")
            return
        
        if os.path.isfile(cvdb):
            print("Current Version Found")
            self.cvConn = sqlite3.connect(cvdb)
        else:
            print("Something's wrong; cannot find Current Version database")
            return
        
    def autoversionFile(self,storeFile,commit = True):
        newFile = self.compareHash(storeFile)
        
        if newFile:
            print("Storing data")
            self.storeFileFn(storeFile,commit)
            
    def storeFileFn(self,fileName,commit):
        stamp = dt2.datetime.now().timestamp()
        with open(fileName,'rb') as wkFile:
            wkBytes = wkFile.read()
            
        self.vcConn.execute("INSERT INTO FileRevisions (Filename,FileData,Timestamp,FileHash) VALUES (?,?,?,?)",(fileName,wkBytes,stamp,self.newHash))
        self.cvConn.execute("UPDATE FileRevisions SET FileData = ?,Timestamp = ?,FileHash = ? WHERE FileName = ?",(wkBytes,stamp,self.newHash,fileName))
        
        if commit:
            self.vcConn.commit()
            self.cvConn.commit()
    
    def autoversionList(self,fileList):
        for ln in fileList:
            self.autoversionFile(ln,False)
        
        self.vcConn.commit()
        self.cvConn.commit()
        
        self.vcConn.close()
        self.cvConn.close()
        
        
    def compareHash(self,storeFile):
    # Confirm that the file is already in the database; if not, return the bytes for the file
    # If the file has already been stored, calculate the hash, and look for it in the database
    # If the hash is present -- the file hasn't been changed; return None
    # If the hash isn't in the DB, return the bytes for the file
        self.newHash = getFileHash(storeFile)
        
        foundFile = self.vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE Filename = ?",[storeFile]).fetchone()
        if foundFile == None:
            print(f"{storeFile} not stored yet")
            return True

        foundHash = self.vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE Filehash = ?",[self.newHash]).fetchone()
        if foundHash == None:
            print(f"{storeFile} has not been changed")
            return False
        
        print(f"{storeFile} has been changed; storing")
        return True

def autoversionFile(storeFile,vcConn=None, cvConn = None):
    if vcConn == None:
        if os.path.isfile(vcdb):
            print("Version control found")
            vcConn = sqlite3.connect(vcdb)
           # vcConn.create_function("sortableTimestamp",1,sortableTimestamp)
        else:
            return      
    if cvConn == None:
        if os.path.isfile(cvdb):
            print("Current Version found")
            cvConn = sqlite3.connect(cvdb)
        else:
            return

    #stamp = dt2.strftime(dt2.now(),"%m/%d/%y %H:%M:%S")
    stamp = dt2.datetime.now().timestamp()

    #newBytes = compareFileFn(vcConn,storeFile)
    newBytes = hashCompare(vcConn,storeFile)
    if newBytes != None:
        print("Storing data")
        storeFileFn(vcConn,(storeFile,newBytes,stamp,getBlobHash(newBytes)))

def hashCompare(vcConn,fileName):
    # Confirm that the file is already in the database; if not, return the bytes for the file
    # If the file has already been stored, calculate the hash, and look for it in the database
    # If the hash is present -- the file hasn't been changed; return None
    # If the hash isn't in the DB, return the bytes for the file
    foundFile = vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE FileName = ?",[fileName]).fetchone()
    if foundFile == None:
        with open(fileName,'rb') as wkFile:
            print("{} not stored yet".format(fileName))
            return wkFile.read()
    newHash = getFileHash(fileName)
    foundHash = vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE FileHash = ?",[newHash]).fetchone()
    if foundHash != None:
        print("{} has not been changed".format(fileName))
        return None
    print("{} has been changed; storing".format(fileName))
    with open(fileName,'rb') as wkFile:
        return wkFile.read()
        
def storeFileFn(vcConn,dataTuple):
    vcConn.execute("INSERT INTO FileRevisions (Filename,FileData,Timestamp,FileHash) VALUES (?,?,?,?)",dataTuple)
    vcConn.commit()

def autoversionList(fileList):
    if os.path.isfile(vcdb):
        print("Version control found")
        vcConn = sqlite3.connect(vcdb)
        vcConn.create_function("sortableTimestamp",1,sortableTimestamp)
        for fn in fileList:
            autoversionFile(fn,vcConn)
        vcConn.close()

def pullProject(projName):
    if os.path.isfile(vcdb):
        print("Version control found")
        vcConn = sqlite3.connect(vcdb)

    res=vcConn.execute("SELECT Filename FROM ProjectFiles NATURAL JOIN Projects NATURAL JOIN StoredFiles WHERE Title = ?",[projName]).fetchall()

    if res == None:
        print ("Project title: ",projName,"does not exist")
        return

    for ln in res:
        curFile=ln[0]
        if not os.path.exists(curFile):
            pullFile(vcConn,curFile)
            continue

        testBytes=compareFileFn(vcConn,curFile)
        if testBytes == None:
            continue

        os.rename(curFile,"1-"+curFile)
        pullProject(vcConn,curFile)

def pullFile(vcConn,fname):
    saveBytes = vcConn.execute("SELECT FileData from (SELECT FileData, filename, max(sortableTimestamp(Timestamp)) FROM FileRevisions GROUP BY Filename) WHERE filename=?",[fname]).fetchone()
    newFile = open(fname,'wb')
    byteCount = newFile.write(saveBytes)
    newFile.close()
    
            
    
    
    




    
    
