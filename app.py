"""
Gym Tracker App - Main Application
A comprehensive workout tracking application built with Streamlit
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# Import authentication module
from src.auth import (
    get_supabase_client, get_cookie_manager, ensure_cookies_loaded,
    continue_cookie_setting_if_needed, _clear_cookie_cache,
    handle_auth_callback, ensure_authentication, get_current_user,
    login_with_email, signup_with_email, login_with_google, logout
)

# Import database and utility modules
from database.db_manager import (
    init_database, save_workout, get_previous_workout, get_previous_workout_session,
    get_exercise_history, get_all_exercises, get_exercises_by_muscle_group,
    add_custom_exercise, get_todays_workouts, get_all_workouts,
    get_muscle_group_stats, get_pr_records, import_workout_from_csv,
    get_exercise_entry_counts, get_exercise_details, update_exercise_steps,
    update_workout_set, delete_workout_set, delete_workout_session,
    get_exercise_workout_counts, get_recent_workout_sessions
)
from utils.calculations import (
    calculate_1rm, convert_unit, standardize_weight,
    calculate_volume, calculate_total_volume
)
from utils.helpers import (
    get_muscle_groups, get_exercise_types, format_weight,
    get_default_exercises, validate_input, get_weight_options, get_reps_options,
    is_assisted_exercise, infer_exercise_type
)

# Page configuration
st.set_page_config(
    page_title="My Gym Tracker",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def render_login_page():
    """Render the login/signup page"""
    st.title("🏋️ My Gym Tracker")
    st.markdown("### 請登入以繼續")
    
    tab_login, tab_signup = st.tabs(["登入", "註冊"])
    
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("登入", type="primary", use_container_width=True):
            if login_with_email(email, password):
                st.success("登入成功！")
                st.rerun()
        
        # Google OAuth
        st.markdown("---")
        google_auth_url = login_with_google()
        if google_auth_url:
            st.link_button("🔒 使用 Google 登入", google_auth_url, use_container_width=True)
        else:
            st.warning("Google 登入未設定。請檢查環境變數設定。")
    
    with tab_signup:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("確認 Password", type="password", key="signup_confirm_password")
        
        if st.button("註冊", type="primary", use_container_width=True):
            if new_password != confirm_password:
                st.error("密碼不一致")
            elif len(new_password) < 6:
                st.error("密碼長度至少需要 6 個字元")
            else:
                if signup_with_email(new_email, new_password):
                    st.success("註冊成功！您已自動登入。")
                    st.rerun()

# ============================================================================
# PAGE 1: LOG WORKOUT (記錄訓練)
# ============================================================================

def render_log_workout_page(user_id: str):
    """Render the Log Workout page"""
    st.header("📝 記錄訓練")
    
    # Date selection
    col1, col2 = st.columns([2, 1])
    with col1:
        workout_date = st.date_input("訓練日期", value=date.today())
    with col2:
        st.write("")  # Spacing
    
    # Muscle group and exercise selection
    muscle_groups = get_muscle_groups()
    
    # Track previous muscle group to detect changes
    if 'previous_muscle_group' not in st.session_state:
        st.session_state.previous_muscle_group = None
    
    selected_muscle_group = st.selectbox("選擇肌肉群", muscle_groups)
    
    # Get exercises for selected muscle group
    exercises = get_exercises_by_muscle_group(user_id, selected_muscle_group)
    if not exercises:
        st.info(f"「{selected_muscle_group}」目前沒有動作，請先在「動作庫管理」頁面新增動作。")
        return
    
    # Clear selected exercise if muscle group changed or if selected exercise is not in current group
    if st.session_state.previous_muscle_group != selected_muscle_group:
        st.session_state.previous_muscle_group = selected_muscle_group
        # Clear selected exercise when muscle group changes
        if 'selected_exercise' in st.session_state:
            st.session_state.selected_exercise = None
    
    # Also clear if selected exercise is not in the current muscle group's exercises
    if 'selected_exercise' in st.session_state and st.session_state.selected_exercise:
        if st.session_state.selected_exercise not in exercises:
            st.session_state.selected_exercise = None
    
    # Initialize selected exercise in session state if not set
    if 'selected_exercise' not in st.session_state:
        st.session_state.selected_exercise = None
    
    # Get workout counts for all exercises
    workout_counts = get_exercise_workout_counts(user_id)
    
    # Exercise selection with buttons
    st.subheader("選擇動作")
    
    # Create button grid (3 columns)
    num_cols = 3
    exercise_cols = st.columns(num_cols)
    
    # Display exercise buttons
    for idx, exercise_name in enumerate(exercises):
        col_idx = idx % num_cols
        with exercise_cols[col_idx]:
            # Get workout count for this exercise
            count = workout_counts.get(exercise_name, 0)
            # Format button label with count
            button_label = f"{exercise_name} ({count})" if count > 0 else exercise_name
            
            # Highlight selected button
            button_type = "primary" if st.session_state.selected_exercise == exercise_name else "secondary"
            if st.button(
                button_label,
                key=f"ex_btn_{exercise_name}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.selected_exercise = exercise_name
                st.rerun()
    
    # Get selected exercise
    selected_exercise = st.session_state.selected_exercise
    
    # Display execution steps if exercise is selected
    if selected_exercise:
        exercise_data = get_exercise_details(user_id, selected_exercise)
        if exercise_data and exercise_data.get('execution_steps'):
            st.info("📋 執行步驟")
            st.markdown(exercise_data['execution_steps'])
    
    # Check if exercise is selected before proceeding
    if not selected_exercise:
        st.info("請選擇一個動作以繼續")
        return
    
    # Auto-fill: Get recent workout sessions (last 3)
    recent_sessions = get_recent_workout_sessions(user_id, selected_exercise, limit=3)
    
    # Get previous workout for fallback (used in form defaults)
    previous_workout = get_previous_workout(user_id, selected_exercise)
    
    # Initialize session state for copied workout
    copy_key = f"copied_workout_{selected_exercise}"
    if copy_key not in st.session_state:
        st.session_state[copy_key] = None
    
    # Display recent workout sessions with copy buttons
    if recent_sessions:
        st.subheader("📊 最近訓練記錄")
        
        # Create columns for side-by-side display (3 columns for 3 workouts)
        num_sessions = len(recent_sessions)
        session_cols = st.columns(num_sessions)
        
        for idx, session in enumerate(recent_sessions):
            with session_cols[idx]:
                # Format date
                session_date = session['date']
                if isinstance(session_date, str):
                    from datetime import datetime
                    try:
                        session_date = datetime.fromisoformat(session_date.replace('Z', '+00:00')).date()
                    except:
                        pass
                
                # Header with date and copy button
                st.markdown(f"**{session_date}**")
                copy_btn_key = f"copy_btn_{selected_exercise}_{idx}_{session['date']}"
                if st.button("📋 複製", key=copy_btn_key, use_container_width=True, type="primary"):
                    st.session_state[copy_key] = session
                    # Also store unit and num_sets in session state to force update
                    copied_unit = session['unit']
                    st.session_state[f"{copy_key}_unit"] = copied_unit
                    st.session_state[f"{copy_key}_num_sets"] = len(session['sets'])
                    # Add a copy timestamp to force form widget reset
                    st.session_state[f"{copy_key}_copied_at"] = time.time()
                    # Clear old unit widget state to force reset
                    old_unit_key = f"unit_{selected_exercise}"
                    if old_unit_key in st.session_state:
                        del st.session_state[old_unit_key]
                    # Also clear any old unit keys with timestamps
                    for key in list(st.session_state.keys()):
                        if key.startswith(f"unit_{selected_exercise}_") and key != f"unit_{selected_exercise}_{int(st.session_state[f'{copy_key}_copied_at'])}":
                            del st.session_state[key]
                    # Clear adjustment states when copying
                    widget_suffix_for_clear = f"_{selected_exercise}_{int(st.session_state[f'{copy_key}_copied_at'])}"
                    for j in range(20):  # Clear up to 20 sets worth of adjustments
                        weight_adj_key = f"weight_adj_{j}{widget_suffix_for_clear}"
                        reps_adj_key = f"reps_adj_{j}{widget_suffix_for_clear}"
                        if weight_adj_key in st.session_state:
                            st.session_state[weight_adj_key] = 0
                        if reps_adj_key in st.session_state:
                            st.session_state[reps_adj_key] = 0
                    st.success("✅ 已複製訓練數據！")
                    st.rerun()
                
                # Display details directly (no expander)
                st.write(f"**單位:** {session['unit']}")
                
                # Display all sets in a table format
                sets_data = []
                for s in session['sets']:
                    sets_data.append({
                        '組數': s['set_order'],
                        '重量': format_weight(s['weight'], session['unit']),
                        '次數': f"{s['reps']} 次"
                    })
                
                if sets_data:
                    sets_df = pd.DataFrame(sets_data)
                    st.dataframe(sets_df, use_container_width=True, hide_index=True)
                
                # Display RPE and Notes if available
                    if session.get('rpe'):
                        st.write(f"**RPE:** {session['rpe']}/10")
                    if session.get('notes'):
                        st.write(f"**備註:** {session['notes']}")
    
    # Dynamic sets input table
    st.subheader("輸入訓練組數")
    
    # Check if we have copied workout data
    copied_data = st.session_state.get(copy_key)
    
    # Number of sets selector - use copied data if available
    num_sets_key = f"{copy_key}_num_sets"
    if num_sets_key in st.session_state:
        default_num_sets = st.session_state[num_sets_key]
    elif copied_data and 'sets' in copied_data:
        default_num_sets = len(copied_data['sets'])
    else:
        default_num_sets = 3
    
    num_sets = st.number_input("組數", min_value=1, max_value=10, value=default_num_sets, step=1, key=f"num_sets_{selected_exercise}")
    
    # Unit selection - use copied data if available
    unit_key = f"{copy_key}_unit"
    copy_timestamp = st.session_state.get(f"{copy_key}_copied_at", 0)
    # Use timestamp in unit key to force reset when copying
    # This ensures the radio button resets when we copy
    unit_widget_key = f"unit_{selected_exercise}_{int(copy_timestamp)}" if copy_timestamp > 0 else f"unit_{selected_exercise}"
    
    # Determine the correct unit index
    # Note: Database might store "notch" but radio button uses "notch/plate"
    unit_map = {"kg": 0, "lb": 1, "notch/plate": 2, "notch": 2}  # Map both "notch" and "notch/plate" to index 2
    default_unit_index = 0
    
    # Priority: 1) stored unit from copy, 2) copied_data unit, 3) default
    if unit_key in st.session_state:
        # Use the stored unit from copied data (highest priority)
        stored_unit = st.session_state[unit_key]
        # Normalize "notch" to "notch/plate" for radio button matching
        if stored_unit == "notch":
            stored_unit = "notch/plate"
        default_unit_index = unit_map.get(stored_unit, 0)
    elif copied_data and 'unit' in copied_data:
        # Use unit from copied data
        copied_unit = copied_data['unit']
        # Normalize "notch" to "notch/plate" for radio button matching
        if copied_unit == "notch":
            copied_unit = "notch/plate"
        default_unit_index = unit_map.get(copied_unit, 0)
    else:
        # Default to kg
        default_unit_index = 0
    
    # Create radio button with the correct index
    # If copy_timestamp > 0, the new key will force a reset and create a new widget
    unit = st.radio("單位", ["kg", "lb", "notch/plate"], index=default_unit_index, horizontal=True, key=unit_widget_key)
    
    # If we have copied data, use the copied unit for weight options and calculations
    # This ensures weights are correctly matched even if radio button hasn't visually updated yet
    effective_unit = unit
    if copied_data and 'unit' in copied_data:
        # When copying, prioritize the copied unit for weight calculations
        # But still respect user's manual unit selection if they change it
        if copy_timestamp > 0:  # Recently copied
            effective_unit = copied_data['unit']
        else:
            effective_unit = unit
    
    # Get weight and reps options based on effective unit
    weight_options = get_weight_options(effective_unit)
    reps_options = get_reps_options()
    
    # Dynamically add copied weights to options list if they don't exist
    # This preserves exact weights like 12, 17, 23 lbs when copying
    if copied_data and 'sets' in copied_data:
        copied_weights = set()
        copied_unit = copied_data.get('unit', effective_unit)
        
        # Extract all weights from copied sets
        for copied_set in copied_data['sets']:
            weight = copied_set['weight']
            # Convert to effective unit if needed
            if copied_unit != effective_unit:
                weight = convert_unit(weight, copied_unit, effective_unit)
            if weight > 0:
                copied_weights.add(weight)
        
        # Add missing weights to options list
        for weight in copied_weights:
            if weight not in weight_options:
                weight_options.append(weight)
        
        # Sort the combined list to maintain order
        weight_options = sorted(weight_options)
    
    # Create dynamic input form
    with st.form("workout_form", clear_on_submit=False):
        sets_data = []
        
        # Create columns for better layout
        col1, col2, col3 = st.columns([1, 1, 2])
        
        # Get copy timestamp to make widget keys unique when copying (already defined above for unit)
        widget_suffix = f"_{selected_exercise}_{int(copy_timestamp)}" if copy_timestamp > 0 else f"_{selected_exercise}"
        
        for i in range(num_sets):
            # Initialize adjustment keys in session state
            weight_adj_key = f"weight_adj_{i}{widget_suffix}"
            reps_adj_key = f"reps_adj_{i}{widget_suffix}"
            if weight_adj_key not in st.session_state:
                st.session_state[weight_adj_key] = 0
            if reps_adj_key not in st.session_state:
                st.session_state[reps_adj_key] = 0
            
            with col1:
                weight_key = f"weight_{i}{widget_suffix}"
                # Get default weight value - prioritize copied data
                default_weight = 0.0
                if copied_data and 'sets' in copied_data and i < len(copied_data['sets']):
                    # Use copied data if available
                    copied_set = copied_data['sets'][i]
                    # Get the unit from copied data
                    copied_unit = copied_data.get('unit', effective_unit)
                    # Use the weight directly if units match, otherwise convert
                    if effective_unit == copied_unit:
                        default_weight = copied_set['weight']
                    else:
                        # Convert weight to current effective unit
                        default_weight = convert_unit(copied_set['weight'], copied_unit, effective_unit)
                elif previous_workout and i == 0:
                    # Fallback to single previous workout value for first set
                    default_weight = previous_workout['weight']
                    if effective_unit != previous_workout['unit']:
                        default_weight = convert_unit(default_weight, previous_workout['unit'], effective_unit)
                
                # Note: With expanded weight options (1lb increments) and dynamic merging,
                # exact matches should be found. But keep this as a safety fallback.
                if default_weight > 0 and default_weight not in weight_options:
                    # Add the weight to options if it's not there (shouldn't happen with 1lb increments)
                    weight_options.append(default_weight)
                    weight_options = sorted(weight_options)
                
                # Find index for default weight
                try:
                    default_weight_index = weight_options.index(default_weight) if default_weight > 0 else 0
                except ValueError:
                    default_weight_index = 0
                
                # Apply adjustment from buttons
                current_weight_index = default_weight_index + st.session_state[weight_adj_key]
                # Clamp to valid range
                current_weight_index = max(0, min(len(weight_options) - 1, current_weight_index))
                
                weight = st.selectbox(
                    f"組 {i+1} - 重量",
                    options=weight_options,
                    index=current_weight_index,
                    key=weight_key,
                    format_func=lambda x: f"{int(x) if x == int(x) else x:.1f} {effective_unit}" if x > 0 else "選擇重量"
                )
            
            with col2:
                reps_key = f"reps_{i}{widget_suffix}"
                # Get default reps value - prioritize copied data
                default_reps = 0
                if copied_data and 'sets' in copied_data and i < len(copied_data['sets']):
                    default_reps = copied_data['sets'][i]['reps']
                elif previous_workout and i == 0:
                    default_reps = previous_workout['reps']
                
                default_reps = default_reps if default_reps in reps_options else 0
                
                # Find index for default reps
                try:
                    default_reps_index = reps_options.index(default_reps)
                except ValueError:
                    default_reps_index = 0
                
                # Apply adjustment from buttons
                current_reps_index = default_reps_index + st.session_state[reps_adj_key]
                # Clamp to valid range
                current_reps_index = max(0, min(len(reps_options) - 1, current_reps_index))
                
                reps = st.selectbox(
                    f"組 {i+1} - 次數",
                    options=reps_options,
                    index=current_reps_index,
                    key=reps_key,
                    format_func=lambda x: f"{x} 次" if x > 0 else "選擇次數"
                )
            
            with col3:
                # Calculate and display 1RM estimate
                if weight > 0 and reps > 0:
                    estimated_1rm = calculate_1rm(weight, reps)
                    st.metric(f"組 {i+1} - 預估 1RM", f"{estimated_1rm:.1f} {effective_unit}")
                else:
                    st.write("")
            
            if weight > 0 and reps > 0:
                sets_data.append({
                    'set_order': i + 1,
                    'weight': weight,
                    'unit': effective_unit,  # Use effective_unit to match the actual unit used for weights
                    'reps': reps
                })
        
        # RPE and Notes - use copied data if available
        col_rpe, col_notes = st.columns(2)
        with col_rpe:
            default_rpe = copied_data['rpe'] if copied_data and copied_data.get('rpe') else 7
            rpe = st.slider("RPE (自覺強度)", min_value=1, max_value=10, value=int(default_rpe), step=1,
                          help="1=非常輕鬆, 10=極限", key=f"rpe{widget_suffix}")
        with col_notes:
            default_notes = copied_data['notes'] if copied_data and copied_data.get('notes') else ""
            notes = st.text_area("備註 (選填)", height=100, value=default_notes,
                               placeholder="例如：左肩有點卡、Notch 4 感覺很輕...", key=f"notes{widget_suffix}")
        
        # Submit button
        submitted = st.form_submit_button("💾 儲存訓練", type="primary")
        
        if submitted:
            if not sets_data:
                st.error("請至少輸入一組有效的訓練數據（重量和次數都大於 0）")
            else:
                # Validate all sets
                valid = True
                for set_data in sets_data:
                    is_valid, error_msg = validate_input(set_data['weight'], set_data['reps'], set_data['unit'])
                    if not is_valid:
                        st.error(f"組 {set_data['set_order']}: {error_msg}")
                        valid = False
                        break
                
                if valid:
                    try:
                        save_workout(user_id, workout_date, selected_exercise, sets_data, rpe, notes)
                        st.success(f"✅ 已儲存 {len(sets_data)} 組 {selected_exercise} 訓練記錄！")
                        st.balloons()
                        # Clear copied data after successful save
                        if copy_key in st.session_state:
                            st.session_state[copy_key] = None
                        # Clear adjustment states after successful save
                        for j in range(num_sets):
                            weight_adj_key = f"weight_adj_{j}{widget_suffix}"
                            reps_adj_key = f"reps_adj_{j}{widget_suffix}"
                            if weight_adj_key in st.session_state:
                                st.session_state[weight_adj_key] = 0
                            if reps_adj_key in st.session_state:
                                st.session_state[reps_adj_key] = 0
                    except Exception as e:
                        st.error(f"儲存失敗: {str(e)}")
    
    # Rest timer (outside form for better functionality)
    st.subheader("⏱️ 休息計時器")
    timer_col1, timer_col2, timer_col3 = st.columns([2, 1, 1])
    
    with timer_col1:
        rest_time = st.selectbox("休息時間", [30, 60, 90, 120, 180], index=1, format_func=lambda x: f"{x} 秒", key="rest_time_selector")
    
    with timer_col2:
        if st.button("開始計時", key="start_timer_btn"):
            st.session_state.timer_running = True
            st.session_state.timer_start = time.time()
            st.session_state.timer_duration = rest_time
    
    with timer_col3:
        if st.button("停止計時", key="stop_timer_btn"):
            st.session_state.timer_running = False
            st.session_state.timer_start = None
    
    # Timer display
    timer_placeholder = st.empty()
    if 'timer_running' in st.session_state and st.session_state.timer_running:
        if 'timer_start' in st.session_state and st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            duration = st.session_state.get('timer_duration', 60)
            remaining = max(0, duration - elapsed)
            if remaining > 0:
                minutes = remaining // 60
                seconds = remaining % 60
                timer_placeholder.info(f"⏱️ 剩餘時間: {minutes:02d}:{seconds:02d} (已過 {elapsed} 秒)")
            else:
                timer_placeholder.success("✅ 休息時間到！")
                st.session_state.timer_running = False
    
    # Display today's workouts
    st.subheader(f"📋 {workout_date} 的訓練記錄")
    today_workouts = get_todays_workouts(user_id, workout_date)
    
    if not today_workouts.empty:
        # Group workouts by exercise
        exercises = today_workouts['exercise_name'].unique()
        
        # Initialize session state for edit/delete operations
        if 'editing_set_id' not in st.session_state:
            st.session_state.editing_set_id = None
        if 'confirm_delete_set_id' not in st.session_state:
            st.session_state.confirm_delete_set_id = None
        if 'confirm_delete_session' not in st.session_state:
            st.session_state.confirm_delete_session = None
        
        # Display workouts grouped by exercise
        for exercise_name in exercises:
            exercise_workouts = today_workouts[today_workouts['exercise_name'] == exercise_name].copy()
            exercise_workouts = exercise_workouts.sort_values('set_order')
            
            # Exercise header with delete session button
            col_header1, col_header2 = st.columns([4, 1])
            with col_header1:
                st.markdown(f"### {exercise_name}")
            with col_header2:
                delete_session_key = f"delete_session_{exercise_name}_{workout_date}"
                if st.button("🗑️ 刪除整個訓練", key=delete_session_key, use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete_session = (exercise_name, workout_date)
                    st.rerun()
            
            # Confirmation dialog for session deletion
            if st.session_state.confirm_delete_session and st.session_state.confirm_delete_session[0] == exercise_name:
                st.warning(f"⚠️ 確定要刪除 {exercise_name} 在 {workout_date} 的所有訓練記錄嗎？")
                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("✅ 確認刪除", key=f"confirm_delete_session_{exercise_name}", type="primary"):
                        deleted_count = delete_workout_session(user_id, workout_date, exercise_name)
                        if deleted_count > 0:
                            st.success(f"✅ 已刪除 {deleted_count} 組訓練記錄")
                            st.session_state.confirm_delete_session = None
                            st.rerun()
                        else:
                            st.error("刪除失敗")
                with col_confirm2:
                    if st.button("❌ 取消", key=f"cancel_delete_session_{exercise_name}"):
                        st.session_state.confirm_delete_session = None
                        st.rerun()
            
            # Display each set
            for idx, row in exercise_workouts.iterrows():
                set_id = row['id']
                set_order = row['set_order']
                weight = row['weight']
                unit = row['unit']
                reps = row['reps']
                rpe = row.get('rpe')
                notes = row.get('notes')
                
                # Check if this set is being edited
                is_editing = st.session_state.editing_set_id == set_id
                is_confirming_delete = st.session_state.confirm_delete_set_id == set_id
                
                if is_editing:
                    # Edit form
                    with st.expander(f"✏️ 編輯組 {set_order}", expanded=True):
                        with st.form(f"edit_form_{set_id}", clear_on_submit=False):
                            col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
                            
                            with col_w1:
                                # Weight options based on current unit
                                weight_options = get_weight_options(unit)
                                default_weight_idx = 0
                                if weight in weight_options:
                                    default_weight_idx = weight_options.index(weight)
                                new_weight = st.selectbox(
                                    "重量",
                                    options=weight_options,
                                    index=default_weight_idx,
                                    key=f"edit_weight_{set_id}",
                                    format_func=lambda x: f"{int(x) if x == int(x) else x:.1f} {unit}" if x > 0 else "選擇重量"
                                )
                            
                            with col_w2:
                                reps_options = get_reps_options()
                                default_reps_idx = 0
                                if reps in reps_options:
                                    default_reps_idx = reps_options.index(reps)
                                new_reps = st.selectbox(
                                    "次數",
                                    options=reps_options,
                                    index=default_reps_idx,
                                    key=f"edit_reps_{set_id}",
                                    format_func=lambda x: f"{x} 次" if x > 0 else "選擇次數"
                                )
                            
                            with col_w3:
                                new_unit = st.radio(
                                    "單位",
                                    ["kg", "lb", "notch/plate"],
                                    index=0 if unit == "kg" else (1 if unit == "lb" else 2),
                                    horizontal=True,
                                    key=f"edit_unit_{set_id}"
                                )
                            
                            col_rpe_edit, col_notes_edit = st.columns(2)
                            with col_rpe_edit:
                                new_rpe = st.slider(
                                    "RPE (自覺強度)",
                                    min_value=1,
                                    max_value=10,
                                    value=int(rpe) if rpe else 7,
                                    step=1,
                                    key=f"edit_rpe_{set_id}",
                                    help="1=非常輕鬆, 10=極限"
                                )
                            with col_notes_edit:
                                new_notes = st.text_area(
                                    "備註 (選填)",
                                    value=notes if notes else "",
                                    height=100,
                                    key=f"edit_notes_{set_id}",
                                    placeholder="例如：左肩有點卡..."
                                )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 儲存", type="primary"):
                                    if new_weight > 0 and new_reps > 0:
                                        success = update_workout_set(
                                            user_id, set_id, new_weight, new_unit,
                                            new_reps, new_rpe, new_notes.strip() if new_notes else None
                                        )
                                        if success:
                                            st.success("✅ 已更新訓練記錄")
                                            st.session_state.editing_set_id = None
                                            st.rerun()
                                        else:
                                            st.error("更新失敗")
                                    else:
                                        st.error("請輸入有效的重量和次數")
                            with col_cancel:
                                if st.form_submit_button("❌ 取消"):
                                    st.session_state.editing_set_id = None
                                    st.rerun()
                
                elif is_confirming_delete:
                    # Delete confirmation
                    st.warning(f"⚠️ 確定要刪除 {exercise_name} 組 {set_order} 的訓練記錄嗎？")
                    col_del1, col_del2 = st.columns(2)
                    with col_del1:
                        if st.button("✅ 確認刪除", key=f"confirm_delete_{set_id}", type="primary"):
                            success = delete_workout_set(user_id, set_id)
                            if success:
                                st.success("✅ 已刪除訓練記錄")
                                st.session_state.confirm_delete_set_id = None
                                st.rerun()
                            else:
                                st.error("刪除失敗")
                    with col_del2:
                        if st.button("❌ 取消", key=f"cancel_delete_{set_id}"):
                            st.session_state.confirm_delete_set_id = None
                            st.rerun()
                
                else:
                    # Display set info with edit/delete buttons
                    col_info, col_edit, col_delete = st.columns([6, 1, 1])
                    
                    with col_info:
                        weight_display = format_weight(weight, unit)
                        rpe_display = f"RPE: {rpe}/10" if rpe else ""
                        notes_display = f"備註: {notes}" if notes else ""
                        info_text = f"組 {set_order}: {weight_display} × {reps} 次"
                        if rpe_display:
                            info_text += f" | {rpe_display}"
                        if notes_display:
                            info_text += f" | {notes_display}"
                        st.write(info_text)
                    
                    with col_edit:
                        if st.button("✏️", key=f"edit_btn_{set_id}", help="編輯"):
                            st.session_state.editing_set_id = set_id
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️", key=f"delete_btn_{set_id}", help="刪除"):
                            st.session_state.confirm_delete_set_id = set_id
                            st.rerun()
            
            st.divider()
        
        # Calculate total volume
        total_volume = 0
        for _, row in today_workouts.iterrows():
            total_volume += calculate_total_volume(row['weight'], row['reps'], row['unit'])
        st.metric("今日總訓練容量", f"{total_volume:.1f} kg")
    else:
        st.info("今天還沒有訓練記錄")


# ============================================================================
# PAGE 2: PROGRESS DASHBOARD (進度儀表板)
# ============================================================================

def calculate_session_metrics(history_df: pd.DataFrame, exercise_name: str = None, bodyweight: float = None) -> pd.DataFrame:
    """Calculate session metrics from history DataFrame"""
    if history_df.empty:
        return pd.DataFrame()
    
    # Ensure date is datetime and sort by date
    history_df = history_df.copy()
    history_df['date'] = pd.to_datetime(history_df['date'])
    history_df = history_df.sort_values('date')
    
    session_data = []
    current_date = None
    session_sets = []
    
    for _, row in history_df.iterrows():
        row_date = row['date']
        
        # Normalize date to date only (remove time component if any)
        if isinstance(row_date, pd.Timestamp):
            row_date = row_date.date()
        elif hasattr(row_date, 'date'):
            row_date = row_date.date()
        
        if current_date != row_date:
            if current_date is not None and session_sets:
                # Check if this is an assisted exercise
                is_assisted = is_assisted_exercise(exercise_name) if exercise_name else False
                
                # Calculate session metrics
                if is_assisted and bodyweight:
                    # For assisted exercises, calculate effective weight
                    # Effective weight = bodyweight - assisted weight
                    # Convert bodyweight to same unit as session
                    session_units = [s['unit'] for s in session_sets]
                    primary_unit = max(set(session_units), key=session_units.count) if session_units else 'kg'
                    
                    # Convert bodyweight to session unit (assuming bodyweight is in lb)
                    from utils.calculations import convert_unit
                    bodyweight_in_unit = convert_unit(bodyweight, 'lb', primary_unit)
                    
                    # Calculate effective weights and find the set with max weight
                    max_set = max(session_sets, key=lambda s: bodyweight_in_unit - s['weight'])
                    max_weight = bodyweight_in_unit - max_set['weight']
                    max_reps = max_set['reps']  # Use reps from the same set as max weight
                    total_volume = sum(calculate_total_volume(bodyweight_in_unit - s['weight'], s['reps'], primary_unit) for s in session_sets)
                    # Calculate 1RM using the weight and reps from the same set that had max weight
                    max_1rm = calculate_1rm(max_weight, max_reps)
                else:
                    # Find the set with max weight
                    max_set = max(session_sets, key=lambda s: s['weight'])
                    max_weight = max_set['weight']
                    max_reps = max_set['reps']  # Use reps from the same set as max weight
                    total_volume = sum(calculate_total_volume(s['weight'], s['reps'], s['unit']) for s in session_sets)
                    # Calculate 1RM using the weight and reps from the same set that had max weight
                    max_1rm = calculate_1rm(max_weight, max_reps)
                    
                    # Get primary unit for this session (most common unit)
                    session_units = [s['unit'] for s in session_sets]
                    primary_unit = max(set(session_units), key=session_units.count) if session_units else 'kg'
                
                session_data.append({
                    'date': pd.Timestamp(current_date),
                    'max_weight': max_weight,
                    'max_reps': max_reps,
                    'total_volume': total_volume,
                    'max_1rm': max_1rm,
                    'sets': len(session_sets),
                    'unit': primary_unit
                })
            current_date = row_date
            session_sets = []
        
        session_sets.append({
            'weight': row['weight'],
            'reps': row['reps'],
            'unit': row['unit']
        })
    
    # Add last session
    if session_sets and current_date is not None:
        # Check if this is an assisted exercise
        is_assisted = is_assisted_exercise(exercise_name) if exercise_name else False
        
        if is_assisted and bodyweight:
            # For assisted exercises, calculate effective weight
            session_units = [s['unit'] for s in session_sets]
            primary_unit = max(set(session_units), key=session_units.count) if session_units else 'kg'
            
            from utils.calculations import convert_unit
            bodyweight_in_unit = convert_unit(bodyweight, 'lb', primary_unit)
            
            # Find the set with max effective weight
            max_set = max(session_sets, key=lambda s: bodyweight_in_unit - s['weight'])
            max_weight = bodyweight_in_unit - max_set['weight']
            max_reps = max_set['reps']  # Use reps from the same set as max weight
            total_volume = sum(calculate_total_volume(bodyweight_in_unit - s['weight'], s['reps'], primary_unit) for s in session_sets)
            # Calculate 1RM using the weight and reps from the same set that had max weight
            max_1rm = calculate_1rm(max_weight, max_reps)
        else:
            # Find the set with max weight
            max_set = max(session_sets, key=lambda s: s['weight'])
            max_weight = max_set['weight']
            max_reps = max_set['reps']  # Use reps from the same set as max weight
            total_volume = sum(calculate_total_volume(s['weight'], s['reps'], s['unit']) for s in session_sets)
            # Calculate 1RM using the weight and reps from the same set that had max weight
            max_1rm = calculate_1rm(max_weight, max_reps)
            
            session_units = [s['unit'] for s in session_sets]
            primary_unit = max(set(session_units), key=session_units.count) if session_units else 'kg'
        
        session_data.append({
            'date': pd.Timestamp(current_date),
            'max_weight': max_weight,
            'max_reps': max_reps,
            'total_volume': total_volume,
            'max_1rm': max_1rm,
            'sets': len(session_sets),
            'unit': primary_unit
        })
    
    session_df = pd.DataFrame(session_data)
    if not session_df.empty:
        session_df = session_df.sort_values('date')
    return session_df


def render_progress_dashboard_page(user_id: str):
    """Render the Progress Dashboard page"""
    st.header("📈 進度儀表板")
    
    # Get all exercises with entry counts
    all_exercises = get_all_exercises(user_id)
    if not all_exercises:
        st.info("還沒有動作記錄，請先在「記錄訓練」頁面開始記錄。")
        return
    
    entry_counts = get_exercise_entry_counts(user_id)
    
    # Group exercises by muscle group
    exercises_by_group = {}
    for ex in all_exercises:
        mg = ex['muscle_group']
        if mg not in exercises_by_group:
            exercises_by_group[mg] = []
        count = entry_counts.get(ex['name'], 0)
        exercises_by_group[mg].append({
            'name': ex['name'],
            'count': count
        })
    
    # Sort exercises within each group by entry count (descending)
    for mg in exercises_by_group:
        exercises_by_group[mg].sort(key=lambda x: x['count'], reverse=True)
    
    # Display exercise selection by muscle groups
    st.subheader("選擇要分析的動作（可多選）")
    
    selected_exercises = []
    
    # Display exercises grouped by muscle group
    for muscle_group in sorted(exercises_by_group.keys()):
        exercises = exercises_by_group[muscle_group]
        if not exercises:
            continue
        
        # Group header with select all/none toggle
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"### {muscle_group}")
        with col_header2:
            group_exercise_names = [ex['name'] for ex in exercises]
            
            # Check if all exercises in this group are selected
            all_selected = all(
                st.session_state.get(f"ex_checkbox_{ex_name}", False)
                for ex_name in group_exercise_names
            )
            
            # Toggle button for the group
            toggle_key = f"group_toggle_{muscle_group}"
            if st.button(
                "取消全選" if all_selected else "全選",
                key=toggle_key,
                use_container_width=True
            ):
                # Toggle all exercises in this group
                new_state = not all_selected
                for ex_name in group_exercise_names:
                    st.session_state[f"ex_checkbox_{ex_name}"] = new_state
                st.rerun()
        
        # Create columns for buttons (3 columns)
        cols = st.columns(3)
        col_idx = 0
        
        for ex_info in exercises:
            ex_name = ex_info['name']
            ex_count = ex_info['count']
            
            with cols[col_idx]:
                # Use checkbox for multi-select
                checkbox_key = f"ex_checkbox_{ex_name}"
                is_checked = st.checkbox(
                    f"{ex_name} ({ex_count})",
                    key=checkbox_key,
                    value=st.session_state.get(checkbox_key, False)
                )
                
                if is_checked:
                    selected_exercises.append(ex_name)
            
            col_idx = (col_idx + 1) % 3
    
    if not selected_exercises:
        st.info("請至少選擇一個動作來查看趨勢圖表")
        return
    
    # Metric selection
    metric = st.radio(
        "選擇顯示指標",
        ["最大重量 (Max Weight)", "總容量 (Total Volume)", "預估 1RM (Estimated 1RM)"],
        horizontal=True
    )
    
    # Determine y column and label
    if metric == "最大重量 (Max Weight)":
        y_col = 'max_weight'
        y_label = '最大重量'
        show_combined = True  # Show both max weight and 1RM together
    elif metric == "總容量 (Total Volume)":
        y_col = 'total_volume'
        y_label = '總容量 (kg)'
        show_combined = False
    else:
        y_col = 'max_1rm'
        y_label = '預估 1RM (最大值)'
        show_combined = False
    
    # Get data for all selected exercises
    all_session_data = []
    
    for exercise_name in selected_exercises:
        history_df = get_exercise_history(user_id, exercise_name)
        
        if history_df.empty:
            continue
        
        history_df['date'] = pd.to_datetime(history_df['date'])
        session_df = calculate_session_metrics(history_df, exercise_name, st.session_state.get('bodyweight', 135.0))
        
        if not session_df.empty:
            session_df['exercise'] = exercise_name
            all_session_data.append(session_df)
    
    if not all_session_data:
        st.info("選取的動作沒有訓練記錄。")
        return
    
    # Combine all data
    combined_df = pd.concat(all_session_data, ignore_index=True)
    
    # Group by unit for separate charts
    # For volume and 1RM, we can show together since they're standardized
    if metric in ["總容量 (Total Volume)", "預估 1RM (Estimated 1RM)"]:
        # These metrics are standardized, show all together
        st.subheader("📊 趨勢圖表")
        fig = px.line(
            combined_df,
            x='date',
            y=y_col,
            color='exercise',
            markers=True,
            title=f"{y_label} 趨勢比較",
            labels={'date': '日期', y_col: y_label, 'exercise': '動作'}
        )
        fig.update_layout(height=500, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    else:
        # For max weight, group by unit and show separate charts
        # If show_combined is True, also show 1RM on the same chart
        st.subheader("📊 趨勢圖表（依單位分組）")
        
        # Get unique units from the data
        if 'unit' not in combined_df.columns:
            # Fallback: show all together if unit info is missing
            st.subheader("📊 趨勢圖表")
            if show_combined:
                # Create chart with both max_weight and max_1rm
                fig = px.line(
                    combined_df,
                    x='date',
                    y='max_weight',
                    color='exercise',
                    markers=True,
                    title=f"最大重量 & 預估 1RM 趨勢比較",
                    labels={'date': '日期', 'max_weight': '最大重量', 'exercise': '動作'},
                    custom_data=['max_reps', 'unit']
                )
                # Update hovertemplate for max_weight traces to include reps
                for i, trace in enumerate(fig.data):
                    if trace.name and '(1RM)' not in trace.name:
                        # This is a max_weight trace, update its hovertemplate
                        exercise_name = trace.name
                        # Get the data for this exercise to access max_reps
                        ex_df = combined_df[combined_df['exercise'] == exercise_name]
                        # Update hovertemplate to show weight and reps
                        trace.hovertemplate = f'<b>{exercise_name}</b><br>日期: %{{x}}<br>最大重量: %{{y:.1f}} %{{customdata[1]}}<br>次數: %{{customdata[0]}}<extra></extra>'
                
                # Add 1RM as secondary line with different style
                for exercise_name in combined_df['exercise'].unique():
                    ex_df = combined_df[combined_df['exercise'] == exercise_name]
                    fig.add_scatter(
                        x=ex_df['date'],
                        y=ex_df['max_1rm'],
                        mode='lines+markers',
                        name=f"{exercise_name} (1RM)",
                        line=dict(dash='dash', width=2),
                        marker=dict(symbol='diamond', size=8),
                        hovertemplate=f'<b>{exercise_name} (1RM)</b><br>日期: %{{x}}<br>預估 1RM: %{{y:.1f}}<extra></extra>'
                    )
                fig.update_layout(
                    height=500,
                    hovermode='x unified',
                    yaxis_title='重量 / 預估 1RM',
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                )
            else:
                # Check if showing max_weight to include reps in tooltip
                if y_col == 'max_weight':
                    fig = px.line(
                        combined_df,
                        x='date',
                        y=y_col,
                        color='exercise',
                        markers=True,
                        title=f"{y_label} 趨勢比較",
                        labels={'date': '日期', y_col: y_label, 'exercise': '動作'},
                        custom_data=['max_reps', 'unit']
                    )
                    # Update hovertemplate for max_weight traces to include reps
                    for i, trace in enumerate(fig.data):
                        if trace.name:
                            exercise_name = trace.name
                            # Get unit from the data
                            ex_df = combined_df[combined_df['exercise'] == exercise_name]
                            if not ex_df.empty:
                                unit = ex_df.iloc[0]['unit'] if 'unit' in ex_df.columns else ''
                                trace.hovertemplate = f'<b>{exercise_name}</b><br>日期: %{{x}}<br>最大重量: %{{y:.1f}} {unit}<br>次數: %{{customdata[0]}}<extra></extra>'
                else:
                    fig = px.line(
                        combined_df,
                        x='date',
                        y=y_col,
                        color='exercise',
                        markers=True,
                        title=f"{y_label} 趨勢比較",
                        labels={'date': '日期', y_col: y_label, 'exercise': '動作'}
                    )
                fig.update_layout(height=500, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Group by unit
            unique_units = combined_df['unit'].unique()
            
            # Create a chart for each unit
            for unit in sorted(unique_units):
                unit_df = combined_df[combined_df['unit'] == unit]
                
                if unit_df.empty:
                    continue
                
                # Display unit label
                unit_label_map = {
                    'kg': '公斤 (kg)',
                    'lb': '磅 (lb)',
                    'notch': '檔位 (notch)',
                    'notch/plate': '檔位/片 (notch/plate)'
                }
                unit_display = unit_label_map.get(unit, unit)
                
                st.markdown(f"### {unit_display}")
                
                if show_combined:
                    # Create chart with both max_weight and max_1rm
                    fig = px.line(
                        unit_df,
                        x='date',
                        y='max_weight',
                        color='exercise',
                        markers=True,
                        title=f"最大重量 & 預估 1RM 趨勢比較 - {unit_display}",
                        labels={'date': '日期', 'max_weight': f'最大重量 ({unit})', 'exercise': '動作'},
                        custom_data=['max_reps', 'unit']
                    )
                    # Update hovertemplate for max_weight traces to include reps
                    for i, trace in enumerate(fig.data):
                        if trace.name and '(1RM)' not in trace.name:
                            # This is a max_weight trace, update its hovertemplate
                            exercise_name = trace.name
                            # Update hovertemplate to show weight and reps
                            trace.hovertemplate = f'<b>{exercise_name}</b><br>日期: %{{x}}<br>最大重量: %{{y:.1f}} {unit}<br>次數: %{{customdata[0]}}<extra></extra>'
                    
                    # Add 1RM as secondary line with different style for each exercise
                    for exercise_name in unit_df['exercise'].unique():
                        ex_df = unit_df[unit_df['exercise'] == exercise_name]
                        fig.add_scatter(
                            x=ex_df['date'],
                            y=ex_df['max_1rm'],
                            mode='lines+markers',
                            name=f"{exercise_name} (1RM)",
                            line=dict(dash='dash', width=2),
                            marker=dict(symbol='diamond', size=8),
                            hovertemplate=f'<b>{exercise_name} (1RM)</b><br>日期: %{{x}}<br>預估 1RM: %{{y:.1f}} {unit}<extra></extra>'
                        )
                    fig.update_layout(
                        height=400,
                        hovermode='x unified',
                        yaxis_title=f'重量 / 預估 1RM ({unit})',
                        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                    )
                else:
                    # Check if showing max_weight to include reps in tooltip
                    if y_col == 'max_weight':
                        fig = px.line(
                            unit_df,
                            x='date',
                            y=y_col,
                            color='exercise',
                            markers=True,
                            title=f"{y_label} 趨勢比較 - {unit_display}",
                            labels={'date': '日期', y_col: f'{y_label} ({unit})', 'exercise': '動作'},
                            custom_data=['max_reps', 'unit']
                        )
                        # Update hovertemplate for max_weight traces to include reps
                        for i, trace in enumerate(fig.data):
                            if trace.name:
                                exercise_name = trace.name
                                trace.hovertemplate = f'<b>{exercise_name}</b><br>日期: %{{x}}<br>最大重量: %{{y:.1f}} {unit}<br>次數: %{{customdata[0]}}<extra></extra>'
                    else:
                        fig = px.line(
                            unit_df,
                            x='date',
                            y=y_col,
                            color='exercise',
                            markers=True,
                            title=f"{y_label} 趨勢比較 - {unit_display}",
                            labels={'date': '日期', y_col: f'{y_label} ({unit})', 'exercise': '動作'}
                        )
                    fig.update_layout(height=400, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
    
    # PR Wall for selected exercises
    st.subheader("🏆 個人紀錄 (PR Wall)")
    
    pr_records = get_pr_records(user_id)
    
    # Create a more compact grid layout (3 columns)
    num_cols = 3
    pr_cols = st.columns(num_cols)
    
    # Color palette for different exercises
    colors = [
        "#E3F2FD",  # Light blue
        "#F3E5F5",  # Light purple
        "#E8F5E9",  # Light green
        "#FFF3E0",  # Light orange
        "#FCE4EC",  # Light pink
        "#E0F2F1",  # Light teal
        "#FFF9C4",  # Light yellow
        "#F1F8E9",  # Light lime
    ]
    
    for idx, exercise_name in enumerate(selected_exercises):
        if exercise_name in pr_records:
            pr = pr_records[exercise_name]
            color = colors[idx % len(colors)]
            col_idx = idx % num_cols
            
            with pr_cols[col_idx]:
                # Create a styled container with background color
                st.markdown(
                    f"""
                    <div style="
                        background-color: {color};
                        padding: 12px;
                        border-radius: 8px;
                        margin-bottom: 10px;
                        border: 1px solid #ccc;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <h4 style="
                            margin: 0 0 8px 0; 
                            padding: 0;
                            color: #333;
                            font-size: 1.1em;
                            font-weight: 600;
                        ">
                            {exercise_name}
                        </h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Display metrics in a compact format with labels and dates on same line
                # Format dates
                def format_dates(dates):
                    if not dates:
                        return ""
                    # Convert to datetime and format
                    try:
                        formatted_dates = []
                        for date_str in dates:
                            if isinstance(date_str, str):
                                dt = pd.to_datetime(date_str)
                                formatted_dates.append(dt.strftime('%Y-%m-%d'))
                            else:
                                formatted_dates.append(str(date_str))
                    except:
                        formatted_dates = [str(d) for d in dates]
                    
                    if len(formatted_dates) == 1:
                        return formatted_dates[0]
                    elif len(formatted_dates) <= 2:
                        return ", ".join(formatted_dates)
                    else:
                        return f"{formatted_dates[0]} (+{len(formatted_dates)-1})"
                
                best_weight_dates_str = format_dates(pr.get('best_weight_dates', []))
                best_reps_dates_str = format_dates(pr.get('best_reps_dates', []))
                best_volume_dates_str = format_dates(pr.get('best_volume_dates', []))
                
                # Get unit for best weight
                best_weight_unit = pr.get('best_weight_unit', 'kg')
                unit_display_map = {
                    'kg': 'kg',
                    'lb': 'lb',
                    'notch': 'notch',
                    'notch/plate': 'notch'
                }
                unit_display = unit_display_map.get(best_weight_unit, best_weight_unit)
                
                # Handle assisted exercises
                is_assisted = pr.get('is_assisted', False)
                bodyweight = st.session_state.get('bodyweight', 135.0)
                
                if is_assisted:
                    # Calculate effective weight for display
                    from utils.calculations import convert_unit
                    bodyweight_in_unit = convert_unit(bodyweight, 'lb', best_weight_unit)
                    effective_weight = bodyweight_in_unit - pr['best_weight']
                    assist_weight = pr['best_weight']
                    
                    weight_display = f"{effective_weight:.1f} {unit_display} (輔助: {assist_weight:.1f} {unit_display})"
                    weight_note = " (較低較好)"
                else:
                    weight_display = f"{pr['best_weight']:.1f} {unit_display}"
                    weight_note = ""
                
                st.markdown(
                    f"""
                    <div style="padding: 0 5px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #666; font-size: 0.9em;">最佳重量{weight_note}:</span>
                            <div style="text-align: right;">
                                <span style="font-weight: bold; color: #333;">{weight_display}</span>
                                {f'<span style="color: #888; font-size: 0.75em; margin-left: 8px;">({best_weight_dates_str})</span>' if best_weight_dates_str else ''}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #666; font-size: 0.9em;">最佳次數:</span>
                            <div style="text-align: right;">
                                <span style="font-weight: bold; color: #333;">{int(pr['best_reps'])}</span>
                                {f'<span style="color: #888; font-size: 0.75em; margin-left: 8px;">({best_reps_dates_str})</span>' if best_reps_dates_str else ''}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #666; font-size: 0.9em;">最佳容量:</span>
                            <div style="text-align: right;">
                                <span style="font-weight: bold; color: #333;">{pr['best_volume']:.1f}</span>
                                {f'<span style="color: #888; font-size: 0.75em; margin-left: 8px;">({best_volume_dates_str})</span>' if best_volume_dates_str else ''}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Muscle group heatmap
    st.subheader("🔥 訓練分布熱力圖")
    
    time_range = st.selectbox("時間範圍", [7, 30, 90, 365], index=1, format_func=lambda x: f"過去 {x} 天")
    
    muscle_stats = get_muscle_group_stats(user_id, days=time_range)
    
    if not muscle_stats.empty:
        # Create pie chart
        fig_pie = px.pie(
            muscle_stats,
            values='total_sets',
            names='muscle_group',
            title=f"過去 {time_range} 天訓練分布",
            hole=0.4
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Display stats table
        st.dataframe(muscle_stats, use_container_width=True, hide_index=True)
    else:
        st.info(f"過去 {time_range} 天沒有訓練記錄。")


# ============================================================================
# PAGE 3: LIBRARY MANAGER (動作庫管理)
# ============================================================================

def render_library_manager_page(user_id: str):
    """Render the Library Manager page"""
    st.header("📚 動作庫管理")
    
    # Add new exercise form
    st.subheader("新增動作")
    
    with st.form("add_exercise_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            exercise_name = st.text_input("動作名稱 *", placeholder="例如: Cable Chest Fly - Low to High")
        with col2:
            muscle_group = st.selectbox("肌肉群 *", get_muscle_groups())
        with col3:
            exercise_type = st.selectbox("動作類型 *", get_exercise_types())
        
        execution_steps = st.text_area(
            "執行步驟 (選填，支援 Markdown)",
            placeholder="例如：\n1. 起始姿勢：...\n2. 動作要領：...\n3. 注意事項：...",
            height=150,
            help="使用 Markdown 格式撰寫執行步驟，支援標題、列表等格式"
        )
        
        submitted = st.form_submit_button("➕ 新增動作", type="primary")
        
        if submitted:
            if not exercise_name:
                st.error("請輸入動作名稱")
            else:
                success = add_custom_exercise(
                    user_id, 
                    exercise_name, 
                    muscle_group, 
                    exercise_type,
                    execution_steps if execution_steps.strip() else None
                )
                if success:
                    st.success(f"✅ 已新增動作: {exercise_name}")
                    st.balloons()
                else:
                    st.error(f"動作「{exercise_name}」已存在")
    
    # Display exercise library
    st.subheader("動作庫列表")
    
    all_exercises = get_all_exercises(user_id)
    
    if all_exercises:
        # Group by muscle group
        exercises_df = pd.DataFrame(all_exercises)
        
        # Display grouped by muscle group
        muscle_groups = exercises_df['muscle_group'].unique()
        
        for mg in muscle_groups:
            with st.expander(f"📂 {mg}", expanded=False):
                mg_exercises = exercises_df[exercises_df['muscle_group'] == mg]
                
                for _, ex in mg_exercises.iterrows():
                    ex_name = ex['name']
                    ex_type = ex['exercise_type']
                    has_steps = ex.get('execution_steps') and str(ex.get('execution_steps')).strip()
                    
                    # Create columns for exercise info and edit button
                    info_col, edit_col = st.columns([4, 1])
                    
                    with info_col:
                        step_indicator = "📋" if has_steps else "📝"
                        st.markdown(f"**{ex_name}** ({ex_type}) {step_indicator}")
                    
                    with edit_col:
                        edit_key = f"edit_steps_{ex_name}"
                        if st.button("編輯步驟", key=edit_key, use_container_width=True):
                            st.session_state[f"editing_{ex_name}"] = True
                            st.rerun()
                    
                    # Show edit form if editing
                    if st.session_state.get(f"editing_{ex_name}", False):
                        with st.form(f"edit_steps_form_{ex_name}", clear_on_submit=False):
                            current_steps = ex.get('execution_steps', '') or ''
                            new_steps = st.text_area(
                                "執行步驟 (支援 Markdown)",
                                value=current_steps,
                                height=150,
                                key=f"steps_input_{ex_name}",
                                help="使用 Markdown 格式撰寫執行步驟"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 儲存", type="primary"):
                                    if update_exercise_steps(user_id, ex_name, new_steps.strip() if new_steps.strip() else None):
                                        st.success(f"✅ 已更新 {ex_name} 的執行步驟")
                                        st.session_state[f"editing_{ex_name}"] = False
                                        st.rerun()
                                    else:
                                        st.error("更新失敗")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ 取消"):
                                    st.session_state[f"editing_{ex_name}"] = False
                                    st.rerun()
                    
                    st.divider()
        
        # Summary
        st.metric("總動作數", len(all_exercises))
    else:
        st.info("動作庫是空的，請新增動作。")


# ============================================================================
# PAGE 4: DATA IMPORT (資料匯入)
# ============================================================================

def render_data_import_page(user_id: str):
    """Render the Data Import page"""
    st.header("📥 資料匯入")
    
    st.markdown("""
    ### 匯入說明
    
    您可以上傳 CSV 檔案來匯入歷史訓練記錄。CSV 檔案應包含以下欄位：
    
    - **Date**: 訓練日期 (格式: YYYY-MM-DD)
    - **Muscle Group**: 肌肉群 (例如: Chest, Back, Arms)
    - **Exercise**: 動作名稱
    - **Set Order**: 組數順序 (1, 2, 3...)
    - **Weight**: 重量
    - **Unit**: 單位 (kg, lb, notch, notch/plate)
    - **Reps**: 次數
    - **Note**: 備註 (選填)
    """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "選擇 CSV 檔案",
        type=['csv'],
        help="上傳包含訓練記錄的 CSV 檔案"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Display preview
            st.subheader("📋 檔案預覽 (前 5 行)")
            st.dataframe(df.head(5), use_container_width=True)
            
            # Check required columns
            required_columns = ['Date', 'Exercise', 'Set Order', 'Weight', 'Unit', 'Reps']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ CSV 檔案缺少必要欄位: {', '.join(missing_columns)}")
                st.info("請確認 CSV 檔案包含以下欄位: Date, Muscle Group, Exercise, Set Order, Weight, Unit, Reps, Note")
            else:
                st.success(f"✅ 檔案格式正確！共 {len(df)} 筆記錄")
                
                # Import button
                if st.button("🚀 開始匯入", type="primary"):
                    with st.spinner("正在匯入資料..."):
                        success_count, error_count, error_messages = import_workout_from_csv(user_id, df)
                    
                    # Display results
                    if success_count > 0:
                        st.success(f"✅ 成功匯入 {success_count} 筆記錄！")
                        st.balloons()
                    
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} 筆記錄匯入失敗")
                        with st.expander("查看錯誤詳情"):
                            for msg in error_messages[:20]:  # Show first 20 errors
                                st.text(msg)
                            if len(error_messages) > 20:
                                st.text(f"... 還有 {len(error_messages) - 20} 個錯誤")
                    
                    if success_count == 0 and error_count == 0:
                        st.info("沒有資料被匯入")
        
        except Exception as e:
            st.error(f"❌ 讀取檔案時發生錯誤: {str(e)}")
            st.info("請確認檔案格式正確且為有效的 CSV 檔案")


# ============================================================================
# MAIN APP ROUTING
# ============================================================================

def main():
    """Main application entry point with authentication"""
    # 1. Clear cookie cache
    _clear_cookie_cache()
    
    # 2. Continue cookie setting if in progress
    if continue_cookie_setting_if_needed():
        st.rerun()
    
    # 3. Ensure cookies are loaded (wait for component)
    if not ensure_cookies_loaded():
        st.stop()
    
    # 4. Handle OAuth callback
    handle_auth_callback()
    
    # 5. Check authentication
    if not ensure_authentication():
        render_login_page()
        return
    
    # 6. Get user ID
    user = get_current_user()
    if not user:
        render_login_page()
        return
    
    user_id = user['id']
    
    # 7. Initialize database (verify tables exist)
    if 'db_initialized' not in st.session_state:
        init_database(user_id)
        st.session_state.db_initialized = True
        # Initialize default exercises if database is empty
        exercises = get_all_exercises(user_id)
        if not exercises:
            default_exercises = get_default_exercises()
            for muscle_group, exercise_list in default_exercises.items():
                for exercise_name in exercise_list:
                    # Use infer_exercise_type for better type detection
                    exercise_type = infer_exercise_type(exercise_name)
                    add_custom_exercise(user_id, exercise_name, muscle_group, exercise_type)
    
    # 8. Sidebar navigation
    st.sidebar.title("🏋️ My Gym Tracker")
    
    # User info and logout
    st.sidebar.markdown(f"**使用者:** {user.get('email', 'Unknown')}")
    if st.sidebar.button("登出", use_container_width=True):
        logout()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navigation buttons
    st.sidebar.markdown("### 📍 導航")
    
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "記錄訓練"
    
    # Define pages with icons
    pages = {
        "記錄訓練": "📝",
        "進度儀表板": "📈",
        "動作庫管理": "📚",
        "資料匯入": "📥"
    }
    
    # Create navigation buttons
    for page_name, icon in pages.items():
        is_active = st.session_state.current_page == page_name
        button_type = "primary" if is_active else "secondary"
        
        if st.sidebar.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type=button_type
        ):
            st.session_state.current_page = page_name
            st.rerun()
    
    # Set page from session state
    page = st.session_state.current_page
    
    # Bodyweight setting for assisted exercises
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ 設定")
    if 'bodyweight' not in st.session_state:
        st.session_state.bodyweight = 135.0  # Default 135 lbs
    
    bodyweight = st.sidebar.number_input(
        "體重 (用於計算輔助動作的有效重量) (lb)",
        min_value=0.0,
        value=st.session_state.bodyweight,
        step=1.0,
        help="此數值用於計算輔助動作的有效重量 (有效重量 = 體重 - 輔助重量)"
    )
    st.session_state.bodyweight = bodyweight
    
    # 9. Route to appropriate page
    if page == "記錄訓練":
        render_log_workout_page(user_id)
    elif page == "進度儀表板":
        render_progress_dashboard_page(user_id)
    elif page == "動作庫管理":
        render_library_manager_page(user_id)
    elif page == "資料匯入":
        render_data_import_page(user_id)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**My Gym Tracker** v1.0")
    st.sidebar.markdown("記錄每一次訓練，見證每一次進步 💪")


if __name__ == "__main__":
    main()

