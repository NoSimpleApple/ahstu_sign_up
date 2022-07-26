@echo off

cd /d %~dp0

if exist ".\venv\Scripts\activate" (
    call .\venv\Scripts\activate
) else (
    echo ERROR: cannot activate the virtual environment
    goto exit
)

if exist ".\src\main.py" (
    python .\src\main.py
) else (
    echo ERROR: main.py not found
)
goto exit

:exit
pause
exit