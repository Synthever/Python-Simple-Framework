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

# Public funtion
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
        
def get_member_by_id(member_id):
    members = load_members()
    return next((member for member in members if member['id_member'] == member_id), None)

def update_member(member_id, updated_member):
    members = load_members()
    for i, member in enumerate(members):
        if member['id_member'] == member_id:
            members[i] = updated_member
            break
    with open('./database/member.json', 'w') as f:
        json.dump({'member': members}, f, indent=4, ensure_ascii=False)
        
def delete_member(member_id):
    members = load_members()
    members = [member for member in members if member['id_member'] != member_id]
    with open('./database/member.json', 'w') as f:
        json.dump({'member': members}, f, indent=4, ensure_ascii=False)
        
def current_user():
    return {
        'username': session['username'],
    }

def load_peminjaman():
    with open('./database/peminjaman.json', 'r') as f:
        return json.load(f)['peminjaman']

def save_peminjaman(peminjaman_list):
    with open('./database/peminjaman.json', 'w') as f:
        json.dump({'peminjaman': peminjaman_list}, f, indent=4, ensure_ascii=False)

def calculate_denda(tanggal_kembali):
    from datetime import datetime
    tanggal_kembali = datetime.strptime(tanggal_kembali, '%Y-%m-%d')
    today = datetime.now()
    if today > tanggal_kembali:
        delta = today - tanggal_kembali
        return int(delta.days * 1000)  # Denda 1000 per hari
    return 0

def is_peminjaman_terlambat(tanggal_kembali):
    from datetime import datetime
    tanggal_kembali = datetime.strptime(tanggal_kembali, '%Y-%m-%d')
    today = datetime.now()
    return today > tanggal_kembali

def get_days_late(tanggal_kembali):
    from datetime import datetime
    tanggal_kembali = datetime.strptime(tanggal_kembali, '%Y-%m-%d')
    today = datetime.now()
    if today > tanggal_kembali:
        delta = today - tanggal_kembali
        return delta.days
    return 0

# Routes Login
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
            session['user_id'] = user['id_petugas']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            return render_template('auth/index.html', error='Invalid username or password')
            
    return render_template('auth/index.html')

# Routes Home
@app.route('/home')
@login_required
def home():
    books = load_books()
    members = load_members()
    peminjaman = load_peminjaman()
    
    # Get active loans and late loans
    active_loans = []
    late_loans = []
    
    for p in peminjaman:
        if p['status'] == 'dipinjam':
            p['buku'] = get_book_by_id(p['id_buku'])
            p['member'] = get_member_by_id(p['id_member'])
            p['denda'] = calculate_denda(p['tanggal_kembali'])
            p['is_terlambat'] = is_peminjaman_terlambat(p['tanggal_kembali'])
            p['days_late'] = get_days_late(p['tanggal_kembali'])
            
            active_loans.append(p)
            if p['is_terlambat']:
                late_loans.append(p)
    
    # Sort late loans by days_late descending
    late_loans.sort(key=lambda x: x['days_late'], reverse=True)
    
    # Calculate total denda from all loans (both active and returned)
    total_denda = sum([calculate_denda(p['tanggal_kembali']) for p in peminjaman])
    
    # Format the total denda with thousand separator
    formatted_total_denda = "{:,}".format(total_denda)
    
    # Get recent loans (last 5)
    recent_loans = peminjaman[-5:]
    for loan in recent_loans:
        loan['buku'] = get_book_by_id(loan['id_buku'])
        loan['member'] = get_member_by_id(loan['id_member'])
        loan['denda'] = calculate_denda(loan['tanggal_kembali'])
        if loan['status'] == 'dipinjam':
            loan['is_terlambat'] = is_peminjaman_terlambat(loan['tanggal_kembali'])
    
    # Get books with low stock (less than 3)
    low_stock_books = [book for book in books if int(book['stock']) < 3]
    
    return render_template('home/index.html', user=current_user(),books=books,members=members,active_loans=active_loans,late_loans=late_loans,total_denda=formatted_total_denda,recent_loans=recent_loans,low_stock_books=low_stock_books)

# Books
@app.route('/books')
@login_required
def book_list():
    books = load_books()
    return render_template('books/list.html', books=books, user=current_user())

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
        
    return render_template('books/add.html', user=current_user())

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
        
    return render_template('books/edit.html', book=book, user=current_user())

@app.route('/books/delete/<int:id>')
@login_required
def book_delete(id):
    book = get_book_by_id(id)
    if not book:
        flash('Buku tidak ditemukan!', 'error')
    else:
        delete_book(id)
        flash('Buku berhasil dihapus!', 'success')
    return redirect(url_for('book_list', user=current_user()))

# Member
@app.route('/members')
@login_required
def member_list():
    members = load_members()
    return render_template('members/list.html', members=members, user=current_user())

@app.route('/members/add', methods=['GET', 'POST'])
@login_required
def member_add():
    if request.method == 'POST':
        members = load_members()
        new_member = {
            "id_member": len(members) + 1,
            "nama": request.form['name'],
            "gender": request.form['gender'],
            "telp": request.form['phone'],
            "alamat": request.form['address'],
            "email": request.form['email']
        }
        members.append(new_member)
        
        with open('./database/member.json', 'w') as f:
            json.dump({'member': members}, f, indent=4, ensure_ascii=False)
            
        flash('Member berhasil ditambahkan!', 'success')
        return redirect(url_for('member_list'))
        
    return render_template('members/add.html', user=current_user())

@app.route('/members/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def member_edit(id):
    member = get_member_by_id(id)
    if not member:
        flash('Member tidak ditemukan!', 'error')
        return redirect(url_for('member_list'))
        
    if request.method == 'POST':
        updated_member = {
            "id_member": id,
            "nama": request.form['name'],
            "gender": request.form['gender'],
            "telp": request.form['phone'],
            "alamat": request.form['address'],
            "email": request.form['email']
        }
        update_member(id, updated_member)
        flash('Member berhasil diupdate!', 'success')
        return redirect(url_for('member_list'))
        
    return render_template('members/edit.html', member=member, user=current_user())

@app.route('/members/delete/<int:id>')
@login_required
def member_delete(id):
    member = get_member_by_id(id)
    if not member:
        flash('Member tidak ditemukan!', 'error')
    else:
        delete_member(id)
        flash('Member berhasil dihapus!', 'success')
    return redirect(url_for('member_list', user=current_user()))

# Peminjaman
@app.route('/peminjaman')
@login_required
def peminjaman_list():
    peminjaman = load_peminjaman()
    # Get related data
    for p in peminjaman:
        p['buku'] = get_book_by_id(p['id_buku'])
        p['member'] = get_member_by_id(p['id_member'])
        if p['status'] == 'dipinjam':
            p['denda'] = calculate_denda(p['tanggal_kembali'])
            # Add late status check
            p['is_terlambat'] = is_peminjaman_terlambat(p['tanggal_kembali'])
            
    return render_template('peminjaman/list.html', peminjaman=peminjaman, user=current_user())

@app.route('/peminjaman/add', methods=['GET', 'POST'])
@login_required
def peminjaman_add():
    if request.method == 'POST':
        book_id = int(request.form['id_buku'])
        book = get_book_by_id(book_id)
        
        # Check if book exists and has stock
        if not book:
            flash('Buku tidak ditemukan!', 'error')
            return redirect(url_for('peminjaman_add'))
            
        if int(book['stock']) <= 0:
            flash('Maaf, stock buku habis!', 'error')
            return redirect(url_for('peminjaman_add'))
        
        from datetime import datetime, timedelta
        
        tanggal_pinjam = request.form['tanggal_pinjam']
        # Calculate return date (+7 days)
        pinjam_date = datetime.strptime(tanggal_pinjam, '%Y-%m-%d')
        kembali_date = pinjam_date + timedelta(days=7)
        
        peminjaman_list = load_peminjaman()
        new_peminjaman = {
            "id_peminjaman": len(peminjaman_list) + 1,
            "id_buku": book_id,
            "id_member": int(request.form['id_member']),
            "id_petugas": session['user_id'],
            "tanggal_pinjam": tanggal_pinjam,
            "tanggal_kembali": kembali_date.strftime('%Y-%m-%d'),
            "status": "dipinjam",
            "denda": 0
        }
        
        # Update book stock
        book['stock'] = str(int(book['stock']) - 1)
        update_book(book_id, book)
        
        peminjaman_list.append(new_peminjaman)
        save_peminjaman(peminjaman_list)
        
        flash('Peminjaman berhasil ditambahkan!', 'success')
        return redirect(url_for('peminjaman_list'))
    
    books = load_books()
    members = load_members()
    return render_template('peminjaman/add.html', books=books, members=members, user=current_user())

@app.route('/peminjaman/return/<int:id>')
@login_required
def peminjaman_return(id):
    peminjaman_list = load_peminjaman()
    for p in peminjaman_list:
        if p['id_peminjaman'] == id:
            p['status'] = 'dikembalikan'
            p['denda'] = calculate_denda(p['tanggal_kembali'])
            
            # Restore book stock
            book = get_book_by_id(p['id_buku'])
            if book:
                book['stock'] = str(int(book['stock']) + 1)
                update_book(p['id_buku'], book)
            break
            
    save_peminjaman(peminjaman_list)
    flash('Buku berhasil dikembalikan!', 'success')
    return redirect(url_for('peminjaman_list'))

@app.route('/peminjaman/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def peminjaman_edit(id):
    peminjaman_list = load_peminjaman()
    peminjaman = next((p for p in peminjaman_list if p['id_peminjaman'] == id), None)
    
    if not peminjaman:
        flash('Data peminjaman tidak ditemukan!', 'error')
        return redirect(url_for('peminjaman_list'))
        
    if request.method == 'POST':
        for p in peminjaman_list:
            if p['id_peminjaman'] == id:
                p['id_buku'] = int(request.form['id_buku'])
                p['id_member'] = int(request.form['id_member'])
                p['tanggal_pinjam'] = request.form['tanggal_pinjam']
                p['tanggal_kembali'] = request.form['tanggal_kembali']
                p['status'] = request.form['status']
                # Recalculate denda if status is "dikembalikan"
                if p['status'] == 'dikembalikan':
                    p['denda'] = calculate_denda(p['tanggal_kembali'])
                break
                
        save_peminjaman(peminjaman_list)
        flash('Data peminjaman berhasil diupdate!', 'success')
        return redirect(url_for('peminjaman_list'))
    
    books = load_books()
    members = load_members()
    return render_template('peminjaman/edit.html', peminjaman=peminjaman, books=books, members=members, user=current_user())

# API
@app.route('/api/search/books')
@login_required
def search_books():
    query = request.args.get('q', '').lower()
    books = load_books()
    results = [b for b in books if query in b['judul'].lower()]
    return json.dumps(results)

@app.route('/api/search/members')
@login_required
def search_members():
    query = request.args.get('q', '').lower()
    members = load_members()
    results = [m for m in members if query in m['nama'].lower()]
    return json.dumps(results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

    
