@echo off
cd /d "%~dp0"
title Mewgenics Cat Editor
echo Starting Mewgenics Cat Editor...
if exist "MewgenicsCatEditor.exe" (
    start "" "MewgenicsCatEditor.exe"
    exit /b 0
)
if exist "dist\MewgenicsCatEditor.exe" (
    start "" "dist\MewgenicsCatEditor.exe"
    exit /b 0
)
