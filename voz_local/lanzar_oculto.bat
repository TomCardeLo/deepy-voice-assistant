@echo off
cd /d "%~dp0"
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
set LOG=%~n1.log
if exist "%LOG%" (
    for %%A in ("%LOG%") do if %%~zA gtr 1048576 type nul > "%LOG%"
)
"C:\Python314\pythonw.exe" %~1 >> "%LOG%" 2>&1
