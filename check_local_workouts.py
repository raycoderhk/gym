"""Quick script to check local SQLite workout logs and help get user_id"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join('data', 'gym_tracker.db')

print("="*60)
print("Local SQLite Workout Logs Checker")
print("="*60)

if not os.path.exists(DB_PATH):
    print(f"\n❌ SQLite database not found at: {DB_PATH}")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if workout_logs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workout_logs'")
    if not cursor.fetchone():
        print("\n❌ 'workout_logs' table not found in database")
        conn.close()
        exit(1)
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM workout_logs")
    total_count = cursor.fetchone()[0]
    
    # Get date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM workout_logs")
    date_range = cursor.fetchone()
    
    # Get unique exercises
    cursor.execute("SELECT COUNT(DISTINCT exercise_name) FROM workout_logs")
    unique_exercises = cursor.fetchone()[0]
    
    # Get unique dates
    cursor.execute("SELECT COUNT(DISTINCT date) FROM workout_logs")
    unique_dates = cursor.fetchone()[0]
    
    print(f"\n✅ Found {total_count} workout log entries")
    print(f"   - Date range: {date_range[0]} to {date_range[1]}")
    print(f"   - Unique exercises: {unique_exercises}")
    print(f"   - Unique workout dates: {unique_dates}")
    
    # Get exercise breakdown
    cursor.execute("""
        SELECT exercise_name, COUNT(*) as count
        FROM workout_logs
        GROUP BY exercise_name
        ORDER BY count DESC
        LIMIT 10
    """)
    top_exercises = cursor.fetchall()
    
    print(f"\n   Top exercises by entry count:")
    for ex, count in top_exercises:
        print(f"     - {ex}: {count} entries")
    
    print("\n" + "="*60)
    print("📋 Next Steps: Get Your User ID and Import")
    print("="*60)
    print("\nTo find your user_id (UUID) for raymondcuhk@gmail.com:")
    print("\nOption 1 - Supabase Dashboard:")
    print("  1. Go to https://supabase.com/dashboard")
    print("  2. Select your project")
    print("  3. Go to Authentication -> Users")
    print("  4. Find raymondcuhk@gmail.com")
    print("  5. Copy the UUID (looks like: 123e4567-e89b-12d3-a456-426614174000)")
    
    print("\nOption 2 - SQL Query:")
    print("  1. Go to Supabase Dashboard -> SQL Editor")
    print("  2. Run: SELECT id, email FROM auth.users WHERE email = 'raymondcuhk@gmail.com';")
    print("  3. Copy the 'id' value")
    
    print("\n" + "="*60)
    print("🚀 Import Command:")
    print("="*60)
    print("\nOnce you have your user_id, run:")
    print("  python database/migrate_workouts_to_supabase.py <your_user_id>")
    print("\nOr test first with dry-run:")
    print("  python database/migrate_workouts_to_supabase.py <your_user_id> --dry-run")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

