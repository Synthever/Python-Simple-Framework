from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

app = Flask(__name__, static_folder='public', static_url_path='/static')
app.secret_key = 'your-secret-key-here'  # Change this in production

JSON_FILE = './database/data.json'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_users():
    with open('./database/auth.json', 'r') as f:
        return json.load(f)['data']

def load_items():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
            return data.get('items', [])
    return []

def save_items(items):
    with open(JSON_FILE, 'w') as f:
        json.dump({'items': items}, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        user = next((user for user in users if user['username'] == username and user['password'] == password), None)
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
        else:
            return render_template('auth/index.html', error='Invalid username or password')
            
    return render_template('auth/index.html')

@app.route('/home')
@login_required
def home():
    items = load_items()
    return render_template('home/index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        items = load_items()
        new_item = {
            'id': len(items) + 1,
            'name': request.form['name'],
            'description': request.form['description']
        }
        items.append(new_item)
        save_items(items)
        return redirect(url_for('home'))
    return render_template('home/add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    items = load_items()
    item = next((item for item in items if item['id'] == id), None)
    if request.method == 'POST':
        item['name'] = request.form['name']
        item['description'] = request.form['description']
        save_items(items)
        return redirect(url_for('home'))
    return render_template('home/edit.html', item=item)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    items = load_items()
    items = [item for item in items if item['id'] != id]
    save_items(items)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
