# Last Edited 11/24/17
import sqlite3
import os.path
import datetime as dt2
import re


from guiBlocks import *

vcdb = "VersionControl.db"
cvdb = "CurrentVersion.db"

def dispRunDateTime():
    """Displays the surrent date and time in the Python shell"""
    print(curDateTime())
    
def stampFile(filename):
    """Adds or edits a comment line at the beginning of filename with the 
    current date to indicate the last time the file was edited."
    """
        
    with open(filename,'r') as curFile:
        fileLines = curFile.readlines()
        
    curLine = 0
    stampLine = -1
    while fileLines[curLine].find("import")<0:
        if re.match("# Last Edited",fileLines[curLine])!=None:
            stampLine = curLine 
        curLine+=1
    
    stampStr = dt2.datetime.now().strftime("# Last Edited" + " %m/%d/%y\n")
    if stampLine == -1:
        stampLine=0
        fileLines = [stampStr]+fileLines
    else:
        fileLines[stampLine] = stampStr
        
        
    with open(filename,'w') as curFile:
        curFile.write("".join(fileLines))
        
        
    
class editLog():
    """This is a class used to help keep track of edits to the projects.  It 
    connects to a VersionControl database and a CurrentVersion database.  
    VersionControl keeps a record of all changes to the code, for as long as 
    it's been tracked.
    CurrentVersion only keeps the most recent version.
    Member Functions:
        __init__: Really just connects to the databases
        autoversionFile checks and logs a single file
        compareHash checks the database-stored version of the file with t he current version, based on the MD5 hash of each
        storeFileFn saves the file to both databases if a change is detected
        autoversionList iterates through a list of files, calling 
            autoversionFile on each.
        """
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
        
    def compareHash(self,storeFile):
        """Determines whether or not storeFile needs to be stored in the database.
        (Returns True if so; False if not)"""
        
        # See if the file already exists in the database.  If not, return True
        foundFile = self.vcConn.execute("SELECT count(RevisionID) FROM FileRevisions WHERE Filename = ?",[storeFile]).fetchone()[0]
        if foundFile == 0:
            print(f"{storeFile} not stored yet")
            return True
        
        curHash = getFileHash(storeFile)
        # If the file exists, compare the new hash against the stored hash; 
        #   if they match, return False (file doesn't need to be stored")
        foundHash = self.vcConn.execute("SELECT count(RevisionID) FROM FileRevisions WHERE FileHash = ?",[curHash]).fetchone()[0]
        if foundHash > 0:
            print(f"{storeFile} has not been changed")
            return False
        
        # If they're different, return true
        print(f"{storeFile} has been changed")
        return True

    def storeFileFn(self,fileName,commit):
        # Add the "last edited stamp and rehash file(existing hash is no longer valid)
        stampFile(fileName)
        curHash = getFileHash(fileName)
        
        stamp = dt2.datetime.now().timestamp()
        with open(fileName,'rb') as wkFile:
            wkBytes = wkFile.read()
            
        self.vcConn.execute("INSERT INTO FileRevisions (Filename,FileData,Timestamp,FileHash) VALUES (?,?,?,?)",(fileName,wkBytes,stamp,curHash))
        self.cvConn.execute("UPDATE FileRevisions SET FileData = ?,Timestamp = ?,FileHash = ? WHERE FileName = ?",(wkBytes,stamp,curHash,fileName))
        
        if commit:
            self.vcConn.commit()
            self.cvConn.commit()

    def autoversionFile(self,storeFile,commit = True):
        newFile = self.compareHash(storeFile)
        
        if newFile:
            print("Storing data")
            self.storeFileFn(storeFile,commit)
            
    
    def autoversionList(self,fileList):
        for ln in fileList:
            self.autoversionFile(ln,False)
        
        self.vcConn.commit()
        self.cvConn.commit()
        
        self.vcConn.close()
        self.cvConn.close()
        
        
##From here down is the old version of the code.  Commenting it out until
##it looks like something needs it again.
#
#def autoversionFile(storeFile,vcConn=None, cvConn = None):
#    if vcConn == None:
#        if os.path.isfile(vcdb):
#            print("Version control found")
#            vcConn = sqlite3.connect(vcdb)
#           # vcConn.create_function("sortableTimestamp",1,sortableTimestamp)
#        else:
#            return      
#    if cvConn == None:
#        if os.path.isfile(cvdb):
#            print("Current Version found")
#            cvConn = sqlite3.connect(cvdb)
#        else:
#            return
#
#    #stamp = dt2.strftime(dt2.now(),"%m/%d/%y %H:%M:%S")
#    stamp = dt2.datetime.now().timestamp()
#
#    #newBytes = compareFileFn(vcConn,storeFile)
#    newBytes = hashCompare(vcConn,storeFile)
#    if newBytes != None:
#        print("Storing data")
#        storeFileFn(vcConn,(storeFile,newBytes,stamp,getBlobHash(newBytes)))
#
#def hashCompare(vcConn,fileName):
#    # Confirm that the file is already in the database; if not, return the bytes for the file
#    # If the file has already been stored, calculate the hash, and look for it in the database
#    # If the hash is present -- the file hasn't been changed; return None
#    # If the hash isn't in the DB, return the bytes for the file
#    foundFile = vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE FileName = ?",[fileName]).fetchone()
#    if foundFile == None:
#        with open(fileName,'rb') as wkFile:
#            print("{} not stored yet".format(fileName))
#            return wkFile.read()
#    newHash = getFileHash(fileName)
#    foundHash = vcConn.execute("SELECT RevisionID FROM FileRevisions WHERE FileHash = ?",[newHash]).fetchone()
#    if foundHash != None:
#        print("{} has not been changed".format(fileName))
#        return None
#    print("{} has been changed; storing".format(fileName))
#    with open(fileName,'rb') as wkFile:
#        return wkFile.read()
#        
#def storeFileFn(vcConn,dataTuple):
#    vcConn.execute("INSERT INTO FileRevisions (Filename,FileData,Timestamp,FileHash) VALUES (?,?,?,?)",dataTuple)
#    vcConn.commit()
#
#def autoversionList(fileList):
#    if os.path.isfile(vcdb):
#        print("Version control found")
#        vcConn = sqlite3.connect(vcdb)
#        vcConn.create_function("sortableTimestamp",1,sortableTimestamp)
#        for fn in fileList:
#            autoversionFile(fn,vcConn)
#        vcConn.close()
#
#def pullProject(projName):
#    if os.path.isfile(vcdb):
#        print("Version control found")
#        vcConn = sqlite3.connect(vcdb)
#
#    res=vcConn.execute("SELECT Filename FROM ProjectFiles NATURAL JOIN Projects NATURAL JOIN StoredFiles WHERE Title = ?",[projName]).fetchall()
#
#    if res == None:
#        print ("Project title: ",projName,"does not exist")
#        return
#
#    for ln in res:
#        curFile=ln[0]
#        if not os.path.exists(curFile):
#            pullFile(vcConn,curFile)
#            continue
#
#        testBytes=compareFileFn(vcConn,curFile)
#        if testBytes == None:
#            continue
#
#        os.rename(curFile,"1-"+curFile)
#        pullProject(vcConn,curFile)
#
#def pullFile(vcConn,fname):
#    saveBytes = vcConn.execute("SELECT FileData from (SELECT FileData, filename, max(sortableTimestamp(Timestamp)) FROM FileRevisions GROUP BY Filename) WHERE filename=?",[fname]).fetchone()
#    newFile = open(fname,'wb')
#    byteCount = newFile.write(saveBytes)
#    newFile.close()
    
            
    
    
    




    
    
