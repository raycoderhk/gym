"""
Authentication module for Gym Tracker App using Supabase
Handles Email/Password and Google OAuth authentication with session persistence via cookies
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

import streamlit as st
from supabase import create_client, Client
from supabase.client import ClientOptions
from dotenv import load_dotenv
import extra_streamlit_components as stx
import requests

# Load environment variables
load_dotenv()

# Cookie names
ACCESS_TOKEN_COOKIE = "gym_access_token"
REFRESH_TOKEN_COOKIE = "gym_refresh_token"

# Check if CookieManager is available
try:
    COOKIE_MANAGER_AVAILABLE = True
except ImportError:
    COOKIE_MANAGER_AVAILABLE = False


def get_supabase_client() -> Client:
    """Initialize and return Supabase client"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    # Use public schema (Supabase PostgREST default)
    # Note: To use 'gymlog' schema, you need to expose it in Supabase Dashboard:
    # Settings -> API -> Exposed schemas -> Add 'gymlog'
    options = ClientOptions(schema="public")
    return create_client(supabase_url, supabase_key, options=options)


def get_cookie_manager():
    """Get or create CookieManager instance (cached in session_state)"""
    if not COOKIE_MANAGER_AVAILABLE:
        return None
    
    if "cookie_manager_instance" not in st.session_state:
        st.session_state.cookie_manager_instance = stx.CookieManager(key="auth_cookie_manager")
    
    return st.session_state.cookie_manager_instance


def _clear_cookie_cache():
    """Clear cookie cache at start of each render"""
    if "cookies_fetched" in st.session_state:
        del st.session_state.cookies_fetched
    if "cached_cookies" in st.session_state:
        del st.session_state.cached_cookies


def _get_all_cookies_cached():
    """Get all cookies with caching to avoid duplicate key errors"""
    # Cache the result in session_state to avoid calling get_all() multiple times
    if "cookies_fetched" not in st.session_state:
        cookie_manager = get_cookie_manager()
        if cookie_manager is None:
            return None
        
        try:
            st.session_state.cached_cookies = cookie_manager.get_all()
            st.session_state.cookies_fetched = True
        except Exception as e:
            print(f"❌ Error calling get_all(): {e}")
            st.session_state.cached_cookies = None
            return None
    
    return st.session_state.cached_cookies


def _get_tokens_from_cookies() -> Tuple[Optional[str], Optional[str]]:
    """Retrieve access and refresh tokens from cookies"""
    cookies = _get_all_cookies_cached()
    if cookies is None:
        return None, None
    
    access_token = cookies.get(ACCESS_TOKEN_COOKIE)
    refresh_token = cookies.get(REFRESH_TOKEN_COOKIE)
    
    return access_token, refresh_token


def _clear_cookies():
    """Clear authentication cookies"""
    cookie_manager = get_cookie_manager()
    if not cookie_manager:
        return
    
    try:
        cookie_manager.delete(ACCESS_TOKEN_COOKIE)
        cookie_manager.delete(REFRESH_TOKEN_COOKIE)
    except Exception as e:
        print(f"Error clearing cookies: {e}")


def _persist_session_to_cookies(access_token: str, refresh_token: str) -> bool:
    """Helper to persist tokens to browser cookies using state machine"""
    cookie_manager = get_cookie_manager()
    if not cookie_manager:
        return False
    
    cookie_set_state = st.session_state.get("cookie_set_state", "start")
    
    try:
        expires_at = datetime.now() + timedelta(days=30)
        
        if cookie_set_state == "start":
            # First render: Set access token
            cookie_manager.set(
                cookie=ACCESS_TOKEN_COOKIE,
                val=access_token,
                expires_at=expires_at
            )
            st.session_state.cookie_set_state = "access_token_set"
            st.session_state.pending_refresh_token = refresh_token
            st.session_state.pending_expires_at = expires_at
            st.rerun()  # Rerun to set refresh token in next render
            return True
        
        elif cookie_set_state == "access_token_set":
            # Second render: Set refresh token
            refresh_token_to_set = st.session_state.get("pending_refresh_token")
            expires_at = st.session_state.get("pending_expires_at")
            
            cookie_manager.set(
                cookie=REFRESH_TOKEN_COOKIE,
                val=refresh_token_to_set,
                expires_at=expires_at
            )
            st.session_state.cookie_set_state = "both_set"
            
            # Clean up and verify
            del st.session_state.pending_refresh_token
            del st.session_state.pending_expires_at
            
            # Verify cookies were set
            time.sleep(0.3)
            _clear_cookie_cache()
            all_cookies = _get_all_cookies_cached()
            if all_cookies:
                has_at = ACCESS_TOKEN_COOKIE in all_cookies
                has_rt = REFRESH_TOKEN_COOKIE in all_cookies
                if has_at and has_rt:
                    st.session_state.cookie_set_state = "start"
                    return True
            
            return True
        
        return True
    except Exception as e:
        print(f"Error setting cookies: {e}")
        st.session_state.cookie_set_state = "start"
        return False


def continue_cookie_setting_if_needed() -> bool:
    """Continue cookie setting process if in progress (state machine continuation)"""
    cookie_set_state = st.session_state.get("cookie_set_state", "start")
    
    if cookie_set_state == "access_token_set":
        # Continue setting refresh token
        refresh_token = st.session_state.get("pending_refresh_token")
        expires_at = st.session_state.get("pending_expires_at")
        
        if refresh_token and expires_at:
            cookie_manager = get_cookie_manager()
            if cookie_manager:
                try:
                    cookie_manager.set(
                        cookie=REFRESH_TOKEN_COOKIE,
                        val=refresh_token,
                        expires_at=expires_at
                    )
                    st.session_state.cookie_set_state = "both_set"
                    
                    # Clean up
                    del st.session_state.pending_refresh_token
                    del st.session_state.pending_expires_at
                    
                    # Verify
                    time.sleep(0.3)
                    _clear_cookie_cache()
                    all_cookies = _get_all_cookies_cached()
                    if all_cookies:
                        has_at = ACCESS_TOKEN_COOKIE in all_cookies
                        has_rt = REFRESH_TOKEN_COOKIE in all_cookies
                        if has_at and has_rt:
                            st.session_state.cookie_set_state = "start"
                            return False
                    
                    return True
                except Exception as e:
                    print(f"Error continuing cookie setting: {e}")
                    st.session_state.cookie_set_state = "start"
                    return False
    
    return False


def ensure_cookies_loaded() -> bool:
    """Blocking wait until the cookie manager connects"""
    if not COOKIE_MANAGER_AVAILABLE:
        return True
    
    cookie_manager = get_cookie_manager()
    if not cookie_manager:
        return True
    
    # Prevent infinite rerun loops
    if "cookie_load_attempts" not in st.session_state:
        st.session_state.cookie_load_attempts = 0
    
    if st.session_state.cookie_load_attempts > 5:
        print("⚠️ CookieManager failed to connect after 5 attempts, proceeding anyway")
        return True
    
    try:
        cookies = _get_all_cookies_cached()
        
        # CRITICAL: None = not connected, {} = connected but empty
        if cookies is None:
            st.session_state.cookie_load_attempts += 1
            print(f"⏳ CookieManager not ready yet (attempt {st.session_state.cookie_load_attempts}/5), waiting...")
            time.sleep(0.5)
            st.rerun()
            return False
        
        # Reset counter on success
        st.session_state.cookie_load_attempts = 0
        return True
    except Exception as e:
        print(f"❌ Error in ensure_cookies_loaded: {e}")
        return True


def restore_session_from_cookies() -> bool:
    """Restore session from cookies (called on page load)"""
    access_token, refresh_token = _get_tokens_from_cookies()
    
    if not access_token:
        return False
    
    if not refresh_token:
        print("⚠️ Refresh token missing from cookies, attempting to restore with access token only...")
        # Try to restore with access token only
        try:
            supabase = get_supabase_client()
            supabase.auth.set_session(access_token, "")
            session = supabase.auth.get_session()
            
            if session and session.user:
                set_session_state(session.user, session)
                # Update cookies with refresh token if available
                if session.refresh_token:
                    _persist_session_to_cookies(session.access_token, session.refresh_token)
                return True
        except Exception as e:
            print(f"Error restoring with access token only: {e}")
            return False
    
    try:
        supabase = get_supabase_client()
        supabase.auth.set_session(access_token, refresh_token)
        session = supabase.auth.get_session()
        
        if session and session.user:
            # Restore session state
            st.session_state.user = {
                "id": session.user.id,
                "email": session.user.email,
                "user_metadata": session.user.user_metadata or {}
            }
            st.session_state.supabase_session = session
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            
            # Update cookies with potentially refreshed tokens
            _persist_session_to_cookies(session.access_token, session.refresh_token)
            return True
    except Exception as e:
        print(f"Error restoring session from cookies: {e}")
        # Try to refresh expired tokens
        try:
            supabase = get_supabase_client()
            supabase.auth.set_session(access_token, refresh_token)
            supabase.auth.refresh_session()
            session = supabase.auth.get_session()
            
            if session and session.user:
                set_session_state(session.user, session)
                return True
        except Exception as refresh_error:
            print(f"Error refreshing session: {refresh_error}")
            _clear_cookies()
    
    return False


def set_session_state(user, session):
    """Centralized function to set session state and persist to cookies"""
    st.session_state.user = {
        "id": user.id,
        "email": user.email,
        "user_metadata": user.user_metadata or {}
    }
    st.session_state.supabase_session = session
    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token
    
    # Persist to cookies
    _persist_session_to_cookies(session.access_token, session.refresh_token)


def login_with_email(email: str, password: str) -> bool:
    """Sign in with email and password"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and response.session:
            set_session_state(response.user, response.session)
            supabase.auth.set_session(response.session.access_token, response.session.refresh_token)
            return True
        return False
    except Exception as e:
        error_msg = str(e)
        if "email not confirmed" in error_msg.lower():
            st.error("⚠️ Email not confirmed. Please check your email.")
        elif "Invalid login credentials" in error_msg:
            st.error("Invalid email or password.")
        else:
            st.error(f"Login failed: {error_msg}")
        return False


def signup_with_email(email: str, password: str) -> bool:
    """Sign up with email and password"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            if response.session:
                # User is immediately logged in (email confirmation disabled)
                set_session_state(response.user, response.session)
                supabase.auth.set_session(response.session.access_token, response.session.refresh_token)
                return True
            else:
                # Email confirmation required
                st.info("Account created! Please check your email to confirm your account.")
                return False
        return False
    except Exception as e:
        st.error(f"Sign up failed: {str(e)}")
        return False


def login_with_google() -> Optional[str]:
    """Initiate Google OAuth login"""
    supabase = get_supabase_client()
    redirect_url = os.getenv('REDIRECT_URL', 'http://localhost:8502')
    
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        
        if hasattr(response, 'url'):
            return response.url
        elif isinstance(response, dict) and 'url' in response:
            return response['url']
        return str(response)
    except Exception:
        return None


def handle_auth_callback() -> bool:
    """Handle OAuth callback and set user in session state"""
    query_params = st.query_params
    
    # Check for OAuth callback with code
    if "code" in query_params:
        code = query_params.get("code")
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            redirect_url = os.getenv('REDIRECT_URL', 'http://localhost:8502')
            
            # Exchange code for session via REST API
            exchange_url = f"{supabase_url}/auth/v1/token?grant_type=authorization_code&code={code}&redirect_to={redirect_url}"
            headers = {
                "apikey": supabase_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(exchange_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Create session object
                class MockSession:
                    def __init__(self, data):
                        self.access_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        self.user = None
                
                session = MockSession(data)
                
                # Get user details
                user_response = requests.get(
                    f"{supabase_url}/auth/v1/user",
                    headers={"apikey": supabase_key, "Authorization": f"Bearer {data['access_token']}"}
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    
                    class MockUser:
                        def __init__(self, data):
                            self.id = data.get("id")
                            self.email = data.get("email")
                            self.user_metadata = data.get("user_metadata", {})
                    
                    user = MockUser(user_data)
                    set_session_state(user, session)
                    
                    st.query_params.clear()
                    st.rerun()
                    return True
        except Exception as e:
            st.error(f"Auth error: {str(e)}")
            
    return False


def logout():
    """Log out and clear session"""
    # Clear session state
    if "user" in st.session_state:
        del st.session_state.user
    if "supabase_session" in st.session_state:
        del st.session_state.supabase_session
    if "access_token" in st.session_state:
        del st.session_state.access_token
    if "refresh_token" in st.session_state:
        del st.session_state.refresh_token
    
    # Clear cookies
    _clear_cookies()
    
    # Clear cookie cache
    _clear_cookie_cache()
    
    # Reset cookie setting state
    if "cookie_set_state" in st.session_state:
        st.session_state.cookie_set_state = "start"


def get_current_user() -> Optional[Dict]:
    """Get authenticated user from session state"""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    # First check session state
    if "user" in st.session_state and st.session_state.user:
        return True
    
    # Try to restore from cookies
    if restore_session_from_cookies():
        return True
    
    return False


def ensure_authentication() -> bool:
    """Ensure user is authenticated, restore from cookies if needed"""
    # Check if already authenticated
    if "user" in st.session_state and st.session_state.user:
        return True
    
    # Try to restore from cookies
    if restore_session_from_cookies():
        return True
    
    return False

