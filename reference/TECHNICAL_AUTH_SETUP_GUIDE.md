# Technical Guide: Email/Gmail Signup/Signin with Supabase in Streamlit

## Overview

This guide documents the complete implementation of email/password and Google OAuth authentication in a Streamlit application using Supabase as the backend authentication provider. This includes all issues encountered during development and their solutions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Setup](#supabase-setup)
3. [Email/Password Authentication](#emailpassword-authentication)
4. [Google OAuth Setup](#google-oauth-setup)
5. [Session Persistence Implementation](#session-persistence-implementation)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [Code Structure](#code-structure)
8. [Testing Checklist](#testing-checklist)

---

## Prerequisites

### Required Packages

```txt
streamlit>=1.28.0
supabase>=2.0.0
python-dotenv>=1.0.0
extra-streamlit-components>=0.1.60
```

### Environment Variables

Create a `.env` file in your project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_public_key_here
REDIRECT_URL=http://localhost:8501
```

**How to get these values:**
1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy the **Project URL** (SUPABASE_URL)
4. Copy the **anon/public** key (SUPABASE_KEY)
5. REDIRECT_URL should match your app's URL (localhost for development, production URL for deployment)

---

## Supabase Setup

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project or use an existing one
3. Note your project URL and API keys

### Step 2: Configure Authentication Providers

#### A. Email/Password Provider (Default - Already Enabled)

Email/password authentication is enabled by default in Supabase. No additional configuration needed.

**Optional: Disable Email Confirmation (for development)**

1. Go to **Authentication** → **Settings**
2. Find **"Enable email confirmations"**
3. Toggle it **OFF** for development/testing
4. Click **Save**

**Note:** For production, keep email confirmation enabled for security.

#### B. Google OAuth Provider

See [Google OAuth Setup](#google-oauth-setup) section below.

### Step 3: Configure Redirect URLs

**CRITICAL:** This step is essential for OAuth to work correctly.

1. Go to **Authentication** → **URL Configuration**
2. In **Redirect URLs**, add:
   - `http://localhost:8501` (for development)
   - `https://your-production-url.com` (for production)
3. Set **Site URL** to your app's URL
4. Click **Save**

**Why this matters:** Supabase needs to know which URLs are allowed for OAuth redirects. Without this, users will be redirected but not logged in.

---

## Email/Password Authentication

### Implementation

The email/password authentication uses Supabase's built-in `sign_in_with_password` and `sign_up` methods.

### Key Functions

#### Sign Up

```python
def signup_with_email(email: str, password: str):
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
```

#### Sign In

```python
def login_with_email(email: str, password: str):
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
```

### UI Implementation

```python
def render_login_page():
    """Render the login/signup page"""
    tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])
    
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", type="primary"):
            if login_with_email(email, password):
                st.success("Logged in successfully!")
                st.rerun()
    
    with tab_signup:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Sign Up", type="primary"):
            if signup_with_email(new_email, new_password):
                st.success("Account created! You can now sign in.")
                st.rerun()
```

---

## Google OAuth Setup

### Step 1: Get Google OAuth Credentials

#### A. Go to Google Cloud Console

1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account

#### B. Create or Select a Project

1. Click the project dropdown at the top
2. Click "New Project" or select an existing one
3. Note your project name

#### C. Enable Google Identity API

1. Go to **APIs & Services** → **Library**
2. Search for "Google Identity" or "Google+ API"
3. Click on it and click **Enable**

#### D. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose "External" (unless you have a Google Workspace)
3. Fill in:
   - **App name**: Your app name (e.g., "FocusTimer Plus")
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click "Save and Continue" through the steps

#### E. Create OAuth 2.0 Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
3. Configure:
   - **Application type**: Web application
   - **Name**: Your app name
   - **Authorized redirect URIs**: Add:
     ```
     https://your-project-id.supabase.co/auth/v1/callback
     ```
     **Important:** Replace `your-project-id` with your actual Supabase project ID (found in your Supabase URL)
4. Click **Create**
5. **Copy your credentials**:
   - **Client ID**: `123456789-abcdefg.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-abcdefghijklmnopqrstuvwxyz`

### Step 2: Configure in Supabase

1. Go to your Supabase dashboard
2. Navigate to **Authentication** → **Providers**
3. Click on **Google** provider
4. Fill in:
   - **Client IDs**: Paste your Google Client ID
   - **Client Secret**: Paste your Google Client Secret
   - **Skip nonce checks**: Leave OFF (default)
   - **Allow users without an email**: Leave OFF (default)
5. Click **Save**

### Step 3: Implementation

```python
def login_with_google():
    """Initiate Google OAuth login"""
    supabase = get_supabase_client()
    redirect_url = os.getenv('REDIRECT_URL', 'http://localhost:8501')
    
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
```

### Step 4: Handle OAuth Callback

```python
def handle_auth_callback():
    """Handle OAuth callback and set user in session state"""
    query_params = st.query_params
    
    # Check for OAuth callback with code
    if "code" in query_params:
        code = query_params.get("code")
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            redirect_url = os.getenv('REDIRECT_URL', 'http://localhost:8501')
            
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
```

### UI Implementation

```python
google_auth_url = login_with_google()
if google_auth_url:
    st.link_button("🔒 Sign in with Google", google_auth_url, use_container_width=True)
else:
    st.warning("Google Sign-In is not configured. Please verify .env settings.")
```

---

## Session Persistence Implementation

### The Problem

**Streamlit's `st.session_state` does NOT persist across hard browser refreshes (F5).** When the page reloads, Python's session state is cleared, losing all authentication tokens.

### Why Cookies?

Unlike `st.session_state` or `localStorage`, cookies are:
- Automatically sent with every HTTP request
- Accessible to Python on the server side
- Persist across browser sessions (with expiration)
- Not blocked by iframe sandboxing (when using proper components)

### Solution: CookieManager from `extra-streamlit-components`

**Package:** `extra-streamlit-components` (specifically `CookieManager`)

**Why It Works:**
- Uses a bi-directional React component (not a sandboxed iframe)
- Can read/write `document.cookie` in the parent browser context
- Sends cookie data back to Python via `postMessage` bridge
- Works across F5 refreshes because cookies are sent with every request

### Critical Implementation Details

#### 1. The Duplicate Key Problem

**Issue:** `CookieManager.set()` uses the same internal key (`'set'`) for all operations. Calling it twice in the same render cycle causes:
```
StreamlitDuplicateElementKey: There are multiple elements with the same key='set'
```

**Solution:** **State Machine Pattern** - Set cookies one at a time across multiple renders:

```python
def _persist_session_to_cookies(access_token, refresh_token):
    """Helper to persist tokens to browser cookies using state machine"""
    cookie_manager = get_cookie_manager()
    if not cookie_manager:
        return False
    
    cookie_set_state = st.session_state.get("cookie_set_state", "start")
    
    try:
        from datetime import datetime, timedelta
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
```

#### 2. The Race Condition Problem

**Issue:** CookieManager is a React component that must "mount" in the browser before it can read cookies. On F5 refresh:
- Python runs immediately
- React component hasn't finished loading yet
- `get_all()` returns `None` (not connected) instead of `{}` (empty but connected)

**Solution:** **Wait Pattern with Rerun**:

```python
def ensure_cookies_loaded():
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
```

**Key Insight:** Check for `None` (not connected) vs `{}` (empty). Use `st.stop()` to prevent rendering until cookies are ready.

#### 3. The Caching Problem

**Issue:** Calling `get_all()` multiple times in the same render causes duplicate key errors.

**Solution:** **Cache the result** per render cycle:

```python
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
```

**Key Insight:** Only call `get_all()` **once per render cycle**. Cache the result and reuse it.

#### 4. The State Continuation Problem

**Issue:** After setting the first cookie and rerunning, the second cookie wasn't being set because the continuation logic wasn't being called.

**Solution:** **Check state at the start of `main()`**:

```python
def main():
    """Main application entry point"""
    # CRITICAL: Clear cookie cache at start of each render
    _clear_cookie_cache()
    
    # Check if we're in the middle of setting cookies (state machine continuation)
    if continue_cookie_setting_if_needed():
        st.rerun()
    
    # Ensure cookies are loaded (wait for CookieManager to connect)
    if not ensure_cookies_loaded():
        st.stop()  # Prevent rendering until cookies are ready
    
    # Now safe to check authentication
    if not ensure_authentication():
        render_login_page()
        return
    
    # Rest of app...
```

### Complete Session Restoration Flow

```python
def restore_session_from_cookies():
    """Restore session from cookies (called on page load)"""
    access_token, refresh_token = _get_tokens_from_cookies()
    
    if not access_token:
        return False
    
    if not refresh_token:
        print("⚠️ Refresh token missing from cookies, attempting to restore with access token only...")
        # Try to restore with access token only (see full implementation in code)
    
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
```

---

## Common Issues and Solutions

### Issue 1: "redirect_uri_mismatch" Error

**Symptom:** After clicking "Sign in with Google", you see an error about redirect URI mismatch.

**Cause:** The redirect URI in Google Cloud Console doesn't match Supabase's callback URL.

**Solution:**
1. In Google Cloud Console, go to **Credentials** → Your OAuth 2.0 Client ID
2. In **Authorized redirect URIs**, add:
   ```
   https://your-project-id.supabase.co/auth/v1/callback
   ```
3. Make sure it matches exactly (including `https://` and no trailing slash)
4. Save and wait a few minutes for changes to propagate

### Issue 2: User Redirected but Not Logged In

**Symptom:** After Google OAuth, user is redirected back but still sees the login page.

**Cause:** Redirect URL not configured in Supabase.

**Solution:**
1. Go to Supabase dashboard → **Authentication** → **URL Configuration**
2. Add your app URL to **Redirect URLs**:
   - `http://localhost:8501` (development)
   - `https://your-production-url.com` (production)
3. Set **Site URL** to your app's URL
4. Click **Save**

### Issue 3: "Email not confirmed" Error

**Symptom:** User signs up but can't sign in, sees "Email not confirmed" error.

**Cause:** Email confirmation is enabled in Supabase.

**Solutions:**

**Option A: Disable Email Confirmation (Development)**
1. Go to Supabase → **Authentication** → **Settings**
2. Toggle **"Enable email confirmations"** OFF
3. Click **Save**

**Option B: Keep Enabled and Resend Confirmation**
1. Go to Supabase → **Authentication** → **Users**
2. Find the user
3. Click **"Resend confirmation email"**

### Issue 4: Session Lost on F5 Refresh

**Symptom:** User logs in successfully, but pressing F5 logs them out.

**Cause:** `st.session_state` doesn't persist across hard refreshes.

**Solution:** Implement CookieManager as described in [Session Persistence Implementation](#session-persistence-implementation) section.

### Issue 5: Duplicate Key Error with CookieManager

**Symptom:** `StreamlitDuplicateElementKey: There are multiple elements with the same key='set'`

**Cause:** Calling `cookie_manager.set()` multiple times in the same render cycle.

**Solution:** Use the state machine pattern to set cookies one at a time across multiple renders (see [The Duplicate Key Problem](#1-the-duplicate-key-problem)).

### Issue 6: CookieManager Returns None

**Symptom:** `_get_tokens_from_cookies()` always returns `None, None` even after login.

**Cause:** CookieManager component hasn't mounted yet (race condition).

**Solution:** Implement `ensure_cookies_loaded()` with wait pattern and rerun logic (see [The Race Condition Problem](#2-the-race-condition-problem)).

### Issue 7: Tokens Not Persisting After Rerun

**Symptom:** First cookie is set, but second cookie isn't set after rerun.

**Cause:** State machine continuation logic not being called at the start of `main()`.

**Solution:** Call `continue_cookie_setting_if_needed()` at the very start of `main()`, before authentication checks.

---

## Code Structure

### File: `src/auth.py`

**Key Functions:**

- `get_supabase_client()`: Initialize Supabase client
- `get_cookie_manager()`: Returns cached CookieManager instance
- `ensure_cookies_loaded()`: Waits for CookieManager to connect
- `_persist_session_to_cookies()`: State machine to set cookies
- `continue_cookie_setting_if_needed()`: Continues cookie-setting after rerun
- `_get_all_cookies_cached()`: Cached cookie reading
- `_get_tokens_from_cookies()`: Retrieve tokens from cookies
- `restore_session_from_cookies()`: Restores session from cookies
- `set_session_state()`: Centralized function to set session state
- `login_with_email()`: Email/password sign in
- `signup_with_email()`: Email/password sign up
- `login_with_google()`: Initiate Google OAuth
- `handle_auth_callback()`: Handle OAuth callback
- `logout()`: Log out and clear session
- `get_current_user()`: Get authenticated user
- `is_authenticated()`: Check authentication status
- `get_supabase_session()`: Get current session or restore from tokens

### File: `app.py`

**Key Functions:**

- `main()`: Main application entry point with cookie initialization
- `ensure_authentication()`: Centralized authentication check
- `render_login_page()`: Login/signup UI

**Critical Pattern in `main()`:**

```python
def main():
    # 1. Clear cookie cache
    _clear_cookie_cache()
    
    # 2. Continue cookie setting if in progress
    if continue_cookie_setting_if_needed():
        st.rerun()
    
    # 3. Ensure cookies are loaded (wait for component)
    if not ensure_cookies_loaded():
        st.stop()
    
    # 4. Check authentication (which uses cookies)
    if not ensure_authentication():
        render_login_page()
        return
    
    # 5. Render main app
    # ...
```

---

## Testing Checklist

### Email/Password Authentication

- [ ] Sign up with new email/password
- [ ] Sign in with correct credentials
- [ ] Sign in with incorrect credentials (should show error)
- [ ] Sign in with unconfirmed email (if email confirmation enabled)
- [ ] Sign out
- [ ] Press F5 after login → Session should persist

### Google OAuth

- [ ] Click "Sign in with Google" button
- [ ] Redirected to Google login page
- [ ] Select Google account
- [ ] Redirected back to app
- [ ] User is logged in
- [ ] Press F5 after login → Session should persist

### Session Persistence

- [ ] Log in successfully
- [ ] Check browser DevTools → Cookies → both `ft_access_token` and `ft_refresh_token` exist
- [ ] Press F5 → Session should persist (no login page)
- [ ] Close browser tab → Reopen → Session should persist
- [ ] Check terminal for duplicate key errors (should be none)
- [ ] Check terminal for "Tokens incomplete" (should only appear briefly during loading)

### Edge Cases

- [ ] Log in → Wait for token expiration → Should auto-refresh
- [ ] Log in → Clear cookies manually → Should show login page
- [ ] Multiple tabs → Log out in one tab → Other tabs should reflect logout
- [ ] Network offline → Should handle gracefully

---

## Best Practices

### 1. Always Use State Machine for Multiple Cookie Operations

**Don't:**
```python
cookie_manager.set("token1", value1)
cookie_manager.set("token2", value2)  # ❌ Duplicate key error!
```

**Do:**
```python
# Use state machine to set one cookie per render
if state == "start":
    cookie_manager.set("token1", value1)
    st.rerun()
elif state == "token1_set":
    cookie_manager.set("token2", value2)
```

### 2. Cache Cookie Reads

**Don't:**
```python
cookies1 = cookie_manager.get_all()  # First call
cookies2 = cookie_manager.get_all()  # ❌ Duplicate key error!
```

**Do:**
```python
cookies = _get_all_cookies_cached()  # Cached, only calls once
token1 = cookies.get("token1")
token2 = cookies.get("token2")
```

### 3. Handle the Race Condition

**Don't:**
```python
cookies = cookie_manager.get_all()
if not cookies:  # ❌ Wrong! None != {}
    return
```

**Do:**
```python
cookies = cookie_manager.get_all()
if cookies is None:  # ✅ Component not connected yet
    st.rerun()
    return False
if not cookies:  # ✅ Connected but empty
    return False
```

### 4. Initialize CookieManager Early

**Do:**
```python
def main():
    # Initialize cookie manager FIRST, before any other logic
    ensure_cookies_loaded()
    # Then check authentication
    if not ensure_authentication():
        render_login_page()
```

### 5. Use Consistent Keys

**Do:**
```python
# Use a consistent key to prevent re-initialization
cookie_manager = stx.CookieManager(key="auth_cookie_manager")
# Cache in session_state to prevent duplicate instances
if "cookie_manager_instance" not in st.session_state:
    st.session_state.cookie_manager_instance = cookie_manager
```

### 6. Error Handling

Always wrap authentication calls in try-except blocks and provide user-friendly error messages:

```python
try:
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    # Handle success...
except Exception as e:
    error_msg = str(e)
    if "email not confirmed" in error_msg.lower():
        st.error("⚠️ Email not confirmed. Please check your email.")
    elif "Invalid login credentials" in error_msg:
        st.error("Invalid email or password.")
    else:
        st.error(f"Login failed: {error_msg}")
```

---

## Production Considerations

### Security

1. **Enable Email Confirmation**: For production, always enable email confirmation in Supabase
2. **HTTPS Only**: Use HTTPS in production (cookies are more secure over HTTPS)
3. **Token Expiration**: Tokens expire after a set time (default 1 hour for access token, 30 days for refresh token)
4. **Environment Variables**: Never commit `.env` file to version control

### Deployment

1. **Update Redirect URLs**: Add production URL to both:
   - Google Cloud Console (OAuth redirect URIs)
   - Supabase (Authentication → URL Configuration)
2. **Update REDIRECT_URL**: Set `REDIRECT_URL` in production environment to your production URL
3. **Test OAuth Flow**: Verify Google OAuth works in production
4. **Monitor Logs**: Check for authentication errors in production logs

### Performance

1. **Cookie Caching**: The cookie caching pattern prevents duplicate key errors and improves performance
2. **Session Restoration**: Only restore session once per page load
3. **Token Refresh**: Automatically refresh expired tokens to avoid unnecessary logins

---

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Streamlit Session State Documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [extra-streamlit-components GitHub](https://github.com/Mohamed-512/Extra-Streamlit-Components)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)

---

## Summary

This implementation provides:

✅ **Email/password authentication** with Supabase  
✅ **Google OAuth authentication** with proper redirect handling  
✅ **Session persistence across F5 refresh** using CookieManager  
✅ **Robust error handling** for common authentication issues  
✅ **Production-ready** patterns and best practices  

The key innovation is using `extra-streamlit-components` CookieManager with a state machine pattern to persist authentication tokens across hard browser refreshes, solving the fundamental limitation of Streamlit's `st.session_state`.

