"""
Migrate existing "手臂 (Arms)" exercises to "二頭肌 (Biceps)" or "三頭肌 (Triceps)"
based on exercise name keywords
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_manager import get_all_exercises, get_supabase
from src.auth import get_supabase_client

load_dotenv()


def categorize_arms_exercise(exercise_name: str) -> str:
    """
    Categorize an arms exercise as Biceps or Triceps based on name
    
    Returns:
        '二頭肌 (Biceps)' or '三頭肌 (Triceps)'
    """
    name_lower = exercise_name.lower()
    
    # Triceps keywords
    triceps_keywords = ['tricep', 'triceps', 'pushdown', 'extension', 'dip', 'overhead']
    
    # Biceps keywords
    biceps_keywords = ['bicep', 'biceps', 'curl', 'preacher', 'hammer']
    
    # Check for triceps first (more specific)
    if any(keyword in name_lower for keyword in triceps_keywords):
        return '三頭肌 (Triceps)'
    
    # Check for biceps
    if any(keyword in name_lower for keyword in biceps_keywords):
        return '二頭肌 (Biceps)'
    
    # Default to Biceps if unclear (most common)
    return '二頭肌 (Biceps)'


def migrate_arms_exercises(user_id: str, dry_run: bool = False):
    """
    Migrate all exercises with "手臂 (Arms)" to Biceps or Triceps
    
    Args:
        user_id: User UUID
        dry_run: If True, only show what would be changed without actually changing
    """
    supabase = get_supabase()
    
    # Get all exercises
    all_exercises = get_all_exercises(user_id)
    
    # Find exercises with "手臂 (Arms)"
    arms_exercises = [ex for ex in all_exercises if ex.get('muscle_group') == '手臂 (Arms)']
    
    if not arms_exercises:
        print("✅ No exercises found with muscle group '手臂 (Arms)'")
        return
    
    print("=" * 70)
    print("Migrate Arms Exercises to Biceps/Triceps")
    print("=" * 70)
    print(f"\nUser ID: {user_id}")
    print(f"Found {len(arms_exercises)} exercise(s) with '手臂 (Arms)' muscle group\n")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    biceps_count = 0
    triceps_count = 0
    
    for ex in arms_exercises:
        ex_name = ex['name']
        new_group = categorize_arms_exercise(ex_name)
        
        print(f"  {ex_name}")
        print(f"    → {new_group}")
        
        if not dry_run:
            try:
                result = supabase.table("exercises")\
                    .update({"muscle_group": new_group})\
                    .eq("user_id", user_id)\
                    .eq("name", ex_name)\
                    .execute()
                
                if result.data:
                    print(f"    ✅ Updated")
                else:
                    print(f"    ⚠️  No update made")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        if new_group == '二頭肌 (Biceps)':
            biceps_count += 1
        else:
            triceps_count += 1
        
        print()
    
    print("=" * 70)
    print(f"Summary:")
    print(f"  Total exercises: {len(arms_exercises)}")
    print(f"  → 二頭肌 (Biceps): {biceps_count}")
    print(f"  → 三頭肌 (Triceps): {triceps_count}")
    if dry_run:
        print(f"\nRun without --dry-run to apply changes")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_arms_to_biceps_triceps.py <user_id_or_email> [--dry-run]")
        print("\nExample:")
        print("  python migrate_arms_to_biceps_triceps.py user@example.com")
        print("  python migrate_arms_to_biceps_triceps.py <uuid> --dry-run")
        sys.exit(1)
    
    user_input = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    # Try to get user_id from email if needed
    try:
        # Check if it's a UUID (36 chars with hyphens)
        if len(user_input) == 36 and user_input.count('-') == 4:
            user_id = user_input
        else:
            # Assume it's an email - try to get user_id
            from revert_exercise_rename import get_user_id_from_email
            user_id = get_user_id_from_email(user_input)
            print(f"Found user_id for email: {user_input}\n")
    except Exception as e:
        print(f"❌ Error getting user_id: {e}")
        print("\nPlease provide either:")
        print("  - Email address (if SUPABASE_SERVICE_ROLE_KEY is set)")
        print("  - User ID (UUID)")
        sys.exit(1)
    
    migrate_arms_exercises(user_id, dry_run=dry_run)


if __name__ == "__main__":
    main()

