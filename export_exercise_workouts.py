"""
Export/Delete/Import workouts for a specific exercise.

Features:
- Export all workouts for a selected exercise to CSV
- Optionally delete all workouts for that exercise
- Optionally re-import the (possibly modified) CSV
"""

import os
import sys
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import (  # noqa: E402
    get_exercise_history,
    get_all_exercises,
    delete_all_exercise_workouts,
    import_workout_from_csv,
)
from src.auth import get_supabase_client  # noqa: E402

load_dotenv()


def export_exercise_to_csv(
    user_id: str,
    exercise_name: str,
    output_file: str,
) -> Optional[int]:
    """
    Export all workouts for an exercise to CSV compatible with import_workout_from_csv.

    Columns: Date, Muscle Group, Exercise, Set Order, Weight, Unit, Reps, Note

    Returns:
        Number of rows exported, or None on error.
    """
    history_df = get_exercise_history(user_id, exercise_name)

    if history_df.empty:
        print(f"❌ No workout history found for '{exercise_name}'")
        return 0

    # Get muscle group from exercises table (fallback to 'Other')
    all_exercises = get_all_exercises(user_id)
    mg_map = {ex["name"]: ex.get("muscle_group", "Other") for ex in all_exercises}
    muscle_group = mg_map.get(exercise_name, "Other")

    export_df = pd.DataFrame(
        {
            "Date": history_df["date"].apply(lambda d: d.isoformat()),
            "Muscle Group": muscle_group,
            "Exercise": exercise_name,
            "Set Order": history_df["set_order"],
            "Weight": history_df["weight"],
            "Unit": history_df["unit"],
            "Reps": history_df["reps"],
            "Note": history_df.get("notes", None),
        }
    )

    export_df.to_csv(output_file, index=False)
    print(f"✅ Exported {len(export_df)} rows for '{exercise_name}' to {output_file}")
    return len(export_df)


def main():
    """Interactive CLI to export / delete / re-import workouts for an exercise."""
    supabase = get_supabase_client()

    # Determine user_id: same approach as calculate_1rm.py
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        result = supabase.table("exercises").select("user_id").limit(1).execute()
        if not result.data:
            print("❌ No users found in database")
            return
        user_id = result.data[0]["user_id"]
        print(f"Using user_id: {user_id}\n")

    # Fetch exercises for this user
    all_exercises = get_all_exercises(user_id)
    if not all_exercises:
        print("❌ No exercises found in database")
        return

    # Group by muscle group for nicer listing
    exercises_by_group = {}
    for ex in all_exercises:
        mg = ex["muscle_group"]
        exercises_by_group.setdefault(mg, []).append(ex["name"])

    print("=" * 70)
    print("📋 Available Exercises")
    print("=" * 70)

    exercise_list = []
    idx = 1
    for mg in sorted(exercises_by_group.keys()):
        print(f"\n{mg}:")
        for ex_name in sorted(exercises_by_group[mg]):
            print(f"  {idx}. {ex_name}")
            exercise_list.append(ex_name)
            idx += 1

    print("\n" + "=" * 70)

    # Select exercise
    while True:
        try:
            selection = input(
                f"\nSelect exercise to export (1-{len(exercise_list)}), or 'q' to quit: "
            ).strip()
            if selection.lower() == "q":
                print("Goodbye!")
                return

            exercise_idx = int(selection) - 1
            if 0 <= exercise_idx < len(exercise_list):
                exercise_name = exercise_list[exercise_idx]
                break
            else:
                print(
                    f"❌ Invalid selection. Please enter a number between 1 and {len(exercise_list)}"
                )
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'.")

    # Default export filename
    safe_name = exercise_name.replace(" ", "_").replace("/", "_")
    default_filename = f"{safe_name}_workouts.csv"
    filename_input = (
        input(
            f"Enter output CSV filename [{default_filename}] (or 'q' to cancel export): "
        )
        .strip()
    )
    if filename_input.lower() == "q":
        print("Export cancelled.")
        return
    output_file = filename_input or default_filename

    # Export
    row_count = export_exercise_to_csv(user_id, exercise_name, output_file)
    if row_count is None or row_count == 0:
        return

    # Ask about deletion
    while True:
        delete_answer = input(
            f"\nDo you want to delete ALL {row_count} workouts for '{exercise_name}' "
            f"from the database now? (y/N): "
        ).strip().lower()
        if delete_answer in ("y", "n", ""):
            break
        print("Please answer 'y' or 'n'.")

    if delete_answer == "y":
        deleted = delete_all_exercise_workouts(user_id, exercise_name)
        print(f"🗑️ Deleted {deleted} workout logs for '{exercise_name}'.")
    else:
        print("No workouts were deleted.")

    # Optional re-import
    while True:
        import_answer = input(
            "\nDo you want to import a CSV file for this exercise now? (y/N): "
        ).strip().lower()
        if import_answer in ("y", "n", ""):
            break
        print("Please answer 'y' or 'n'.")

    if import_answer != "y":
        print("Done. You can re-import later using the app's Data Import page or a script.")
        return

    csv_path = (
        input(
            f"Enter CSV path to import "
            f"[press Enter to use '{output_file}' that was just exported]: "
        )
        .strip()
    )
    if not csv_path:
        csv_path = output_file

    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return

    print(f"📥 Importing from {csv_path} ...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return

    success_count, error_count, error_messages = import_workout_from_csv(user_id, df)
    print(f"✅ Imported {success_count} rows.")
    if error_count > 0:
        print(f"⚠️ {error_count} rows failed to import. First few errors:")
        for msg in error_messages[:10]:
            print(f"   - {msg}")


if __name__ == "__main__":
    main()


