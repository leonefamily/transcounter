@echo off

CD /D "%~dp0"

IF EXIST ".venv\Scripts\activate.bat" (
  SET "VENV=.venv"
) ELSE IF EXIST "venv\Scripts\activate.bat" (
  SET "VENV=venv"
) ELSE (
  ECHO No virtual environment found. Run install.bat first.
  EXIT /B 1
)

CALL "%VENV%\Scripts\activate.bat"
extrapolator %*

IF %ERRORLEVEL% NEQ 0 (
ECHO:
ECHO Got error
ECHO:
pause
)
