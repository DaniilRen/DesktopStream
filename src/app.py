# app.py
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "addresses.db")

# Initialize DB and create table if not exists
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_addr TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()

        # Insert sample addresses if table is empty
        c.execute("SELECT COUNT(*) FROM addresses")
        count = c.fetchone()[0]
        if count == 0:
            sample_addresses = ['192.168.0.142']
            c.executemany("INSERT INTO addresses (ip_addr) VALUES (?)",
                          [(addr,) for addr in sample_addresses])
            conn.commit()

# Helper functions for DB operations
def get_all_addresses():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT ip_addr FROM addresses ORDER BY ip_addr")
        return [row[0] for row in c.fetchall()]

def add_address(addr):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO addresses (ip_addr) VALUES (?)", (addr,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def delete_address(addr):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM addresses WHERE ip_addr = ?", (addr,))
        conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'add_address' in request.form:
            new_addr = request.form.get('new_address', '').strip()
            if new_addr:
                success = add_address(new_addr)
                if success:
                    flash(f'Адрес {new_addr} добавлен', 'success')
                else:
                    flash('Этот адрес уже есть в сохранённых', 'warning')
            else:
                flash('Введите корректный адрес', 'error')
            return redirect(url_for('index'))

        if 'delete_address' in request.form:
            del_addr = request.form.get('del_address')
            if del_addr:
                delete_address(del_addr)
                flash(f'Адрес {del_addr} удалён', 'success')
            return redirect(url_for('index'))

        if 'connect_manual' in request.form:
            manual_addr = request.form.get('manual_address', '').strip()
            if manual_addr:
                return redirect(f'http://{manual_addr}:5500')  # Redirect outside Flask app
            else:
                flash('Введите адрес подключения', 'error')
                return redirect(url_for('index'))

    addresses = get_all_addresses()
    return render_template('index.html', addresses=addresses)


@app.route('/connect/<path:ip_addr>')
def connect_remote(ip_addr):
    # Redirect user to the streaming page on the given IP and port 5500
    return redirect(f'http://{ip_addr}:5500')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
