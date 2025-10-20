# Start Airflow Standalone (Without Docker)
# This script sets up and starts Apache Airflow in standalone mode

Write-Host "=" -ForegroundColor Cyan
Write-Host "🚀 Airflow Standalone Startup Script" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

# Configuration - Auto-detect project root from script location
$ProjectRoot = Split-Path -Parent $PSCommandPath
$AirflowHome = "$ProjectRoot\airflow_local"
$VenvPath = "$ProjectRoot\..\. venv"

# If you want to specify manually, uncomment and edit the line below:
# $ProjectRoot = "C:\Your\Path\To\brewery_case"

# Set environment variables
$env:AIRFLOW_HOME = $AirflowHome
$env:PYTHONPATH = $ProjectRoot

Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Cyan
Write-Host "🏠 Airflow Home: $AirflowHome" -ForegroundColor Cyan
Write-Host ""

# Navigate to project
Set-Location $ProjectRoot

# Check if virtual environment exists
if (-not (Test-Path "$VenvPath\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found at: $VenvPath" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvPath
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& "$VenvPath\Scripts\Activate.ps1"

# Check if Airflow is installed
$airflowInstalled = pip list 2>$null | Select-String "apache-airflow"
if (-not $airflowInstalled) {
    Write-Host "📦 Installing Apache Airflow..." -ForegroundColor Yellow
    pip install apache-airflow==2.8.0 --quiet
    pip install -r requirements.txt --quiet
}

# Initialize Airflow database if needed
if (-not (Test-Path "$AirflowHome\airflow.db")) {
    Write-Host "🗄️  Initializing Airflow database..." -ForegroundColor Yellow
    airflow db init
    
    Write-Host "👤 Creating admin user..." -ForegroundColor Yellow
    airflow users create `
        --username admin `
        --firstname Admin `
        --lastname User `
        --role Admin `
        --email admin@example.com `
        --password admin
    
    # Configure DAGs folder
    Write-Host "⚙️  Configuring DAGs folder..." -ForegroundColor Yellow
    $configPath = "$AirflowHome\airflow.cfg"
    $dagsPath = "$ProjectRoot\dags"
    (Get-Content $configPath) -replace 'dags_folder = .*', "dags_folder = $dagsPath" | Set-Content $configPath
}

Write-Host ""
Write-Host "=" -ForegroundColor Green
Write-Host "✅ Airflow is ready!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Web UI will be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "👤 Username: admin" -ForegroundColor Yellow
Write-Host "🔑 Password: admin" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 DAGs location: $ProjectRoot\dags" -ForegroundColor Cyan
Write-Host "📝 Logs location: $AirflowHome\logs" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  To stop Airflow: Press Ctrl+C" -ForegroundColor Magenta
Write-Host ""
Write-Host "Starting Airflow in standalone mode..." -ForegroundColor Green
Write-Host ""

# Start Airflow standalone
airflow standalone
