"""
Helper utilities for Gym Tracker App
Includes common helper functions
"""

from datetime import date, datetime
from typing import List, Tuple


def get_muscle_groups() -> List[str]:
    """
    Get list of muscle groups
    
    Returns:
        List of muscle group names
    """
    return [
        '胸 (Chest)',
        '背 (Back)',
        '肩 (Shoulders)',
        '腿 (Legs)',
        '手臂 (Arms)',
        '核心 (Core)',
        '其他 (Other)'
    ]


def map_muscle_group(csv_muscle_group: str) -> str:
    """
    Map CSV muscle group name to app's muscle group format
    
    Args:
        csv_muscle_group: Muscle group from CSV (e.g., "Chest", "Back")
    
    Returns:
        Mapped muscle group in app format (e.g., "胸 (Chest)")
    """
    mapping = {
        'chest': '胸 (Chest)',
        'back': '背 (Back)',
        'shoulders': '肩 (Shoulders)',
        'shoulder': '肩 (Shoulders)',
        'legs': '腿 (Legs)',
        'leg': '腿 (Legs)',
        'arms': '手臂 (Arms)',
        'arm': '手臂 (Arms)',
        'core': '核心 (Core)',
        'other': '其他 (Other)'
    }
    
    # Normalize input (lowercase, strip whitespace)
    normalized = csv_muscle_group.lower().strip()
    
    # Direct match
    if normalized in mapping:
        return mapping[normalized]
    
    # Partial match (e.g., "Chest" matches "chest")
    for key, value in mapping.items():
        if key in normalized or normalized in key:
            return value
    
    # Default to Other if no match
    return '其他 (Other)'


def infer_exercise_type(exercise_name: str) -> str:
    """
    Infer exercise type from exercise name
    
    Args:
        exercise_name: Name of the exercise
    
    Returns:
        Exercise type (Barbell, Dumbbell, Machine, Cable, Bodyweight, Other)
    """
    name_lower = exercise_name.lower()
    
    if any(keyword in name_lower for keyword in ['barbell', 'bb ']):
        return 'Barbell'
    elif any(keyword in name_lower for keyword in ['dumbbell', 'db ', 'single-arm']):
        return 'Dumbbell'
    elif any(keyword in name_lower for keyword in ['cable', 'pulley']):
        return 'Cable'
    elif any(keyword in name_lower for keyword in ['machine', 'seated', 'press machine']):
        return 'Machine'
    elif any(keyword in name_lower for keyword in ['pull-up', 'push-up', 'dip', 'plank', 'bodyweight']):
        return 'Bodyweight'
    else:
        return 'Other'


def is_assisted_exercise(exercise_name: str) -> bool:
    """
    Check if an exercise is an assisted exercise
    
    Args:
        exercise_name: Name of the exercise
    
    Returns:
        True if the exercise is assisted (lower weight = better performance)
    """
    assisted_keywords = ['assisted', 'assist', '減重', '輔助']
    exercise_lower = exercise_name.lower()
    return any(keyword in exercise_lower for keyword in assisted_keywords)


def get_exercise_types() -> List[str]:
    """
    Get list of exercise types
    
    Returns:
        List of exercise type names
    """
    return [
        'Barbell',
        'Dumbbell',
        'Machine',
        'Cable',
        'Bodyweight',
        'Other'
    ]


def format_date(date_obj: date) -> str:
    """
    Format date object to string
    
    Args:
        date_obj: Date object
    
    Returns:
        Formatted date string (YYYY-MM-DD)
    """
    return date_obj.strftime('%Y-%m-%d')


def parse_date(date_str: str) -> date:
    """
    Parse date string to date object
    
    Args:
        date_str: Date string (YYYY-MM-DD)
    
    Returns:
        Date object
    """
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def validate_input(weight: float, reps: int, unit: str) -> Tuple[bool, str]:
    """
    Validate workout input data
    
    Args:
        weight: Weight value
        reps: Number of repetitions
        unit: Weight unit
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if weight < 0:
        return False, "重量不能為負數"
    
    if reps < 0:
        return False, "次數不能為負數"
    
    if reps == 0 and weight > 0:
        return False, "次數不能為 0"
    
    if unit not in ['kg', 'lb', 'notch', 'notch/plate']:
        return False, "不支援的單位"
    
    return True, ""


def format_weight(weight: float, unit: str) -> str:
    """
    Format weight with unit for display
    
    Args:
        weight: Weight value
        unit: Weight unit
    
    Returns:
        Formatted weight string
    """
    if unit == 'notch' or unit == 'notch/plate':
        return f"{int(weight)} {unit}"
    else:
        return f"{weight:.1f} {unit}"


def get_weight_options(unit: str) -> List[float]:
    """
    Get weight options for dropdown based on unit
    
    Args:
        unit: Weight unit (kg, lb, or notch/plate)
    
    Returns:
        List of weight values
    """
    if unit == "kg":
        # Common kg weights: 0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, then by 5kg up to 200kg
        weights = [0.0]
        weights.extend([2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0])
        weights.extend([i * 5.0 for i in range(5, 41)])  # 25 to 200 in 5kg steps
        return weights
    elif unit == "lb":
        # Common lb weights: 0, 5, 10, then by 5lb up to 450lb
        weights = [0.0]
        weights.extend([5.0, 10.0])
        weights.extend([i * 5.0 for i in range(3, 91)])  # 15 to 450 in 5lb steps
        return weights
    else:  # notch/plate
        # Notch/plate: 0 to 30
        return [float(i) for i in range(31)]


def get_reps_options() -> List[int]:
    """
    Get reps options for dropdown
    
    Returns:
        List of rep values
    """
    # Common rep ranges: 0, then 1-30
    return [0] + list(range(1, 31))


def get_default_exercises() -> dict:
    """
    Get default exercise library organized by muscle group
    Includes all exercises from user's database
    
    Returns:
        Dictionary with muscle groups as keys and exercise lists as values
    """
    return {
        '胸 (Chest)': [
            'Barbell Bench Press',
            'Bench Press',
            'Cable Chest Fly (Mid/Kneeling)',
            'Cable Chest Fly (High-to-Low)',
            'Cable Chest Fly (Low-to-High)',
            'Seated Chest Press (Machine)',
            'Seated Chest Press (Horizontal)',
            'Seated Chest Press (Vertical)',
            'Machine Chest Fly',
            'Incline Dumbbell Press',
            'Dumbbell Fly',
            'Incline Bench Press',
            'Cable Chest Fly',
            'Push-up'
        ],
        '背 (Back)': [
            'Single-Arm Cable Row',
            'Lat Pulldown (Wide)',
            'Lat Pulldown (Reverse)',
            'Lat Pulldown (Narrow)',
            'Pull-up',
            'Assisted Pull-up',
            'Seated Cable Row (Both Hands)',
            'Back Extension',
            'Dead Hang',
            'Lat Pulldown',
            'Barbell Row',
            'Dumbbell Row',
            'Cable Row'
        ],
        '肩 (Shoulders)': [
            'Overhead Press',
            'Lateral Raise',
            'Front Raise',
            'Rear Delt Fly',
            'Shrug'
        ],
        '腿 (Legs)': [
            'Squat',
            'Deadlift',
            'Leg Press',
            'Leg Curl',
            'Leg Extension'
        ],
        '手臂 (Arms)': [
            'Preacher Curl',
            'Dumbbell Bicep Curl (Single Arm)',
            'Bicep Curl',
            'Tricep Extension',
            'Hammer Curl',
            'Tricep Dip'
        ],
        '核心 (Core)': [
            'Plank',
            'Crunches',
            'Russian Twist',
            'Leg Raise'
        ],
        '其他 (Other)': []
    }

