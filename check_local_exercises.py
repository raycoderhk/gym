"""Quick script to check local SQLite exercises and help get user_id"""

import sqlite3
import os
import sys

DB_PATH = os.path.join('data', 'gym_tracker.db')

print("="*60)
print("Local SQLite Exercise Checker")
print("="*60)

if not os.path.exists(DB_PATH):
    print(f"\n❌ SQLite database not found at: {DB_PATH}")
    sys.exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if exercises table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'")
    if not cursor.fetchone():
        print("\n❌ 'exercises' table not found in database")
        conn.close()
        sys.exit(1)
    
    cursor.execute("SELECT name, muscle_group, exercise_type FROM exercises ORDER BY name")
    exercises = cursor.fetchall()
    
    print(f"\n✅ Found {len(exercises)} exercises in local SQLite database:\n")
    for i, ex in enumerate(exercises, 1):
        print(f"  {i}. {ex[0]} ({ex[1]}, {ex[2]})")
    
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
    
    print("\nOption 3 - From App (if logged in):")
    print("  1. Log in to your deployed app")
    print("  2. Open browser DevTools (F12) -> Console")
    print("  3. The user ID should be visible in the app sidebar")
    
    print("\n" + "="*60)
    print("🚀 Import Command:")
    print("="*60)
    print("\nOnce you have your user_id, run:")
    print("  python database/migrate_sqlite_to_supabase.py <your_user_id>")
    print("\nOr test first with dry-run:")
    print("  python database/migrate_sqlite_to_supabase.py <your_user_id> --dry-run")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

