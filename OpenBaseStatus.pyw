import os
import time
import shutil
import re
##import tkinter.messagebox as tkmb
##
##tkmb.showinfo(message="Ran")

os.chdir(r'C:\Users\gregory.w.anderson\Documents\Admin -- Status')

files = [ln for ln in os.scandir()]

lastFile = files[0]

for workFile in files[1:]:
    if workFile.stat().st_mtime > lastFile.stat().st_mtime:
        lastFile = workFile

baseFile = lastFile.name
dateMatch = time.strftime(r"%y\d{4}")
newDate = time.strftime("%y%m%d")
newFile = re.sub(dateMatch,newDate,baseFile)

if not os.path.isfile(newFile):
    shutil.copy(baseFile,newFile)

os.startfile(newFile)





