Option Explicit

Dim objShell, objFSO, scriptDir, mainScript, pyPath

Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

scriptDir  = objFSO.GetParentFolderName(WScript.ScriptFullName)
mainScript = scriptDir & "\wifi_professional.py"

If Not objFSO.FileExists(mainScript) Then
    MsgBox "wifi_professional.py not found.", vbCritical, "WiFi Tool"
    WScript.Quit 1
End If

pyPath = ""
On Error Resume Next
pyPath = objShell.RegRead("HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath\") & "pythonw.exe"
On Error GoTo 0
If Not objFSO.FileExists(pyPath) Then
    On Error Resume Next
    pyPath = objShell.RegRead("HKCU\SOFTWARE\Python\PythonCore\3.11\InstallPath\") & "pythonw.exe"
    On Error GoTo 0
End If
If Not objFSO.FileExists(pyPath) Then
    pyPath = "pythonw.exe"
End If

Dim adminCheck
adminCheck = objShell.Run("cmd /c net session >nul 2>&1", 0, True)
If adminCheck <> 0 Then
    Dim oSA
    Set oSA = CreateObject("Shell.Application")
    oSA.ShellExecute "wscript.exe", _
        chr(34) & WScript.ScriptFullName & chr(34), _
        scriptDir, "runas", 0
    WScript.Quit
End If

Dim cmd
cmd = chr(34) & pyPath & chr(34) & " " & chr(34) & mainScript & chr(34)
objShell.Run cmd, 0, False
