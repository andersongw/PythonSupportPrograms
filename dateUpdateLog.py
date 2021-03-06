# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 20:57:48 2018

@author: Greg
"""

import sqlite3
import datetime as dt

wkFile = "GeneralDataLog.db"
try:
    curDB = sqlite3.connect(wkFile)
    print("DB Opened")
except:
    print("something went wrong")


#allDates = curDB.execute("SELECT CommuteID,Date FROM CommuteData").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE CommuteData SET TextDate = ?, DateStamp = ? WHERE CommuteID = ?",[dateStr,dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])

#allDates = curDB.execute("SELECT DayID,Date FROM DayJournal").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE DayJournal SET DateStamp = ? WHERE DayID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])

#allDates = curDB.execute("SELECT BookID,Date FROM BookTracking").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE BookTracking SET DateStamp = ? WHERE BookID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])

#allDates = curDB.execute("SELECT DayID,Date FROM SleepData").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE SleepData SET DateStamp = ? WHERE DayID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])
    
#allDates = curDB.execute("SELECT BellaCareID,Date FROM BellaCareTracking").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE BellaCareTracking SET DateStamp = ? WHERE BellaCareID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])
#
#allDates = curDB.execute("SELECT ArabellaID,Date FROM BellaData").fetchall()
#for idNum,dateStr in allDates:
#    curDB.execute("UPDATE BellaData SET DateStamp = ? WHERE ArabellaID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])

allDef = curDB.execute("SELECT DefconID,Date, HRec, SRec FROM DefconData").fetchall()
allRec = curDB.execute("SELECT RecID, Date FROM RecData").fetchall()
recDates = {d for d,i in allRec}
for idNum,dateStr,hr,sr in allDef:
    stmp = dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp()
    curDB.execute("UPDATE DefconData SET DateStamp = ? WHERE DefconID = ?",[stmp,idNum])
    if not dateStr in recDates:
        curDB.execute("INSERT INTO RecData (DateStamp,HRec,SRec) VALUES (?,?,?)",[stmp,hr,sr])
for idNum,dateStr in allRec:
    curDB.execute("UPDATE RecData SET DateStamp = ? WHERE RecID = ?",[dt.datetime.strptime(dateStr,"%m/%d/%y").timestamp(),idNum])
   



curDB.commit()
curDB.close()