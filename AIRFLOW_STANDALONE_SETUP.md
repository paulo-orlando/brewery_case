# 🚀 Running Airflow WITHOUT Docker

> **📝 Important:** Replace `<PROJECT_ROOT>` with your actual project path throughout this guide.  
> Example: `C:\Users\YourName\Projects\brewery_case` or wherever you cloned this repository.

Yes! You can run Airflow directly on Windows without Docker. Here are your options:

---

## 📋 Option 1: Airflow Standalone Mode (Recommended for Development)

This is the **simplest** way to run Airflow locally without Docker.

### ✅ Prerequisites

```powershell
# Python 3.8 - 3.11 (3.12 not fully supported yet)
python --version

# Should output: Python 3.11.x or similar
```

### 📦 Installation Steps

#### Step 1: Create/Activate Virtual Environment

```powershell
# Navigate to project
cd <PROJECT_ROOT>

# Activate existing venv (or create new one)
..\. venv\Scripts\Activate.ps1

# Or create new Airflow-specific venv
python -m venv airflow_venv
.\airflow_venv\Scripts\Activate.ps1
```

#### Step 2: Set Airflow Home Directory

```powershell
# Set AIRFLOW_HOME environment variable (important!)
$env:AIRFLOW_HOME = "<PROJECT_ROOT>\airflow_local"

# Make it permanent (optional)
[System.Environment]::SetEnvironmentVariable('AIRFLOW_HOME', '<PROJECT_ROOT>\airflow_local', 'User')
```

#### Step 3: Install Airflow

```powershell
# Install Airflow with constraints for Python 3.11
$AIRFLOW_VERSION = "2.8.0"
$PYTHON_VERSION = "3.11"
$CONSTRAINT_URL = "https://raw.githubusercontent.com/apache/airflow/constraints-$AIRFLOW_VERSION/constraints-$PYTHON_VERSION.txt"

pip install "apache-airflow==$AIRFLOW_VERSION" --constraint $CONSTRAINT_URL

# Or simpler (already in requirements.txt)
pip install apache-airflow==2.8.0
```

#### Step 4: Install Project Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt
```

#### Step 5: Initialize Airflow Database

```powershell
# Initialize the database (SQLite by default)
airflow db init

# This creates:
# - $AIRFLOW_HOME/airflow.db (SQLite database)
# - $AIRFLOW_HOME/airflow.cfg (configuration file)
# - $AIRFLOW_HOME/logs/ (log directory)
```

#### Step 6: Create Admin User

```powershell
# Create an admin user for the web UI
airflow users create `
    --username admin `
    --firstname Admin `
    --lastname User `
    --role Admin `
    --email admin@example.com `
    --password admin
```

#### Step 7: Configure DAGs Path

```powershell
# Edit airflow.cfg to point to your DAGs folder
notepad $env:AIRFLOW_HOME\airflow.cfg

# Find and update this line:
# dags_folder = <PROJECT_ROOT>\dags
```

Or use PowerShell to update it automatically:

```powershell
$configPath = "$env:AIRFLOW_HOME\airflow.cfg"
$dagsPath = "<PROJECT_ROOT>\dags"
(Get-Content $configPath) -replace 'dags_folder = .*', "dags_folder = $dagsPath" | Set-Content $configPath
```

#### Step 8: Start Airflow Standalone

```powershell
# Start Airflow in standalone mode (all-in-one)
airflow standalone

# This starts:
# - Webserver (http://localhost:8080)
# - Scheduler
# - Triggerer
# All in one process!
```

**Or start services separately** (for more control):

```powershell
# Terminal 1: Start the webserver
airflow webserver --port 8080

# Terminal 2: Start the scheduler
airflow scheduler

# Terminal 3: (Optional) Start the triggerer for deferred operators
airflow triggerer
```

#### Step 9: Access Airflow UI

```
URL: http://localhost:8080
Username: admin
Password: admin
```

---

## 🔧 Option 2: Full Airflow Setup with PostgreSQL (Production-like)

For a more robust setup similar to Docker, you can use PostgreSQL as the backend.

### Prerequisites

1. Install PostgreSQL for Windows from: https://www.postgresql.org/download/windows/
2. During installation, remember the password for the `postgres` user

### Setup Steps

#### 1. Create Airflow Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE airflow_db;
CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
\q
```

#### 2. Install PostgreSQL Driver

```powershell
pip install apache-airflow[postgres]
# Or
pip install psycopg2-binary
```

#### 3. Update Airflow Configuration

```powershell
# Edit airflow.cfg
notepad $env:AIRFLOW_HOME\airflow.cfg

# Update these settings:
# sql_alchemy_conn = postgresql+psycopg2://airflow_user:airflow_pass@localhost:5432/airflow_db
# executor = LocalExecutor  # Better than SequentialExecutor
```

Or use PowerShell:

```powershell
$configPath = "$env:AIRFLOW_HOME\airflow.cfg"
$sqlConn = "postgresql+psycopg2://airflow_user:airflow_pass@localhost:5432/airflow_db"
(Get-Content $configPath) -replace 'sql_alchemy_conn = .*', "sql_alchemy_conn = $sqlConn" | Set-Content $configPath
(Get-Content $configPath) -replace 'executor = .*', "executor = LocalExecutor" | Set-Content $configPath
```

#### 4. Initialize Database

```powershell
airflow db init
```

#### 5. Start Services

```powershell
# Terminal 1: Webserver
airflow webserver --port 8080

# Terminal 2: Scheduler
airflow scheduler
```

---

## 📝 Configuration for Your Project

### Update paths in `airflow.cfg`:

```ini
[core]
dags_folder = <PROJECT_ROOT>\dags
base_log_folder = <PROJECT_ROOT>\airflow_local\logs
plugins_folder = <PROJECT_ROOT>\plugins

[logging]
logging_level = INFO
```

### Add Project to Python Path

Create a `.env` file or add to your DAG:

```python
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

---

## 🎯 Quick Start Script

Create a PowerShell script `start_airflow_local.ps1`:

```powershell
# start_airflow_local.ps1

# Set environment
$env:AIRFLOW_HOME = "<PROJECT_ROOT>\airflow_local"
cd <PROJECT_ROOT>

# Activate virtual environment
..\. venv\Scripts\Activate.ps1

Write-Host "🚀 Starting Airflow Standalone Mode..." -ForegroundColor Green
Write-Host "📊 DAGs folder: dags/" -ForegroundColor Cyan
Write-Host "🌐 Web UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "👤 Username: admin | Password: admin" -ForegroundColor Yellow
Write-Host ""

# Start Airflow
airflow standalone
```

Then run:

```powershell
.\start_airflow_local.ps1
```

---

## 🔄 Managing Airflow Services

### Check DAG Status

```powershell
# List all DAGs
airflow dags list

# List runs for brewery_pipeline
airflow dags list-runs -d brewery_pipeline

# Trigger a DAG manually
airflow dags trigger brewery_pipeline

# Check task states
airflow tasks states-for-dag-run brewery_pipeline <run_id>
```

### Pause/Unpause DAGs

```powershell
# Pause a DAG
airflow dags pause brewery_pipeline

# Unpause a DAG
airflow dags unpause brewery_pipeline
```

### Test Individual Tasks

```powershell
# Test a specific task without running full DAG
airflow tasks test brewery_pipeline extract_brewery_data 2025-10-20
```

---

## 📊 Comparison: Docker vs Standalone Airflow

| Feature | Docker Airflow | Standalone Airflow |
|---------|---------------|-------------------|
| **Setup Time** | 5-10 minutes | 2-5 minutes |
| **Dependencies** | Docker Desktop | Python only |
| **Resource Usage** | Higher (containers) | Lower (native) |
| **Isolation** | Fully isolated | Shared with system |
| **Database** | PostgreSQL | SQLite (or PostgreSQL) |
| **Production-like** | ✅ Yes | ⚠️ Less so (SQLite) |
| **Multi-executor** | ✅ Yes | ⚠️ Limited |
| **Best for** | Production, Teams | Development, Solo |
| **Windows Support** | Requires WSL2/Docker | Native support |
| **Port Conflicts** | Isolated | Can conflict |
| **Debugging** | More complex | Easier |
| **Performance** | Overhead | Faster |

---

## 🐛 Troubleshooting

### Issue: Airflow command not found

```powershell
# Make sure venv is activated
..\. venv\Scripts\Activate.ps1

# Verify installation
pip list | findstr airflow
```

### Issue: Database locked (SQLite)

```powershell
# Stop all Airflow processes
Get-Process | Where-Object {$_.ProcessName -like "*airflow*"} | Stop-Process -Force

# Delete lock file
Remove-Item "$env:AIRFLOW_HOME\airflow.db-shm" -ErrorAction SilentlyContinue
Remove-Item "$env:AIRFLOW_HOME\airflow.db-wal" -ErrorAction SilentlyContinue
```

### Issue: DAGs not showing up

```powershell
# Check DAGs folder path
airflow config get-value core dags_folder

# Manually scan DAGs
airflow dags list-import-errors

# Check logs
Get-Content "$env:AIRFLOW_HOME\logs\scheduler\latest\*.log" | Select-Object -Last 50
```

### Issue: Module not found errors

```powershell
# Ensure project is in Python path
$env:PYTHONPATH = "<PROJECT_ROOT>;$env:PYTHONPATH"

# Or add to DAG file:
import sys
sys.path.insert(0, '<PROJECT_ROOT>')  # Replace with your actual path
```

---

## 🎓 Recommended Workflow

### For Development:
1. **Use Standalone Airflow** with SQLite
2. Quick iterations and testing
3. Easy debugging

### For Production-like Testing:
1. **Use Airflow with PostgreSQL** (no Docker)
2. Test with LocalExecutor
3. Validate before deploying to real production

### For Team/Production:
1. **Use Docker + Airflow** (current setup)
2. Closer to production environment
3. Better isolation and reproducibility

---

## 📚 Additional Resources

- **Official Docs:** https://airflow.apache.org/docs/apache-airflow/stable/start.html
- **Installation Guide:** https://airflow.apache.org/docs/apache-airflow/stable/installation/
- **Configuration Reference:** https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html

---

## ✅ Quick Commands Reference

```powershell
# Setup
$env:AIRFLOW_HOME = "<PROJECT_ROOT>\airflow_local"
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Start (Standalone)
airflow standalone

# Start (Separate Services)
airflow webserver --port 8080  # Terminal 1
airflow scheduler               # Terminal 2

# Manage DAGs
airflow dags list
airflow dags trigger brewery_pipeline
airflow dags list-runs -d brewery_pipeline

# Test
airflow tasks test brewery_pipeline extract_brewery_data 2025-10-20

# Stop
# Press Ctrl+C in each terminal
```

---

## 🎯 Summary

**Yes, you can run Airflow without Docker!**

**Easiest method:** Use `airflow standalone` command
- ✅ Single command to start everything
- ✅ Perfect for development and testing
- ✅ No Docker required
- ✅ Lower resource usage

**Your three options:**
1. 🐍 **Python Standalone** (`run_pipeline_standalone.py`) - No Airflow needed
2. 🌬️ **Airflow Standalone** (SQLite) - Simple Airflow setup
3. 🐋 **Docker + Airflow** (Current) - Production-like setup

Choose based on your needs! 🚀
