from PIL import Image, ImageTk 
import tkinter as tk 

root = tk.Tk()
img = Image.open("jellyfish.jpg")
tkimage = ImageTk.PhotoImage(img)
tk.Label(root, image=tkimage).pack()
root.mainloop()
