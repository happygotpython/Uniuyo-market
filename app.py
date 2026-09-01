import os
import sqlite3

from PIL import Image

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-fallback-key-change-me')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('market.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            image TEXT,
            category TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_roommates_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roommates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT NOT NULL,
            bio TEXT,
            image TEXT,
            contact TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_users_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
  
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass 
    conn.commit()
    conn.close()

def create_wallets_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            balance REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_withdrawals_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_platform_wallet_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_wallet (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO platform_wallet (id, balance) VALUES (1, 0.0)')
    conn.commit()
    conn.close()

def create_orders_table():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            buyer_id INTEGER,
            seller_id INTEGER,
            price REAL NOT NULL,
            commission REAL NOT NULL,
            seller_payout REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products LIMIT 6')
    listings = cursor.fetchall()
    conn.close()
    return render_template('homepage.html', listings=listings)

@app.route('/signup', methods=['GET', 'POST'])
def making_account():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = init_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            
            new_user_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO wallets (user_id, balance)
                VALUES (?, 0.0)
            ''', (new_user_id,))

            conn.commit()
            conn.close()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            error = 'Email already exists. Please use a different email.'

    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = init_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user is None:
            conn.close()
            error = 'No Account Found!'
        elif check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']

            cursor.execute('SELECT * FROM wallets WHERE user_id = ?', (user['id'],))
            wallet = cursor.fetchone()

            if wallet is None:
                cursor.execute('INSERT INTO wallets (user_id, balance) VALUES (?, 0.0)', (user['id'],))
                conn.commit()

            conn.close()
            flash('Welcome back!', 'success')
            return redirect(url_for('home'))
        else:
            conn.close()
            error = 'Invalid email or password'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/shop')
def shop():
    category_filter = request.args.get('category')
    search_query = request.args.get('q')

    conn = init_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM products WHERE 1=1'
    params = []

    if category_filter and category_filter != 'All':
        query += ' AND category = ?'
        params.append(category_filter)

    if search_query:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        params.append(f'%{search_query}%')
        params.append(f'%{search_query}%')

    cursor.execute(query, params)
    listings = cursor.fetchall()
    conn.close()

    return render_template('shop.html', listings=listings, active_category=category_filter or 'All')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user_id' not in session:
        flash('Please login to sell items.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        category = request.form['category']
        description = request.form['description']
        user_id = session['user_id']

        image_path = 'images/default-item.jpg'

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                img = Image.open(file)
                img.thumbnail((800, 800)) 
                img.save(file_path, optimize=True, quality=85)

                image_path = f'uploads/{filename}'

        conn = init_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (user_id, name, price, quantity, image, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, price, quantity, image_path, category, description))
        conn.commit()
        conn.close()

        flash('Product listed successfully!', 'success')
        return redirect(url_for('shop'))

    return render_template('sell.html')

@app.route('/roommates')
def roommates():
    level_filter = request.args.get('level')
    search_query = request.args.get('q')

    conn = init_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM roommates WHERE 1=1'
    params = []

    if level_filter:
        query += ' AND level = ?'
        params.append(level_filter)

    if search_query:
        query += ' AND (name LIKE ? OR bio LIKE ?)'
        params.append(f'%{search_query}%')
        params.append(f'%{search_query}%')

    cursor.execute(query, params)
    roommate_list = cursor.fetchall()
    conn.close()
    return render_template('roommates.html', roommates=roommate_list)

@app.route('/post-roommate', methods=['GET', 'POST'])
def post_roommate():
    if 'user_id' not in session:
        flash('Please login to post a roommate listing.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        level = request.form['level']
        bio = request.form['bio']
        contact = request.form['contact']
        
        image_path = 'images/default-avatar.jpg'

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
              
                img = Image.open(file)
                img.thumbnail((800, 800))
                img.save(file_path, optimize=True, quality=85)

                image_path = f'uploads/{filename}'

        conn = init_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO roommates (name, level, bio, image, contact)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, level, bio, image_path, contact))
        conn.commit()
        conn.close()

        flash('Roommate request posted!', 'success')
        return redirect(url_for('roommates'))

    return render_template('post_roommate.html')

@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    if 'user_id' not in session:
        flash('Please login to buy items.', 'danger')
        return redirect(url_for('login'))

    buyer_id = session['user_id']

    conn = init_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if not product or product['quantity'] < 1:
        conn.close()
        flash('Item is out of stock!', 'danger')
        return redirect(url_for('shop'))

    if product['user_id'] == buyer_id:
        conn.close()
        flash("You can't buy your own listing!", 'warning')
        return redirect(url_for('shop'))

    cursor.execute('SELECT balance FROM wallets WHERE user_id = ?', (buyer_id,))
    buyer_wallet = cursor.fetchone()
    current_balance = buyer_wallet['balance'] if buyer_wallet else 0.0

    if current_balance < product['price']:
        conn.close()
        flash('Insufficient wallet balance! Please top up your account.', 'warning')
        return redirect(url_for('wallet'))

    seller_id = product['user_id']
    total_price = product['price']
    commission = total_price * 0.05
    seller_payout = total_price - commission

    cursor.execute('UPDATE wallets SET balance = balance - ? WHERE user_id = ?', (total_price, buyer_id))
    cursor.execute('UPDATE wallets SET balance = balance + ? WHERE user_id = ?', (seller_payout, seller_id))
    cursor.execute('UPDATE platform_wallet SET balance = balance + ? WHERE id = 1', (commission,))
    cursor.execute('UPDATE products SET quantity = quantity - 1 WHERE id = ?', (product_id,))

    cursor.execute('''
        INSERT INTO orders (product_id, product_name, buyer_id, seller_id, price, commission, seller_payout)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, product['name'], buyer_id, seller_id, total_price, commission, seller_payout))

    conn.commit()
    conn.close()

    flash('Purchase successful! Item bought.', 'success')
    return redirect(url_for('shop'))

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user_id' not in session:
        flash('Please login to access your wallet.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = init_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        amount = float(request.form['amount'])
        bank_name = request.form['bank_name']
        account_number = request.form['account_number']

        cursor.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
        user_wallet = cursor.fetchone()

        if user_wallet and user_wallet['balance'] >= amount and amount > 0:
            cursor.execute('UPDATE wallets SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
            cursor.execute('''
                INSERT INTO withdrawals (user_id, amount, bank_name, account_number)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, bank_name, account_number))
            conn.commit()
            flash('Withdrawal request submitted successfully!', 'success')
        else:
            flash('Invalid amount or insufficient balance.', 'danger')

    cursor.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
    user_wallet = cursor.fetchone()
    balance = user_wallet['balance'] if user_wallet else 0.0
    
    cursor.execute('SELECT * FROM withdrawals WHERE user_id = ? ORDER BY id DESC', (user_id,))
    history = cursor.fetchall()
    conn.close()

    return render_template('wallet.html', balance=balance, history=history)

@app.route('/topup', methods=['POST'])
def topup():
    if 'user_id' not in session:
        flash('Please login to top up.', 'danger')
        return redirect(url_for('login'))
    
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        conn = init_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET balance = balance + ? WHERE user_id = ?', (amount, session['user_id']))
        conn.commit()
        conn.close()
        flash(f'Successfully added ₦{amount:.2f} to your wallet!', 'success')
        
    return redirect(url_for('wallet'))

@app.route('/admin/withdrawals')
def admin_withdrawals():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'danger')
        return redirect(url_for('login'))

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()

    if not user or user['is_admin'] != 1:
        conn.close()
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('home'))

    cursor.execute('''
        SELECT withdrawals.id, withdrawals.amount, withdrawals.bank_name, 
               withdrawals.account_number, withdrawals.status, users.username, users.email
        FROM withdrawals
        JOIN users ON withdrawals.user_id = users.id
        ORDER BY withdrawals.id DESC
    ''')
    requests_list = cursor.fetchall()
    conn.close()

    return render_template('admin_withdrawals.html', requests=requests_list)

@app.route('/admin/withdrawals/complete/<int:withdrawal_id>', methods=['POST'])
def complete_withdrawal(withdrawal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE withdrawals SET status = 'Completed' WHERE id = ?", (withdrawal_id,))
    conn.commit()
    conn.close()

    flash('Withdrawal request marked as paid!', 'success')
    return redirect(url_for('admin_withdrawals'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('shop'))

    return render_template('product_detail.html', product=product)

@app.route('/admin/earnings')
def admin_earnings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()

    if not user or user['is_admin'] != 1:
        conn.close()
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('home'))

    cursor.execute('SELECT balance FROM platform_wallet WHERE id = 1')
    platform_balance = cursor.fetchone()['balance']
    conn.close()

    return f"Platform earnings so far: ₦{platform_balance:.2f}"

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login to view your orders.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = init_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM orders WHERE buyer_id = ? ORDER BY created_at DESC', (user_id,))
    purchases = cursor.fetchall()

    cursor.execute('SELECT * FROM orders WHERE seller_id = ? ORDER BY created_at DESC', (user_id,))
    sales = cursor.fetchall()

    conn.close()
    return render_template('orders.html', purchases=purchases, sales=sales)

if __name__ == '__main__':
    create_table()
    create_roommates_table()
    create_users_table()
    create_wallets_table()
    create_withdrawals_table()
    create_platform_wallet_table()
    create_orders_table()
    app.run(debug=True)