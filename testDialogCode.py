from guiBlocks import *
import tkinter as tkinter



class testDialog(dataDialog):
    def body(self,master):
        self.mainFrame = tk.Frame(master)
        self.mainFrame.grid()	
        testData = dataFieldLeft(self.mainFrame,"Test")
        self.result = None
        return testData.field
		

win  = tk.Tk()
tst = testDialog(win)		