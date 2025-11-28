"""
Database management module for Gym Tracker App
Handles all SQLite database operations
"""

import sqlite3
import os
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Database file path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'gym_tracker.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_connection():
    """Get database connection"""
    # Ensure data directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_database():
    """Initialize database and create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Read and execute schema
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()


def save_workout(date: date, exercise_name: str, sets: List[Dict], rpe: Optional[int] = None, notes: Optional[str] = None):
    """
    Save workout data to database
    
    Args:
        date: Workout date
        exercise_name: Name of the exercise
        sets: List of dictionaries with keys: weight, unit, reps, set_order
        rpe: Rate of Perceived Exertion (1-10)
        notes: Optional notes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    for set_data in sets:
        cursor.execute("""
            INSERT INTO workout_logs (date, exercise_name, set_order, weight, unit, reps, rpe, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            exercise_name,
            set_data.get('set_order', 1),
            set_data['weight'],
            set_data['unit'],
            set_data['reps'],
            rpe,
            notes
        ))
    
    conn.commit()
    conn.close()


def get_previous_workout(exercise_name: str) -> Optional[Dict]:
    """
    Get the most recent workout for a specific exercise
    
    Returns:
        Dictionary with previous workout data or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT weight, unit, reps, rpe, date
        FROM workout_logs
        WHERE exercise_name = ?
        ORDER BY date DESC, set_order ASC
        LIMIT 1
    """, (exercise_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'weight': result[0],
            'unit': result[1],
            'reps': result[2],
            'rpe': result[3],
            'date': result[4]
        }
    return None


def get_exercise_history(exercise_name: str, days: Optional[int] = None) -> pd.DataFrame:
    """
    Get exercise history as DataFrame
    
    Args:
        exercise_name: Name of the exercise
        days: Number of days to look back (None for all)
    
    Returns:
        DataFrame with exercise history
    """
    conn = get_connection()
    
    if days:
        query = """
            SELECT date, set_order, weight, unit, reps, rpe, notes
            FROM workout_logs
            WHERE exercise_name = ? AND date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC, set_order ASC
        """
        df = pd.read_sql_query(query, conn, params=(exercise_name, days))
    else:
        query = """
            SELECT date, set_order, weight, unit, reps, rpe, notes
            FROM workout_logs
            WHERE exercise_name = ?
            ORDER BY date DESC, set_order ASC
        """
        df = pd.read_sql_query(query, conn, params=(exercise_name,))
    
    conn.close()
    return df


def get_all_exercises() -> List[Dict]:
    """
    Get all exercises from the library
    
    Returns:
        List of exercise dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, muscle_group, exercise_type
        FROM exercises
        ORDER BY muscle_group, name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': row[0],
            'name': row[1],
            'muscle_group': row[2],
            'exercise_type': row[3]
        }
        for row in results
    ]


def get_exercise_entry_counts() -> Dict[str, int]:
    """
    Get entry count for each exercise
    
    Returns:
        Dictionary with exercise names as keys and entry counts as values
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT exercise_name, COUNT(*) as count
        FROM workout_logs
        GROUP BY exercise_name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return {row[0]: row[1] for row in results}


def get_exercises_by_muscle_group(muscle_group: str) -> List[str]:
    """
    Get exercise names for a specific muscle group
    
    Returns:
        List of exercise names
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name
        FROM exercises
        WHERE muscle_group = ?
        ORDER BY name
    """, (muscle_group,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in results]


def add_custom_exercise(name: str, muscle_group: str, exercise_type: str) -> bool:
    """
    Add a custom exercise to the library
    
    Returns:
        True if successful, False if exercise already exists
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO exercises (name, muscle_group, exercise_type)
            VALUES (?, ?, ?)
        """, (name, muscle_group, exercise_type))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_todays_workouts(workout_date: date) -> pd.DataFrame:
    """
    Get all workouts for a specific date
    
    Returns:
        DataFrame with today's workouts
    """
    conn = get_connection()
    
    query = """
        SELECT exercise_name, set_order, weight, unit, reps, rpe, notes
        FROM workout_logs
        WHERE date = ?
        ORDER BY exercise_name, set_order ASC
    """
    
    df = pd.read_sql_query(query, conn, params=(workout_date,))
    conn.close()
    return df


def get_all_workouts(days: Optional[int] = None) -> pd.DataFrame:
    """
    Get all workout logs
    
    Args:
        days: Number of days to look back (None for all)
    
    Returns:
        DataFrame with all workouts
    """
    conn = get_connection()
    
    if days:
        query = """
            SELECT date, exercise_name, set_order, weight, unit, reps, rpe, notes
            FROM workout_logs
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC, exercise_name, set_order ASC
        """
        df = pd.read_sql_query(query, conn, params=(days,))
    else:
        query = """
            SELECT date, exercise_name, set_order, weight, unit, reps, rpe, notes
            FROM workout_logs
            ORDER BY date DESC, exercise_name, set_order ASC
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df


def get_muscle_group_stats(days: int = 30) -> pd.DataFrame:
    """
    Get training volume statistics by muscle group
    
    Args:
        days: Number of days to analyze
    
    Returns:
        DataFrame with muscle group statistics
    """
    conn = get_connection()
    
    query = """
        SELECT 
            e.muscle_group,
            COUNT(wl.id) as total_sets,
            COUNT(DISTINCT wl.date) as workout_days
        FROM workout_logs wl
        JOIN exercises e ON wl.exercise_name = e.name
        WHERE wl.date >= date('now', '-' || ? || ' days')
        GROUP BY e.muscle_group
        ORDER BY total_sets DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(days,))
    conn.close()
    return df


def import_workout_from_csv(df: pd.DataFrame) -> Tuple[int, int, List[str]]:
    """
    Import workout data from CSV DataFrame
    
    Args:
        df: DataFrame with columns: Date, Muscle Group, Exercise, Set Order, Weight, Unit, Reps, Note
    
    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    from utils.helpers import map_muscle_group, infer_exercise_type
    
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    error_messages = []
    
    # Required columns
    required_columns = ['Date', 'Exercise', 'Set Order', 'Weight', 'Unit', 'Reps']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_messages.append(f"缺少必要欄位: {', '.join(missing_columns)}")
        conn.close()
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
            cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,))
            if cursor.fetchone() is None:
                # Add exercise to library
                exercise_type = infer_exercise_type(exercise_name)
                try:
                    cursor.execute("""
                        INSERT INTO exercises (name, muscle_group, exercise_type)
                        VALUES (?, ?, ?)
                    """, (exercise_name, muscle_group, exercise_type))
                except sqlite3.IntegrityError:
                    # Exercise might have been added by another row, ignore
                    pass
            
            # Insert workout log
            cursor.execute("""
                INSERT INTO workout_logs (date, exercise_name, set_order, weight, unit, reps, rpe, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (workout_date, exercise_name, set_order, weight, unit, reps, None, notes))
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            error_messages.append(f"第 {idx + 2} 行: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    return success_count, error_count, error_messages


def clear_all_data() -> Tuple[int, int]:
    """
    Clear all workout logs and exercises from database
    
    Returns:
        Tuple of (deleted_workout_logs_count, deleted_exercises_count)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get counts before deletion
    cursor.execute("SELECT COUNT(*) FROM workout_logs")
    workout_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM exercises")
    exercise_count = cursor.fetchone()[0]
    
    # Delete all data
    cursor.execute("DELETE FROM workout_logs")
    cursor.execute("DELETE FROM exercises")
    
    conn.commit()
    conn.close()
    
    return workout_count, exercise_count


def get_pr_records() -> Dict[str, Dict]:
    """
    Get personal records for all exercises with dates
    
    Returns:
        Dictionary with exercise names as keys and PR data as values
        Each PR includes the value and the date(s) when it was achieved
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all exercises
    cursor.execute("SELECT DISTINCT exercise_name FROM workout_logs")
    exercises = [row[0] for row in cursor.fetchall()]
    
    pr_dict = {}
    
    for exercise_name in exercises:
        # Get best weight, unit, and its date(s)
        cursor.execute("""
            SELECT date, weight, unit
            FROM workout_logs
            WHERE exercise_name = ?
            ORDER BY weight DESC, date DESC
            LIMIT 1
        """, (exercise_name,))
        best_weight_row = cursor.fetchone()
        best_weight = best_weight_row[1] if best_weight_row else 0
        best_weight_unit = best_weight_row[2] if best_weight_row else 'kg'
        best_weight_date = best_weight_row[0] if best_weight_row else None
        
        # Get all dates with best weight (in case of ties)
        cursor.execute("""
            SELECT DISTINCT date
            FROM workout_logs
            WHERE exercise_name = ? AND weight = ?
            ORDER BY date DESC
        """, (exercise_name, best_weight))
        best_weight_dates = [row[0] for row in cursor.fetchall()]
        
        # Get best reps and its date(s)
        cursor.execute("""
            SELECT date, reps
            FROM workout_logs
            WHERE exercise_name = ?
            ORDER BY reps DESC, date DESC
            LIMIT 1
        """, (exercise_name,))
        best_reps_row = cursor.fetchone()
        best_reps = best_reps_row[1] if best_reps_row else 0
        best_reps_date = best_reps_row[0] if best_reps_row else None
        
        # Get all dates with best reps
        cursor.execute("""
            SELECT DISTINCT date
            FROM workout_logs
            WHERE exercise_name = ? AND reps = ?
            ORDER BY date DESC
        """, (exercise_name, best_reps))
        best_reps_dates = [row[0] for row in cursor.fetchall()]
        
        # Get best volume and its date(s)
        cursor.execute("""
            SELECT date, weight, reps, (weight * reps) as volume
            FROM workout_logs
            WHERE exercise_name = ?
            ORDER BY (weight * reps) DESC, date DESC
            LIMIT 1
        """, (exercise_name,))
        best_volume_row = cursor.fetchone()
        best_volume = best_volume_row[3] if best_volume_row else 0
        best_volume_date = best_volume_row[0] if best_volume_row else None
        
        # Get all dates with best volume
        cursor.execute("""
            SELECT DISTINCT date
            FROM workout_logs
            WHERE exercise_name = ? AND (weight * reps) = ?
            ORDER BY date DESC
        """, (exercise_name, best_volume))
        best_volume_dates = [row[0] for row in cursor.fetchall()]
        
        pr_dict[exercise_name] = {
            'best_weight': best_weight,
            'best_weight_unit': best_weight_unit,
            'best_weight_dates': best_weight_dates,
            'best_reps': best_reps,
            'best_reps_dates': best_reps_dates,
            'best_volume': best_volume,
            'best_volume_dates': best_volume_dates
        }
    
    conn.close()
    return pr_dict

