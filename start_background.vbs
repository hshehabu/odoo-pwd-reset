Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = ScriptDir

PythonExe = ScriptDir & "\venv\Scripts\pythonw.exe"
ScriptFile = ScriptDir & "\server.py"

If Not FSO.FileExists(PythonExe) Then
    MsgBox "Python virtual environment not found at: " & PythonExe, 16, "Odoo Reset Service Error"
    WScript.Quit 1
End If

' Run completely detached and hidden (0)
WshShell.Run Chr(34) & PythonExe & Chr(34) & " " & Chr(34) & ScriptFile & Chr(34), 0, False

Set WshShell = Nothing
Set FSO = Nothing
