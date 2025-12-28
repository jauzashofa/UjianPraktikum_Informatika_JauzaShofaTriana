from flask import Flask, render_template, request, redirect, url_for, session, make_response
from models import KategoriProduk, Produk, Transaksi, User

app = Flask(__name__)
app.secret_key = "jelectro-secret-key-123"


def login_required():
    return 'user_id' in session


def admin_only():
    return session.get("role") == "admin"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # jika sudah login, langsung ke shop
        return redirect(url_for('shop'))

    message = ""
    last_username = request.cookies.get('last_username', '')
    next_page = request.args.get('next') or url_for('index')  # default ke index

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.check_login(username, password)

        if user:
            session['user_id'] = user['id_user']
            session['username'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'admin':
                session['login_info'] = 'admin'
                next_page = url_for('index')  # admin tetap ke index/admin panel
            else:
                session['login_info'] = 'user'
                # tetap pakai next_page, default ke shop

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
    resp.set_cookie("last_username", "", max_age=0)
    return resp


@app.route('/')
def index():
    kategori = KategoriProduk.get_all()
    produk = Produk.get_all()

    # ambil pesan sukses sekali saja
    success = session.pop('success', False)

    return render_template(
        'index.html',
        kategori=kategori,
        produk=produk,
        success=success
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        User.create_user(
            request.form.get("username"),
            request.form.get("password"),
            "user"
        )
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/contact', methods=['POST'])
def contact():
    nama = request.form.get('nama')
    email = request.form.get('email')
    pesan = request.form.get('pesan')

    # (opsional) simpan ke database / kirim email

    # set flag sukses (sementara)
    session['success'] = True

    return redirect(url_for('index'))


@app.route('/produk')
def produk():
    if not login_required() or not admin_only():
        return redirect(url_for('login'))

    data = Produk.get_all()
    return render_template('produk.html', data=data)


@app.route('/produk/create', methods=['GET', 'POST'])
def produk_create():
    if not admin_only():
        return redirect(url_for('index'))

    kategori = KategoriProduk.get_all()

    if request.method == 'POST':
        nama_produk = request.form.get('nama_produk')
        id_kategori = request.form.get('id_kategori')
        harga = request.form.get('harga')
        stok = request.form.get('stok')

        Produk.create(nama_produk, id_kategori, harga, stok)

        session['alert'] = 'Produk berhasil ditambahkan'
        session['alert_type'] = 'success'
        return redirect(url_for('produk'))

    return render_template('produk_create.html', kategori=kategori)



@app.route('/produk/update/<int:id_produk>', methods=['GET', 'POST'])
def produk_update(id_produk):
    if not admin_only():
        return redirect(url_for('login'))

    produk = Produk.get_by_id(id_produk)
    kategori = KategoriProduk.get_all()

    if request.method == 'POST':
        Produk.update(
            id_produk,
            request.form['nama_produk'],
            request.form['id_kategori'],
            request.form['harga'],
            request.form['stok']
        )
        session['alert'] = 'Produk berhasil diperbarui'
        session['alert_type'] = 'success'
        return redirect(url_for('produk'))

    return render_template('produk_update.html', produk=produk, kategori=kategori)


@app.route('/produk/delete/<int:id_produk>')
def produk_delete(id_produk):
    if not admin_only():
        return redirect(url_for('login'))

    Produk.delete(id_produk)
    session['alert'] = 'Produk berhasil dihapus'
    session['alert_type'] = 'danger'
    return redirect(url_for('produk'))


@app.route('/kategori')
def kategori():
    if not login_required() or not admin_only():
        return redirect(url_for('login'))

    data = KategoriProduk.get_all()
    return render_template('kategori.html', data=data)


@app.route('/kategori/create', methods=['GET', 'POST'])
def kategori_create():
    if not login_required() or not admin_only():
        return redirect(url_for('login'))

    if request.method == 'POST':
        KategoriProduk.create(
            request.form['nama_kategori'],
            request.form['deskripsi']
        )
        session['alert'] = 'Kategori berhasil ditambahkan'
        session['alert_type'] = 'success'
        return redirect(url_for('kategori'))
    return render_template('kategori_create.html')


@app.route('/kategori/update/<int:id_kategori>', methods=['GET', 'POST'])
def kategori_update(id_kategori):
    if not login_required() or not admin_only():
        return redirect(url_for('login'))

    kategori = next(
        (k for k in KategoriProduk.get_all() if k['id_kategori'] == id_kategori),
        None
    )

    if request.method == 'POST':
        KategoriProduk.update(
            id_kategori,
            request.form['nama_kategori'],
            request.form['deskripsi']
        )
        session['alert'] = 'Kategori berhasil diperbarui'
        session['alert_type'] = 'success'
        return redirect(url_for('kategori'))

    return render_template('kategori_update.html', kategori=kategori)


@app.route('/kategori/delete/<int:id_kategori>')
def kategori_delete(id_kategori):
    if not login_required() or not admin_only():
        return redirect(url_for('login'))

    KategoriProduk.delete(id_kategori)
    session['alert'] = 'Kategori berhasil dihapus'
    session['alert_type'] = 'danger'
    return redirect(url_for('kategori'))



@app.route('/shop')
def shop():
    data = Produk.get_all()
    return render_template('shop.html', produk=data)


@app.route('/checkout/<int:id_produk>', methods=['GET', 'POST'])
def checkout(id_produk):
    if not login_required():
        return redirect(url_for('login'))

    produk = Produk.get_by_id(id_produk)

    if not produk or produk['stok'] <= 0:
        session['beli_error'] = "Produk tidak tersedia atau stok habis!"
        session.modified = True
        return redirect(url_for('shop'))

    if request.method == 'POST':
        try:
            jumlah = int(request.form['jumlah'])
        except ValueError:
            session['beli_error'] = "Jumlah beli tidak valid!"
            session.modified = True
            return redirect(url_for('checkout', id_produk=id_produk))

        if jumlah <= 0:
            session['beli_error'] = "Jumlah beli minimal 1!"
            session.modified = True
            return redirect(url_for('checkout', id_produk=id_produk))

        if jumlah > produk['stok']:
            session['beli_error'] = "Stok tidak cukup!"
            session.modified = True
            return redirect(url_for('checkout', id_produk=id_produk))

        total = produk['harga'] * jumlah

        # Simpan transaksi
        Transaksi.create(
            session['user_id'],
            id_produk,
            jumlah,
            total
        )
        # Kurangi stok produk
        Produk.kurangi_stok(id_produk, jumlah)
        # Set pesan sukses
        session['beli_success'] = f"✅ Anda berhasil membeli {jumlah} {produk['nama_produk']} dengan total Rp {total}"
        session.modified = True

        return redirect(url_for('shop'))

    return render_template("checkout.html", produk=produk)


@app.route('/transaksi')
def transaksi():
    if not admin_only():
        return redirect(url_for('index'))

    data = Transaksi.get_all()
    return render_template('transaksi.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
