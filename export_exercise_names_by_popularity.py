"""
Export exercise names sorted by popularity (workout session count).

This exports exercise names in order of popularity (most used first) 
to help LLMs standardize exercise names when users upload workouts.
"""

import os
import sys
import json
from typing import Dict

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_exercise_workout_counts, get_all_exercises  # noqa: E402
from src.auth import get_supabase_client  # noqa: E402

load_dotenv()


def export_exercise_names_by_popularity(user_id: str, output_file: str = "exercise_names_by_popularity.json"):
    """
    Export exercise names sorted by popularity (workout session count).
    
    Args:
        user_id: User UUID
        output_file: Output file path (JSON format)
    
    Returns:
        Number of exercises exported
    """
    # Get workout counts for each exercise
    workout_counts = get_exercise_workout_counts(user_id)
    
    # Get all exercises to include metadata
    all_exercises = get_all_exercises(user_id)
    exercise_metadata = {ex["name"]: ex for ex in all_exercises}
    
    # Combine counts with exercise metadata
    exercises_data = []
    for exercise_name, count in sorted(workout_counts.items(), key=lambda x: x[1], reverse=True):
        exercise_info = {
            "name": exercise_name,
            "workout_sessions": count,
            "muscle_group": exercise_metadata.get(exercise_name, {}).get("muscle_group", "Unknown"),
            "exercise_type": exercise_metadata.get(exercise_name, {}).get("exercise_type", "Unknown")
        }
        exercises_data.append(exercise_info)
    
    # Also include exercises with 0 workouts (from exercises table but no workouts yet)
    exercises_with_workouts = set(workout_counts.keys())
    for ex in all_exercises:
        if ex["name"] not in exercises_with_workouts:
            exercises_data.append({
                "name": ex["name"],
                "workout_sessions": 0,
                "muscle_group": ex.get("muscle_group", "Unknown"),
                "exercise_type": ex.get("exercise_type", "Unknown")
            })
    
    # Sort again to ensure 0-count exercises are at the end
    exercises_data.sort(key=lambda x: x["workout_sessions"], reverse=True)
    
    # Export to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exercises_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(exercises_data)} exercises to {output_file}")
    print(f"\nTop 10 most popular exercises:")
    for i, ex in enumerate(exercises_data[:10], 1):
        print(f"  {i}. {ex['name']} ({ex['workout_sessions']} sessions)")
    
    return len(exercises_data)


def export_simple_list(user_id: str, output_file: str = "exercise_names_by_popularity.txt"):
    """
    Export a simple text file with exercise names, one per line, sorted by popularity.
    This format is easier for LLMs to parse as a simple list.
    
    Args:
        user_id: User UUID
        output_file: Output file path (TXT format)
    
    Returns:
        Number of exercises exported
    """
    # Get workout counts for each exercise
    workout_counts = get_exercise_workout_counts(user_id)
    
    # Sort by popularity (descending)
    sorted_exercises = sorted(workout_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for exercise_name, count in sorted_exercises:
            f.write(f"{exercise_name}\n")
    
    print(f"Exported {len(sorted_exercises)} exercises to {output_file}")
    print(f"\nTop 10 most popular exercises:")
    for i, (name, count) in enumerate(sorted_exercises[:10], 1):
        print(f"  {i}. {name} ({count} sessions)")
    
    return len(sorted_exercises)


def main():
    """Main function to export exercise names by popularity."""
    supabase = get_supabase_client()
    
    # Determine user_id
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        result = supabase.table("exercises").select("user_id").limit(1).execute()
        if not result.data:
            print("No users found in database")
            return
        user_id = result.data[0]["user_id"]
        print(f"Using user_id: {user_id}\n")
    
    # Export both formats
    print("=" * 70)
    print("Exporting Exercise Names by Popularity")
    print("=" * 70)
    
    # Export detailed JSON
    export_exercise_names_by_popularity(user_id, "exercise_names_by_popularity.json")
    
    print("\n" + "-" * 70)
    
    # Export simple text list
    export_simple_list(user_id, "exercise_names_by_popularity.txt")
    
    print("\n" + "=" * 70)
    print("Export complete!")
    print("\nFiles created:")
    print("  - exercise_names_by_popularity.json (detailed with metadata)")
    print("  - exercise_names_by_popularity.txt (simple list for LLM)")


if __name__ == "__main__":
    main()

