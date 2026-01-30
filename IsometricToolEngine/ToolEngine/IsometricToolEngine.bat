


@echo off

:: Paths
SET pythonExe=D:\Python\python.exe
SET mainScriptPath=D:\ismometricFiles\IsometricToolEngine\ToolEngine\calling_main.py
SET logDir=D:\ismometricFiles\IsometricToolEngine\logs

:: Create log directory if it does not exist
IF NOT EXIST "%logDir%" (
    mkdir "%logDir%"
)

:: Get the current date and time in a format suitable for filenames
SET currentDateTime=%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
SET currentDateTime=%currentDateTime: =0%

:: Define log file name with the timestamp
SET logFile=%logDir%\IsometricToolEngine_log_%currentDateTime%.txt

:: Check if the main script file exists
IF EXIST "%mainScriptPath%" (
    "%pythonExe%" "%mainScriptPath%" %1 > "%logFile%" 2>&1
    IF %ERRORLEVEL% EQU 0 (
        echo Main script completed successfully. >> "%logFile%"
    ) ELSE (
        echo Main script encountered an error. >> "%logFile%"
    )
) ELSE (
    echo The file %mainScriptPath% does not exist. > "%logFile%"
)