from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

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
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            image TEXT,
            category TEXT,
            description TEXT
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
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def home():
    return render_template('homepage.html')

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
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            error = 'Email already exists. Please use a different email.'
        conn.close()
        return render_template('signup.html', error=error)
        conn.close()
        return redirect(url_for('login'))

    return render_template('signup.html')

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
        conn.close()

        if user is None:
            error = 'No Account Found!'
        elif check_password_hash(user['password'], password):
            return f'Welcome back, {user["username"]}!'
        else:
            error = 'Invalid email or password'

    return render_template('login.html', error=error)

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
    if request.method == 'POST':
        name = request.form['name']
        level = request.form['level']
        bio = request.form['bio']
        contact = request.form['contact']
        image = 'images/default-avatar.jpg'

        conn = init_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO roommates (name, level, bio, image, contact)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, level, bio, image, contact))
        conn.commit()
        conn.close()

        return redirect(url_for('roommates'))

    return render_template('post_roommate.html')

@app.route('/shop')
def shop():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    listings = cursor.fetchall()
    conn.close()
    return render_template('shop.html', listings=listings)

if __name__ == '__main__':
    create_table()
    create_roommates_table()
    create_users_table()
    app.run(debug=True)