@echo off

cd /d %~dp0

if exist ".\main\main.exe" (
    .\main\main.exe
) else (
    echo ERROR: main.exe not found
)
goto exit

:exit
echo ... & pause
exit