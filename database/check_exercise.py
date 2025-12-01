"""Quick script to check if Preacher Curl (Single Arm) exists in database"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth import get_supabase_client

load_dotenv()

supabase = get_supabase_client()

# Get all exercises with "Preacher" or "Bicep Curl" in the name
result = supabase.table("exercises")\
    .select("name, muscle_group, exercise_type")\
    .or_("name.ilike.%Preacher%,name.ilike.%Bicep Curl%")\
    .execute()

print("Exercises found:")
print("=" * 60)
if result.data:
    for ex in result.data:
        print(f"Name: {ex['name']}")
        print(f"Muscle Group: {ex['muscle_group']}")
        print(f"Type: {ex['exercise_type']}")
        print("-" * 60)
else:
    print("No exercises found")

