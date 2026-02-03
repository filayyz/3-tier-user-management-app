"""Flask User Management App with REST API and Cloud SQL."""
import os
import logging
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
import bcrypt

from db import get_connection

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize database on app startup
@app.before_request
def ensure_db():
    """Ensure database table exists before first request."""
    if not hasattr(app, '_db_initialized'):
        init_db()
        app._db_initialized = True


def get_db():
    """Get database connection. Creates new connection per request for reliability."""
    return get_connection()


def init_db():
    """Initialize database and create table if not exists."""
    from db import _use_sqlite
    db = get_db()
    cursor = db.cursor()
    if _use_sqlite():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255),
                email VARCHAR(255),
                Address TEXT,
                phonenumber VARCHAR(255),
                password VARCHAR(255)
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                Address TEXT,
                phonenumber VARCHAR(255),
                password VARCHAR(255)
            )
        """)
    db.commit()
    cursor.close()
    db.close()


def row_to_dict(row):
    """Convert database row to dict, excluding password."""
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "address": row[3],
        "phonenumber": row[4],
    }


# ============== Web Routes ==============

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method != 'POST':
        return redirect(url_for('index'))

    name = request.form.get('name')
    email = request.form.get('email')
    address = request.form.get('address')
    phonenumber = request.form.get('phonenumber')
    password = request.form.get('password')

    if not all([name, email, address, phonenumber, password]):
        return redirect(url_for('index'))

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO user (name, email, Address, phonenumber, password) VALUES (%s, %s, %s, %s, %s)",
                (name, email, address, phonenumber, hashed_password)
            )
            db.commit()
            cursor.execute("SELECT * FROM user ORDER BY id DESC LIMIT 1")
            data = cursor.fetchall()
        finally:
            cursor.close()
            db.close()

        return render_template('submitteddata.html', data=data)
    except Exception as e:
        logging.error(f"Error adding user: {e}")
        return f"Error: {str(e)}", 500


@app.route('/get-data', methods=['GET', 'POST'])
def get_data():
    if request.method == 'POST':
        input_id = request.form.get('input_id')
        if not input_id:
            return render_template('get_data.html')

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM user WHERE id = %s", (input_id,))
            data = cursor.fetchall()
        finally:
            cursor.close()
            db.close()

        return render_template('data.html', data=data, input_id=input_id)
    return render_template('get_data.html')


@app.route('/users')
def users_list():
    """Page showing all users (fetches via API)."""
    return render_template('users.html')


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_data(id):
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM user WHERE id = %s", (id,))
            db.commit()
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('users_list'))
    return render_template('delete.html', id=id)


# ============== REST API ==============

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Fetch all users from the database."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id, name, email, Address, phonenumber FROM user ORDER BY id")
        rows = cursor.fetchall()
        users = [
            {"id": r[0], "name": r[1], "email": r[2], "address": r[3], "phonenumber": r[4]}
            for r in rows
        ]
        return jsonify({"users": users})
    finally:
        cursor.close()
        db.close()


@app.route('/api/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """Fetch a single user by ID."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id, name, email, Address, phonenumber FROM user WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            abort(404)
        return jsonify({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "address": row[3],
            "phonenumber": row[4],
        })
    finally:
        cursor.close()
        db.close()


@app.route('/api/users', methods=['POST'])
def api_create_user():
    """Create a new user. Expects JSON body."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ['name', 'email', 'address', 'phonenumber', 'password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    hashed_password = bcrypt.hashpw(
        data['password'].encode('utf-8'), bcrypt.gensalt()
    )

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO user (name, email, Address, phonenumber, password) VALUES (%s, %s, %s, %s, %s)",
            (data['name'], data['email'], data['address'], data['phonenumber'], hashed_password)
        )
        db.commit()
        user_id = cursor.lastrowid
    finally:
        cursor.close()
        db.close()

    return jsonify({
        "id": user_id,
        "name": data['name'],
        "email": data['email'],
        "address": data['address'],
        "phonenumber": data['phonenumber'],
    }), 201


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """Delete a user by ID."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
        db.commit()
        if cursor.rowcount == 0:
            abort(404)
    finally:
        cursor.close()
        db.close()
    return jsonify({"message": "User deleted"}), 200


# ============== Startup ==============

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, port=port, host='0.0.0.0')
