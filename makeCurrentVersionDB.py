# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 23:22:28 2017

@author: Greg
"""

import sqlite3

conn = sqlite3.connect("CurrentVersion.db")
fileList = conn.execute("SELECT DISTINCT FileName FROM FileRevisions").fetchall()
for ln in fileList:
    lastTime = conn.execute("SELECT max(Timestamp) FROM FileRevisions WHERE Filename = ?",ln).fetchone()
    conn.execute("DELETE FROM FileRevisions WHERE Filename = ? and Timestamp < ?",ln+lastTime)

newList = conn.execute("SELECT * FROM FileRevisions").fetchall()
print(len(newList))

conn.commit()
conn.close()