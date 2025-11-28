-- Gym Tracker Database Schema

-- Workout logs table
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    exercise_name TEXT NOT NULL,
    set_order INTEGER NOT NULL,
    weight REAL NOT NULL,
    unit TEXT NOT NULL,
    reps INTEGER NOT NULL,
    rpe INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exercise library table
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    muscle_group TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_workout_logs_date ON workout_logs(date);
CREATE INDEX IF NOT EXISTS idx_workout_logs_exercise ON workout_logs(exercise_name);
CREATE INDEX IF NOT EXISTS idx_exercises_muscle_group ON exercises(muscle_group);

