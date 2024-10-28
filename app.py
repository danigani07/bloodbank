from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='bloodbank-db.clacek8ey7ty.us-east-1.rds.amazonaws.com',  # e.g., 'your-db-instance.abc123xyz.us-east-1.rds.amazonaws.com'
        user='admin',
        password='bloodbank12345',
        database='bloodbankdb'
    )

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                       (username, password, role))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['role'] = user[2]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

# Dashboard route
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

# Schedule donation route
@app.route('/schedule_donation', methods=['GET', 'POST'])
def schedule_donation():
    if request.method == 'POST':
        blood_type = request.form['blood_type']
        donation_time = request.form['donation_time']
        location = request.form['location']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO donations (user_id, blood_type, donation_time, location) VALUES (%s, %s, %s, %s)",
                       (session['user_id'], blood_type, donation_time, location))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Donation scheduled successfully!')
        return redirect(url_for('dashboard'))

    return render_template('schedule_donation.html')

# Blood request route
@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        blood_type = request.form['blood_type']
        quantity = request.form['quantity']
        urgency = request.form['urgency']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO blood_requests (user_id, blood_type, quantity, urgency) VALUES (%s, %s, %s, %s)",
                       (session['user_id'], blood_type, quantity, urgency))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Blood request submitted successfully!')
        return redirect(url_for('dashboard'))

    return render_template('request_blood.html')

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
