"""Fix Preacher Curl (Single Arm) muscle group to 二頭肌 (Biceps)"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth import get_supabase_client

load_dotenv()

supabase = get_supabase_client()

# Update muscle group for Preacher Curl (Single Arm)
result = supabase.table("exercises")\
    .update({"muscle_group": "二頭肌 (Biceps)"})\
    .eq("name", "Preacher Curl (Single Arm)")\
    .execute()

if result.data:
    print(f"✅ Updated {len(result.data)} exercise(s) to muscle group '二頭肌 (Biceps)'")
    for ex in result.data:
        print(f"   - {ex['name']} is now in {ex['muscle_group']}")
else:
    print("No exercises found to update")

