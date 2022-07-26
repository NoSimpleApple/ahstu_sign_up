@echo off

cd /d %~dp0

if exist ".\dist\main.exe" (
    .\dist\main.exe
) else (
    echo ERROR: main.exe not found
)
goto exit

:exit
echo ... & pause
exit