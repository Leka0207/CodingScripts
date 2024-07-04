import customtkinter as ctk
from time import strftime
from datetime import datetime
import pytz

class WorldClock:
    def __init__(self, root):
        self.root = root
        self.root.title('World Clock')
        self.root.geometry('500x300')
        
        # Set the appearance mode of the application
        ctk.set_appearance_mode("dark")  # Modes: "light", "dark", "system"
        ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
        
        self.timezone_var = ctk.StringVar()
        self.timezone_var.set('UTC')
        
        self.label = ctk.CTkLabel(self.root, text="", font=('calibri', 40, 'bold'))
        self.label.pack(anchor='center', pady=20)
        
        self.timezone_menu = ctk.CTkComboBox(self.root, variable=self.timezone_var, values=pytz.all_timezones)
        self.timezone_menu.pack(anchor='center', pady=10)
        self.timezone_menu.bind('<<ComboboxSelected>>', self.update_time)
        
        self.update_time()
        
    def update_time(self, event=None):
        selected_timezone = self.timezone_var.get()
        tz = pytz.timezone(selected_timezone)
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z%z')
        self.label.configure(text=current_time)
        self.root.after(1000, self.update_time)

if __name__ == '__main__':
    root = ctk.CTk()
    app = WorldClock(root)
    root.mainloop()