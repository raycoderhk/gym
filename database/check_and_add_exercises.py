"""
Check existing exercises and add execution steps, or create exercises if they don't exist
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
from utils.helpers import infer_exercise_type, get_muscle_groups

load_dotenv()


def find_exercise_by_name(exercises_list, target_name):
    """Find exercise by name (case-insensitive, partial match)"""
    target_lower = target_name.lower()
    for ex in exercises_list:
        if ex['name'].lower() == target_lower:
            return ex['name']
        # Try partial match
        if target_lower in ex['name'].lower() or ex['name'].lower() in target_lower:
            return ex['name']
    return None


def add_exercise_steps_with_creation(user_id: str):
    """Add execution steps, creating exercises if they don't exist"""
    
    # Get all existing exercises
    all_exercises = get_all_exercises(user_id)
    print(f"Found {len(all_exercises)} existing exercises in database\n")
    
    # Exercise 1: Assisted Pull-Up
    assisted_pullup_steps = """## 執行步驟

### 握法策略
- **組數 1, 2, 4**: **中立握法** (Neutral Grip) - 掌心相對，保護肩膀
- **組數 3**: **安全寬握** (Safe Wide Grip) - 手比肩膀稍寬

### 安全注意事項
- 啟動核心 (Hollow Body)
- 如果左肩在寬握時感到夾擠，立即切換為中立握法

### 節奏
- 快速向上 (1秒)
- 頂峰收縮 (1秒)
- 控制下降 (2-3秒)

### 組數結構

**熱身組 (Warm-up Set):**
- **70+ lbs 輔助** × 10 次 (輕負荷，活動關節。中立握法)

**組數 1 (目標: 力量):**
- **28 lbs 輔助** × 5–8 次 (**中立握法**)

**組數 2 (目標: 容量):**
- **34 lbs 輔助** × 8–10 次 (**中立握法**)

**組數 3 (目標: 肌肥大):**
- **34-40 lbs 輔助** × 8–10 次 (**安全寬握**)

**組數 4 (目標: 力竭):**
- **46-52 lbs 輔助** × 12–15+ 次 (**中立握法**)
"""

    # Exercise 2: Single Arm Cable Row
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

    exercises_to_update = [
        {
            "name": "Assisted Pull-Up",
            "steps": assisted_pullup_steps,
            "muscle_group": "Back",
            "exercise_type": "Machine"
        },
        {
            "name": "Single-Arm Cable Row",
            "steps": single_arm_cable_row_steps,
            "muscle_group": "Back",
            "exercise_type": "Cable"
        }
    ]
    
    print("=" * 60)
    print("Adding Execution Steps to Exercises")
    print("=" * 60)
    print(f"\nUser ID: {user_id}\n")
    
    success_count = 0
    created_count = 0
    error_count = 0
    
    for ex in exercises_to_update:
        ex_name = ex["name"]
        steps = ex["steps"]
        muscle_group = ex["muscle_group"]
        exercise_type = ex["exercise_type"]
        
        print(f"Processing: {ex_name}")
        
        # Try to find existing exercise
        existing_name = find_exercise_by_name(all_exercises, ex_name)
        
        if existing_name:
            print(f"  Found existing exercise: '{existing_name}'")
            # Update execution steps
            if update_exercise_steps(user_id, existing_name, steps):
                print(f"  [SUCCESS] Updated execution steps")
                success_count += 1
            else:
                print(f"  [ERROR] Failed to update execution steps")
                error_count += 1
        else:
            # Exercise doesn't exist, create it
            print(f"  Exercise not found, creating new exercise...")
            exercise_type_inferred = infer_exercise_type(ex_name)
            if add_custom_exercise(user_id, ex_name, muscle_group, exercise_type_inferred, steps):
                print(f"  [SUCCESS] Created exercise with execution steps")
                created_count += 1
                success_count += 1
            else:
                print(f"  [ERROR] Failed to create exercise (may already exist with different name)")
                error_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  [SUCCESS] {success_count}")
    print(f"  [CREATED] {created_count}")
    print(f"  [ERRORS] {error_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python database/check_and_add_exercises.py <user_id>")
        print("\nExample:")
        print("  python database/check_and_add_exercises.py 296e1b06-c10d-4045-a642-e0797958f592")
        sys.exit(1)
    
    user_id = sys.argv[1]
    add_exercise_steps_with_creation(user_id)

