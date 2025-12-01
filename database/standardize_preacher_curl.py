"""
Script to standardize Preacher Curl exercise names
Renames "Preacher Curl" and "Dumbbell Bicep Curl (Single Arm)" to "Preacher Curl (Single Arm)"
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import rename_exercise, get_supabase
from src.auth import get_supabase_client

load_dotenv()


def standardize_preacher_curl(user_id: str = None):
    """
    Standardize Preacher Curl exercise names for a user
    
    Args:
        user_id: User UUID (if None, will process all users)
    """
    supabase = get_supabase_client()
    
    # Standardize to this name
    standard_name = "Preacher Curl (Single Arm)"
    
    # Old names to replace
    old_names = [
        "Preacher Curl",
        "Dumbbell Bicep Curl (Single Arm)"
    ]
    
    if user_id:
        # Process specific user
        print(f"Standardizing Preacher Curl for user: {user_id}")
        
        # First, check if standard name already exists
        existing = supabase.table("exercises")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("name", standard_name)\
            .execute()
        
        standard_exists = existing.data is not None and len(existing.data) > 0
        
        if standard_exists:
            print(f"  ⚠️  Exercise '{standard_name}' already exists for this user")
            print(f"  Will merge workout logs and delete duplicate exercises")
        
        # Process each old name
        total_exercises_deleted = 0
        total_logs_updated = 0
        
        for old_name in old_names:
            if old_name == standard_name:
                continue  # Skip if already the standard name
            
            print(f"\n  Processing '{old_name}'...")
            
            # First, update workout logs to use standard name
            logs_result = supabase.table("workout_logs")\
                .update({"exercise_name": standard_name})\
                .eq("user_id", user_id)\
                .eq("exercise_name", old_name)\
                .execute()
            
            logs_updated = len(logs_result.data) if logs_result.data else 0
            total_logs_updated += logs_updated
            
            if logs_updated > 0:
                print(f"    ✅ Updated {logs_updated} workout log record(s)")
            
            # Then, delete the duplicate exercise record (if standard already exists)
            if standard_exists:
                exercise_result = supabase.table("exercises")\
                    .delete()\
                    .eq("user_id", user_id)\
                    .eq("name", old_name)\
                    .execute()
                
                exercises_deleted = len(exercise_result.data) if exercise_result.data else 0
                total_exercises_deleted += exercises_deleted
                
                if exercises_deleted > 0:
                    print(f"    ✅ Deleted {exercises_deleted} duplicate exercise record(s)")
            else:
                # Standard doesn't exist, so rename the exercise
                exercise_result = supabase.table("exercises")\
                    .update({"name": standard_name})\
                    .eq("user_id", user_id)\
                    .eq("name", old_name)\
                    .execute()
                
                exercises_updated = len(exercise_result.data) if exercise_result.data else 0
                total_exercises_deleted += exercises_updated
                
                if exercises_updated > 0:
                    print(f"    ✅ Renamed {exercises_updated} exercise record(s)")
                    standard_exists = True  # Now it exists
        
        print(f"\n  📊 Summary:")
        print(f"    - Exercises processed: {total_exercises_deleted}")
        print(f"    - Workout logs updated: {total_logs_updated}")
        
    else:
        # Process all users
        print("Standardizing Preacher Curl for all users...")
        
        # Get all users who have these exercises
        for old_name in old_names:
            if old_name == standard_name:
                continue
            
            print(f"\n  Processing '{old_name}'...")
            
            # Get all exercises with this name
            exercises = supabase.table("exercises")\
                .select("user_id")\
                .eq("name", old_name)\
                .execute()
            
            if not exercises.data:
                print(f"    No exercises found with name '{old_name}'")
                continue
            
            # Group by user_id
            user_ids = list(set([ex['user_id'] for ex in exercises.data]))
            print(f"    Found {len(user_ids)} user(s) with this exercise")
            
            for uid in user_ids:
                print(f"    Processing user: {uid}")
                # Recursively call for each user
                standardize_preacher_curl(user_id=uid)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # User ID provided as argument
        user_id = sys.argv[1]
        standardize_preacher_curl(user_id=user_id)
    else:
        # Process all users
        response = input("Process all users? (y/n): ")
        if response.lower() == 'y':
            standardize_preacher_curl()
        else:
            user_id = input("Enter user ID (UUID): ")
            if user_id:
                standardize_preacher_curl(user_id=user_id)
            else:
                print("No user ID provided. Exiting.")

