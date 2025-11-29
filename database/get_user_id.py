"""
Helper script to get user UUID from email address
"""

import os
import sys
from dotenv import load_dotenv
from src.auth import get_supabase_client

load_dotenv()

def get_user_id_by_email(email: str):
    """Get user UUID from email using Supabase Admin API"""
    try:
        supabase = get_supabase_client()
        
        # Query auth.users table (requires service role key or admin access)
        # Note: This might not work with anon key, you may need to use the app UI
        print(f"Looking up user ID for: {email}")
        print("\nNote: If this doesn't work, you can:")
        print("1. Log in to your app and check the browser console")
        print("2. Check Supabase Dashboard -> Authentication -> Users")
        print("3. Run SQL in Supabase SQL Editor:")
        print(f"   SELECT id, email FROM auth.users WHERE email = '{email}';")
        
        # Try to get user info (this might require admin key)
        # For now, we'll just provide instructions
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_user_id.py <email>")
        print("Example: python get_user_id.py raymondcuhk@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    get_user_id_by_email(email)

