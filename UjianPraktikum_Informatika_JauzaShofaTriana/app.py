from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
from datetime import timedelta
from models import KategoriProduk, Produk, Transaksi, User

app = Flask(__name__)
app.secret_key = "jelectro-secret-key-123"
app.permanent_session_lifetime = timedelta(days=30)

# ===== HELPERS =====
def login_required():
    return 'user_id' in session

def admin_only():
    return session.get("role") == "admin"

@app.before_request
def make_session_permanent():
    session.permanent = True

# ===== ROUTES =====
@app.route('/')
def index():
    kategori = KategoriProduk.get_all()
    produk = Produk.get_all()
    success = session.pop('success', False)
    return render_template('index.html', kategori=kategori, produk=produk, success=success)

# ===== LOGIN / LOGOUT =====
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('shop'))

    message = ""
    last_username = request.cookies.get('last_username','')
    next_page = request.args.get('next') or url_for('index')

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.check_login(username, password)

        if user:
            session['user_id'] = user['id_user']
            session['username'] = user['username']
            session['role'] = user['role']

            # ===== ALERT LOGIN SESUAI ROLE (DITAMBAHKAN) =====
            if user['role'] == 'admin':
                flash(f"Selamat datang, {user['username']}! Anda masuk sebagai admin.", "success")
            else:
                flash(f"Selamat datang, {user['username']}! Anda masuk sebagai user.", "success")

            resp = make_response(redirect(next_page))
            resp.set_cookie("last_username", username, max_age=60*60*24*7)
            return resp
        else:
            message = "Username atau password salah."

    return render_template('login.html', message=message, last_username=last_username, next_page=next_page)

@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie("last_username","", max_age=0)
    return resp

# ===== REGISTER =====
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        User.create_user(request.form.get("username"), request.form.get("password"), "user")
        flash("Akun berhasil dibuat! Silakan login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ===== CONTACT =====
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        flash("Pesan berhasil dikirim!", "success")
        return redirect(url_for('index'))
    return redirect(url_for('index'))

# ===== SHOP =====
@app.route('/shop')
def shop():
    produk = Produk.get_all()

    # ===== AMBIL SESSION ALERT BELI (SUDAH ADA, TIDAK DIUBAH) =====
    beli_error = session.pop('beli_error', None)
    beli_success = session.pop('beli_success', None)

    return render_template(
        'shop.html',
        produk=produk,
        beli_error=beli_error,
        beli_success=beli_success
    )

@app.route('/checkout/<int:id_produk>', methods=['GET','POST'])
def checkout(id_produk):
    if not login_required():
        return redirect(url_for('login'))

    try:
        produk = Produk.get_by_id(id_produk)
        if not produk:
            session['beli_error'] = "Link tidak valid atau produk sudah dihapus."
            return redirect(url_for('shop'))

        if produk['stok'] <= 0:
            session['beli_error'] = f"Stok {produk['nama_produk']} habis!"
            return redirect(url_for('shop'))

        if request.method == 'POST':
            jumlah = int(request.form['jumlah'])

            if jumlah <= 0 or jumlah > produk['stok']:
                session['beli_error'] = "Jumlah beli tidak valid!"
                return redirect(url_for('checkout', id_produk=id_produk))

            total = produk['harga'] * jumlah
            Transaksi.create(session['user_id'], id_produk, jumlah, total)

            # ===== ALERT BELI SUCCESS =====
            session['beli_success'] = (
                f"Anda berhasil membeli {jumlah} "
                f"{produk['nama_produk']} dengan total Rp {total}"
            )

            return redirect(url_for('shop'))

    except Exception as e:
        session['beli_error'] = f"Ada error saat memproses link: {str(e)}"
        return redirect(url_for('shop'))

    return render_template("checkout.html", produk=produk)

# ===== ADMIN =====
@app.route('/produk')
def produk():
    if not login_required() or not admin_only():
        return redirect(url_for('login'))
    data = Produk.get_all()
    return render_template('produk.html', data=data)

@app.route('/produk/create', methods=['GET','POST'])
def produk_create():
    if not admin_only():
        return redirect(url_for('index'))
    kategori = KategoriProduk.get_all()
    if request.method=='POST':
        Produk.create(
            request.form['nama_produk'],
            request.form['id_kategori'],
            request.form['harga'],
            request.form['stok']
        )
        flash('Produk berhasil ditambahkan', 'success')
        return redirect(url_for('produk'))
    return render_template('produk_create.html', kategori=kategori)

@app.route('/produk/update/<int:id_produk>', methods=['GET','POST'])
def produk_update(id_produk):
    if not admin_only():
        return redirect(url_for('login'))
    produk_obj = Produk.get_by_id(id_produk)
    if not produk_obj:
        flash("Produk tidak ditemukan!", "danger")
        return redirect(url_for('produk'))
    kategori = KategoriProduk.get_all()
    if request.method=='POST':
        Produk.update(
            id_produk,
            request.form['nama_produk'],
            request.form['id_kategori'],
            request.form['harga'],
            request.form['stok']
        )
        flash('Produk berhasil diperbarui', 'success')
        return redirect(url_for('produk'))
    return render_template('produk_update.html', produk=produk_obj, kategori=kategori)

@app.route('/produk/delete/<int:id_produk>')
def produk_delete(id_produk):
    if not admin_only():
        return redirect(url_for('login'))
    Produk.delete(id_produk)
    flash('Produk berhasil dihapus', 'danger')
    return redirect(url_for('produk'))

@app.route('/kategori')
def kategori():
    if not login_required() or not admin_only():
        return redirect(url_for('login'))
    data = KategoriProduk.get_all()
    return render_template('kategori.html', data=data)

@app.route('/kategori/create', methods=['GET','POST'])
def kategori_create():
    if not admin_only():
        return redirect(url_for('login'))
    if request.method=='POST':
        KategoriProduk.create(
            request.form['nama_kategori'],
            request.form['deskripsi']
        )
        flash('Kategori berhasil ditambahkan', 'success')
        return redirect(url_for('kategori'))
    return render_template('kategori_create.html')

@app.route('/kategori/update/<int:id_kategori>', methods=['GET','POST'])
def kategori_update(id_kategori):
    if not admin_only():
        return redirect(url_for('login'))
    kategori_obj = next(
        (k for k in KategoriProduk.get_all() if k['id_kategori']==id_kategori),
        None
    )
    if not kategori_obj:
        flash("Kategori tidak ditemukan!", "danger")
        return redirect(url_for('kategori'))
    if request.method=='POST':
        KategoriProduk.update(
            id_kategori,
            request.form['nama_kategori'],
            request.form['deskripsi']
        )
        flash('Kategori berhasil diperbarui', 'success')
        return redirect(url_for('kategori'))
    return render_template('kategori_update.html', kategori=kategori_obj)

@app.route('/kategori/delete/<int:id_kategori>')
def kategori_delete(id_kategori):
    if not admin_only():
        return redirect(url_for('login'))
    KategoriProduk.delete(id_kategori)
    flash('Kategori berhasil dihapus', 'danger')
    return redirect(url_for('kategori'))

@app.route('/transaksi')
def transaksi():
    if not admin_only():
        return redirect(url_for('index'))
    data = Transaksi.get_all()
    return render_template('transaksi.html', data=data)

if __name__=='__main__':
    app.run(debug=True)
