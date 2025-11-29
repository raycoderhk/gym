"""
Migration script to import workout logs from local SQLite to Supabase
Reads workout_logs from local SQLite database and imports to Supabase for a specific user
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import date
import requests
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import get_supabase, save_workout
from src.auth import get_supabase_client

load_dotenv()

# Local SQLite database path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'gym_tracker.db')


def get_sqlite_connection():
    """Get SQLite database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"SQLite database not found at: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def get_workout_logs_from_sqlite():
    """Get all workout logs from SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT date, exercise_name, set_order, weight, unit, reps, rpe, notes
            FROM workout_logs
            ORDER BY date, exercise_name, set_order
        """)
        
        results = cursor.fetchall()
        workout_logs = []
        for row in results:
            workout_logs.append({
                'date': row[0],
                'exercise_name': row[1],
                'set_order': row[2],
                'weight': row[3],
                'unit': row[4],
                'reps': row[5],
                'rpe': row[6],
                'notes': row[7]
            })
        return workout_logs
    finally:
        conn.close()


def group_workouts_by_session(workout_logs):
    """
    Group workout logs by date and exercise to form workout sessions
    Returns a list of sessions, each containing multiple sets
    """
    sessions = {}
    
    for log in workout_logs:
        # Use date and exercise_name as session key
        session_key = (log['date'], log['exercise_name'])
        
        if session_key not in sessions:
            sessions[session_key] = {
                'date': log['date'],
                'exercise_name': log['exercise_name'],
                'sets': [],
                'rpe': log['rpe'],
                'notes': log['notes']
            }
        
        # Add set to session
        sessions[session_key]['sets'].append({
            'set_order': log['set_order'],
            'weight': log['weight'],
            'unit': log['unit'],
            'reps': log['reps']
        })
    
    return list(sessions.values())


def get_user_id_from_email(email: str) -> str:
    """
    Get user UUID from email address by querying Supabase auth.users
    Tries multiple methods to retrieve user_id
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        print(f"   Looking up user_id for: {email}")
        
        # Method 1: Try using Supabase Admin API (requires service role key)
        if service_role_key:
            try:
                response = requests.get(
                    f"{supabase_url}/auth/v1/admin/users",
                    headers={
                        "apikey": service_role_key,
                        "Authorization": f"Bearer {service_role_key}",
                        "Content-Type": "application/json"
                    },
                    params={"page": 1, "per_page": 1000}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('users', [])
                    for user in users:
                        if user.get('email', '').lower() == email.lower():
                            user_id = user.get('id')
                            print(f"   ✅ Found user_id via Admin API: {user_id}")
                            return user_id
            except Exception as e:
                print(f"   ⚠️  Admin API method failed: {e}")
        
        # Method 2: Try RPC call to get_user_id_by_email function
        # (Requires running create_user_lookup_function.sql first)
        try:
            supabase = get_supabase_client()
            result = supabase.rpc('get_user_id_by_email', {'user_email': email}).execute()
            if result.data and len(result.data) > 0:
                user_id = result.data[0].get('id')
                if user_id:
                    print(f"   ✅ Found user_id via RPC function: {user_id}")
                    return user_id
        except Exception as e:
            # Function might not exist yet - that's OK, we'll try other methods
            pass
        
        # If all automatic methods fail, provide helpful instructions
        print(f"   ⚠️  Could not automatically retrieve user_id")
        print(f"   ")
        print(f"   To enable automatic lookup:")
        print(f"   1. Run database/create_user_lookup_function.sql in Supabase SQL Editor")
        print(f"   2. Or add SUPABASE_SERVICE_ROLE_KEY to your .env file")
        print(f"   ")
        print(f"   Or manually get user_id:")
        print(f"   SELECT id, email FROM auth.users WHERE email = '{email}';")
        print(f"   Then run: --user-id <the_id>")
        return None
        
    except Exception as e:
        print(f"   ❌ Error getting user_id: {e}")
        import traceback
        traceback.print_exc()
        return None


def migrate_workouts_to_supabase(user_id: str = None, email: str = None, dry_run: bool = False):
    """
    Migrate workout logs from SQLite to Supabase
    
    Args:
        user_id: UUID of the user in Supabase
        dry_run: If True, only show what would be imported without actually importing
    """
    print("=" * 60)
    print("Workout Logs Migration: SQLite → Supabase")
    print("=" * 60)
    
    # Get user_id if email provided
    if not user_id and email:
        print(f"\n0. Looking up user_id for email: {email}")
        user_id = get_user_id_from_email(email)
        if not user_id:
            print(f"\n❌ Could not find user_id for {email}")
            print(f"   Please provide user_id manually or check Supabase Dashboard")
            return
    
    if not user_id:
        print(f"\n❌ user_id is required")
        return
    
    print(f"\n   Using user_id: {user_id}")
    
    # Get workout logs from SQLite
    print(f"\n1. Reading workout logs from SQLite database...")
    print(f"   Database path: {DB_PATH}")
    
    try:
        sqlite_logs = get_workout_logs_from_sqlite()
        print(f"   ✅ Found {len(sqlite_logs)} workout log entries in SQLite")
    except FileNotFoundError as e:
        print(f"   ❌ Error: {e}")
        return
    except Exception as e:
        print(f"   ❌ Error reading SQLite: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not sqlite_logs:
        print("   ⚠️  No workout logs found in SQLite database")
        return
    
    # Group into sessions
    print(f"\n2. Grouping workout logs into sessions...")
    sessions = group_workouts_by_session(sqlite_logs)
    print(f"   ✅ Found {len(sessions)} workout sessions")
    
    # Display summary
    print(f"\n3. Workout sessions summary:")
    exercise_counts = {}
    date_range = {'min': None, 'max': None}
    
    for session in sessions:
        ex_name = session['exercise_name']
        exercise_counts[ex_name] = exercise_counts.get(ex_name, 0) + 1
        
        session_date = session['date']
        if isinstance(session_date, str):
            session_date = date.fromisoformat(session_date)
        
        if date_range['min'] is None or session_date < date_range['min']:
            date_range['min'] = session_date
        if date_range['max'] is None or session_date > date_range['max']:
            date_range['max'] = session_date
    
    print(f"   - Date range: {date_range['min']} to {date_range['max']}")
    print(f"   - Unique exercises: {len(exercise_counts)}")
    print(f"   - Total sessions: {len(sessions)}")
    
    # Show first few sessions as preview
    print(f"\n   Preview (first 5 sessions):")
    for i, session in enumerate(sessions[:5], 1):
        print(f"     {i}. {session['date']} - {session['exercise_name']} ({len(session['sets'])} sets)")
    
    if len(sessions) > 5:
        print(f"     ... and {len(sessions) - 5} more sessions")
    
    # Check Supabase connection
    print(f"\n4. Checking Supabase connection...")
    try:
        supabase = get_supabase()
        print(f"   ✅ Connected to Supabase")
    except Exception as e:
        print(f"   ❌ Error connecting to Supabase: {e}")
        print(f"   Make sure SUPABASE_URL and SUPABASE_KEY are set in environment variables")
        return
    
    # Dry run mode
    if dry_run:
        print(f"\n5. DRY RUN MODE - No changes will be made")
        print(f"   Would import {len(sessions)} workout sessions")
        print(f"   Total sets: {sum(len(s['sets']) for s in sessions)}")
        return
    
    # Import workouts
    print(f"\n5. Importing workout sessions to Supabase...")
    success_count = 0
    error_count = 0
    errors = []
    
    for i, session in enumerate(sessions, 1):
        try:
            # Parse date
            session_date = session['date']
            if isinstance(session_date, str):
                session_date = date.fromisoformat(session_date)
            elif hasattr(session_date, 'date'):
                session_date = session_date.date()
            
            # Prepare sets data
            sets_data = []
            for set_info in session['sets']:
                sets_data.append({
                    'set_order': set_info['set_order'],
                    'weight': float(set_info['weight']),
                    'unit': set_info['unit'],
                    'reps': int(set_info['reps'])
                })
            
            # Save workout session
            save_workout(
                user_id=user_id,
                workout_date=session_date,
                exercise_name=session['exercise_name'],
                sets=sets_data,
                rpe=session.get('rpe'),
                notes=session.get('notes')
            )
            
            success_count += 1
            if i % 10 == 0 or i == len(sessions):
                print(f"   Progress: {i}/{len(sessions)} sessions imported...")
            
        except Exception as e:
            error_count += 1
            error_msg = f"Error importing session {i} ({session['date']} - {session['exercise_name']}): {str(e)}"
            errors.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Migration Summary:")
    print(f"  ✅ Successfully imported: {success_count} workout sessions")
    print(f"  ❌ Failed: {error_count} sessions")
    print(f"  📊 Total sets imported: {sum(len(s['sets']) for s in sessions[:success_count])}")
    print(f"{'=' * 60}")
    
    if errors:
        print(f"\nErrors (showing first 10):")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


if __name__ == "__main__":
    print("Workout Logs Migration Tool: SQLite → Supabase")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python migrate_workouts_to_supabase.py <user_id> [--dry-run]")
        print("  python migrate_workouts_to_supabase.py --email <email> [--dry-run]")
        print("\nExample:")
        print("  python migrate_workouts_to_supabase.py 123e4567-e89b-12d3-a456-426614174000")
        print("  python migrate_workouts_to_supabase.py --email raymondcuhk@gmail.com")
        print("  python migrate_workouts_to_supabase.py --email raymondcuhk@gmail.com --dry-run")
        print("\nNote: For --email to work automatically, run:")
        print("  database/create_user_lookup_function.sql in Supabase SQL Editor first")
        sys.exit(1)
    
    user_id = None
    email = None
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    # Parse arguments
    if "--email" in sys.argv or "--user-id" in sys.argv:
        if "--email" in sys.argv:
            email_idx = sys.argv.index("--email")
            if email_idx + 1 < len(sys.argv):
                email = sys.argv[email_idx + 1]
            else:
                print("❌ Error: --email requires an email address")
                sys.exit(1)
        elif "--user-id" in sys.argv:
            user_id_idx = sys.argv.index("--user-id")
            if user_id_idx + 1 < len(sys.argv):
                user_id = sys.argv[user_id_idx + 1]
            else:
                print("❌ Error: --user-id requires a UUID")
                sys.exit(1)
    else:
        # First argument is user_id (backward compatibility)
        user_id = sys.argv[1]
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    
    migrate_workouts_to_supabase(user_id=user_id, email=email, dry_run=dry_run)

