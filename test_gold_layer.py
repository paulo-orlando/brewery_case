"""
Test script for the Gold layer.
Tests reading Silver data and creating aggregations.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gold.gold_layer import create_gold_aggregations

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def main():
    print_header("🥇 GOLD LAYER TEST")
    
    # Paths
    base_path = Path(__file__).parent / 'data'
    silver_path = base_path / 'silver' / 'breweries'
    gold_path = base_path / 'gold' / 'breweries_by_type_location'
    
    # Check if Silver exists
    if not silver_path.exists():
        print("❌ Silver layer not found!")
        print(f"   Expected path: {silver_path}")
        print("\n💡 Run first: python run_pipeline_standalone.py")
        return 1
    
    print(f"📂 Silver Layer: {silver_path}")
    print(f"📂 Gold Layer (target): {gold_path}")
    
    # Count Parquet files
    parquet_files = list(silver_path.rglob('*.parquet'))
    print(f"📄 Parquet files found: {len(parquet_files)}")
    
    if len(parquet_files) == 0:
        print("\n❌ No Parquet files found in Silver layer!")
        return 1
    
    # Create output directory
    gold_path.mkdir(parents=True, exist_ok=True)
    
    # Execute aggregation
    print("\n🔄 Executing Gold aggregation...")
    print("-" * 80)
    
    start_time = datetime.now()
    
    try:
        result = create_gold_aggregations(
            input_path=str(silver_path),
            output_path=str(gold_path)
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_header("✅ AGGREGATION COMPLETED SUCCESSFULLY!")
        
        print(f"⏱️  Execution time: {duration:.2f} seconds")
        print(f"📊 Source records: {result['source_records']:,}")
        print(f"📊 Aggregated rows: {result['aggregated_rows']:,}")
        
        print("\n📁 Generated files:")
        for file_type, file_path in result['output_files'].items():
            file_size = Path(file_path).stat().st_size / 1024
            print(f"   • {file_type.upper()}: {Path(file_path).name} ({file_size:.2f} KB)")
        
        # Show summary statistics
        print("\n📈 General Statistics:")
        summary = result['summary']
        print(f"   • Total breweries: {summary['total_breweries']:,}")
        print(f"   • Unique countries: {summary['unique_countries']}")
        print(f"   • Unique states: {summary['unique_states']}")
        print(f"   • Unique cities: {summary['unique_cities']}")
        
        print("\n🍺 Brewery Types:")
        for brew_type, count in list(summary['brewery_types'].items())[:5]:
            print(f"   • {brew_type}: {count:,}")
        
        print("\n🏆 Top 5 States:")
        for state, count in list(summary['top_10_states'].items())[:5]:
            print(f"   • {state}: {count:,} breweries")
        
        print("\n✅ Data Quality:")
        dq = summary['data_quality']
        print(f"   • With coordinates: {dq['pct_with_coordinates']:.1f}%")
        print(f"   • With complete address: {dq['pct_with_complete_address']:.1f}%")
        
        # Read and show aggregation preview
        print("\n📊 Aggregation Preview (Top 10 combinations):")
        print("-" * 80)
        
        import pandas as pd
        df_agg = pd.read_parquet(result['output_files']['parquet'])
        
        top_10 = df_agg.nlargest(10, 'brewery_count')
        
        print(top_10[['country', 'state', 'brewery_type', 'brewery_count', 
                      'unique_cities', 'pct_with_coordinates']].to_string(index=False))
        
        print_header("🎉 TEST COMPLETED!")
        
        return 0
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_header("❌ AGGREGATION ERROR!")
        
        print(f"⏱️  Time until error: {duration:.2f} seconds")
        print(f"❌ Error: {str(e)}")
        print(f"\n💡 Error type: {type(e).__name__}")
        
        import traceback
        print("\n📋 Traceback completo:")
        print("-" * 80)
        traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
