"""
Script to calculate 1RM for exercises
Shows a list of exercises and lets you choose which one to analyze
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_exercise_history, get_all_exercises
from utils.calculations import calculate_1rm
from src.auth import get_supabase_client

load_dotenv()


def calculate_exercise_1rm(exercise_name: str, user_id: str):
    """
    Calculate 1RM for a specific exercise
    
    Args:
        exercise_name: Name of the exercise
        user_id: User UUID
    """
    # Get exercise history
    history_df = get_exercise_history(user_id, exercise_name)
    
    if history_df.empty:
        print(f"❌ No workout history found for '{exercise_name}'")
        return
    
    print(f"\n📊 1RM Analysis for: {exercise_name}")
    print("=" * 70)
    
    # Calculate 1RM for each set
    max_1rm = 0
    max_1rm_set = None
    all_1rms = []
    
    for _, row in history_df.iterrows():
        weight = row['weight']
        reps = row['reps']
        unit = row['unit']
        date = row['date']
        set_order = row['set_order']
        
        # Skip if invalid data
        if weight <= 0 or reps <= 0:
            continue
        
        # Calculate 1RM
        estimated_1rm = calculate_1rm(weight, reps)
        all_1rms.append({
            'date': date,
            'set_order': set_order,
            'weight': weight,
            'unit': unit,
            'reps': reps,
            '1rm': estimated_1rm
        })
        
        # Track maximum
        if estimated_1rm > max_1rm:
            max_1rm = estimated_1rm
            max_1rm_set = {
                'date': date,
                'set_order': set_order,
                'weight': weight,
                'unit': unit,
                'reps': reps,
                '1rm': estimated_1rm
            }
    
    if not all_1rms:
        print("❌ No valid sets found (all sets have weight or reps <= 0)")
        return
    
    # Display results
    print(f"\n🏆 Maximum Estimated 1RM: {max_1rm:.1f} {max_1rm_set['unit']}")
    print(f"   Achieved on: {max_1rm_set['date']}")
    print(f"   Set {max_1rm_set['set_order']}: {max_1rm_set['weight']} {max_1rm_set['unit']} × {max_1rm_set['reps']} reps")
    
    # Show top 5 1RM estimates
    print(f"\n📈 Top 5 1RM Estimates:")
    sorted_1rms = sorted(all_1rms, key=lambda x: x['1rm'], reverse=True)
    for i, set_data in enumerate(sorted_1rms[:5], 1):
        print(f"   {i}. {set_data['1rm']:.1f} {set_data['unit']} - {set_data['date']} (Set {set_data['set_order']}: {set_data['weight']} {set_data['unit']} × {set_data['reps']} reps)")
    
    # Calculate average 1RM from all sets
    avg_1rm = sum(s['1rm'] for s in all_1rms) / len(all_1rms)
    print(f"\n📊 Average 1RM (all sets): {avg_1rm:.1f} {max_1rm_set['unit']}")
    print(f"   Total sets analyzed: {len(all_1rms)}")
    
    print("\n" + "=" * 70)


def main():
    """Main function to run the 1RM calculator"""
    supabase = get_supabase_client()
    
    # Get user_id (use first user found, or allow selection)
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # Get first user from exercises table
        result = supabase.table("exercises")\
            .select("user_id")\
            .limit(1)\
            .execute()
        
        if not result.data:
            print("❌ No users found in database")
            return
        
        user_id = result.data[0]['user_id']
        print(f"Using user_id: {user_id}\n")
    
    # Get all exercises for this user
    all_exercises = get_all_exercises(user_id)
    
    if not all_exercises:
        print("❌ No exercises found in database")
        return
    
    # Group exercises by muscle group
    exercises_by_group = {}
    for ex in all_exercises:
        mg = ex['muscle_group']
        if mg not in exercises_by_group:
            exercises_by_group[mg] = []
        exercises_by_group[mg].append(ex['name'])
    
    # Display exercises grouped by muscle group
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
    
    # Get user selection
    while True:
        try:
            selection = input(f"\nSelect exercise (1-{len(exercise_list)}) or 'all' for all exercises, 'q' to quit: ").strip()
            
            if selection.lower() == 'q':
                print("Goodbye!")
                break
            elif selection.lower() == 'all':
                # Calculate for all exercises
                for ex_name in exercise_list:
                    calculate_exercise_1rm(ex_name, user_id)
                break
            else:
                exercise_idx = int(selection) - 1
                if 0 <= exercise_idx < len(exercise_list):
                    exercise_name = exercise_list[exercise_idx]
                    calculate_exercise_1rm(exercise_name, user_id)
                    
                    # Ask if they want to analyze another exercise
                    another = input("\nAnalyze another exercise? (y/n): ").strip().lower()
                    if another != 'y':
                        break
                else:
                    print(f"❌ Invalid selection. Please enter a number between 1 and {len(exercise_list)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number, 'all', or 'q'")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    main()

