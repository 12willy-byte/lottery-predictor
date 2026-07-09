Set WshShell = CreateObject("WScript.Shell")
Set sc = WshShell.CreateShortcut("C:\Users\Administrator\Desktop\彩票选号系统.lnk")
sc.TargetPath = "C:\Python311\pythonw.exe"
sc.Arguments = "C:\Users\Administrator\Documents\彩票选票机\main.py"
sc.WorkingDirectory = "C:\Users\Administrator\Documents\彩票选票机"
sc.Description = "彩票智能选号系统"
sc.Save