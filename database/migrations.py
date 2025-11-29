"""
Migration script to import data from CSV to Supabase
Reads from CSV file and imports to Supabase with a hardcoded user_id
"""

import pandas as pd
import sys
from database.db_manager import import_workout_from_csv

def migrate_from_csv(csv_file_path: str, user_id: str):
    """
    Migrate workout data from CSV to Supabase
    
    Args:
        csv_file_path: Path to the CSV file
        user_id: UUID of the user to import data for
    """
    print(f"Reading CSV file: {csv_file_path}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file_path)
        print(f"Found {len(df)} rows in CSV")
        
        # Import data
        print("Starting import...")
        success_count, error_count, error_messages = import_workout_from_csv(user_id, df)
        
        # Display results
        print(f"\n{'='*50}")
        print(f"Import completed!")
        print(f"✅ Success: {success_count} rows")
        print(f"❌ Errors: {error_count} rows")
        print(f"{'='*50}\n")
        
        if error_messages:
            print("Error details:")
            for msg in error_messages[:20]:  # Show first 20 errors
                print(f"  - {msg}")
            if len(error_messages) > 20:
                print(f"  ... and {len(error_messages) - 20} more errors")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return 0, 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python migrations.py <csv_file_path> <user_id>")
        print("Example: python migrations.py my_gym_history.csv 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    user_uuid = sys.argv[2]
    
    migrate_from_csv(csv_path, user_uuid)

