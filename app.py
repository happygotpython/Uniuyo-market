from email.message import Message

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
            quantity INTEGER NOT NULL
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


if __name__ == '__main__':
        app.run(debug=True)