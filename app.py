from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "gym_secret_key"

# =========================
# ADMIN LOGIN
# =========================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect('database/gym.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT,
        membership_plan TEXT,
        membership_status TEXT,
        expiry_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workout_plan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        plan TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diet_plan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        diet TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        amount TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()


if not os.path.exists("database"):
    os.makedirs("database")

init_db()
# =========================
# HOME
# =========================
@app.route('/')
def home():
    return render_template('index.html')

# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database/gym.db')
        cursor = conn.cursor()

        cursor.execute("""
        SELECT fullname, membership_plan, membership_status, expiry_date
        FROM users
        WHERE email=? AND password=?
        """, (email, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = email
            return redirect(url_for('dashboard'))

        return "Invalid login"

    return render_template('login.html')

# =========================
# SIGNUP
# =========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        membership = request.form['membership']

        if membership == "Basic":
            expiry = datetime.now() + timedelta(days=30)
        elif membership == "Pro":
            expiry = datetime.now() + timedelta(days=90)
        else:
            expiry = datetime.now() + timedelta(days=365)

        expiry = expiry.strftime("%d-%m-%Y")

        conn = sqlite3.connect('database/gym.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO users(fullname,email,phone,password,membership_plan,membership_status,expiry_date)
            VALUES(?,?,?,?,?,?,?)
            """, (fullname, email, phone, password, membership, "ACTIVE", expiry))

            conn.commit()
            conn.close()

            return redirect(url_for('login'))

        except:
            conn.close()
            return "Email already exists"

    return render_template('signup.html')

# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']

    conn = sqlite3.connect('database/gym.db')
    cursor = conn.cursor()

    cursor.execute("SELECT fullname, membership_plan, membership_status, expiry_date FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE email=?", (email,))
    attendance = cursor.fetchone()[0]

    cursor.execute("SELECT plan FROM workout_plan WHERE email=?", (email,))
    workout_data = cursor.fetchone()

    cursor.execute("SELECT diet FROM diet_plan WHERE email=?", (email,))
    diet_data = cursor.fetchone()

    conn.close()

    workout = workout_data[0] if workout_data else "Not Assigned Yet"
    diet = diet_data[0] if diet_data else "Not Assigned Yet"

    expiry_date = datetime.strptime(user[3], "%d-%m-%Y")
    days_left = (expiry_date - datetime.now()).days

    if days_left < 0:
        alert = "❌ Membership Expired"
    elif days_left <= 7:
        alert = f"⚠️ Expires in {days_left} days"
    else:
        alert = "✅ Active Membership"

    return render_template(
        "dashboard.html",
        username=user[0],
        plan=user[1],
        status=user[2],
        expiry=user[3],
        attendance=attendance,
        workout=workout,
        diet=diet,
        alert=alert
    )

# =========================
# ATTENDANCE
# =========================
@app.route('/mark-attendance')
def mark_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']
    today = datetime.now().strftime("%d-%m-%Y")

    conn = sqlite3.connect('database/gym.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance WHERE email=? AND date=?", (email, today))

    if not cursor.fetchone():
        cursor.execute("INSERT INTO attendance(email,date) VALUES(?,?)", (email, today))

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# =========================
# PAYMENT
# =========================
@app.route('/pay')
def pay():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']

    conn = sqlite3.connect('database/gym.db')
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO payments(email,amount,status)
    VALUES(?,?,?)
    """, (email, "999", "PAID"))

    conn.commit()
    conn.close()

    return "<h2>Payment Successful ✅</h2><a href='/dashboard'>Go Back</a>"

# =========================
# BMI
# =========================
@app.route('/bmi', methods=['GET', 'POST'])
def bmi():
    bmi_value = None
    category = None

    if request.method == 'POST':
        height = float(request.form['height'])
        weight = float(request.form['weight'])

        height = height / 100
        bmi_value = round(weight / (height * height), 2)

        if bmi_value < 18.5:
            category = "Underweight"
        elif bmi_value < 25:
            category = "Normal"
        elif bmi_value < 30:
            category = "Overweight"
        else:
            category = "Obese"

    return render_template("bmi.html", bmi=bmi_value, category=category)

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run()