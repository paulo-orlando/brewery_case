# 🏅 Medallion Architecture Guide

## 📚 What is Medallion Architecture?

Medallion architecture is a design pattern for organizing data lakes into progressively more refined and optimized layers, similar to medals: **Bronze** (raw), **Silver** (refined), and **Gold** (premium).

---

## 🥉 BRONZE LAYER

### **Objective**
Store raw data exactly as received from the source, with minimal transformation.

### **Characteristics**
- ✅ Data in original form (JSON)
- ✅ Preserves complete API structure
- ✅ Adds ingestion metadata (timestamp, source)
- ✅ Serves as historical "source of truth"
- ✅ Allows re-processing if necessary

### **Location**
```
data/bronze/breweries/{execution_date}/
  └── bronze_breweries_{timestamp}.json
```

### **File Structure**
```json
{
  "bronze_metadata": {
    "ingestion_timestamp": "2025-10-19T10:30:00",
    "source_file": "breweries_2025-10-19.json",
    "record_count": 8000,
    "layer": "bronze"
  },
  "source_metadata": {...},
  "data": [
    {
      "id": "abc123",
      "name": "Brewery Name",
      "brewery_type": "micro",
      ...
    }
  ]
}
```

### **Responsible Code**
`src/bronze/bronze_layer.py` → function `save_to_bronze()`

---

## 🥈 SILVER LAYER

### **Objective**
Clean, validated, and optimized data for analytical consumption.

### **Characteristics**
- ✅ Parquet format (columnar, compressed)
- ✅ Partitioned by `country` and `state`
- ✅ Schema enforcement (validated data types)
- ✅ Cleaned and standardized data
- ✅ Data quality flags
- ✅ Deduplication applied
- ✅ Derived fields added

### **Location**
```
data/silver/breweries/
  ├── country=United States/
  │   ├── state=California/
  │   │   └── part-0.parquet
  │   ├── state=Texas/
  │   │   └── part-0.parquet
  │   └── state=New York/
  │       └── part-0.parquet
  ├── country=Canada/
  │   └── state=Ontario/
  │       └── part-0.parquet
  └── country=Unknown/
      └── state=Unknown/
          └── part-0.parquet
```

### **Applied Transformations**
1. **Data Cleaning**
   - Empty values → `None`
   - Remove extra spaces
   - String standardization

2. **Derived Fields**
   - `ingestion_date` - ingestion date
   - `ingestion_timestamp` - complete timestamp
   - `location_key` - composite key (country_state)
   - `has_complete_address` - boolean flag
   - `has_coordinates` - boolean flag

3. **Validations**
   - Convert latitude/longitude to numeric
   - Deduplication by ID
   - Null value handling

4. **Optimizations**
   - Snappy compression
   - Parquet dictionaries usage
   - Statistics per column

### **Responsible Code**
`src/silver/silver_layer.py` → function `transform_to_silver()`

### **Query with Pandas**
```python
import pandas as pd

# Read entire Silver layer
df = pd.read_parquet('data/silver/breweries')

# Read only one country
df_usa = pd.read_parquet('data/silver/breweries', 
                         filters=[('country', '=', 'United States')])

# Read only one state
df_ca = pd.read_parquet('data/silver/breweries',
                        filters=[('country', '=', 'United States'),
                                ('state', '=', 'California')])
```

---

## 🥇 GOLD LAYER

### **Objective**
Aggregations ready for BI, dashboards, and business analysis.

### **Characteristics**
- ✅ Aggregated and summarized data
- ✅ Calculated business metrics
- ✅ Multiple formats (Parquet, CSV, JSON)
- ✅ Optimized for fast reading
- ✅ Ready for BI tools (Tableau, Power BI, etc.)

### **Location**
```
data/gold/breweries_by_type_location/
  ├── breweries_by_type_location_{date}.parquet
  ├── breweries_by_type_location_{date}.csv
  └── summary_statistics_{date}.json
```

### **Created Aggregations**

#### **1. Main Aggregation - By Type and Location**
```csv
country,state,brewery_type,brewery_count,unique_cities,avg_latitude,avg_longitude,pct_with_coordinates,pct_with_address
United States,California,micro,450,85,37.2741,-121.8765,87.50,92.30
United States,California,brewpub,120,45,37.5432,-122.1234,85.00,90.00
United States,Texas,micro,380,72,30.2672,-97.7431,82.10,88.50
...
```

**Included metrics:**
- `brewery_count` - total breweries
- `unique_cities` - number of unique cities
- `avg_latitude` - average latitude
- `avg_longitude` - average longitude
- `pct_with_coordinates` - % with coordinates
- `pct_with_address` - % with complete address

#### **2. General Statistics (JSON)**
```json
{
  "total_breweries": 8000,
  "unique_countries": 3,
  "unique_states": 52,
  "unique_cities": 2500,
  "brewery_types": {
    "micro": 4500,
    "brewpub": 2000,
    "regional": 1000,
    "large": 500
  },
  "top_10_states": {...},
  "top_10_cities": {...},
  "data_quality": {
    "records_with_coordinates": 6800,
    "pct_with_coordinates": 85.00,
    "records_with_complete_address": 7200,
    "pct_with_complete_address": 90.00
  }
}
```

### **Responsible Code**
`src/gold/gold_layer.py` → function `create_gold_aggregations()`

---

## 🔍 How to Query Each Layer

### **Option 1: Ready-Made Python Script**
```bash
python check_medallion_structure.py
```

### **Option 2: Manual Queries**

#### **Bronze (JSON)**
```python
import json

with open('data/bronze/breweries/2025-10-19/bronze_breweries_20251019_103000.json') as f:
    bronze_data = json.load(f)
    
print(f"Total records: {bronze_data['bronze_metadata']['record_count']}")
print(f"First record: {bronze_data['data'][0]}")
```

#### **Silver (Parquet)**
```python
import pandas as pd

# Read all
df = pd.read_parquet('data/silver/breweries')

# Statistics
print(df.info())
print(df.describe())

# Filters
df_micro = df[df['brewery_type'] == 'micro']
df_ca = df[df['state'] == 'California']
```

#### **Gold (CSV or Parquet)**
```python
import pandas as pd

# Aggregations
agg = pd.read_csv('data/gold/breweries_by_type_location/breweries_by_type_location_20251019.csv')

# Top states
top_states = agg.groupby('state')['brewery_count'].sum().sort_values(ascending=False).head(10)
print(top_states)

# Statistics
import json
with open('data/gold/breweries_by_type_location/summary_statistics_20251019.json') as f:
    stats = json.load(f)
    print(json.dumps(stats, indent=2))
```

---

## 📊 Layer Comparison

| Aspect | Bronze | Silver | Gold |
|---------|--------|--------|------|
| **Format** | JSON | Parquet | Parquet + CSV + JSON |
| **Size** | Large (text) | Medium (compressed) | Small (aggregated) |
| **Performance** | Slow | Fast | Very Fast |
| **Usage** | Historical backup | Exploratory analysis | Dashboards/BI |
| **Transformations** | None | Many | Aggregations |
| **Partitioning** | By date | By country/state | Not partitioned |
| **Update** | Append-only | Overwrite partitions | Overwrite all |

---

## 🚀 Data Flow

```
API (Open Brewery DB)
    ↓
┌─────────────────┐
│ RAW (temporary) │  Raw JSON
└────────┬────────┘
         ↓
┌─────────────────┐
│  BRONZE         │  JSON + metadata
│  (preserve)     │  Complete history
└────────┬────────┘
         ↓
┌─────────────────┐
│  SILVER         │  Partitioned Parquet
│  (curate)       │  Clean data
└────────┬────────┘
         ↓
┌─────────────────┐
│  GOLD           │  Aggregations
│  (aggregate)    │  Business metrics
└─────────────────┘
```

---

## 💡 Best Practices

### **Bronze**
- ✅ Never delete Bronze data
- ✅ Use for reprocessing if Silver/Gold fail
- ✅ Keep for compliance/auditing

### **Silver**
- ✅ Apply strict validations
- ✅ Document transformations
- ✅ Use smart partitioning
- ✅ Test data quality

### **Gold**
- ✅ Create specific aggregations per use case
- ✅ Keep multiple formats for different consumers
- ✅ Document business metrics
- ✅ Update regularly

---

## 🔧 Maintenance

### **Check disk space**
```bash
du -sh data/bronze data/silver data/gold
```

### **Clean old data** (example)
```python
from pathlib import Path
from datetime import datetime, timedelta

# Delete Bronze > 90 days
cutoff = datetime.now() - timedelta(days=90)
for file in Path('data/bronze').rglob('*.json'):
    if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
        file.unlink()
```
