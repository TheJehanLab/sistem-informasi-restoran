from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # ganti sesuai password mysql kamu
app.config['MYSQL_DB'] = 'restoran_db'

mysql = MySQL(app)

# Route login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Pastikan password ada di index 2, sesuaikan dengan urutan kolom di tabel
            if check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
                flash('Login berhasil!', 'success')
                if user[4] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('pelanggan_dashboard'))
            else:
                flash('Password salah!', 'danger')
        else:
            flash('Username tidak ditemukan!', 'danger')
    return render_template('auth/login.html')

# Route register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        cur = mysql.connection.cursor()
        # cek username sudah ada atau belum
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username sudah terdaftar!', 'danger')
            cur.close()
            return redirect(url_for('register'))

        cur.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                    (username, password, email, role))
        mysql.connection.commit()
        cur.close()

        flash('Registrasi berhasil, silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

# Dashboard admin
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin/dashboard.html')
    else:
        flash('Anda harus login sebagai admin!', 'danger')
        return redirect(url_for('login'))

# Dashboard pelanggan
@app.route('/pelanggan/dashboard')
def pelanggan_dashboard():
    if 'role' in session and session['role'] == 'pelanggan':
        return render_template('pelanggan/dashboard.html')
    else:
        flash('Anda harus login sebagai pelanggan!', 'danger')
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Berhasil logout.', 'success')
    return redirect(url_for('login'))

# Pastikan sudah import
from flask import abort

# Fungsi cek admin login
def admin_required():
    if 'role' not in session or session['role'] != 'admin':
        flash('Anda harus login sebagai admin!', 'danger')
        return False
    return True

# Daftar menu makanan/minuman
@app.route('/admin/menu')
def menu_list():
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu ORDER BY kategori, nama")
    menus = cur.fetchall()
    cur.close()
    return render_template('admin/menu_list.html', menus=menus)

# Tambah menu
@app.route('/admin/menu/tambah', methods=['GET', 'POST'])
def menu_tambah():
    if not admin_required():
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama']
        kategori = request.form['kategori']
        harga = request.form['harga']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO menu (nama, kategori, harga) VALUES (%s, %s, %s)",
                    (nama, kategori, harga))
        mysql.connection.commit()
        cur.close()

        flash('Menu berhasil ditambahkan!', 'success')
        return redirect(url_for('menu_list'))

    return render_template('admin/menu_tambah.html')

# Edit menu
@app.route('/admin/menu/edit/<int:id>', methods=['GET', 'POST'])
def menu_edit(id):
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu WHERE id=%s", (id,))
    menu = cur.fetchone()

    if not menu:
        cur.close()
        flash('Menu tidak ditemukan!', 'danger')
        return redirect(url_for('menu_list'))

    if request.method == 'POST':
        nama = request.form['nama']
        kategori = request.form['kategori']
        harga = request.form['harga']

        cur.execute("UPDATE menu SET nama=%s, kategori=%s, harga=%s WHERE id=%s",
                    (nama, kategori, harga, id))
        mysql.connection.commit()
        cur.close()

        flash('Menu berhasil diupdate!', 'success')
        return redirect(url_for('menu_list'))

    cur.close()
    return render_template('admin/menu_edit.html', menu=menu)

# Hapus menu
@app.route('/admin/menu/hapus/<int:id>', methods=['POST'])
def menu_hapus(id):
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM menu WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Menu berhasil dihapus!', 'success')
    return redirect(url_for('menu_list'))

# Daftar pelanggan (role = 'pelanggan' saja)
@app.route('/admin/pelanggan')
def pelanggan_list():
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email FROM users WHERE role = 'pelanggan' ORDER BY id")
    pelanggan = cur.fetchall()
    cur.close()
    return render_template('admin/pelanggan_list.html', pelanggan=pelanggan)


# Tambah pelanggan baru
@app.route('/admin/pelanggan/tambah', methods=['GET', 'POST'])
def pelanggan_tambah():
    if not admin_required():
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        role = 'pelanggan'  # otomatis role pelanggan

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                    (username, password, email, role))
        mysql.connection.commit()
        cur.close()
        flash('Pelanggan berhasil ditambahkan!', 'success')
        return redirect(url_for('pelanggan_list'))

    return render_template('admin/pelanggan_tambah.html')


# Edit pelanggan
@app.route('/admin/pelanggan/edit/<int:id>', methods=['GET', 'POST'])
def pelanggan_edit(id):
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email FROM users WHERE id=%s AND role='pelanggan'", (id,))
    pelanggan = cur.fetchone()

    if not pelanggan:
        cur.close()
        flash('Pelanggan tidak ditemukan!', 'danger')
        return redirect(url_for('pelanggan_list'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        cur.execute("UPDATE users SET username=%s, email=%s WHERE id=%s AND role='pelanggan'",
                    (username, email, id))
        mysql.connection.commit()
        cur.close()
        flash('Pelanggan berhasil diupdate!', 'success')
        return redirect(url_for('pelanggan_list'))

    cur.close()
    return render_template('admin/pelanggan_edit.html', pelanggan=pelanggan)


# Hapus pelanggan
@app.route('/admin/pelanggan/hapus/<int:id>', methods=['POST'])
def pelanggan_hapus(id):
    if not admin_required():
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s AND role='pelanggan'", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Pelanggan berhasil dihapus!', 'success')
    return redirect(url_for('pelanggan_list'))


if __name__ == '__main__':
    app.run(debug=True)
