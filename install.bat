@echo off

SETLOCAL EnableDelayedExpansion

REM resolve WD
SET "SCRIPT_DIR=%~dp0"
CD /D "%SCRIPT_DIR%"

REM Create a virtual environment named .venv or venv in the script's directory if neither exists
IF EXIST ".venv" (
    SET "VENV_DIR=.venv"
) ELSE IF EXIST "venv" (
    SET "VENV_DIR=venv"
) ELSE (
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to create virtual environment
        EXIT /B 1
    )
    SET "VENV_DIR=.venv"
)

CALL "%VENV_DIR%\Scripts\activate.bat"

REM install/update the current project
pip install --disable-pip-version-check --upgrade setuptools wheel
pip install --disable-pip-version-check .

IF %ERRORLEVEL% NEQ 0 (
    ECHO:
    ECHO Install failed, consult the errors above
    ECHO:
    EXIT /B 1
) ELSE (
ECHO:
ECHO Install complete, you may close the window
ECHO:
)

pause

ENDLOCAL
