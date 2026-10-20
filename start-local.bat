@echo off
setlocal
cd /d "%~dp0"

if not exist .env (
  copy .env.example .env >nul
)

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is not installed or not on PATH.
  echo Install Docker Desktop and start it, then double-click this file again.
  pause
  exit /b 1
)

start "Property Intelligence API" http://localhost:8000/health
start "Property Intelligence Web" http://localhost:3000

docker compose up --build

pause
