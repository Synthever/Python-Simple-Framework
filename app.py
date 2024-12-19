from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps
import jinja2

app = Flask(__name__, static_folder='public', static_url_path='/static')
app.secret_key = 'your-secret-key-here'
app.url_map.strict_slashes = False  # Add this line to handle trailing slashes

JSON_FILE = './database/auth.json'
JSON_FILE = './database/buku.json'
JSON_FILE = './database/member.json'

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

def load_books():
    with open('./database/buku.json', 'r') as f:
        return json.load(f)['buku']
    
def load_members():
    with open('./database/member.json', 'r') as f:
        return json.load(f)['member']

def get_book_by_id(book_id):
    books = load_books()
    return next((book for book in books if book['id_buku'] == book_id), None)

def update_book(book_id, updated_book):
    books = load_books()
    for i, book in enumerate(books):
        if book['id_buku'] == book_id:
            books[i] = updated_book
            break
    with open('./database/buku.json', 'w') as f:
        json.dump({'buku': books}, f, indent=4, ensure_ascii=False)

def delete_book(book_id):
    books = load_books()
    books = [book for book in books if book['id_buku'] != book_id]
    with open('./database/buku.json', 'w') as f:
        json.dump({'buku': books}, f, indent=4, ensure_ascii=False)

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

# Books
@app.route('/books')
@login_required
def book_list():
    books = load_books()
    return render_template('books/list.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def book_add():
    if request.method == 'POST':
        books = load_books()
        new_book = {
            "id_buku": len(books) + 1,
            "judul": request.form['title'],
            "pengarang": request.form['author'],
            "penerbit": request.form['publisher'],
            "tahun_terbit": request.form['year'],
            "stock": request.form['stock'],
            "rak": request.form['rack']
        }
        books.append(new_book)
        
        with open('./database/buku.json', 'w') as f:
            json.dump({'buku': books}, f, indent=4, ensure_ascii=False)
            
        flash('Buku berhasil ditambahkan!', 'success')
        return redirect(url_for('book_list'))
        
    return render_template('books/add.html')

@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def book_edit(id):
    book = get_book_by_id(id)
    if not book:
        flash('Buku tidak ditemukan!', 'error')
        return redirect(url_for('book_list'))
        
    if request.method == 'POST':
        updated_book = {
            "id_buku": id,
            "judul": request.form['title'],
            "pengarang": request.form['author'],
            "penerbit": request.form['publisher'],
            "tahun_terbit": request.form['year'],
            "stock": request.form['stock'],
            "rak": request.form['rack']
        }
        update_book(id, updated_book)
        flash('Buku berhasil diupdate!', 'success')
        return redirect(url_for('book_list'))
        
    return render_template('books/edit.html', book=book)

@app.route('/books/delete/<int:id>')
@login_required
def book_delete(id):
    book = get_book_by_id(id)
    if not book:
        flash('Buku tidak ditemukan!', 'error')
    else:
        delete_book(id)
        flash('Buku berhasil dihapus!', 'success')
    return redirect(url_for('book_list'))

# Member

@app.route('/members')
@login_required
def member_list():
    members = load_members()
    return render_template('members/list.html', members=members)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
