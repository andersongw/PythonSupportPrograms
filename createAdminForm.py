#import os
#import fnmatch
#import time
#import shutil
#import subprocess
#import win32com.client as w32
#import os.path
#import sys

import tkinter.messagebox as tkmb
##
tkmb.showinfo(message="Ran")
"""
class createForm():
    def __init__(self, baseFile):
        self.timeDir = r'C:\Users\gregory.w.anderson\Documents\Timekeeping'
        self.baseFile = baseFile
#os.chdir(timeDir)
    
    def createBlank(self):
        subName = self.baseFile.replace("Base",time.strftime("%y%m%d"))
        newFile = os.path.join(self.timeDir,subName+".pdf")
        fullBaseFile = os.path.join(self.timeDir,self.baseFile)
        
        if not os.path.isfile(newFile):
            shutil.copy(fullBaseFile,newFile)       

#os.startfile(newFile)
    def fillForm(self):
        acro = subprocess.call([r"C:\Program Files (x86)\Adobe\Acrobat 11.0\Acrobat\acrobat.exe","/n",newFile])

        pdfs = fnmatch.filter(os.listdir(),"*.pdf")
        self.signedForm = [ln for ln in pdfs if (ln.count(subName)>0 and ln.lower().count("signed")>0)][0]
        
    def createEmail(self):
        
        try:
            outlook = w32.Dispatch("Outlook.Application")
            msg = outlook.CreateItem(0)
            msg.To="timothy.scherer@navy.mil"
            msg.Subject = "Leave Slip"
            msg.Body = "Tim,\n\nPlease approve.\n\nThanks,\n\nGreg"
            msg.Attachments.Add(os.path.join(self.timeDir,self.signedForm))
            
        except Exception as e:
            print(e)
        msg.Display()
        
    def executeForm(self):
        try:
            self.createBlank()
            self.fillForm()
            self.createEmail()
        except Exception as e:
            print(e)
            print(f"It would have been {self.baseFile}")
"""     
# Main Program Code
print("Starting")
"""if len(sys.argv)==1:
    frm = createForm("GWA Base Leave Slip")
else:
    arg = sys.argv[-1].lower()
	print(arg)
    if arg == "leave":
        frm = createForm("GWA Base Leave Slip")
    elif arg == "telework":
        frm = createForm("GWA Telework Request Form Base")
    elif arg == "ot":
        frm = createForm("GWA OT Form Base")
    else:
        print("Unknown argument; choose between 'Leave', 'Telework', or 'OT'.  Exiting.")
        exit()
        
frm.executeForm()
"""     
time.sleep(5)


