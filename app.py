from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from flask_cors import CORS
from contextlib import contextmanager

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Improved database connection with context manager
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=os.getenv('bloodbank-db.clacek8ey7ty.us-east-1.rds.amazonaws.com'),
            user=os.getenv('admin'),
            password=os.getenv('bloodbank12345'),
            database=os.getenv('bloodbridge')
        )
        yield conn
    except mysql.connector.Error as e:
        flash(f'Database connection error: Please try again later', 'error')
        raise e
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            role = request.form['role']
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                           (username, password, role))
                conn.commit()
                cursor.close()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                cursor.close()
            
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['role'] = user[2]
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!')
        except Exception as e:
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session['role']
    if role == 'donor':
        return render_template('donor_dashboard.html')
    elif role == 'requestor':
        return render_template('requestor_dashboard.html')
    elif role in ['donation_camp_manager', 'inventory_manager']:
        return render_template('manager_dashboard.html')

@app.route('/schedule_donation', methods=['GET', 'POST'])
def schedule_donation():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            blood_type = request.form['blood_type']
            donation_time = request.form['donation_time']
            location = request.form['location']
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO donations (user_id, blood_type, donation_time, location) VALUES (%s, %s, %s, %s)",
                           (session['user_id'], blood_type, donation_time, location))
                conn.commit()
                cursor.close()
            flash('Donation scheduled successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Failed to schedule donation. Please try again.', 'error')

    return render_template('schedule_donation.html')

@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            blood_type = request.form['blood_type']
            quantity = request.form['quantity']
            urgency = request.form['urgency']
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO blood_requests (user_id, blood_type, quantity, urgency) VALUES (%s, %s, %s, %s)",
                           (session['user_id'], blood_type, quantity, urgency))
                conn.commit()
                cursor.close()
            flash('Blood request submitted successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Failed to submit blood request. Please try again.', 'error')

    return render_template('request_blood.html')

if __name__ == '__main__':
    # Add production-ready server configuration
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
