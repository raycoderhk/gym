"""
Script to clear all data from the database
Run: python clear_data.py
"""
from database.db_manager import clear_all_data

print("⚠️  警告：此操作將清除所有訓練記錄和動作庫！")
print("此操作無法復原！")
response = input("確定要清除所有資料嗎？(輸入 'YES' 確認): ")

if response == 'YES':
    workout_count, exercise_count = clear_all_data()
    print(f"✅ 已清除所有資料：")
    print(f"   - {workout_count} 筆訓練記錄")
    print(f"   - {exercise_count} 個動作")
    print("\n資料庫已清空，您可以重新匯入資料。")
else:
    print("❌ 操作已取消。")

