"""
Database management module for Gym Tracker App
Handles all Supabase PostgreSQL database operations
"""

import os
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
from supabase import Client

from src.auth import get_supabase_client

# Schema name
# Note: Using 'public' schema for Supabase PostgREST compatibility
# To use 'gymlog' schema, expose it in Supabase Dashboard: Settings -> API -> Exposed schemas
SCHEMA = "public"


def get_supabase() -> Client:
    """Get Supabase client"""
    return get_supabase_client()


def init_database(user_id: str):
    """
    Initialize database and create tables if they don't exist
    Note: This should be run once via Supabase SQL editor, not from the app
    The schema.sql file contains the SQL to run in Supabase dashboard
    """
    # Tables should be created via Supabase SQL editor
    # This function is kept for compatibility but doesn't execute SQL
    # Instead, we can verify tables exist by trying a simple query
    try:
        supabase = get_supabase()
        # Try to query workout_logs to verify table exists
        result = supabase.table("workout_logs").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Warning: Could not verify database tables: {e}")
        print("Please run the SQL from database/schema.sql in Supabase SQL editor")
        return False


def save_workout(user_id: str, workout_date: date, exercise_name: str, sets: List[Dict], rpe: Optional[int] = None, notes: Optional[str] = None):
    """
    Save workout data to database
    
    Args:
        user_id: User UUID
        workout_date: Workout date
        exercise_name: Name of the exercise
        sets: List of dictionaries with keys: weight, unit, reps, set_order
        rpe: Rate of Perceived Exertion (1-10)
        notes: Optional notes
    """
    supabase = get_supabase()
    
    for set_data in sets:
        data = {
            "user_id": user_id,
            "date": workout_date.isoformat(),
            "exercise_name": exercise_name,
            "set_order": set_data.get('set_order', 1),
            "weight": set_data['weight'],
            "unit": set_data['unit'],
            "reps": set_data['reps'],
            "rpe": rpe,
            "notes": notes
        }
        
        supabase.table("workout_logs").insert(data).execute()


def get_previous_workout(user_id: str, exercise_name: str) -> Optional[Dict]:
    """
    Get the most recent workout for a specific exercise
    
    Returns:
        Dictionary with previous workout data or None
    """
    supabase = get_supabase()
    
    result = supabase.table("workout_logs")\
        .select("weight, unit, reps, rpe, date")\
        .eq("user_id", user_id)\
        .eq("exercise_name", exercise_name)\
        .order("date", desc=True)\
        .order("set_order", desc=False)\
        .limit(1)\
        .execute()
    
    if result.data:
        row = result.data[0]
        return {
            'weight': row['weight'],
            'unit': row['unit'],
            'reps': row['reps'],
            'rpe': row.get('rpe'),
            'date': row['date']
        }
    return None


def get_previous_workout_session(user_id: str, exercise_name: str) -> Optional[Dict]:
    """
    Get all sets from the most recent workout session for a specific exercise
    
    Returns:
        Dictionary with:
        - 'date': workout date
        - 'unit': unit used
        - 'sets': list of sets with weight, reps, set_order
        - 'rpe': RPE value (if available)
        - 'notes': notes (if available)
        Or None if no previous workout exists
    """
    supabase = get_supabase()
    
    # First, get the most recent workout date for this exercise
    date_result = supabase.table("workout_logs")\
        .select("date")\
        .eq("user_id", user_id)\
        .eq("exercise_name", exercise_name)\
        .order("date", desc=True)\
        .limit(1)\
        .execute()
    
    if not date_result.data:
        return None
    
    last_date = date_result.data[0]['date']
    
    # Get all sets from that date
    result = supabase.table("workout_logs")\
        .select("set_order, weight, unit, reps, rpe, notes")\
        .eq("user_id", user_id)\
        .eq("exercise_name", exercise_name)\
        .eq("date", last_date)\
        .order("set_order", desc=False)\
        .execute()
    
    if result.data:
        # Get unit, rpe, and notes from first set (should be same for all sets in a session)
        first_set = result.data[0]
        sets = [
            {
                'set_order': row['set_order'],
                'weight': row['weight'],
                'reps': row['reps']
            }
            for row in result.data
        ]
        
        return {
            'date': last_date,
            'unit': first_set['unit'],
            'sets': sets,
            'rpe': first_set.get('rpe'),
            'notes': first_set.get('notes')
        }
    return None


def get_recent_workout_sessions(user_id: str, exercise_name: str, limit: int = 3) -> List[Dict]:
    """
    Get the last N workout sessions for a specific exercise
    
    Args:
        user_id: User UUID
        exercise_name: Name of the exercise
        limit: Number of recent sessions to return (default: 3)
    
    Returns:
        List of dictionaries, each containing:
        - 'date': workout date
        - 'unit': unit used
        - 'sets': list of sets with weight, reps, set_order
        - 'rpe': RPE value (if available)
        - 'notes': notes (if available)
    """
    supabase = get_supabase()
    
    # Get unique workout dates for this exercise, ordered by date descending
    date_result = supabase.table("workout_logs")\
        .select("date")\
        .eq("user_id", user_id)\
        .eq("exercise_name", exercise_name)\
        .order("date", desc=True)\
        .execute()
    
    if not date_result.data:
        return []
    
    # Get unique dates
    unique_dates = []
    seen_dates = set()
    for row in date_result.data:
        workout_date = row['date']
        if workout_date not in seen_dates:
            unique_dates.append(workout_date)
            seen_dates.add(workout_date)
            if len(unique_dates) >= limit:
                break
    
    # Get all sets for each date
    sessions = []
    for workout_date in unique_dates:
        result = supabase.table("workout_logs")\
            .select("set_order, weight, unit, reps, rpe, notes")\
            .eq("user_id", user_id)\
            .eq("exercise_name", exercise_name)\
            .eq("date", workout_date)\
            .order("set_order", desc=False)\
            .execute()
        
        if result.data:
            first_set = result.data[0]
            sets = [
                {
                    'set_order': row['set_order'],
                    'weight': row['weight'],
                    'reps': row['reps']
                }
                for row in result.data
            ]
            
            sessions.append({
                'date': workout_date,
                'unit': first_set['unit'],
                'sets': sets,
                'rpe': first_set.get('rpe'),
                'notes': first_set.get('notes')
            })
    
    return sessions


def get_exercise_history(user_id: str, exercise_name: str, days: Optional[int] = None) -> pd.DataFrame:
    """
    Get exercise history as DataFrame
    
    Args:
        user_id: User UUID
        exercise_name: Name of the exercise
        days: Number of days to look back (None for all)
    
    Returns:
        DataFrame with exercise history
    """
    supabase = get_supabase()
    
    query = supabase.table("workout_logs")\
        .select("date, set_order, weight, unit, reps, rpe, notes")\
        .eq("user_id", user_id)\
        .eq("exercise_name", exercise_name)
    
    if days:
        # Calculate cutoff date
        from datetime import timedelta
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        query = query.gte("date", cutoff_date)
    
    result = query.order("date", desc=True)\
        .order("set_order", desc=False)\
        .execute()
    
    if result.data:
        df = pd.DataFrame(result.data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame(columns=['date', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes'])


def get_all_exercises(user_id: str) -> List[Dict]:
    """
    Get all exercises from the library for a user
    
    Returns:
        List of exercise dictionaries
    """
    supabase = get_supabase()
    
    try:
        # Try to select with execution_steps (if column exists)
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type, execution_steps")\
            .eq("user_id", user_id)\
            .order("muscle_group")\
            .order("name")\
            .execute()
    except Exception:
        # Fallback: select without execution_steps if column doesn't exist yet
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type")\
            .eq("user_id", user_id)\
            .order("muscle_group")\
            .order("name")\
            .execute()
        # Add None for execution_steps to maintain consistent structure
        if result.data:
            for row in result.data:
                row['execution_steps'] = None
    
    return result.data if result.data else []


def get_exercise_entry_counts(user_id: str) -> Dict[str, int]:
    """
    Get entry count for each exercise
    
    Returns:
        Dictionary with exercise names as keys and entry counts as values
    """
    supabase = get_supabase()
    
    # Use RPC or aggregate query
    # Since Supabase doesn't have direct GROUP BY in select, we'll fetch all and count in Python
    result = supabase.table("workout_logs")\
        .select("exercise_name")\
        .eq("user_id", user_id)\
        .execute()
    
    counts = {}
    if result.data:
        for row in result.data:
            exercise_name = row['exercise_name']
            counts[exercise_name] = counts.get(exercise_name, 0) + 1
    
    return counts


def get_exercise_workout_counts(user_id: str) -> Dict[str, int]:
    """
    Get workout session count for each exercise (counts unique dates per exercise)
    
    Returns:
        Dictionary with exercise names as keys and workout session counts as values
    """
    supabase = get_supabase()
    
    # Get all workout logs with date and exercise_name
    result = supabase.table("workout_logs")\
        .select("exercise_name, date")\
        .eq("user_id", user_id)\
        .execute()
    
    # Count unique date+exercise combinations (workout sessions)
    session_counts = {}
    if result.data:
        seen_sessions = set()
        for row in result.data:
            exercise_name = row['exercise_name']
            workout_date = row['date']
            session_key = (exercise_name, workout_date)
            
            if session_key not in seen_sessions:
                seen_sessions.add(session_key)
                session_counts[exercise_name] = session_counts.get(exercise_name, 0) + 1
    
    return session_counts


def get_exercises_by_muscle_group(user_id: str, muscle_group: str) -> List[str]:
    """
    Get exercise names for a specific muscle group
    
    Returns:
        List of exercise names
    """
    supabase = get_supabase()
    
    result = supabase.table("exercises")\
        .select("name")\
        .eq("user_id", user_id)\
        .eq("muscle_group", muscle_group)\
        .order("name")\
        .execute()
    
    return [row['name'] for row in result.data] if result.data else []


def add_custom_exercise(user_id: str, name: str, muscle_group: str, exercise_type: str, execution_steps: Optional[str] = None) -> bool:
    """
    Add a custom exercise to the library
    
    Args:
        user_id: User UUID
        name: Exercise name
        muscle_group: Muscle group
        exercise_type: Exercise type
        execution_steps: Optional markdown-formatted execution steps
    
    Returns:
        True if successful, False if exercise already exists
    """
    supabase = get_supabase()
    
    try:
        data = {
            "user_id": user_id,
            "name": name,
            "muscle_group": muscle_group,
            "exercise_type": exercise_type
        }
        if execution_steps:
            data["execution_steps"] = execution_steps
        supabase.table("exercises").insert(data).execute()
        return True
    except Exception as e:
        # Check if it's a unique constraint violation
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False
        raise


def get_exercise_details(user_id: str, exercise_name: str) -> Optional[Dict]:
    """
    Get full exercise details including execution steps
    
    Args:
        user_id: User UUID
        exercise_name: Name of the exercise
    
    Returns:
        Dictionary with exercise details or None
    """
    supabase = get_supabase()
    
    try:
        # Try to select with execution_steps (if column exists)
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type, execution_steps")\
            .eq("user_id", user_id)\
            .eq("name", exercise_name)\
            .limit(1)\
            .execute()
    except Exception:
        # Fallback: select without execution_steps if column doesn't exist yet
        result = supabase.table("exercises")\
            .select("id, name, muscle_group, exercise_type")\
            .eq("user_id", user_id)\
            .eq("name", exercise_name)\
            .limit(1)\
            .execute()
        # Add None for execution_steps to maintain consistent structure
        if result.data and len(result.data) > 0:
            result.data[0]['execution_steps'] = None
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def update_exercise_steps(user_id: str, exercise_name: str, execution_steps: Optional[str]) -> bool:
    """
    Update execution steps for an exercise
    
    Args:
        user_id: User UUID
        exercise_name: Name of the exercise
        execution_steps: Markdown-formatted execution steps (None to clear)
    
    Returns:
        True if successful, False if exercise not found
    """
    supabase = get_supabase()
    
    try:
        result = supabase.table("exercises")\
            .update({"execution_steps": execution_steps})\
            .eq("user_id", user_id)\
            .eq("name", exercise_name)\
            .execute()
        
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        print(f"Error updating exercise steps: {e}")
        return False


def get_todays_workouts(user_id: str, workout_date: date) -> pd.DataFrame:
    """
    Get all workouts for a specific date
    
    Returns:
        DataFrame with today's workouts (includes id field for update/delete operations)
    """
    supabase = get_supabase()
    
    result = supabase.table("workout_logs")\
        .select("id, exercise_name, set_order, weight, unit, reps, rpe, notes")\
        .eq("user_id", user_id)\
        .eq("date", workout_date.isoformat())\
        .order("exercise_name")\
        .order("set_order")\
        .execute()
    
    if result.data:
        return pd.DataFrame(result.data)
    return pd.DataFrame(columns=['id', 'exercise_name', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes'])


def get_all_workouts(user_id: str, days: Optional[int] = None) -> pd.DataFrame:
    """
    Get all workout logs
    
    Args:
        user_id: User UUID
        days: Number of days to look back (None for all)
    
    Returns:
        DataFrame with all workouts
    """
    supabase = get_supabase()
    
    query = supabase.table("workout_logs")\
        .select("date, exercise_name, set_order, weight, unit, reps, rpe, notes")\
        .eq("user_id", user_id)
    
    if days:
        from datetime import timedelta
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        query = query.gte("date", cutoff_date)
    
    result = query.order("date", desc=True)\
        .order("exercise_name")\
        .order("set_order")\
        .execute()
    
    if result.data:
        df = pd.DataFrame(result.data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame(columns=['date', 'exercise_name', 'set_order', 'weight', 'unit', 'reps', 'rpe', 'notes'])


def get_muscle_group_stats(user_id: str, days: int = 30) -> pd.DataFrame:
    """
    Get training volume statistics by muscle group
    
    Args:
        user_id: User UUID
        days: Number of days to analyze
    
    Returns:
        DataFrame with muscle group statistics
    """
    # Get all workouts in the time period
    workouts_df = get_all_workouts(user_id, days)
    
    if workouts_df.empty:
        return pd.DataFrame(columns=['muscle_group', 'total_sets', 'workout_days'])
    
    # Get exercises to map to muscle groups
    exercises = get_all_exercises(user_id)
    exercise_to_muscle = {ex['name']: ex['muscle_group'] for ex in exercises}
    
    # Add muscle_group to workouts
    workouts_df['muscle_group'] = workouts_df['exercise_name'].map(exercise_to_muscle)
    workouts_df = workouts_df.dropna(subset=['muscle_group'])
    
    # Group by muscle group
    stats = workouts_df.groupby('muscle_group').agg({
        'date': ['count', 'nunique']
    }).reset_index()
    
    stats.columns = ['muscle_group', 'total_sets', 'workout_days']
    stats = stats.sort_values('total_sets', ascending=False)
    
    return stats


def import_workout_from_csv(user_id: str, df: pd.DataFrame) -> Tuple[int, int, List[str]]:
    """
    Import workout data from CSV DataFrame
    
    Args:
        user_id: User UUID
        df: DataFrame with columns: Date, Muscle Group, Exercise, Set Order, Weight, Unit, Reps, Note
    
    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    from utils.helpers import map_muscle_group, infer_exercise_type
    
    supabase = get_supabase()
    
    success_count = 0
    error_count = 0
    error_messages = []
    
    # Required columns
    required_columns = ['Date', 'Exercise', 'Set Order', 'Weight', 'Unit', 'Reps']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_messages.append(f"缺少必要欄位: {', '.join(missing_columns)}")
        return 0, 0, error_messages
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Parse date
            if pd.isna(row['Date']):
                error_count += 1
                error_messages.append(f"第 {idx + 2} 行: 日期為空")
                continue
            
            workout_date = pd.to_datetime(row['Date']).date()
            
            # Get exercise name
            exercise_name = str(row['Exercise']).strip()
            if not exercise_name:
                error_count += 1
                error_messages.append(f"第 {idx + 2} 行: 動作名稱為空")
                continue
            
            # Get muscle group and map it
            muscle_group = map_muscle_group(str(row.get('Muscle Group', 'Other')).strip())
            
            # Get set order
            set_order = int(row['Set Order']) if pd.notna(row['Set Order']) else 1
            
            # Get weight
            weight = float(row['Weight']) if pd.notna(row['Weight']) else 0.0
            
            # Get unit
            unit = str(row['Unit']).strip().lower()
            if unit not in ['kg', 'lb', 'notch', 'notch/plate']:
                # Try to normalize
                if 'notch' in unit or 'plate' in unit:
                    unit = 'notch/plate'
                elif 'lb' in unit or 'pound' in unit:
                    unit = 'lb'
                else:
                    unit = 'kg'
            
            # Get reps
            reps = int(row['Reps']) if pd.notna(row['Reps']) else 0
            
            # Get notes
            notes = str(row.get('Note', '')).strip() if pd.notna(row.get('Note', '')) else None
            if notes == '':
                notes = None
            
            # Validate data
            if weight < 0 or reps < 0:
                error_count += 1
                error_messages.append(f"第 {idx + 2} 行: 重量或次數為負數")
                continue
            
            # Ensure exercise exists in exercises table
            existing = supabase.table("exercises")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("name", exercise_name)\
                .execute()
            
            if not existing.data:
                # Add exercise to library
                exercise_type = infer_exercise_type(exercise_name)
                try:
                    supabase.table("exercises").insert({
                        "user_id": user_id,
                        "name": exercise_name,
                        "muscle_group": muscle_group,
                        "exercise_type": exercise_type
                    }).execute()
                except Exception:
                    # Exercise might have been added by another row, ignore
                    pass
            
            # Insert workout log
            supabase.table("workout_logs").insert({
                "user_id": user_id,
                "date": workout_date.isoformat(),
                "exercise_name": exercise_name,
                "set_order": set_order,
                "weight": weight,
                "unit": unit,
                "reps": reps,
                "rpe": None,
                "notes": notes
            }).execute()
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            error_messages.append(f"第 {idx + 2} 行: {str(e)}")
            continue
    
    return success_count, error_count, error_messages


def clear_all_data(user_id: str) -> Tuple[int, int]:
    """
    Clear all workout logs and exercises from database for a user
    
    Returns:
        Tuple of (deleted_workout_logs_count, deleted_exercises_count)
    """
    supabase = get_supabase()
    
    # Get counts before deletion
    workout_result = supabase.table("workout_logs")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    workout_count = workout_result.count if hasattr(workout_result, 'count') else 0
    
    exercise_result = supabase.table("exercises")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    exercise_count = exercise_result.count if hasattr(exercise_result, 'count') else 0
    
    # Delete all data for user
    supabase.table("workout_logs").delete().eq("user_id", user_id).execute()
    supabase.table("exercises").delete().eq("user_id", user_id).execute()
    
    return workout_count, exercise_count


def get_pr_records(user_id: str) -> Dict[str, Dict]:
    """
    Get personal records for all exercises with dates
    
    Returns:
        Dictionary with exercise names as keys and PR data as values
        Each PR includes the value and the date(s) when it was achieved
    """
    supabase = get_supabase()
    
    # Get all exercises for this user
    result = supabase.table("workout_logs")\
        .select("exercise_name")\
        .eq("user_id", user_id)\
        .execute()
    
    exercises = list(set([row['exercise_name'] for row in result.data])) if result.data else []
    
    pr_dict = {}
    
    # Import helper function
    from utils.helpers import is_assisted_exercise
    
    for exercise_name in exercises:
        is_assisted = is_assisted_exercise(exercise_name)
        
        # Get all logs for this exercise
        logs_result = supabase.table("workout_logs")\
            .select("date, weight, unit, reps")\
            .eq("user_id", user_id)\
            .eq("exercise_name", exercise_name)\
            .execute()
        
        if not logs_result.data:
            continue
        
        logs_df = pd.DataFrame(logs_result.data)
        logs_df['date'] = pd.to_datetime(logs_df['date']).dt.date
        
        # Get best weight, unit, and its date(s)
        if is_assisted:
            best_weight = logs_df['weight'].min()
        else:
            best_weight = logs_df['weight'].max()
        
        best_weight_rows = logs_df[logs_df['weight'] == best_weight]
        best_weight_unit = best_weight_rows.iloc[0]['unit'] if not best_weight_rows.empty else 'kg'
        best_weight_dates = sorted(best_weight_rows['date'].unique().tolist(), reverse=True)
        
        # Get best reps and its date(s)
        best_reps = logs_df['reps'].max()
        best_reps_rows = logs_df[logs_df['reps'] == best_reps]
        best_reps_dates = sorted(best_reps_rows['date'].unique().tolist(), reverse=True)
        
        # Get best volume and its date(s)
        logs_df['volume'] = logs_df['weight'] * logs_df['reps']
        best_volume = logs_df['volume'].max()
        best_volume_rows = logs_df[logs_df['volume'] == best_volume]
        best_volume_dates = sorted(best_volume_rows['date'].unique().tolist(), reverse=True)
        
        pr_dict[exercise_name] = {
            'best_weight': float(best_weight),
            'best_weight_unit': best_weight_unit,
            'best_weight_dates': best_weight_dates,
            'best_reps': int(best_reps),
            'best_reps_dates': best_reps_dates,
            'best_volume': float(best_volume),
            'best_volume_dates': best_volume_dates,
            'is_assisted': is_assisted
        }
    
    return pr_dict


def rename_exercise(user_id: str, old_name: str, new_name: str) -> Tuple[int, int]:
    """
    Rename an exercise in both exercises table and workout_logs table
    
    Args:
        user_id: User UUID
        old_name: Current exercise name
        new_name: New exercise name
    
    Returns:
        Tuple of (exercises_updated_count, workout_logs_updated_count)
    """
    supabase = get_supabase()
    
    exercises_updated = 0
    workout_logs_updated = 0
    
    try:
        # Update exercises table
        result_exercises = supabase.table("exercises")\
            .update({"name": new_name})\
            .eq("user_id", user_id)\
            .eq("name", old_name)\
            .execute()
        
        exercises_updated = len(result_exercises.data) if result_exercises.data else 0
        
        # Update workout_logs table
        result_logs = supabase.table("workout_logs")\
            .update({"exercise_name": new_name})\
            .eq("user_id", user_id)\
            .eq("exercise_name", old_name)\
            .execute()
        
        workout_logs_updated = len(result_logs.data) if result_logs.data else 0
        
    except Exception as e:
        print(f"Error renaming exercise: {e}")
    
    return exercises_updated, workout_logs_updated


def update_workout_set(user_id: str, set_id: int, weight: float, unit: str, reps: int, rpe: Optional[int] = None, notes: Optional[str] = None) -> bool:
    """
    Update a single workout set by ID
    
    Args:
        user_id: User UUID
        set_id: Workout log ID
        weight: Weight value
        unit: Unit (kg, lb, notch, notch/plate)
        reps: Number of reps
        rpe: Rate of Perceived Exertion (1-10, optional)
        notes: Optional notes
    
    Returns:
        True if successful, False if set not found or user doesn't own it
    """
    supabase = get_supabase()
    
    try:
        # First verify the set exists and belongs to the user
        check_result = supabase.table("workout_logs")\
            .select("id")\
            .eq("id", set_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check_result.data:
            return False
        
        # Update the set
        update_data = {
            "weight": weight,
            "unit": unit,
            "reps": reps
        }
        
        if rpe is not None:
            update_data["rpe"] = rpe
        if notes is not None:
            update_data["notes"] = notes
        
        result = supabase.table("workout_logs")\
            .update(update_data)\
            .eq("id", set_id)\
            .eq("user_id", user_id)\
            .execute()
        
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        print(f"Error updating workout set: {e}")
        return False


def delete_workout_set(user_id: str, set_id: int) -> bool:
    """
    Delete a single workout set by ID
    
    Args:
        user_id: User UUID
        set_id: Workout log ID
    
    Returns:
        True if successful, False if set not found or user doesn't own it
    """
    supabase = get_supabase()
    
    try:
        # First verify the set exists and belongs to the user
        check_result = supabase.table("workout_logs")\
            .select("id")\
            .eq("id", set_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not check_result.data:
            return False
        
        # Delete the set
        result = supabase.table("workout_logs")\
            .delete()\
            .eq("id", set_id)\
            .eq("user_id", user_id)\
            .execute()
        
        return True
    except Exception as e:
        print(f"Error deleting workout set: {e}")
        return False


def get_workout_session_ids(user_id: str, workout_date: date, exercise_name: str) -> List[int]:
    """
    Get all set IDs for a workout session (same date + exercise)
    
    Args:
        user_id: User UUID
        workout_date: Workout date
        exercise_name: Name of the exercise
    
    Returns:
        List of workout log IDs
    """
    supabase = get_supabase()
    
    result = supabase.table("workout_logs")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("date", workout_date.isoformat())\
        .eq("exercise_name", exercise_name)\
        .execute()
    
    if result.data:
        return [row['id'] for row in result.data]
    return []


def delete_workout_session(user_id: str, workout_date: date, exercise_name: str) -> int:
    """
    Delete all sets for a workout session (same date + exercise)
    
    Args:
        user_id: User UUID
        workout_date: Workout date
        exercise_name: Name of the exercise
    
    Returns:
        Number of deleted sets (0 if none found or user doesn't own them)
    """
    supabase = get_supabase()
    
    try:
        # First get the IDs to count them
        set_ids = get_workout_session_ids(user_id, workout_date, exercise_name)
        
        if not set_ids:
            return 0
        
        # Delete all sets for this session
        result = supabase.table("workout_logs")\
            .delete()\
            .eq("user_id", user_id)\
            .eq("date", workout_date.isoformat())\
            .eq("exercise_name", exercise_name)\
            .execute()
        
        return len(set_ids)
    except Exception as e:
        print(f"Error deleting workout session: {e}")
        return 0


def delete_all_exercise_workouts(user_id: str, exercise_name: str) -> int:
    """
    Delete all workout logs for a specific exercise (across all dates).

    Args:
        user_id: User UUID
        exercise_name: Name of the exercise

    Returns:
        Number of deleted workout logs (0 if none found or user doesn't own them)
    """
    supabase = get_supabase()

    try:
        # First get IDs to know how many rows will be deleted
        result = supabase.table("workout_logs")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("exercise_name", exercise_name)\
            .execute()

        if not result.data:
            return 0

        set_ids = [row["id"] for row in result.data]

        # Delete all logs for this exercise
        supabase.table("workout_logs")\
            .delete()\
            .eq("user_id", user_id)\
            .eq("exercise_name", exercise_name)\
            .execute()

        return len(set_ids)
    except Exception as e:
        print(f"Error deleting all workouts for exercise '{exercise_name}': {e}")
        return 0
