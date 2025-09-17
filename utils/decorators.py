from functools import wraps
from flask import session, flash, redirect, url_for
from .supabase_client import supabase
from gotrue.errors import AuthApiError

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = session.get('access_token')
        refresh_token = session.get('refresh_token')
        if not all([access_token, refresh_token]):
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('login'))
        try:
            supabase.auth.set_session(access_token, refresh_token)
        except AuthApiError:
            session.clear()
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin_logged_in'):
            flash("You must be logged in as an admin to view this page.", "warning")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function