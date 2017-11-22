
import os
import subprocess
import threading
import win32com.client as w32

test = subprocess.call([r"C:\Program Files (x86)\Adobe\Acrobat 11.0\Acrobat\acrobat.exe","/n",r"C:\Users\gregory.w.anderson\Documents\Timekeeping\GWA Leave Slip 171026.pdf"])

##try:
##    test.wait(30)
##except subprocess.TimeoutExpired:
##    print("30 sec wait")
    
print("looks complete")

outlook = w32.Dispatch("Outlook.Application")
msg = outlook.CreateItem(0)
msg.To="timothy.scherer@navy.mil"
msg.Subject = "Leave Slip"
msg.Body = "Tim,\n\nPlease approve.\n\nThanks,\n\nGreg"
msg.Attachments.Add(r"C:\Users\gregory.w.anderson\Documents\Timekeeping\GWA Leave Slip 171026.pdf")

msg.Display()

print("The emaul wshould be showing")
