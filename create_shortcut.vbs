
Set WshShell = CreateObject("WScript.Shell")
Set Shortcut = WshShell.CreateShortcut("C:\Users\Administrator\Desktop\彩票选号系统.lnk")
Shortcut.TargetPath = "C:\Python311\pythonw.exe"
Shortcut.Arguments = "C:\Users\Administrator\Desktop\启动彩票系统.pyw"
Shortcut.WorkingDirectory = "C:\Users\Administrator\Documents\彩票选票机"
Shortcut.Description = "彩票智能选号系统 v2.0"
Shortcut.Save
