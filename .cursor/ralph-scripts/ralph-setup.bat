@echo off
REM Ralph Wiggum for Cursor - Windows Batch Setup Script
REM Simple launcher for the PowerShell script

powershell.exe -ExecutionPolicy Bypass -File "%~dp0..\..\..\scripts\ralph-setup.ps1" %*
