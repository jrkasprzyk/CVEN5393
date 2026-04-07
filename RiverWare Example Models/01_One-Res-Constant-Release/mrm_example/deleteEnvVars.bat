@echo off

rem ============================================
rem Delete the Environment Variable: MRM_EXAMPLE_DIR
rem Note: If run from a network (UNC) path, Windows may show a warning.
rem This is harmless and can be ignored.
rem ============================================

echo.
echo Removing the env variable MRM_EXAMPLE_DIR...

REG delete HKCU\Environment /F /V MRM_EXAMPLE_DIR >nul 2>&1

REG query HKCU\Environment /V MRM_EXAMPLE_DIR >nul 2>&1

if %errorlevel%==0 (
    echo Something went wrong: variable still exists.
) else (
    echo Done. MRM_EXAMPLE_DIR has been removed.
)

echo.
echo Note: You may need to reopen terminals or dialogs to see the change.
echo.
pause