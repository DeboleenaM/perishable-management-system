from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db_connection
from datetime import datetime, timedelta, date
from functools import wraps  # ✅ for admin decorator

main = Blueprint('main', __name__)

# ------------------- Role Decorator ----------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Access denied: Admins only.")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- Auth Routes -------------------------
@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username'] = username
            session['role'] = user.get('role', 'staff')  # Default to 'staff' if missing
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'staff')  # Optional: default role

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful. Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('main.login'))
    return render_template('dashboard.html', username=session['username'], role=session.get('role'))

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

# ------------------- Inventory --------------------------
@main.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']
        shelf_life = request.form['shelf_life']
        added_date = request.form['added_date']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, category, quantity, price, shelf_life, added_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, category, quantity, price, shelf_life, added_date))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('main.view_inventory'))
    return render_template('add_product.html')

@main.route('/view_inventory')
def view_inventory():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('inventory.html', items=items)

# ------------------- Helpers ----------------------------
def normalize_date(d):
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    elif isinstance(d, date):
        return d
    else:
        raise ValueError("Unknown date format: " + str(d))

# ------------------- Admin-Only Routes ------------------
@main.route('/view_expired')
@admin_required
def view_expired():
    today = datetime.now().date()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products')
    all_products = cursor.fetchall()

    expired = []
    for product in all_products:
        added_date = normalize_date(product['added_date'])
        shelf_life = int(product['shelf_life'])
        expiry_date = added_date + timedelta(days=shelf_life)
        if today > expiry_date:
            product['days_expired'] = (today - expiry_date).days
            expired.append(product)

    cursor.close()
    conn.close()
    return render_template('expired_items.html', expired_items=expired)

@main.route('/view_discounted')
@admin_required
def view_discounted():
    today = datetime.now().date()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM products')
    all_products = cursor.fetchall()

    discounted = []
    for product in all_products:
        added_date = normalize_date(product['added_date'])
        shelf_life = int(product['shelf_life'])
        days_passed = (today - added_date).days
        if days_passed > (shelf_life * 0.7) and days_passed <= shelf_life:
            product['discounted_price'] = round(float(product['price']) * 0.8, 2)
            discounted.append(product)

    cursor.close()
    conn.close()
    return render_template('discounted_items.html', discounted_items=discounted)


@main.route('/remove', methods=['POST'])
@admin_required  # if you're using this decorator
def remove_item():
    item_id = request.form.get('item_id')
    if not item_id:
        flash("Item ID is missing", "danger")
        return redirect(url_for('main.view_inventory'))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (item_id,))
        conn.commit()
        flash("Item removed successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('main.view_inventory'))

@main.route('/view_users')
@admin_required
def view_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, email, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('users.html', users=users)
