-- Migration script to add execution_steps column to exercises table
-- Run this in Supabase SQL Editor if the column doesn't exist yet

ALTER TABLE public.exercises 
ADD COLUMN IF NOT EXISTS execution_steps TEXT;

-- Add comment to column
COMMENT ON COLUMN public.exercises.execution_steps IS 'Markdown-formatted execution steps for the exercise';

