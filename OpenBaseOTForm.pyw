import os
import time
import shutil
##import tkinter.messagebox as tkmb
##
##tkmb.showinfo(message="Ran")

os.chdir(r'C:\Users\gregory.w.anderson\Documents\Timekeeping')
baseFile = "GWA OT Form Base.pdf"
newFile = baseFile.replace("Base",time.strftime("%y%m%d"))

if not os.path.isfile(newFile):
    shutil.copy(baseFile,newFile)

os.startfile(newFile)





