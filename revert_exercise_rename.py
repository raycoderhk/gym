"""
Script to revert accidental exercise renames
Usage: python revert_exercise_rename.py <user_id_or_email> <from_exercise> <to_exercise> [date1] [date2] ...
If no dates provided, will revert ALL workouts for that exercise
Accepts either user_id (UUID) or email address
"""

import os
import sys
import requests
from pathlib import Path
from datetime import date, datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_manager import (
    get_supabase, get_exercise_history, rename_workout_sessions,
    get_workout_sessions_by_exercise
)
from src.auth import get_supabase_client

load_dotenv()


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
        raise ValueError(
            f"Could not automatically retrieve user_id for email: {email}\n"
            f"To enable automatic lookup:\n"
            f"  1. Add SUPABASE_SERVICE_ROLE_KEY to your .env file, OR\n"
            f"  2. Run database/create_user_lookup_function.sql in Supabase SQL Editor\n"
            f"Or manually get user_id from Supabase dashboard and use UUID instead."
        )
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error getting user_id from email: {e}")


def get_user_id(user_input: str) -> str:
    """
    Get user_id from either email or UUID
    Returns the user_id (UUID)
    """
    # Check if it's a UUID (contains hyphens and is 36 chars)
    if len(user_input) == 36 and user_input.count('-') == 4:
        # Looks like a UUID, return as-is
        return user_input
    else:
        # Assume it's an email, try to get user_id
        return get_user_id_from_email(user_input)


def get_workout_dates_for_exercise(user_id: str, exercise_name: str):
    """Get all unique dates for an exercise"""
    sessions = get_workout_sessions_by_exercise(user_id, exercise_name)
    dates = []
    for session in sessions:
        session_date = session['date']
        if isinstance(session_date, str):
            session_date = datetime.fromisoformat(session_date).date()
        dates.append(session_date)
    return sorted(dates, reverse=True)


def main():
    if len(sys.argv) < 4:
        print("Usage: python revert_exercise_rename.py <user_id_or_email> <from_exercise> <to_exercise> [date1] [date2] ...")
        print("\nExample:")
        print('  python revert_exercise_rename.py user@example.com "Assisted Pull-up" "Triceps Pushdown (Lat Pulldown machine)"')
        print('  python revert_exercise_rename.py <uuid> "Assisted Pull-up" "Triceps Pushdown (Lat Pulldown machine)" "2025-12-05" "2025-12-04"')
        print("\nAccepts either email address or user_id (UUID)")
        print("If no dates provided, will show all dates and ask for confirmation before reverting ALL.")
        sys.exit(1)
    
    user_input = sys.argv[1]
    from_exercise = sys.argv[2]  # Current name (e.g., "Assisted Pull-up")
    to_exercise = sys.argv[3]    # Original name (e.g., "Triceps Pushdown (Lat Pulldown machine)")
    
    # Get user_id from email or UUID
    try:
        user_id = get_user_id(user_input)
        if user_input != user_id:
            print(f"Found user_id for email: {user_input}")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease provide either:")
        print("  - Email address (if SUPABASE_SERVICE_ROLE_KEY is set)")
        print("  - User ID (UUID)")
        sys.exit(1)
    
    # Get dates if provided
    dates = None
    if len(sys.argv) > 4:
        dates = []
        for date_str in sys.argv[4:]:
            try:
                d = datetime.fromisoformat(date_str).date()
                dates.append(d)
            except ValueError:
                print(f"Warning: Invalid date format '{date_str}', skipping")
    
    print("=" * 70)
    print("Revert Exercise Rename")
    print("=" * 70)
    print(f"\nUser ID: {user_id}")
    print(f"From (current name): {from_exercise}")
    print(f"To (original name): {to_exercise}")
    
    # Check if from_exercise has workouts
    from_sessions = get_workout_sessions_by_exercise(user_id, from_exercise)
    if not from_sessions:
        print(f"\n❌ No workouts found for '{from_exercise}'")
        sys.exit(1)
    
    print(f"\nFound {len(from_sessions)} workout session(s) for '{from_exercise}':")
    for session in from_sessions:
        session_date = session['date']
        if isinstance(session_date, str):
            session_date = datetime.fromisoformat(session_date).date()
        print(f"  - {session_date}: {session['summary']}")
    
    # If dates not provided, show all and ask
    if dates is None:
        all_dates = [s['date'] for s in from_sessions]
        # Convert string dates to date objects
        date_objects = []
        for d in all_dates:
            if isinstance(d, str):
                d = datetime.fromisoformat(d).date()
            date_objects.append(d)
        
        print(f"\n⚠️  No specific dates provided. This will revert ALL {len(date_objects)} session(s).")
        response = input("\nDo you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        dates = date_objects
    else:
        # Validate provided dates exist
        from_dates = {s['date'] if not isinstance(s['date'], str) else datetime.fromisoformat(s['date']).date() 
                      for s in from_sessions}
        valid_dates = [d for d in dates if d in from_dates]
        invalid_dates = [d for d in dates if d not in from_dates]
        
        if invalid_dates:
            print(f"\n⚠️  Warning: Some dates not found in '{from_exercise}': {invalid_dates}")
        
        if not valid_dates:
            print(f"\n❌ No valid dates to revert")
            sys.exit(1)
        
        dates = valid_dates
        print(f"\nWill revert {len(dates)} session(s) on: {sorted(dates)}")
    
    # Perform revert
    print(f"\nReverting '{from_exercise}' → '{to_exercise}'...")
    updated_count = rename_workout_sessions(user_id, from_exercise, to_exercise, dates)
    
    if updated_count > 0:
        print(f"\n✅ Successfully reverted {updated_count} workout record(s)!")
        print(f"   '{from_exercise}' → '{to_exercise}'")
    else:
        print(f"\n❌ No records were updated. Please check the exercise names and dates.")


if __name__ == "__main__":
    main()

