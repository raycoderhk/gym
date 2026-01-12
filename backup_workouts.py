"""
Backup Export Script for Gym Tracker
Exports all workout records and exercises to CSV files for regular backups.

Usage:
    python backup_workouts.py [user_id]
    
If user_id is not provided, the script will auto-detect from the database.
"""

import os
import sys
from datetime import date
from typing import Optional, List, Dict

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions

load_dotenv()


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client (standalone version without Streamlit).
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    # Use public schema (Supabase PostgREST default)
    options = ClientOptions(schema="public")
    return create_client(supabase_url, supabase_key, options=options)


def get_user_id() -> Optional[str]:
    """
    Get user_id from environment variable, command-line argument, or auto-detect from database.
    Priority: USER_ID env var > command-line arg > auto-detect
    
    Returns:
        user_id string or None if not found
    """
    # Check environment variable first (for GitHub Actions)
    user_id = os.getenv("USER_ID")
    if user_id:
        print(f"Using user_id from environment variable: {user_id}\n")
        return user_id
    
    # Check command-line argument
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        print(f"Using user_id from command line: {user_id}\n")
        return user_id
    
    # Auto-detect from database
    try:
        supabase = get_supabase_client()
        result = supabase.table("exercises").select("user_id").limit(1).execute()
        if not result.data:
            print("❌ No users found in database")
            return None
        user_id = result.data[0]["user_id"]
        print(f"Auto-detected user_id: {user_id}\n")
        return user_id
    except Exception as e:
        print(f"❌ Error detecting user_id: {e}")
        return None


def get_all_workouts(user_id: str) -> pd.DataFrame:
    """
    Get all workout logs for a user (standalone version).
    
    Args:
        user_id: User UUID
        
    Returns:
        DataFrame with all workouts
    """
    supabase = get_supabase_client()
    
    result = supabase.table("workout_logs")\
        .select("date, exercise_name, set_order, weight, unit, reps, rpe, notes")\
        .eq("user_id", user_id)\
        .order("date", desc=True)\
        .order("exercise_name")\
        .order("set_order")\
        .execute()
    
    if result.data:
        df = pd.DataFrame(result.data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame(columns=['date', 'exercise_name', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes'])


def get_all_exercises(user_id: str) -> List[Dict]:
    """
    Get all exercises for a user (standalone version).
    
    Args:
        user_id: User UUID
        
    Returns:
        List of exercise dictionaries
    """
    supabase = get_supabase_client()
    
    try:
        # Try to select with execution_steps (if column exists)
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type, execution_steps, created_at")\
            .eq("user_id", user_id)\
            .order("muscle_group")\
            .order("name")\
            .execute()
    except Exception:
        # Fallback: select without execution_steps if column doesn't exist yet
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type, created_at")\
            .eq("user_id", user_id)\
            .order("muscle_group")\
            .order("name")\
            .execute()
        # Add None for execution_steps to maintain consistent structure
        if result.data:
            for row in result.data:
                row['execution_steps'] = None
    
    return result.data if result.data else []


def export_workouts_to_csv(user_id: str, output_file: str) -> int:
    """
    Export all workout logs to CSV.
    
    Args:
        user_id: User UUID
        output_file: Output CSV file path
        
    Returns:
        Number of rows exported
    """
    try:
        workouts_df = get_all_workouts(user_id)
        
        if workouts_df.empty:
            print("⚠️  No workout records found")
            # Create empty CSV with correct columns
            empty_df = pd.DataFrame(columns=[
                'date', 'exercise_name', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes'
            ])
            empty_df.to_csv(output_file, index=False)
            return 0
        
        # Convert date to ISO format string for CSV
        workouts_df['date'] = workouts_df['date'].apply(lambda d: d.isoformat() if isinstance(d, date) else str(d))
        
        # Reorder columns for better readability
        column_order = ['date', 'exercise_name', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes']
        workouts_df = workouts_df[column_order]
        
        workouts_df.to_csv(output_file, index=False)
        return len(workouts_df)
    except Exception as e:
        print(f"❌ Error exporting workouts: {e}")
        raise


def export_exercises_to_csv(user_id: str, output_file: str) -> int:
    """
    Export all exercises to CSV.
    
    Args:
        user_id: User UUID
        output_file: Output CSV file path
        
    Returns:
        Number of rows exported
    """
    try:
        exercises = get_all_exercises(user_id)
        
        if not exercises:
            print("⚠️  No exercises found")
            # Create empty CSV with correct columns
            empty_df = pd.DataFrame(columns=[
                'name', 'muscle_group', 'exercise_type', 'execution_steps', 'created_at'
            ])
            empty_df.to_csv(output_file, index=False)
            return 0
        
        # Convert to DataFrame
        exercises_df = pd.DataFrame(exercises)
        
        # Select and reorder columns (exclude 'id' as it's database-specific)
        column_order = ['name', 'muscle_group', 'exercise_type', 'execution_steps']
        if 'created_at' in exercises_df.columns:
            column_order.append('created_at')
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in exercises_df.columns]
        exercises_df = exercises_df[available_columns]
        
        exercises_df.to_csv(output_file, index=False)
        return len(exercises_df)
    except Exception as e:
        print(f"❌ Error exporting exercises: {e}")
        raise


def main():
    """Main backup export function."""
    print("=" * 70)
    print("🏋️  Gym Tracker - Backup Export")
    print("=" * 70)
    print()
    
    # Get user_id
    user_id = get_user_id()
    if not user_id:
        print("❌ Cannot proceed without user_id")
        sys.exit(1)
    
    # Generate date-based filenames
    today = date.today()
    date_str = today.isoformat()
    workouts_file = f"workouts_{date_str}.csv"
    exercises_file = f"exercises_{date_str}.csv"
    
    print(f"📅 Backup date: {date_str}")
    print(f"📁 Output directory: {os.getcwd()}")
    print()
    
    # Export workouts
    print("📊 Exporting workout records...")
    try:
        workout_count = export_workouts_to_csv(user_id, workouts_file)
        print(f"✅ Exported {workout_count} workout records to '{workouts_file}'")
    except Exception as e:
        print(f"❌ Failed to export workouts: {e}")
        sys.exit(1)
    
    print()
    
    # Export exercises
    print("📚 Exporting exercise library...")
    try:
        exercise_count = export_exercises_to_csv(user_id, exercises_file)
        print(f"✅ Exported {exercise_count} exercises to '{exercises_file}'")
    except Exception as e:
        print(f"❌ Failed to export exercises: {e}")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("✅ Backup completed successfully!")
    print("=" * 70)
    print(f"\n📄 Files created:")
    print(f"   - {workouts_file} ({workout_count} records)")
    print(f"   - {exercises_file} ({exercise_count} records)")
    print(f"\n💾 Backup location: {os.path.abspath('.')}")


if __name__ == "__main__":
    main()
