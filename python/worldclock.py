import tkinter as tk
from tkinter import ttk
from time import strftime
from datetime import datetime
import pytz

class WorldClock:
    def __init__(self, root):
        self.root = root
        self.root.title('World Clock')
        self.root.geometry('400x200')
        
        self.timezone_var = tk.StringVar()
        self.timezone_var.set('UTC')
        
        self.label = ttk.Label(self.root, font=('calibri', 40, 'bold'), foreground='black')
        self.label.pack(anchor='center', pady=20)
        
        self.timezone_menu = ttk.Combobox(self.root, textvariable=self.timezone_var, values=pytz.all_timezones)
        self.timezone_menu.pack(anchor='center', pady=10)
        self.timezone_menu.bind('<<ComboboxSelected>>', self.update_time)
        
        self.update_time()
        
    def update_time(self, event=None):
        selected_timezone = self.timezone_var.get()
        tz = pytz.timezone(selected_timezone)
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z%z')
        self.label.config(text=current_time)
        self.root.after(1000, self.update_time)

if __name__ == '__main__':
    root = tk.Tk()
    app = WorldClock(root)
    root.mainloop()