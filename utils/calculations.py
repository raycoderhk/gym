"""
Calculation utilities for Gym Tracker App
Includes 1RM calculation, unit conversion, and volume calculations
"""


def calculate_1rm(weight: float, reps: int) -> float:
    """
    Calculate estimated 1RM using Epley formula
    
    Formula: Weight × (1 + Reps/30)
    
    Args:
        weight: Weight lifted
        reps: Number of repetitions
    
    Returns:
        Estimated 1RM
    """
    if reps <= 0:
        return weight
    if reps == 1:
        return weight
    
    return weight * (1 + reps / 30)


def convert_unit(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert weight between different units
    
    Supported units:
    - kg: kilograms
    - lb: pounds
    - notch: cable machine notch (assumed 1 notch ≈ 2.5 kg)
    
    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit
    
    Returns:
        Converted value
    """
    if from_unit == to_unit:
        return value
    
    # Convert to kg first (standard unit)
    if from_unit == 'kg':
        kg_value = value
    elif from_unit == 'lb':
        kg_value = value * 0.453592  # 1 lb = 0.453592 kg
    elif from_unit == 'notch' or from_unit == 'notch/plate':
        kg_value = value * 2.5  # Assume 1 notch ≈ 2.5 kg
    else:
        # Unknown unit, return as is
        return value
    
    # Convert from kg to target unit
    if to_unit == 'kg':
        return kg_value
    elif to_unit == 'lb':
        return kg_value / 0.453592
    elif to_unit == 'notch' or to_unit == 'notch/plate':
        return kg_value / 2.5
    else:
        return kg_value


def standardize_weight(weight: float, unit: str) -> float:
    """
    Convert weight to kilograms for standardized analysis
    
    Args:
        weight: Weight value
        unit: Original unit
    
    Returns:
        Weight in kilograms
    """
    return convert_unit(weight, unit, 'kg')


def calculate_volume(weight: float, reps: int) -> float:
    """
    Calculate training volume (weight × reps)
    
    Args:
        weight: Weight lifted
        reps: Number of repetitions
    
    Returns:
        Training volume
    """
    return weight * reps


def calculate_total_volume(weight: float, reps: int, unit: str) -> float:
    """
    Calculate total volume in standardized units (kg)
    
    Args:
        weight: Weight lifted
        reps: Number of repetitions
        unit: Weight unit
    
    Returns:
        Total volume in kg
    """
    weight_kg = standardize_weight(weight, unit)
    return calculate_volume(weight_kg, reps)


def calculate_session_volume(sets: list) -> float:
    """
    Calculate total volume for a training session
    
    Args:
        sets: List of dictionaries with 'weight', 'reps', 'unit' keys
    
    Returns:
        Total session volume in kg
    """
    total_volume = 0.0
    for set_data in sets:
        weight = set_data.get('weight', 0)
        reps = set_data.get('reps', 0)
        unit = set_data.get('unit', 'kg')
        total_volume += calculate_total_volume(weight, reps, unit)
    return total_volume

