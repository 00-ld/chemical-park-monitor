@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "STARTUP_CHECK_ONLY="
if /I "%~1"=="--check" set "STARTUP_CHECK_ONLY=1"

set "MYSQL_PORT=3306"
set "ALGORITHM_PORT=8000"
set "YOLO_PORT=8001"
set "BACKEND_PORT=8081"
set "FRONTEND_PORT=5173"

set "MYSQL_DATABASE=chemical"
set "SPRING_PROFILES_ACTIVE=local"
set "ANALYSIS_SERVICE_URL=http://127.0.0.1:%YOLO_PORT%/api/analysis/person"
set "CORS_ALLOWED_ORIGINS=http://localhost:%FRONTEND_PORT%,http://127.0.0.1:%FRONTEND_PORT%"

if not defined DB_PASSWORD if defined SPRING_DATASOURCE_PASSWORD set "DB_PASSWORD=%SPRING_DATASOURCE_PASSWORD%"
if not defined DB_PASSWORD if defined MYSQL_ROOT_PASSWORD set "DB_PASSWORD=%MYSQL_ROOT_PASSWORD%"

echo.
echo ==========================================
echo  Chemical Park Monitor Startup
echo ==========================================
echo Project: %ROOT%
echo.

call :command_exists "node"
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install Node.js/npm first.
  pause
  exit /b 1
)

call :command_exists "npm"
if errorlevel 1 (
  echo [ERROR] npm was not found. Install Node.js/npm first.
  pause
  exit /b 1
)

call :command_exists "python"
if errorlevel 1 (
  echo [ERROR] Python was not found. Install Python and add it to PATH.
  pause
  exit /b 1
)

call :command_exists "mvn.cmd"
if errorlevel 1 (
  echo [ERROR] Maven mvn.cmd was not found. Install Maven and add it to PATH.
  pause
  exit /b 1
)

if defined STARTUP_CHECK_ONLY (
  echo [OK] startup.bat dependency and entry check passed.
  exit /b 0
)

if not defined DB_PASSWORD (
  echo [INFO] DB_PASSWORD / SPRING_DATASOURCE_PASSWORD / MYSQL_ROOT_PASSWORD was not found.
  set /p "DB_PASSWORD=Input local MySQL root password: "
)

if not defined DB_PASSWORD (
  echo [ERROR] Database password is empty. Backend cannot start.
  pause
  exit /b 1
)

set "SPRING_DATASOURCE_PASSWORD=%DB_PASSWORD%"
set "MYSQL_ROOT_PASSWORD=%DB_PASSWORD%"
set "SPRING_DATASOURCE_URL=jdbc:mysql://127.0.0.1:%MYSQL_PORT%/%MYSQL_DATABASE%?useUnicode=true^&characterEncoding=utf-8^&serverTimezone=Asia/Shanghai^&useSSL=false^&allowPublicKeyRetrieval=true"

call :ensure_mysql
if errorlevel 1 (
  pause
  exit /b 1
)

call :start_service "%ALGORITHM_PORT%" "Algorithm API" "%ROOT%\algorithm" "python -m uvicorn api_server:app --host 127.0.0.1 --port %ALGORITHM_PORT% --reload"
call :start_service "%YOLO_PORT%" "YOLO Person API" "%ROOT%\algorithm" "python -m uvicorn polo:app --host 127.0.0.1 --port %YOLO_PORT% --reload"
call :start_service "%BACKEND_PORT%" "Java Backend" "%ROOT%\backend" "mvn.cmd spring-boot:run"
call :start_service "%FRONTEND_PORT%" "Frontend Dev Server" "%ROOT%\frontend" "npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT% --open /index.html"

echo.
echo ==========================================
echo  Startup commands have been sent
echo ==========================================
echo Frontend:     http://127.0.0.1:%FRONTEND_PORT%/index.html
echo Backend:      http://127.0.0.1:%BACKEND_PORT%/api
echo Algorithm:    http://127.0.0.1:%ALGORITHM_PORT%/docs
echo YOLO:         http://127.0.0.1:%YOLO_PORT%/docs
echo Database:     127.0.0.1:%MYSQL_PORT% / %MYSQL_DATABASE%
echo.
echo If a service fails, check the corresponding command window.
pause
exit /b 0

:ensure_mysql
call :is_port_listening "%MYSQL_PORT%"
if not errorlevel 1 (
  echo [SKIP] MySQL port %MYSQL_PORT% is already listening.
  exit /b 0
)

call :command_exists "docker"
if errorlevel 1 (
  echo [ERROR] MySQL is not listening on %MYSQL_PORT%, and Docker was not found.
  echo         Start local MySQL first, or install and start Docker Desktop.
  exit /b 1
)

docker compose version >nul 2>nul || (
  echo [ERROR] Docker Compose is not available. Check Docker Desktop.
  exit /b 1
)

echo [START] MySQL is not running. Starting Docker service chemical-mysql...
pushd "%ROOT%\deploy" >nul
set "MYSQL_DATABASE=%MYSQL_DATABASE%"
set "MYSQL_ROOT_PASSWORD=%MYSQL_ROOT_PASSWORD%"
docker compose -f docker-compose.yml up -d mysql
set "MYSQL_START_ERROR=%ERRORLEVEL%"
popd >nul
if not "%MYSQL_START_ERROR%"=="0" (
  echo [ERROR] Docker MySQL startup failed.
  exit /b 1
)

echo [WAIT] Waiting for MySQL port %MYSQL_PORT%...
for /l %%i in (1,1,30) do (
  call :is_port_listening "%MYSQL_PORT%"
  if not errorlevel 1 (
    echo [OK] MySQL is ready.
    exit /b 0
  )
  timeout /t 2 /nobreak >nul
)

echo [ERROR] MySQL startup timed out. Check Docker Desktop and chemical-mysql logs.
exit /b 1

:start_service
set "PORT=%~1"
set "TITLE=%~2"
set "DIR=%~3"
set "CMD=%~4"

call :is_port_listening "%PORT%"
if not errorlevel 1 (
  echo [SKIP] %TITLE% port %PORT% is already listening.
  exit /b 0
)

if not exist "%DIR%" (
  echo [ERROR] %TITLE% directory was not found: %DIR%
  exit /b 1
)

echo [START] %TITLE% on port %PORT%
start "%TITLE%" cmd /k "cd /d ""%DIR%"" && %CMD%"
exit /b 0

:is_port_listening
set "CHECK_PORT=%~1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -State Listen -LocalPort %CHECK_PORT% -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
exit /b %ERRORLEVEL%

:command_exists
set "CHECK_COMMAND=%~1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-Command '%CHECK_COMMAND%' -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
exit /b %ERRORLEVEL%
