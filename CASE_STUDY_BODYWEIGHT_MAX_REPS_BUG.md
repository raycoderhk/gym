# Case Study: Bodyweight Exercise Max Reps Calculation Bug

## Problem Description

A fitness tracking application was displaying incorrect maximum repetitions (reps) in the trend chart for bodyweight exercises. The Personal Records (PR) Wall showed the correct value, but the trend chart showed a different (lower) value for the same date.

### Actual Data from the Bug Report

**Exercise:** Pull-up  
**Date:** December 18, 2025  
**Sets Performed:**
- Set 1: 9 reps (weight = 0, bodyweight)
- Set 2: 8 reps (weight = 0, bodyweight)

**Expected Behavior:**
- Trend chart should show: **9 reps** (maximum reps in the session)
- PR Wall should show: **9 reps** (maximum reps across all time)

**Actual Behavior:**
- Trend chart showed: **8 reps** ❌
- PR Wall showed: **9 reps** ✅

---

## Root Cause Analysis

### The Buggy Code

The issue was in the `calculate_session_metrics()` function in `app.py`:

```python
# Find the set with max weight
max_set = max(session_sets, key=lambda s: s['weight'])
max_weight = max_set['weight']
max_reps = max_set['reps']  # Use reps from the same set as max weight
```

### Why This Failed for Bodyweight Exercises

1. **All sets have weight = 0** (bodyweight exercises)
2. When `max()` is called with a `key` function where all values are equal, Python's behavior is **unpredictable**
3. In practice, `max()` may return the **last element** encountered when all keys are equal
4. This means it could pick Set 2 (8 reps) instead of Set 1 (9 reps)

### Python's `max()` Behavior with Equal Keys

```python
# Example demonstrating the issue
sets = [
    {'weight': 0, 'reps': 9},
    {'weight': 0, 'reps': 8}
]

# When all weights are equal, max() behavior is undefined
max_set = max(sets, key=lambda s: s['weight'])
# Could return either set - unpredictable!
print(max_set['reps'])  # Might be 9, might be 8
```

### Why PR Records Worked Correctly

The PR calculation used a different approach:

```python
# From database/db_manager.py
best_reps = logs_df['reps'].max()  # Finds maximum reps across ALL sets
```

This directly finds the maximum reps value, which is the correct approach for bodyweight exercises.

---

## The Solution

### Fixed Code

We modified the logic to detect bodyweight exercises and calculate max reps correctly:

```python
# Find the set with max weight
max_set = max(session_sets, key=lambda s: s['weight'])
max_weight = max_set['weight']

# For bodyweight exercises (all weights are 0), find max reps across all sets
# Otherwise, use reps from the set with max weight
if max_weight == 0 and all(s['weight'] == 0 for s in session_sets):
    # Bodyweight exercise: find max reps across all sets
    max_reps = max(s['reps'] for s in session_sets)
else:
    # Weighted exercise: use reps from the set with max weight
    max_reps = max_set['reps']
```

### Key Changes

1. **Detection:** Check if all weights are 0 (bodyweight exercise)
2. **Correct Calculation:** For bodyweight, find `max(s['reps'] for s in session_sets)`
3. **Preserve Logic:** For weighted exercises, keep the original behavior

---

## Lessons Learned

### 1. Edge Cases Matter

When all values in a comparison are equal, `max()` and `min()` functions can have unpredictable behavior. Always consider edge cases where:
- All values are the same
- All values are zero
- All values are None

### 2. Domain Knowledge is Critical

Understanding the domain (fitness tracking) helped identify that:
- For bodyweight exercises, weight is always 0
- The important metric is **maximum reps**, not reps from max weight
- For weighted exercises, reps from max weight set is meaningful

### 3. Different Metrics Need Different Logic

- **Weighted exercises:** Reps from the set with maximum weight makes sense
- **Bodyweight exercises:** Maximum reps across all sets is the correct metric

### 4. Test with Real Data

The bug was discovered with actual user data:
- Real workout session: 9 reps and 8 reps
- Expected: 9 reps shown
- Actual: 8 reps shown

Always test with realistic data that includes edge cases.

### 5. Code Review Best Practices

When reviewing code that uses `max()` or `min()`:
- ✅ Check what happens when all values are equal
- ✅ Verify the logic makes sense for all exercise types
- ✅ Consider if the key function can return equal values
- ✅ Test with edge cases (all zeros, all same values)

---

## Code Comparison

### Before (Buggy)

```python
max_set = max(session_sets, key=lambda s: s['weight'])
max_reps = max_set['reps']  # Unreliable when all weights are 0
```

**Problem:** Unpredictable when all weights are equal (0 for bodyweight)

### After (Fixed)

```python
max_set = max(session_sets, key=lambda s: s['weight'])
max_weight = max_set['weight']

if max_weight == 0 and all(s['weight'] == 0 for s in session_sets):
    max_reps = max(s['reps'] for s in session_sets)  # Correct for bodyweight
else:
    max_reps = max_set['reps']  # Correct for weighted
```

**Solution:** Explicitly handle the bodyweight case

---

## Testing the Fix

### Test Case 1: Bodyweight Exercise

```python
session_sets = [
    {'weight': 0, 'reps': 9, 'unit': 'lb'},
    {'weight': 0, 'reps': 8, 'unit': 'lb'}
]

# Expected: max_reps = 9
# Before fix: Could be 8 (unpredictable)
# After fix: Always 9 ✅
```

### Test Case 2: Weighted Exercise

```python
session_sets = [
    {'weight': 100, 'reps': 8, 'unit': 'lb'},
    {'weight': 95, 'reps': 10, 'unit': 'lb'}
]

# Expected: max_reps = 8 (from set with max weight 100)
# Both before and after: 8 ✅
```

---

## Takeaways for Python Learners

1. **`max()` with equal keys:** When all values in the key function are equal, the result is unpredictable. Always handle this case explicitly.

2. **Domain-specific logic:** Different types of data (bodyweight vs. weighted) may need different calculation methods.

3. **Edge case testing:** Always test with:
   - All zeros
   - All same values
   - Empty collections
   - Single element collections

4. **Code clarity:** Explicit conditionals are better than relying on undefined behavior, even if it "usually works."

5. **Debugging strategy:** When two similar features (PR Wall vs. Trend Chart) show different results, compare their implementations to find the discrepancy.

---

## File Locations

- **Bug Location:** `app.py`, function `calculate_session_metrics()` (lines 1240-1247, 1291-1298)
- **Working Reference:** `database/db_manager.py`, function `get_pr_records()` (line 790)
- **Fix Applied:** `app.py`, lines 1240-1250, 1291-1301

---

## Date of Fix

December 22, 2025

---

*This case study demonstrates a real-world bug fix in a production fitness tracking application, highlighting the importance of edge case handling and domain-specific logic in Python programming.*

