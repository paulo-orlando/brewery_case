"""
Standalone script to execute the complete pipeline without Docker/Airflow.
Executes all stages of the Medallion architecture sequentially.
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import pipeline functions
from src.api.brewery_api import fetch_brewery_data
from src.bronze.bronze_layer import save_to_bronze
from src.silver.silver_layer import transform_to_silver
from src.gold.gold_layer import create_gold_aggregations
from src.common.data_quality import check_data_quality

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)


def print_separator(char='=', length=100):
    """Prints visual separator."""
    print(f"\n{char * length}\n")


def print_stage(stage_name, emoji='🔄'):
    """Prints stage header."""
    print_separator('=')
    print(f"{emoji} STAGE: {stage_name}")
    print_separator('=')


def main():
    """Executes the complete pipeline."""
    start_time = datetime.now()
    
    print_separator('=')
    print("🚀 BREWERY DATA PIPELINE - ARQUITETURA MEDALLION")
    print("   Standalone Execution (Without Docker)")
    print_separator('=')
    print(f"⏰ Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator('-')
    
    # Configure paths
    base_path = Path(__file__).parent / 'data'
    execution_date = datetime.now().strftime('%Y-%m-%d')
    
    raw_path = base_path / 'raw' / execution_date
    bronze_path = base_path / 'bronze' / 'breweries' / execution_date
    silver_path = base_path / 'silver' / 'breweries'
    gold_path = base_path / 'gold' / 'breweries_by_type_location'
    
    # Create directories
    for path in [raw_path, bronze_path, silver_path, gold_path]:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created/verified: {path}")
    
    results = {}
    
    try:
        # STAGE 1: Extract - Fetch data from API
        print_stage("1/5 - EXTRACT: Fetch data from API", "📡")
        
        api_result = fetch_brewery_data(
            base_url='https://api.openbrewerydb.org/v1/breweries',
            output_path=str(raw_path),
            per_page=200
        )
        
        results['extract'] = api_result
        print(f"✅ Extraction complete!")
        print(f"   • Total breweries: {api_result['records_extracted']}")
        print(f"   • File saved: {api_result['output_file']}")
        print(f"   • Timestamp: {api_result['timestamp']}")
        
        # STAGE 2: Bronze - Save raw data
        print_stage("2/5 - BRONZE: Save raw data", "🥉")
        
        bronze_result = save_to_bronze(
            input_path=str(raw_path),
            output_path=str(bronze_path)
        )
        
        results['bronze'] = bronze_result
        print(f"✅ Bronze layer complete!")
        print(f"   • Total records: {bronze_result['total_records']}")
        print(f"   • Files processed: {bronze_result['files_processed']}")
        
        # STAGE 3: Silver - Transform and partition
        print_stage("3/5 - SILVER: Transform and partition", "🥈")
        
        # Clean existing Silver data before processing
        if silver_path.exists():
            logger.info(f"Cleaning existing Silver layer data: {silver_path}")
            shutil.rmtree(silver_path)
            silver_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Silver layer cleaned and recreated")
        
        silver_result = transform_to_silver(
            input_path=str(bronze_path),
            output_path=str(silver_path),
            partition_cols=['country', 'state']
        )
        
        results['silver'] = silver_result
        print(f"✅ Silver layer complete!")
        print(f"   • Total records: {silver_result['total_records']}")
        print(f"   • Partitions created: country={silver_result['unique_countries']}, state={silver_result['unique_states']}")
        print(f"   • Output directory: {silver_result['output_path']}")
        
        # STAGE 4: Data Quality - Validate Silver data BEFORE Gold
        print_stage("4/6 - QUALITY: Validate Silver data quality", "✅")
        
        quality_result = check_data_quality(
            input_path=str(silver_path),
            layer='silver'
        )
        
        results['quality'] = quality_result
        print(f"✅ Quality check complete!")
        print(f"   • Status: {quality_result['status']}")
        print(f"   • Total validated records: {quality_result['total_records']}")
        print(f"   • Checks performed: {quality_result['checks_performed']}")
        print(f"   • Checks passed: {quality_result['checks_passed']}")
        print(f"   • Success rate: {quality_result['success_rate']:.1f}%")
        
        if quality_result['issues']:
            print(f"\n   ⚠️  Issues found:")
            for issue in quality_result['issues']:
                print(f"      • {issue}")
        
        # Stop pipeline if quality check failed
        if quality_result['status'] == 'FAILED':
            print(f"\n❌ PIPELINE STOPPED: Data quality check failed!")
            print(f"   Critical failures: {quality_result['critical_failures']}")
            print(f"   Please fix data quality issues before proceeding to Gold layer.")
            logger.error("Pipeline stopped due to data quality failures")
            return 1
        
        # STAGE 5: Gold - Create aggregations
        print_stage("5/6 - GOLD: Create aggregations", "🥇")
        
        gold_result = create_gold_aggregations(
            input_path=str(silver_path),
            output_path=str(gold_path)
        )
        
        results['gold'] = gold_result
        print(f"✅ Gold layer complete!")
        print(f"   • Source records: {gold_result['source_records']}")
        print(f"   • Aggregated rows: {gold_result['aggregated_rows']}")
        print(f"   • Generated files:")
        print(f"      - Parquet: {Path(gold_result['output_files']['parquet']).name}")
        print(f"      - CSV: {Path(gold_result['output_files']['csv']).name}")
        print(f"      - JSON: {Path(gold_result['output_files']['summary']).name}")
        
        # STAGE 6: Final Summary
        print_stage("6/6 - SUMMARY: Pipeline completed", "🎉")
        
        # SUMMARY
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        print_separator('=')
        print("🎉 PIPELINE EXECUTED SUCCESSFULLY!")
        print_separator('=')
        print(f"⏰ Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        print_separator('-')
        
        print("\n📊 EXECUTION SUMMARY:\n")
        print(f"   1️⃣  EXTRACT:  {results['extract']['records_extracted']:,} records extracted")
        print(f"   2️⃣  BRONZE:   {results['bronze']['total_records']:,} records saved")
        print(f"   3️⃣  SILVER:   {results['silver']['total_records']:,} records cleaned")
        print(f"   4️⃣  QUALITY:  {results['quality']['success_rate']:.1f}% quality (Status: {results['quality']['status']})")
        print(f"   5️⃣  GOLD:     {results['gold']['aggregated_rows']:,} rows aggregated")
        
        print("\n📁 DATA STRUCTURE CREATED:\n")
        print(f"   📂 data/")
        print(f"   ├── 📂 raw/{execution_date}/")
        print(f"   ├── 📂 bronze/breweries/{execution_date}/")
        print(f"   ├── 📂 silver/breweries/ (partitioned by country/state)")
        print(f"   └── 📂 gold/breweries_by_type_location/")
        
        print("\n🔍 NEXT STEPS:\n")
        print("   • Execute: python check_medallion_structure.py")
        print("   • View the data in the directory: data/")
        print("   • Check the guide: MEDALLION_GUIDE.md")
        
        print_separator('=')
        
        # Save summary
        import json
        summary_file = base_path / f'pipeline_summary_{execution_date}.json'
        # Convert numpy/pandas types to JSON-serializable Python types
        def convert_to_serializable(obj):
            """Recursively convert non-JSON-serializable types."""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return int(obj) if isinstance(obj, np.integer) else float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        summary = {
            'execution_date': execution_date,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': total_duration,
            'status': 'SUCCESS',
            'stages': convert_to_serializable(results)
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Execution summary saved in: {summary_file}")
        
        return 0
        
    except Exception as e:
        print_separator('=')
        print(f"❌ PIPELINE EXECUTION ERROR!")
        print_separator('=')
        print(f"Error: {str(e)}")
        logger.exception("Error during pipeline execution")
        
        # Save error
        import json
        error_file = base_path / f'pipeline_error_{execution_date}.json'
        error_info = {
            'execution_date': execution_date,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, indent=2, ensure_ascii=False)
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
