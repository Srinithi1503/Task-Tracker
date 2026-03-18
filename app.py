from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB = "tasks.db"

# =====================
# DATABASE CONNECTION
# =====================
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# =====================
# CREATE TABLES
# =====================
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    FOREIGN KEY(user_id) REFERENCES users(id)
                 )''')
    conn.commit()
    conn.close()

init_db()

# =====================
# ROUTES
# =====================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# ---------------------
# LOGIN
# ---------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login Successful ✅")
            return redirect(url_for('index'))
        else:
            flash("Invalid Credentials ❌")
            return redirect(url_for('login'))
    return render_template("login.html")

# ---------------------
# SIGNUP
# ---------------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
            conn.commit()
            flash("Signup Successful ✅ Login now")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists ❌")
            return redirect(url_for('signup'))
        finally:
            conn.close()
    return render_template("signup.html")

# ---------------------
# LOGOUT
# ---------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged Out 🔒")
    return redirect(url_for('login'))

# ---------------------
# DASHBOARD
# ---------------------
@app.route('/index', methods=['GET','POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # ADD TASK
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description','')
        deadline = request.form['deadline']
        priority = request.form['priority']
        c.execute("INSERT INTO tasks (user_id,title,description,deadline,priority) VALUES (?,?,?,?,?)",
                  (session['user_id'], title, description, deadline, priority))
        conn.commit()
        flash("Task added ✅")
    
    # FILTER & SEARCH
    filter_status = request.args.get('filter', 'All')
    search = request.args.get('search','')

    query = "SELECT * FROM tasks WHERE user_id=?"
    params = [session['user_id']]
    if filter_status != 'All':
        query += " AND status=?"
        params.append(filter_status)
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    c.execute(query, params)
    tasks = c.fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks, username=session['username'], search=search)

# ---------------------
# UPDATE STATUS
# ---------------------
@app.route('/update_status/<int:task_id>')
def update_status(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM tasks WHERE id=? AND user_id=?", (task_id, session['user_id']))
    task = c.fetchone()
    if task:
        new_status = 'Completed' if task['status']=='Pending' else 'Pending'
        c.execute("UPDATE tasks SET status=? WHERE id=? AND user_id=?", (new_status, task_id, session['user_id']))
        conn.commit()
        flash("Task status updated 🔄")
    conn.close()
    return redirect(url_for('index'))

# ---------------------
# DELETE TASK
# ---------------------
@app.route('/delete/<int:task_id>')
def delete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Task deleted ❌")
    return redirect(url_for('index'))

# ---------------------
# EDIT TASK
# ---------------------
@app.route('/edit/<int:task_id>', methods=['GET','POST'])
def edit(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (task_id, session['user_id']))
    task = c.fetchone()
    if not task:
        flash("Task not found ❌")
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description','')
        deadline = request.form['deadline']
        priority = request.form['priority']
        c.execute("UPDATE tasks SET title=?, description=?, deadline=?, priority=? WHERE id=? AND user_id=?",
                  (title, description, deadline, priority, task_id, session['user_id']))
        conn.commit()
        flash("Task updated 🔄")
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template("edit.html", task=task)

# =====================
# RUN APP
# =====================
if __name__ == "__main__":
    app.run(debug=True)