"""
Update execution steps for Single-Arm Cable Row specifically
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import (
    get_all_exercises, get_exercise_details, update_exercise_steps, 
    add_custom_exercise
)
from utils.helpers import infer_exercise_type

load_dotenv()


def update_single_arm_cable_row(user_id: str):
    """Update Single-Arm Cable Row execution steps"""
    
    single_arm_cable_row_steps = """## 執行步驟

### 優先順序
- **先做左側** (較弱/受傷側)
- 右側必須與左側次數相同，不要做更多

### 動作要領
- 保持胸部挺起
- 不要扭轉軀幹
- 手肘拉向臀部口袋方向

### 穩定性
- 雙腳穩固踩地
- 非工作側手放在大腿上支撐

### 組數結構

**熱身組 (Warm-up Set):**
- **Notch 2** × 10-12 次 (專注於完整伸展和流暢收縮)

**組數 1 (目標: PR 力量):**
- **Notch 4.5** × 6–8 次

**組數 2 (目標: 容量):**
- **Notch 4** × 8–10 次

**組數 3 (目標: 肌肥大):**
- **Notch 3.5 (或 3)** × 10–12 次

**組數 4 (目標: 肌耐力):**
- **Notch 2.5 (或 3)** × 15–20 次 (快速拉，慢速放)
"""

    print("=" * 60)
    print("Updating Single-Arm Cable Row")
    print("=" * 60)
    print(f"\nUser ID: {user_id}\n")
    
    # Get all exercises
    all_exercises = get_all_exercises(user_id)
    
    # Check if "Single-Arm Cable Row" exists
    target_name = "Single-Arm Cable Row"
    found = False
    
    for ex in all_exercises:
        if ex['name'] == target_name:
            found = True
            print(f"Found exercise: '{target_name}'")
            if update_exercise_steps(user_id, target_name, single_arm_cable_row_steps):
                print(f"[SUCCESS] Updated execution steps for '{target_name}'")
            else:
                print(f"[ERROR] Failed to update execution steps")
            break
    
    if not found:
        print(f"Exercise '{target_name}' not found in database")
        print("Available exercises with 'cable' or 'row' in name:")
        for ex in all_exercises:
            name_lower = ex['name'].lower()
            if 'cable' in name_lower or 'row' in name_lower:
                print(f"  - {ex['name']}")
        
        # Check if we should create it
        print(f"\nWould you like to create '{target_name}'?")
        print("If yes, the exercise will be created with execution steps.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python database/update_single_arm_cable_row.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    update_single_arm_cable_row(user_id)

