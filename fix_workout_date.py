"""
Fix workout date script - Update workouts from one date to another.

This script is useful when you accidentally imported workouts with the wrong date.
For example, if you imported yesterday's workouts but marked them as today.
"""

import os
import sys
from datetime import date, timedelta
from typing import Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import update_workout_date, get_todays_workouts
from src.auth import get_supabase_client

load_dotenv()


def get_user_id_from_email(email: str) -> Optional[str]:
    """Get user_id from email using RPC function"""
    supabase = get_supabase_client()
    
    # Try RPC function (requires create_user_lookup_function.sql to be run)
    try:
        result = supabase.rpc('get_user_id_by_email', {'user_email': email}).execute()
        if result.data and len(result.data) > 0:
            user_id = result.data[0].get('id')
            if user_id:
                print(f"Found user_id for {email}: {user_id}")
                return user_id
    except Exception as e:
        # RPC function might not exist
        error_msg = str(e).lower()
        if 'function' in error_msg and 'does not exist' in error_msg:
            print(f"\nWarning: RPC function 'get_user_id_by_email' not found.")
            print("To enable email lookup, run this SQL in Supabase SQL Editor:")
            print("  database/create_user_lookup_function.sql")
        pass
    
    return None


def get_user_id(user_input: str) -> Optional[str]:
    """
    Get user_id from either email or UUID
    Returns the user_id (UUID) or None if not found
    """
    # Check if it's a UUID (contains hyphens and is 36 chars)
    if len(user_input) == 36 and user_input.count('-') == 4:
        # Looks like a UUID, return as-is
        return user_input
    else:
        # Assume it's an email, try to get user_id
        return get_user_id_from_email(user_input)


def main():
    """Main function to update workout dates."""
    supabase = get_supabase_client()
    
    # Parse arguments
    # Possible formats:
    # 1. No args: use first user, today -> yesterday
    # 2. 1 arg: user_id/email, use today -> yesterday
    # 3. 2 args: user_id/email, old_date (new_date = old_date - 1 day)
    # 4. 3 args: user_id/email, old_date, new_date
    
    user_id = None
    old_date = None
    new_date = None
    
    # Determine what arguments were provided
    if len(sys.argv) == 1:
        # No arguments - use first user, default dates
        result = supabase.table("exercises").select("user_id").limit(1).execute()
        if not result.data:
            print("No users found in database")
            return
        user_id = result.data[0]["user_id"]
        print(f"Using user_id: {user_id}\n")
        old_date = date.today()
        new_date = old_date - timedelta(days=1)
    elif len(sys.argv) == 2:
        # 1 argument - could be user_id/email or old_date
        arg1 = sys.argv[1]
        # Check if it looks like a date (YYYY-MM-DD format)
        if len(arg1) == 10 and arg1.count('-') == 2:
            # It's a date, use first user
            result = supabase.table("exercises").select("user_id").limit(1).execute()
            if not result.data:
                print("No users found in database")
                return
            user_id = result.data[0]["user_id"]
            try:
                from datetime import datetime
                old_date = datetime.strptime(arg1, "%Y-%m-%d").date()
                new_date = old_date - timedelta(days=1)
            except ValueError:
                print("Error: Date format should be YYYY-MM-DD")
                return
        else:
            # It's a user_id/email
            user_id = get_user_id(arg1)
            if not user_id:
                print(f"Error: Could not find user_id for '{arg1}'")
                print("\nPossible solutions:")
                print("1. If you provided an email, make sure the RPC function exists:")
                print("   Run database/create_user_lookup_function.sql in Supabase SQL Editor")
                print("2. Or provide the UUID directly instead of email")
                print("3. Or run without user_id to use the first user in database")
                return
            old_date = date.today()
            new_date = old_date - timedelta(days=1)
    elif len(sys.argv) == 3:
        # 2 arguments - could be:
        # 1. user_id/email and old_date (new_date = old_date - 1)
        # 2. old_date and new_date (use first user)
        arg1 = sys.argv[1]
        arg2 = sys.argv[2]
        
        # Check if both arguments look like dates
        def looks_like_date(s):
            return len(s) == 10 and s.count('-') == 2
        
        if looks_like_date(arg1) and looks_like_date(arg2):
            # Both are dates - use first user
            result = supabase.table("exercises").select("user_id").limit(1).execute()
            if not result.data:
                print("No users found in database")
                return
            user_id = result.data[0]["user_id"]
            try:
                from datetime import datetime
                old_date = datetime.strptime(arg1, "%Y-%m-%d").date()
                new_date = datetime.strptime(arg2, "%Y-%m-%d").date()
            except ValueError:
                print("Error: Date format should be YYYY-MM-DD")
                print("Usage: python fix_workout_date.py [user_id/email] [old_date] [new_date]")
                return
        else:
            # First is user_id/email, second is old_date
            user_input = arg1
            user_id = get_user_id(user_input)
            if not user_id:
                print(f"Error: Could not find user_id for '{user_input}'")
                print("\nPossible solutions:")
                print("1. If you provided an email, make sure the RPC function exists:")
                print("   Run database/create_user_lookup_function.sql in Supabase SQL Editor")
                print("2. Or provide the UUID directly instead of email")
                return
            try:
                from datetime import datetime
                old_date = datetime.strptime(arg2, "%Y-%m-%d").date()
                new_date = old_date - timedelta(days=1)
            except ValueError:
                print("Error: Date format should be YYYY-MM-DD")
                print("Usage: python fix_workout_date.py [user_id/email] [old_date] [new_date]")
                return
    elif len(sys.argv) >= 4:
        # 3+ arguments - user_id/email, old_date, new_date
        user_input = sys.argv[1]
        user_id = get_user_id(user_input)
        if not user_id:
            print(f"Error: Could not find user_id for '{user_input}'")
            print("\nPossible solutions:")
            print("1. If you provided an email, make sure the RPC function exists:")
            print("   Run database/create_user_lookup_function.sql in Supabase SQL Editor")
            print("2. Or provide the UUID directly instead of email")
            return
        try:
            from datetime import datetime
            old_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
            new_date = datetime.strptime(sys.argv[3], "%Y-%m-%d").date()
        except ValueError:
            print("Error: Date format should be YYYY-MM-DD")
            print("Usage: python fix_workout_date.py [user_id/email] [old_date] [new_date]")
            print("Example: python fix_workout_date.py raymondcuhk@gmail.com 2025-12-22 2025-12-21")
            return
    
    # Show what will be updated
    print("=" * 70)
    print("Fix Workout Date")
    print("=" * 70)
    print(f"Old date (incorrect): {old_date}")
    print(f"New date (correct):   {new_date}")
    print()
    
    # Check if there are workouts on the old date
    workouts = get_todays_workouts(user_id, old_date)
    if workouts.empty:
        print(f"No workouts found for {old_date}")
        print("Nothing to update.")
        return
    
    # Show summary
    exercises = workouts['exercise_name'].unique()
    total_sets = len(workouts)
    print(f"Found {len(exercises)} exercises with {total_sets} total sets")
    print("\nExercises to update:")
    for exercise_name in exercises:
        exercise_sets = len(workouts[workouts['exercise_name'] == exercise_name])
        print(f"  - {exercise_name}: {exercise_sets} sets")
    
    # Confirm before updating
    print("\n" + "-" * 70)
    confirm = input("Do you want to proceed with updating the dates? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Update cancelled.")
        return
    
    # Update the dates
    print(f"\nUpdating workouts from {old_date} to {new_date}...")
    updated_count = update_workout_date(user_id, old_date, new_date)
    
    if updated_count > 0:
        print(f"Successfully updated {updated_count} workout records!")
        print(f"\nAll workouts from {old_date} have been moved to {new_date}")
    else:
        print("No workouts were updated. Please check the dates and try again.")


if __name__ == "__main__":
    main()

