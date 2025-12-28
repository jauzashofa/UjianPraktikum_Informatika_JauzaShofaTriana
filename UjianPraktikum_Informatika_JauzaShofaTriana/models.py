import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# DATABASE
# =========================
class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='elektronik',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True  # <<< PENTING, langsung commit ke DB
        )

    def query(self, sql, params=None):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def fetchall(self, sql, params=None):
        cursor = self.query(sql, params)
        return cursor.fetchall()

    def fetchone(self, sql, params=None):
        cursor = self.query(sql, params)
        return cursor.fetchone()

db = Database()


# =========================
# KATEGORI PRODUK
# =========================
class KategoriProduk:
    @staticmethod
    def create(nama_kategori, deskripsi):
        sql = """
        INSERT INTO kategori_produk (nama_kategori, deskripsi)
        VALUES (%s, %s)
        """
        db.query(sql, (nama_kategori, deskripsi))
        return True

    @staticmethod
    def get_all():
        sql = "SELECT * FROM kategori_produk"
        return db.fetchall(sql)

    @staticmethod
    def update(id_kategori, nama_kategori, deskripsi):
        sql = """
        UPDATE kategori_produk
        SET nama_kategori = %s, deskripsi = %s
        WHERE id_kategori = %s
        """
        db.query(sql, (nama_kategori, deskripsi, id_kategori))
        return True

    @staticmethod
    def delete(id_kategori):
        sql = "DELETE FROM kategori_produk WHERE id_kategori = %s"
        db.query(sql, (id_kategori,))
        return True


# =========================
# PRODUK
# =========================
class Produk:
    @staticmethod
    def create(nama_produk, id_kategori, harga, stok):
        # pastikan id_kategori valid
        kategori = KategoriProduk.get_all()
        valid_ids = [k['id_kategori'] for k in kategori]
        if int(id_kategori) not in valid_ids:
            raise ValueError("id_kategori tidak valid!")

        sql = """
        INSERT INTO produk (nama_produk, id_kategori, harga, stok)
        VALUES (%s, %s, %s, %s)
        """
        db.query(sql, (nama_produk, id_kategori, harga, stok))
        return True

    @staticmethod
    def get_all():
        sql = """
        SELECT p.*, k.nama_kategori
        FROM produk p
        JOIN kategori_produk k ON p.id_kategori = k.id_kategori
        """
        return db.fetchall(sql)

    @staticmethod
    def get_by_id(id_produk):
        sql = "SELECT * FROM produk WHERE id_produk = %s"
        return db.fetchone(sql, (id_produk,))

    @staticmethod
    def update(id_produk, nama_produk, id_kategori, harga, stok):
        sql = """
        UPDATE produk
        SET nama_produk = %s,
            id_kategori = %s,
            harga = %s,
            stok = %s
        WHERE id_produk = %s
        """
        db.query(sql, (nama_produk, id_kategori, harga, stok, id_produk))
        return True

    @staticmethod
    def delete(id_produk):
        sql = "DELETE FROM produk WHERE id_produk = %s"
        db.query(sql, (id_produk,))
        return True

    @staticmethod
    def kurangi_stok(id_produk, jumlah):
        sql = "UPDATE produk SET stok = stok - %s WHERE id_produk = %s"
        db.query(sql, (jumlah, id_produk))
        return True


# =========================
# TRANSAKSI
# =========================
class Transaksi:
    @staticmethod
    def create(id_user, id_produk, jumlah, total):
        sql = """
        INSERT INTO transaksi (id_user, id_produk, jumlah, total)
        VALUES (%s, %s, %s, %s)
        """
        db.query(sql, (id_user, id_produk, jumlah, total))
        return True

    @staticmethod
    def get_all():
        sql = """
        SELECT t.*, u.username, p.nama_produk
        FROM transaksi t
        JOIN users u ON t.id_user = u.id_user
        JOIN produk p ON t.id_produk = p.id_produk
        ORDER BY t.id_transaksi DESC
        """
        return db.fetchall(sql)


# =========================
# USER
# =========================
class User:
    @staticmethod
    def create_user(username, password, role):
        hashed = generate_password_hash(password)
        sql = """
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        """
        db.query(sql, (username, hashed, role))
        return True

    @staticmethod
    def check_login(username, password):
        sql = "SELECT * FROM users WHERE username = %s"
        user = db.fetchone(sql, (username,))
        if user and check_password_hash(user['password'], password):
            return user
        return None
