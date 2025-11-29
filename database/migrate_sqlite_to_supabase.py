"""
Migration script to import exercise records from local SQLite to Supabase
Reads exercises from local SQLite database and imports to Supabase for a specific user
"""

import sqlite3
import os
import sys
from pathlib import Path
from database.db_manager import get_supabase, add_custom_exercise, get_all_exercises

# Local SQLite database path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'gym_tracker.db')


def get_sqlite_connection():
    """Get SQLite database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"SQLite database not found at: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def get_exercises_from_sqlite():
    """Get all exercises from SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name, muscle_group, exercise_type
            FROM exercises
            ORDER BY name
        """)
        
        results = cursor.fetchall()
        exercises = [
            {
                'name': row[0],
                'muscle_group': row[1],
                'exercise_type': row[2]
            }
            for row in results
        ]
        return exercises
    finally:
        conn.close()


def migrate_exercises_to_supabase(user_id: str, dry_run: bool = False):
    """
    Migrate exercises from SQLite to Supabase
    
    Args:
        user_id: UUID of the user in Supabase
        dry_run: If True, only show what would be imported without actually importing
    """
    print("=" * 60)
    print("Exercise Migration: SQLite → Supabase")
    print("=" * 60)
    
    # Get exercises from SQLite
    print(f"\n1. Reading exercises from SQLite database...")
    print(f"   Database path: {DB_PATH}")
    
    try:
        sqlite_exercises = get_exercises_from_sqlite()
        print(f"   ✅ Found {len(sqlite_exercises)} exercises in SQLite")
    except FileNotFoundError as e:
        print(f"   ❌ Error: {e}")
        return
    except Exception as e:
        print(f"   ❌ Error reading SQLite: {e}")
        return
    
    if not sqlite_exercises:
        print("   ⚠️  No exercises found in SQLite database")
        return
    
    # Display exercises to be imported
    print(f"\n2. Exercises to import:")
    for i, ex in enumerate(sqlite_exercises, 1):
        print(f"   {i}. {ex['name']} ({ex['muscle_group']}, {ex['exercise_type']})")
    
    # Get existing exercises in Supabase
    print(f"\n3. Checking existing exercises in Supabase...")
    try:
        supabase = get_supabase()
        existing_exercises = get_all_exercises(user_id)
        existing_names = {ex['name'] for ex in existing_exercises}
        print(f"   ✅ Found {len(existing_exercises)} existing exercises in Supabase")
    except Exception as e:
        print(f"   ❌ Error connecting to Supabase: {e}")
        print(f"   Make sure SUPABASE_URL and SUPABASE_KEY are set in environment variables")
        return
    
    # Filter out exercises that already exist
    new_exercises = [ex for ex in sqlite_exercises if ex['name'] not in existing_names]
    duplicate_exercises = [ex for ex in sqlite_exercises if ex['name'] in existing_names]
    
    print(f"\n4. Analysis:")
    print(f"   - New exercises to import: {len(new_exercises)}")
    print(f"   - Duplicate exercises (will skip): {len(duplicate_exercises)}")
    
    if duplicate_exercises:
        print(f"\n   Duplicate exercises (already exist in Supabase):")
        for ex in duplicate_exercises:
            print(f"     - {ex['name']}")
    
    if not new_exercises:
        print("\n   ✅ All exercises already exist in Supabase. Nothing to import.")
        return
    
    # Dry run mode
    if dry_run:
        print(f"\n5. DRY RUN MODE - No changes will be made")
        print(f"   Would import {len(new_exercises)} exercises:")
        for ex in new_exercises:
            print(f"     - {ex['name']} ({ex['muscle_group']}, {ex['exercise_type']})")
        return
    
    # Import exercises
    print(f"\n5. Importing exercises to Supabase...")
    success_count = 0
    error_count = 0
    errors = []
    
    for ex in new_exercises:
        try:
            success = add_custom_exercise(user_id, ex['name'], ex['muscle_group'], ex['exercise_type'])
            if success:
                success_count += 1
                print(f"   ✅ Imported: {ex['name']}")
            else:
                error_count += 1
                error_msg = f"Failed to import {ex['name']} (may already exist)"
                errors.append(error_msg)
                print(f"   ⚠️  {error_msg}")
        except Exception as e:
            error_count += 1
            error_msg = f"Error importing {ex['name']}: {str(e)}"
            errors.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Migration Summary:")
    print(f"  ✅ Successfully imported: {success_count} exercises")
    print(f"  ❌ Failed: {error_count} exercises")
    print(f"  ⏭️  Skipped (duplicates): {len(duplicate_exercises)} exercises")
    print(f"{'=' * 60}")
    
    if errors:
        print(f"\nErrors:")
        for error in errors:
            print(f"  - {error}")


def get_user_id_from_email(email: str):
    """
    Get user UUID from email address
    Note: This requires the user to be logged in or provide their UUID directly
    """
    print(f"\n⚠️  Note: You need to provide your user UUID.")
    print(f"   To find your UUID:")
    print(f"   1. Log in to your Supabase app")
    print(f"   2. Check the browser console or network tab for your user ID")
    print(f"   3. Or check Supabase Dashboard -> Authentication -> Users")
    print(f"   4. Or use: SELECT id FROM auth.users WHERE email = '{email}';")
    return None


if __name__ == "__main__":
    print("Exercise Migration Tool: SQLite → Supabase")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python migrate_sqlite_to_supabase.py <user_id> [--dry-run]")
        print("\nExample:")
        print("  python migrate_sqlite_to_supabase.py 123e4567-e89b-12d3-a456-426614174000")
        print("  python migrate_sqlite_to_supabase.py 123e4567-e89b-12d3-a456-426614174000 --dry-run")
        print("\nTo find your user_id:")
        print("  1. Log in to your app")
        print("  2. Check Supabase Dashboard -> Authentication -> Users")
        print("  3. Or run SQL: SELECT id FROM auth.users WHERE email = 'raymondcuhk@gmail.com';")
        sys.exit(1)
    
    user_id = sys.argv[1]
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    
    migrate_exercises_to_supabase(user_id, dry_run=dry_run)

