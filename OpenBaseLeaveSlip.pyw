import os
import fnmatch
import time
import shutil
import subprocess
import win32com.client as w32
import os.path

##import tkinter.messagebox as tkmb
##
##tkmb.showinfo(message="Ran")

timeDir = r'C:\Users\gregory.w.anderson\Documents\Timekeeping'

os.chdir(timeDir)
baseFile = "GWA Leave Slip Base"
subName = baseFile.replace("Base",time.strftime("%y%m%d"))
newFile = subName+".pdf"

if not os.path.isfile(newFile):
    shutil.copy(baseFile,newFile)

#os.startfile(newFile)

acro = subprocess.call([r"C:\Program Files (x86)\Adobe\Acrobat 11.0\Acrobat\acrobat.exe","/n",newFile])

pdfs = fnmatch.filter(os.listdir(),"*.pdf")
signedForm = [ln for ln in pdfs if (ln.count(subName)>0 and ln.lower().count("signed")>0)][0]

try:
    outlook = w32.Dispatch("Outlook.Application")
    msg = outlook.CreateItem(0)
    msg.To="timothy.scherer@navy.mil"
    msg.Subject = "Leave Slip"
    msg.Body = "Tim,\n\nPlease approve.\n\nThanks,\n\nGreg"
    msg.Attachments.Add(os.path.join(timeDir,signedForm))
    
except Exception as e:
    print(e)
msg.Display()
