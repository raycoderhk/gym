-- PostgreSQL schema for Gym Tracker App
-- Uses 'public' schema for Supabase PostgREST compatibility
-- All tables include user_id for multi-user support
-- 
-- Note: To use 'gymlog' schema instead:
-- 1. Create schema: CREATE SCHEMA IF NOT EXISTS gymlog;
-- 2. Expose it in Supabase Dashboard: Settings -> API -> Exposed schemas -> Add 'gymlog'
-- 3. Update schema references in src/auth.py and database/db_manager.py

-- workout_logs table
CREATE TABLE IF NOT EXISTS public.workout_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    exercise_name TEXT NOT NULL,
    set_order INTEGER NOT NULL,
    weight REAL NOT NULL,
    unit TEXT NOT NULL,
    reps INTEGER NOT NULL,
    rpe INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- exercises table
CREATE TABLE IF NOT EXISTS public.exercises (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    muscle_group TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    execution_steps TEXT,  -- Markdown-formatted execution steps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)  -- Each user's exercise names are unique
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_workout_logs_user_id ON public.workout_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_logs_date ON public.workout_logs(date);
CREATE INDEX IF NOT EXISTS idx_workout_logs_exercise_name ON public.workout_logs(exercise_name);
CREATE INDEX IF NOT EXISTS idx_exercises_user_id ON public.exercises(user_id);
CREATE INDEX IF NOT EXISTS idx_exercises_muscle_group ON public.exercises(muscle_group);
