# Files Excluded from Git (Non-Core Files)

This document lists all files that are ignored by git because they are not part of the core solution for the brewery data pipeline challenge.

## 📋 Categories of Ignored Files

### 1. **Python Generated Files**
- `__pycache__/` - Python bytecode cache directories
- `*.pyc`, `*.pyo`, `*.py[cod]` - Compiled Python files
- `*$py.class` - Java class files (if using Jython)
- `.pytest_cache/` - Pytest cache
- `.coverage` - Coverage data file
- `htmlcov/` - HTML coverage reports

### 2. **Virtual Environment**
- `.venv/` - Python virtual environment
- `venv/`, `ENV/`, `env/` - Alternative venv names
- All installed packages in virtual environment

### 3. **Airflow Generated Files**
- `logs/` - Airflow execution logs
- `airflow.db` - Local Airflow database
- `airflow.cfg` - Airflow configuration (generated)
- `airflow-webserver.pid` - Process ID file
- `airflow-scheduler.pid` - Scheduler process ID
- `standalone_admin_password.txt` - Auto-generated password

### 4. **Data Files (Generated at Runtime)**
- `data/` - All data directories (raw/bronze/silver/gold)
- `*.csv` - CSV outputs
- `*.parquet` - Parquet files
- `*.json` - JSON data files (except config files)

**Note**: Config files like `requirements.txt`, `package.json`, `pytest.ini` are **NOT** ignored.

### 5. **Docker Generated Files**
- `docker/logs/` - Docker container logs
- `docker/plugins/` - Airflow plugins
- `docker-compose.override.yml` - Local Docker overrides

### 6. **IDE & Editor Files**
- `.vscode/` - VSCode settings
- `.idea/` - PyCharm/IntelliJ settings
- `*.swp`, `*.swo` - Vim swap files
- `.DS_Store` - macOS Finder metadata
- `Thumbs.db` - Windows thumbnail cache

### 7. **Test Output Files**
- `.pytest_cache/` - Pytest cache
- `.coverage` - Coverage.py data
- `htmlcov/` - HTML coverage reports
- `coverage.xml` - Coverage XML report
- `test_results.xml` - Test results

### 8. **Environment & Secrets**
- `.env` - Environment variables
- `.env.local` - Local environment overrides
- `*.pem`, `*.key` - SSL certificates and keys
- `secrets/` - Secrets directory

### 9. **Temporary Files**
- `*.tmp`, `*.temp` - Temporary files
- `*.bak` - Backup files
- `*.orig` - Original files from merges
- `tmp/`, `temp/` - Temporary directories

### 10. **Non-Core Project Files** (Specific to this project)

#### Old/Test Scripts (Not Part of Solution):
- ❌ `src/api/api.py` - Old test API script
- ❌ `src/api/api2.py` - Another test API script
- ❌ `src/api/test_api.py` - Old test file in wrong location
- ❌ `dags/teste_dag.py` - Test DAG (not part of solution)
- ❌ `teste_python.py` - Test Python file in root

#### Reference/Helper Files:
- ❌ `scripts/` - Helper scripts directory (like list_tree.py)
- ❌ `PySpark_Cheatsheet.md` - Reference document

---

## ✅ Core Files KEPT in Git (Solution Files)

### **Source Code (Core Solution)**
- ✅ `src/api/brewery_api.py` - API extraction module
- ✅ `src/bronze/bronze_layer.py` - Bronze layer
- ✅ `src/silver/silver_layer.py` - Silver layer
- ✅ `src/gold/gold_layer.py` - Gold layer
- ✅ `src/common/data_quality.py` - Quality checks
- ✅ `src/tests/test_api.py` - API unit tests
- ✅ `src/tests/test_bronze.py` - Bronze unit tests
- ✅ `src/__init__.py` - Package init files (all layers)

### **Airflow**
- ✅ `dags/brewery_pipeline.py` - Main DAG

### **Docker**
- ✅ `docker/Dockerfile` - Container image definition
- ✅ `docker/docker-compose.yml` - Service orchestration

### **Configuration**
- ✅ `requirements.txt` - Python dependencies
- ✅ `pytest.ini` - Test configuration
- ✅ `.gitignore` - Git ignore rules

### **Setup Scripts**
- ✅ `setup.sh` - Linux/Mac setup script
- ✅ `setup.ps1` - Windows PowerShell setup script

### **Documentation**
- ✅ `README.md` - Main documentation
- ✅ `QUICKSTART.md` - Quick start guide
- ✅ `MONITORING.md` - Monitoring strategy
- ✅ `SOLUTION_SUMMARY.md` - Solution summary
- ✅ `GITIGNORE_SUMMARY.md` - This file

---

## 🔍 Currently Ignored Files in Your Repo

Based on `git status --ignored`, these files/directories are currently ignored:

```
!! .coverage                    # Coverage data file
!! .pytest_cache/               # Pytest cache directory
!! htmlcov/                     # HTML coverage reports
!! src/__pycache__/             # Python cache (src)
!! src/api/__pycache__/         # Python cache (api)
!! src/tests/__pycache__/       # Python cache (tests)
```

**Additional files that WILL be ignored when created:**
- `data/` (when you run the pipeline)
- `logs/` (when Airflow runs)
- `.venv/` (if you recreate virtual environment)
- `.env` (if you create environment file)

---

## 📝 To Verify What's Ignored

Run these commands:

```powershell
# List all ignored files
git status --ignored

# List only ignored files (short format)
git status --ignored --short | Select-String "^!!"

# Check if specific file is ignored
git check-ignore -v data/raw/breweries.json
git check-ignore -v htmlcov/index.html
```

---

## 🗂️ Clean Repository Structure

After ignoring non-core files, your repository contains only:
1. ✅ Source code for the solution
2. ✅ Tests
3. ✅ Docker configuration
4. ✅ Documentation
5. ✅ Setup scripts
6. ✅ Configuration files

**Everything else** (runtime data, caches, logs, IDE files) is ignored!

---

## 🧹 To Clean Ignored Files

If you want to delete all ignored files from your working directory:

```powershell
# Preview what would be removed
git clean -ndX

# Actually remove ignored files (be careful!)
git clean -fdX
```

**Warning**: This will delete `htmlcov/`, `.pytest_cache/`, `__pycache__/`, etc.

---

## ✨ Benefits

✅ Cleaner repository
✅ Smaller clone size
✅ No accidental commits of generated files
✅ No IDE-specific files in repo
✅ No data files or logs in version control
✅ Focus only on source code and documentation

---

Last updated: 2025-10-19
