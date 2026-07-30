@echo off
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --app=http://127.0.0.1:8123 ^
  --start-fullscreen ^
  --user-data-dir="%LOCALAPPDATA%\JarvisHUD"
