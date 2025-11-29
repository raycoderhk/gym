-- SQL function to look up user_id by email
-- Run this once in Supabase SQL Editor to enable automatic user_id lookup

CREATE OR REPLACE FUNCTION public.get_user_id_by_email(user_email TEXT)
RETURNS TABLE(id UUID, email TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT au.id, au.email
  FROM auth.users au
  WHERE au.email = user_email
  LIMIT 1;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.get_user_id_by_email(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_user_id_by_email(TEXT) TO anon;

