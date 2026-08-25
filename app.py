from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template("login.html")

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

@app.route('/add-test-product')
def add_test_product():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, price, quantity, image, category, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Sample Laptop', 150000, 1, 'images/trial.jpg', 'Electronics', 'A test product for the shop page'))
    conn.commit()
    conn.close()
    return 'Test product added! Go check /shop'



if __name__ == '__main__':
    create_table()
    create_roommates_table()
    app.run(debug=True)