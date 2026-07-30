Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Users\antho\OneDrive\Desktop\Project JARVIS\Project JARVIS\jarvis\jarvis"
sh.Run "cmd /c .venv\Scripts\python.exe run.py >> jarvis.log 2>&1", 0, False
WScript.Sleep 30000
sh.Run "jarvis-hud.bat", 0, False
