Set objFSO = CreateObject("Scripting.FileSystemObject")
carpeta = objFSO.GetParentFolderName(WScript.ScriptFullName)

Set objShell = CreateObject("WScript.Shell")
script = WScript.Arguments(0)
objShell.Run """" & carpeta & "\lanzar_oculto.bat"" """ & script & """", 0, False
