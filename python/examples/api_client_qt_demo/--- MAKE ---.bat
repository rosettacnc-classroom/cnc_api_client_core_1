:: ===
::  MAKE_ALL %1
::      %1  -pause   | -nopause                 Pause or not for a keyboard click
::
:START
echo off

:: debug settings
set DEBUG=0
@if "%DEBUG%"=="1" (
    @echo on
    SET "ECHO_OFF="
    SET "ERR_REDIRECT="
) else (
    @echo off
    SET "ECHO_OFF=echo off"
    SET "ERR_REDIRECT=2>nul"
)

:: === define console settings ===
mode con:cols=120 lines=39
cls

echo.
echo  ======================================
echo   Select the MAKE Operation to Perform
echo  ======================================
echo  X - CLEAR SERVICE FILES
echo.
echo  Z - EXIT
echo.

choice /N /C:XZ /M "CHOOSE ONE OF UPPON OPTIONS:" 
if %ERRORLEVEL% == 1  call :CLEAR_SERVICE_FILES
if %ERRORLEVEL% == 2  exit
goto END

:: ===
::  Clear Service Files
::
:CLEAR_SERVICE_FILES
    @echo off
    :: === generic roules ===
    @for /F "tokens=*" %%G in ('dir /B /AD /S *__pycache__*') do rmdir /S /Q "%%G" %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *__history*') do rmdir /S /Q "%%G" %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *__recovery*') do rmdir /S /Q "%%G" %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *Win32*') do del "%%G\*.DCU" /S /Q %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *Win64*') do del "%%G\*.DCU" /S /Q %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *objects*') do del "%%G\*.DCU" /S /Q %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *objects*') do del "%%G\*.XML" /S /Q %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AD /S *Release*') do del "%%G\*.DCU" /S /Q %ERR_REDIRECT%
    @for /F "tokens=*" %%G in ('dir /B /AH /S "Thumbs.db"') do del /AH /S /Q "%%G" %ERR_REDIRECT%
    del *.bin %ERR_REDIRECT%
    del *.drc %ERR_REDIRECT%
    del *.elf %ERR_REDIRECT%
    del *.gex %ERR_REDIRECT%
    del *.identcache %ERR_REDIRECT%
    del *.lib %ERR_REDIRECT%
    del *.map %ERR_REDIRECT%
    del *.oca %ERR_REDIRECT%
    del *.rsm %ERR_REDIRECT%
    del *.tds %ERR_REDIRECT%
    goto:eof

:: ===
::  End Script Point
::
:END
    pause
    goto START