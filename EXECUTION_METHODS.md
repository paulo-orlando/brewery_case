# 🎯 Three Ways to Run Your Brewery Pipeline

> **📝 Note:** Replace `<PROJECT_ROOT>` with your actual project path.  
> Example: `C:\path\to\brewery_case` or where you cloned this repository.

## Quick Comparison

| Method | Command | Setup Time | Best For |
|--------|---------|------------|----------|
| **1️⃣ Python Standalone** | `python run_pipeline_standalone.py` | 1 min | Quick runs, testing |
| **2️⃣ Airflow (No Docker)** | `.\start_airflow_local.ps1` | 5 min | Scheduling, monitoring |
| **3️⃣ Docker + Airflow** | `docker-compose up` | 10 min | Production, teams |

---

## 1️⃣ Python Standalone (Simplest)

### When to Use
- ✅ Quick one-off runs
- ✅ Development and debugging
- ✅ No need for scheduling
- ✅ Learning the pipeline

### How to Run

```powershell
cd <PROJECT_ROOT>
..\. venv\Scripts\Activate.ps1
python run_pipeline_standalone.py
```

### Pros & Cons

✅ **Pros:**
- Fastest to start
- No additional setup
- Easy to debug
- Direct Python execution

❌ **Cons:**
- No web UI
- No scheduling
- No retry logic
- No monitoring dashboard
- Manual execution only

### Output Location
Same as other methods:
- `data/raw/` - Raw API data
- `data/bronze/` - Validated JSON
- `data/silver/` - Cleaned Parquet
- `data/gold/` - Aggregated analytics

---

## 2️⃣ Airflow Standalone (No Docker)

### When to Use
- ✅ Need scheduling/automation
- ✅ Want web UI monitoring
- ✅ Don't want Docker overhead
- ✅ Solo development
- ✅ Windows native support

### How to Run

**One-time setup:**
```powershell
cd <PROJECT_ROOT>
.\start_airflow_local.ps1
```

**Access:**
- Web UI: http://localhost:8080
- Username: `admin`
- Password: `admin`

### Pros & Cons

✅ **Pros:**
- Web UI dashboard
- DAG visualization
- Scheduling support
- Task monitoring
- Retry logic
- No Docker needed
- Native Windows performance
- Lower resource usage

❌ **Cons:**
- SQLite database (not production-grade)
- Single machine only
- No container isolation
- Requires local Airflow install

### Architecture

```
Airflow Standalone
├── Webserver (UI) ───┐
├── Scheduler ────────┼─> SQLite DB (airflow.db)
└── Triggerer ────────┘
    ↓
Your DAGs (dags/brewery_pipeline.py)
    ↓
Pipeline Code (src/)
    ↓
Data Output (data/)
```

---

## 3️⃣ Docker + Airflow (Current Setup)

### When to Use
- ✅ Team development
- ✅ Production-like environment
- ✅ Need PostgreSQL
- ✅ Multiple executors
- ✅ Complete isolation

### How to Run

```powershell
cd <PROJECT_ROOT>\docker
docker-compose up -d
```

**Access:**
- Web UI: http://localhost:8080
- Username: `admin`
- Password: `admin`

### Pros & Cons

✅ **Pros:**
- Production-like setup
- PostgreSQL database
- Container isolation
- Multiple services
- Team consistency
- Easy to replicate
- Full Airflow features

❌ **Cons:**
- Requires Docker Desktop
- Higher resource usage
- Slower startup
- More complex debugging
- WSL2 needed on Windows

### Architecture

```
Docker Compose
├── airflow-webserver (Container)
├── airflow-scheduler (Container)
└── postgres (Container)
    ↓
Mounted Volumes
├── dags/ (your DAG files)
├── src/ (your code)
└── data/ (output)
```

---

## 📊 Detailed Feature Comparison

| Feature | Python Standalone | Airflow Standalone | Docker + Airflow |
|---------|------------------|-------------------|------------------|
| **Web UI** | ❌ No | ✅ Yes | ✅ Yes |
| **Scheduling** | ❌ Manual | ✅ Cron/Interval | ✅ Cron/Interval |
| **Monitoring** | 📝 Logs only | 📊 Dashboard | 📊 Dashboard |
| **Retry Logic** | ❌ No | ✅ Configurable | ✅ Configurable |
| **Task Dependencies** | ❌ Sequential | ✅ DAG-based | ✅ DAG-based |
| **Database** | ❌ None | SQLite | PostgreSQL |
| **Executor** | ❌ N/A | LocalExecutor | LocalExecutor |
| **Parallelism** | ❌ No | ⚠️ Limited | ✅ Full |
| **Resource Usage** | 🟢 Low | 🟡 Medium | 🔴 High |
| **Setup Time** | 🟢 1 min | 🟡 5 min | 🔴 10 min |
| **Debugging** | 🟢 Easy | 🟡 Medium | 🔴 Complex |
| **Production Ready** | ❌ No | ⚠️ Dev only | ✅ Yes |
| **Windows Native** | ✅ Yes | ✅ Yes | ⚠️ Requires WSL2 |
| **Team Sharing** | ⚠️ Scripts | ⚠️ Config | ✅ Containers |

---

## 🎯 Recommended Workflow

### 🏃 Quick Testing
```powershell
# Just run the pipeline once
python run_pipeline_standalone.py
```

### 💻 Local Development
```powershell
# With UI and scheduling
.\start_airflow_local.ps1
```

### 👥 Team/Production
```powershell
# Full Docker setup
cd docker
docker-compose up -d
```

---

## 🔄 Migration Between Methods

### From Standalone to Airflow

Your DAG file (`dags/brewery_pipeline.py`) works with both!

Just point Airflow to your DAGs folder:
```powershell
$env:AIRFLOW_HOME = "<PROJECT_ROOT>\airflow_local"
# DAGs folder is automatically configured
```

### From Airflow Standalone to Docker

All your data is in `data/` folder, which is mounted in Docker:
```yaml
# docker-compose.yml already has:
volumes:
  - ../data:/opt/airflow/data
```

No migration needed! 🎉

---

## 📝 Quick Start Commands

### Python Standalone
```powershell
cd <PROJECT_ROOT>
..\. venv\Scripts\Activate.ps1
python run_pipeline_standalone.py
```

### Airflow Standalone
```powershell
cd <PROJECT_ROOT>
.\start_airflow_local.ps1
# Then open: http://localhost:8080
```

### Docker + Airflow
```powershell
cd <PROJECT_ROOT>\docker
docker-compose up -d
# Then open: http://localhost:8080
```

---

## 💡 Pro Tips

### Use Python Standalone When:
- 🔍 Debugging specific transformation logic
- 🧪 Testing new features quickly
- 📊 Running ad-hoc data analysis
- 🎓 Learning the pipeline structure

### Use Airflow Standalone When:
- ⏰ Need scheduled runs
- 📈 Want to monitor execution
- 🔄 Testing DAG logic
- 👤 Solo development with scheduling

### Use Docker When:
- 👥 Working in a team
- 🏭 Production deployment
- 🔒 Need isolation
- 🎯 Require PostgreSQL features

---

## 🆘 Support

- **Python Issues:** Check `pipeline_execution.log`
- **Airflow Issues:** Check `$env:AIRFLOW_HOME\logs\`
- **Docker Issues:** Check `docker logs <container_name>`

For detailed guides, see:
- `AIRFLOW_STANDALONE_SETUP.md` - Full Airflow setup
- `OUTPUT_ACCESS_GUIDE.md` - Where to find outputs
- `README.md` - General documentation

---

## ✅ Summary

**All three methods produce the same output!**

Choose based on your needs:
- 🏃 **Speed** → Python Standalone
- 🎯 **Features** → Airflow Standalone  
- 🏭 **Production** → Docker + Airflow

You can switch between them anytime! 🚀
