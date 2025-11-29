"""
Script to add execution steps for specific exercises
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import get_exercise_details, update_exercise_steps, get_supabase
from src.auth import get_supabase_client

load_dotenv()


def get_user_id_from_email(email: str):
    """Get user_id from email using the lookup function"""
    try:
        supabase = get_supabase()
        result = supabase.rpc('get_user_id_by_email', {'user_email': email}).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('id')
    except:
        pass
    return None


def add_exercise_steps(user_id: str):
    """Add execution steps for Assisted Pull-Up and Single Arm Cable Row"""
    
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
            "steps": assisted_pullup_steps
        },
        {
            "name": "Single Arm Cable Row",
            "steps": single_arm_cable_row_steps
        }
    ]
    
    print("=" * 60)
    print("Adding Execution Steps to Exercises")
    print("=" * 60)
    print(f"\nUser ID: {user_id}\n")
    
    success_count = 0
    error_count = 0
    
    for ex in exercises_to_update:
        ex_name = ex["name"]
        steps = ex["steps"]
        
        print(f"Updating: {ex_name}")
        
        # Check if exercise exists
        exercise_data = get_exercise_details(user_id, ex_name)
        if not exercise_data:
            print(f"  [WARNING] Exercise '{ex_name}' not found in database")
            print(f"  Please create this exercise first in the Library Manager")
            error_count += 1
            continue
        
        # Update execution steps
        if update_exercise_steps(user_id, ex_name, steps):
            print(f"  [SUCCESS] Successfully updated execution steps")
            success_count += 1
        else:
            print(f"  [ERROR] Failed to update execution steps")
            error_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  [SUCCESS] {success_count}")
    print(f"  [ERRORS] {error_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python database/add_exercise_steps.py <user_id>")
        print("  python database/add_exercise_steps.py --email <email>")
        print("\nExample:")
        print("  python database/add_exercise_steps.py 123e4567-e89b-12d3-a456-426614174000")
        print("  python database/add_exercise_steps.py --email raymondcuhk@gmail.com")
        sys.exit(1)
    
    user_id = None
    email = None
    
    if "--email" in sys.argv:
        email_idx = sys.argv.index("--email")
        if email_idx + 1 < len(sys.argv):
            email = sys.argv[email_idx + 1]
            user_id = get_user_id_from_email(email)
            if not user_id:
                print(f"[ERROR] Could not find user_id for email: {email}")
                print("Please provide user_id directly or run the lookup function SQL first")
                print("\nTo find your user_id, run this SQL in Supabase SQL Editor:")
                print(f"SELECT id, email FROM auth.users WHERE email = '{email}';")
                sys.exit(1)
        else:
            print("[ERROR] --email requires an email address")
            sys.exit(1)
    else:
        user_id = sys.argv[1]
    
    add_exercise_steps(user_id)

