import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from utils.supabase_client import supabase, supabase_admin
from utils.decorators import login_required, admin_password_required

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ====================
# USER AUTHENTICATION ROUTES
# ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            supabase.auth.sign_in_with_otp({"email": email})
            flash("A login code has been sent to your email.", "info")
            return redirect(url_for('verify', email=email))
        except Exception as e:
            flash(f"Error sending OTP: {e}", "danger")
    return render_template('auth/login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if session.get('user'):
        return redirect(url_for('user_dashboard'))
    email = request.args.get('email')
    if not email:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        otp = request.form.get('otp')
        try:
            res = supabase.auth.verify_otp({"email": email, "token": otp, "type": "email"})
            if res.user and res.session:
                session['user'] = {'id': res.user.id, 'email': res.user.email}
                session['access_token'] = res.session.access_token
                # PROACTIVELY FIXED: Added refresh_token to prevent future JWT expired errors for users
                session['refresh_token'] = res.session.refresh_token
                flash("Login successful!", "success")
                return redirect(url_for('user_dashboard'))
            else:
                flash("Invalid or expired OTP. Please try again.", "danger")
        except Exception as e:
            flash(f"Error during verification: {e}", "danger")
    
    return render_template('auth/verify.html', email=email)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# ====================
# ADMIN PASSWORD AUTH ROUTES
# ====================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '441106':
            session['is_admin_logged_in'] = True
            flash("Admin login successful.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Incorrect admin password.", "danger")
            # It's better to redirect back to the login page on failure
            return redirect(url_for('admin_login'))

    return render_template('auth/admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin_logged_in', None)
    flash("You have been logged out from the admin panel.", "info")
    return redirect(url_for('index'))

# ====================
# PUBLIC ROUTES
# ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    try:
        menu_items = supabase.table('menu').select('*').order('category').execute()
        return render_template('menu.html', menu=menu_items.data)
    except Exception as e:
        flash(f"Could not load menu: {e}", "danger")
        return render_template('menu.html', menu=[])

# ====================
# USER-FACING ROUTES
# ====================
@app.route('/dashboard')
@login_required
def user_dashboard():
    user_id = session['user']['id']
    try:
        profile = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        orders = supabase.table('orders').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(5).execute()
        bookings = supabase.table('bookings').select('*').eq('user_id', user_id).order('booking_date', desc=True).limit(5).execute()
        return render_template('user/dashboard.html', profile=profile.data, orders=orders.data, bookings=bookings.data)
    except Exception as e:
        flash(f"Error fetching dashboard data: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user']['id']
    if request.method == 'POST':
        try:
            supabase.table('profiles').update({
                'full_name': request.form.get('full_name'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address')
            }).eq('id', user_id).execute()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating profile: {e}", "danger")
        return redirect(url_for('profile'))
        
    profile_data = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
    return render_template('user/profile.html', profile=profile_data.data)

@app.route('/order', methods=['POST'])
@login_required
def place_order():
    user_id = session['user']['id']
    items_json = request.form.get('items')
    if not items_json or items_json == '[]':
        flash("Your cart is empty.", "danger")
        return redirect(url_for('menu'))
    cart_items = json.loads(items_json)
    try:
        item_ids = [item['item_id'] for item in cart_items]
        menu_items_res = supabase.table('menu').select('id, price').in_('id', item_ids).execute()
        menu_items_db = {str(item['id']): item['price'] for item in menu_items_res.data}
        total_price = 0
        for item in cart_items:
            price = float(menu_items_db.get(str(item['item_id']), 0))
            total_price += price * item['quantity']
        supabase.table('orders').insert({'user_id': user_id, 'items': cart_items, 'total_price': total_price}).execute()
        flash("Order placed successfully! Thank you.", "success")
        return redirect(url_for('user_dashboard'))
    except Exception as e:
        flash(f"Error placing order: {e}", "danger")
        return redirect(url_for('menu'))

@app.route('/book', methods=['POST'])
@login_required
def book_venue():
    user_id = session['user']['id']
    try:
        supabase.table('bookings').insert({
            'user_id': user_id,
            'booking_date': request.form.get('booking_date'),
            'time_slot': request.form.get('time_slot')
        }).execute()
        flash("Venue booked successfully! Awaiting confirmation.", "success")
    except Exception as e:
        flash(f"Error booking venue: {e}", "danger")
    return redirect(url_for('user_dashboard'))

# ====================
# ADMIN ROUTES (USING PRIVILEGED CLIENT)
# ====================
@app.route('/admin')
@admin_password_required
def admin_dashboard():
    try:
        users = supabase_admin.table('profiles').select('id', count='exact').execute()
        orders = supabase_admin.table('orders').select('id', count='exact').execute()
        bookings = supabase_admin.table('bookings').select('id', count='exact').execute()
        return render_template('admin/dashboard.html', user_count=users.count, order_count=orders.count, booking_count=bookings.count)
    except Exception as e:
        flash(f"Error loading admin dashboard: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/admin/users')
@admin_password_required
def admin_users():
    users = supabase_admin.from_('profiles').select('id, full_name, phone, address, role').execute()
    return render_template('admin/users.html', users=users.data)

@app.route('/admin/orders')
@admin_password_required
def admin_orders():
    orders = supabase_admin.table('orders').select('*, profiles(full_name)').order('created_at', desc=True).execute()
    return render_template('admin/orders.html', orders=orders.data)

@app.route('/admin/bookings')
@admin_password_required
def admin_bookings():
    bookings = supabase_admin.table('bookings').select('*, profiles(full_name)').order('booking_date', desc=True).execute()
    return render_template('admin/bookings.html', bookings=bookings.data)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@admin_password_required
def update_order_status(order_id):
    supabase_admin.table('orders').update({'status': request.form.get('status')}).eq('id', order_id).execute()
    flash(f"Order #{order_id} status updated.", "success")
    return redirect(url_for('admin_orders'))

@app.route('/admin/bookings/update/<int:booking_id>', methods=['POST'])
@admin_password_required
def update_booking_status(booking_id):
    supabase_admin.table('bookings').update({'status': request.form.get('status')}).eq('id', booking_id).execute()
    flash(f"Booking #{booking_id} status updated.", "success")
    return redirect(url_for('admin_bookings'))

if __name__ == '__main__':
    app.run(debug=True)