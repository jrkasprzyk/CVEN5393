@echo off

rem ============================================
rem Set Environment Variable MRM_EXAMPLE_DIR to script directory
rem Note: If run from a network (UNC) path, Windows may show a warning.
rem This is harmless and can be ignored.
rem ============================================

rem Set the variable locally first
set "MRM_EXAMPLE_DIR=%~dp0"

rem The above variable has an extra quote, which we will remove
set "MRM_EXAMPLE_DIR=%MRM_EXAMPLE_DIR:~0,-1%

rem Now set the environment variable to persist after the batch script exits
setx MRM_EXAMPLE_DIR "%MRM_EXAMPLE_DIR%"

echo.
echo Now, the value of MRM_EXAMPLE_DIR on your machine is:
reg query HKCU\Environment /V MRM_EXAMPLE_DIR

pause