# Brewery Data Pipeline - Quick Start Guide (v0.0.6)

## 🎯 What You'll Need

- Docker & Docker Compose installed (Option 1)
- OR Python 3.11+ (Option 2 - Standalone)
- 4GB+ RAM available
- Internet connection (to fetch API data)

## 🚀 3-Minute Setup

### Option 1: Docker (Recommended for Production)

```bash
# 1. Navigate to the project
cd brewery_case

# 2. Start services
cd docker
docker-compose up -d

# 3. Wait ~2 minutes for initialization
docker-compose ps

# 4. Access Airflow
# URL: http://localhost:8080
# Username: airflow
# Password: airflow

# 5. Run the pipeline
# In Airflow UI: Toggle ON the brewery_pipeline DAG and click "Trigger DAG"
```

### Option 2: Standalone Execution (NEW - No Docker Required!)

**Perfect for development, testing, and quick runs**

```powershell
# Windows PowerShell
cd brewery_case

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run complete pipeline (all layers in ~20-45 seconds)
python run_pipeline_standalone.py

# Check results
python check_medallion_structure.py
```

```bash
# Linux/Mac
cd brewery_case

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run complete pipeline
python run_pipeline_standalone.py

# Check results
python check_medallion_structure.py
```

### Option 3: Manual Layer Testing (Development)

```powershell
# Windows PowerShell
cd brewery_case
.\setup.ps1

# Test individual modules
python src\api\brewery_api.py .\data\raw
python src\bronze\bronze_layer.py .\data\raw .\data\bronze
python src\silver\silver_layer.py .\data\bronze .\data\silver
python src\gold\gold_layer.py .\data\silver .\data\gold
```

```bash
# Linux/Mac
cd brewery_case
./setup.sh

# Test individual modules
python src/api/brewery_api.py ./data/raw
python src/bronze/bronze_layer.py ./data/raw ./data/bronze
python src/silver/silver_layer.py ./data/bronze ./data/silver
python src/gold/gold_layer.py ./data/silver ./data/gold
```

## 📊 Viewing Results

### Gold Layer Outputs

After the pipeline runs, check:

```powershell
# View aggregated CSV (human-readable)
type data\gold\breweries_by_type_location\breweries_by_type_location_*.csv

# View summary statistics
type data\gold\breweries_by_type_location\summary_statistics_*.json
```

### Sample Output

**Breweries by Type and Location** (CSV):
```csv
country,state,brewery_type,brewery_count,unique_cities,avg_latitude,avg_longitude
United States,California,micro,450,85,36.7783,-119.4179
United States,California,brewpub,230,52,37.2744,-119.2705
United States,Oregon,micro,380,45,44.0582,-121.3152
...
```

**Summary Statistics** (JSON):
```json
{
  "total_breweries": 8123,
  "unique_countries": 12,
  "unique_states": 65,
  "brewery_types": {
    "micro": 4250,
    "brewpub": 2100,
    "regional": 980,
    "large": 450,
    "contract": 343
  },
  "top_10_states": {
    "California": 892,
    "Texas": 567,
    "New York": 489,
    ...
  }
}
```

## 🧪 Testing

```powershell
# Run all tests
pytest src\tests\ -v

# Run specific layer tests
pytest src\tests\test_api.py -v
pytest src\tests\test_bronze.py -v

# With coverage report
pytest src\tests\ -v --cov=src --cov-report=html
# View: htmlcov/index.html
```

## 🔍 Monitoring Pipeline

### View Logs

```bash
# Docker
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver

# Local
# Check: logs/scheduler/latest/brewery_pipeline/
```

### Check Data Quality

```bash
# Manual quality check
python src/common/data_quality.py ./data/silver silver
```

## 🛠️ Troubleshooting

### Pipeline Fails at API Extraction

**Symptom**: Task `extract_brewery_data` fails
**Solution**: Check internet connection, API might be rate-limiting
```bash
# Test API manually
curl https://api.openbrewerydb.org/v1/breweries?page=1&per_page=10
```

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Verify PYTHONPATH includes project root
```bash
# Docker: Rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Local: Reinstall
pip install -r requirements.txt
```

### Permission Denied

**Symptom**: Can't write to data directories
**Solution**: Fix permissions
```bash
# Docker
chmod -R 777 ./data ./logs

# Windows: Run PowerShell as Administrator
```

## 📈 Expected Timeline

| Task | Duration | Status Indicators |
|------|----------|-------------------|
| API Extract | 2-3 min | Progress: "Fetching page X..." |
| Bronze Load | 30 sec | File appears in data/bronze/ |
| Silver Transform | 1-2 min | Parquet files in data/silver/ |
| Gold Aggregate | 30 sec | CSV + JSON in data/gold/ |
| Quality Check | 10 sec | "Quality check PASSED" |
| **Total** | **5-7 min** | All tasks green in Airflow UI |

## 💡 Pro Tips

1. **View Parquet files**:
```python
import pandas as pd
df = pd.read_parquet('data/silver/breweries')
print(df.head())
print(df.info())
```

2. **Query specific partition**:
```python
df = pd.read_parquet(
    'data/silver/breweries',
    filters=[('country', '==', 'United States'), ('state', '==', 'California')]
)
```

3. **Monitor disk usage**:
```bash
du -sh data/*
# Expected: raw ~5MB, bronze ~6MB, silver ~4MB, gold ~500KB
```

4. **Re-run failed task only**:
In Airflow UI: Click failed task → "Clear" → Confirm

## 🌟 What's Next?

- [ ] Add incremental processing (only fetch new data)
- [ ] Implement data versioning
- [ ] Add more aggregations (time-series, geographic clusters)
- [ ] Set up monitoring dashboard (Grafana)
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Add ML features (brewery recommendations, trend analysis)

## 📞 Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review logs in `logs/` directory
- Open a GitHub issue with:
  - Error message
  - Logs (last 50 lines)
  - Python/Docker version
  - OS version

## ✅ Verification Checklist

After setup, verify:
- [ ] Airflow UI loads at http://localhost:8080
- [ ] `brewery_pipeline` DAG appears in DAG list
- [ ] DAG has 5 tasks visible in graph view
- [ ] All tasks have proper dependencies (linear chain)
- [ ] Data directories exist: data/{raw,bronze,silver,gold}
- [ ] Tests pass: `pytest src/tests/ -v`

---

**Ready to run? Just execute the Docker commands above and trigger the DAG in Airflow UI!**
