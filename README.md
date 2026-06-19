# KlinikConnect
**Sistem Informasi Manajemen Fasilitas Kesehatan Tingkat Pertama (Klinik)**

KlinikConnect adalah aplikasi berbasis web dengan arsitektur REST API murni yang dirancang untuk mendigitalisasi operasional administrasi klinik.

## Studi Kasus & Solusi
Banyak klinik berskala kecil hingga menengah masih sangat bergantung pada pencatatan berbasis kertas, seperti buku besar manual dan tumpukan map rekam medis. Ketergantungan pada dokumen fisik ini memicu masalah operasional yang krusial:
1. **Limbah & Inefisiensi Ruang:** Penumpukan arsip memakan ruang penyimpanan fisik yang besar, boros biaya kertas, dan menciptakan beban pengelolaan dokumen dari waktu ke waktu.
2. **Risiko Kehilangan & Kerusakan:** Data riwayat medis pasien serta dokumen kredensial penting seperti Surat Izin Praktik (SIP) tenaga medis sangat rentan terselip, rusak, atau hilang.
3. **Pelayanan Lambat:** Pencarian data secara manual dari tumpukan kertas membuat antrean pasien tidak terpetakan dengan baik dan menghambat respons pelayanan kesehatan.

**KlinikConnect** dikembangkan untuk memberikan solusi digitalisasi *paperless* (tanpa kertas) yang terpusat. Aplikasi ini memetakan relasi antara entitas **Dokter**, **Pasien**, dan **Jadwal Praktik** menjadi sebuah sistem **Reservasi** yang terstruktur. Transisi menuju ekosistem *paperless* ini tidak hanya memastikan transparansi jadwal dan keamanan berkas (melalui sistem unggah *file* lokal), tetapi juga mendorong terciptanya fasilitas kesehatan yang jauh lebih efisien, hemat ruang, dan ramah lingkungan.

## Teknologi yang Digunakan
Sistem ini menonjolkan pemahaman fundamental arsitektur perangkat lunak dengan tidak menggunakan framework *backend* raksasa:
* **Backend:** Pure Python 3 (`http.server`) & modul `cgi` untuk *multipart/form-data*.
* **Database:** MySQL Relational Database.
* **Frontend:** HTML5, Vanilla JavaScript (Fetch API), dan Bootstrap 5.

## Fitur Unggulan
Aplikasi ini sudah memenuhi spesifikasi **CRUD (Create, Read, Update, Delete) Penuh** lintas tabel, meliputi:
1. **Manajemen Tenaga Medis:** Registrasi, edit, dan hapus data dokter beserta **Upload Foto Profil**.
2. **Registrasi Pasien Terpadu:** Pendataan pasien baru beserta **Upload Foto Identitas/KTP**.
3. **Reservasi Cerdas:** Pembuatan tiket kunjungan dengan relasi otomatis antara pasien yang terdaftar dan jadwal praktik dokter yang tersedia.
4. **Validasi Status:** Pengubahan status reservasi (Menunggu / Selesai / Batal) secara *real-time*.

## Struktur Database (5 Tabel Relasional)
Menggunakan arsitektur RDBMS dengan *Primary Key* dan *Foreign Key* yang ketat:
1. `admin`
2. `pasien`
3. `dokter`
4. `jadwal_praktik`
5. `reservasi`
6. `rekam_medis`

## Petunjuk Instalasi & Operasional 

**1. Persiapan Database (MySQL) menggunakan XAMPP**
* Pastikan Apache dan MySQL berjalan di XAMPP, kemudian pada menu MySQL  tekan menu admin.
* Tampilan phpMyAdmin akan muncul (`http://localhost/phpmyadmin`).
* Buat database baru bernama `klinikconnect`.
* Jalankan (eksekusi) *script* SQL untuk membangun struktur tabel. Berikut script SQL-nya:
-- ==========================================================
-- SCRIPT DATABASE KLINIKCONNECT
-- ==========================================================

-- ==========================================================
-- 1. TABEL ADMIN (UNTUK FITUR LOGIN/AUTENTIKASI)
-- ==========================================================
CREATE TABLE admin (
    id INT(11) AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Menyuntikkan 1 akun pengelola secara default agar bisa langsung login
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- ==========================================================
-- 2. TABEL DOKTER
-- ==========================================================
CREATE TABLE dokter (
    id_dokter INT(11) AUTO_INCREMENT PRIMARY KEY,
    nama_dokter VARCHAR(100) NOT NULL,
    spesialisasi VARCHAR(50) NOT NULL,
    no_izin_praktik VARCHAR(50) NOT NULL UNIQUE,
    foto_profil VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 3. TABEL PASIEN
-- ==========================================================
CREATE TABLE pasien (
    id_pasien INT(11) AUTO_INCREMENT PRIMARY KEY,
    nik VARCHAR(16) NOT NULL UNIQUE,
    nama_lengkap VARCHAR(100) NOT NULL,
    tanggal_lahir DATE NOT NULL,
    no_telepon VARCHAR(15) NOT NULL,
    alamat TEXT DEFAULT NULL,
    foto_pasien VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 4. TABEL JADWAL PRAKTIK
-- ==========================================================
CREATE TABLE jadwal_praktik (
    id_jadwal INT(11) AUTO_INCREMENT PRIMARY KEY,
    id_dokter INT(11) NOT NULL,
    hari_praktik VARCHAR(10) NOT NULL,
    jam_mulai TIME NOT NULL,
    jam_selesai TIME NOT NULL,
    kuota_pasien INT(11) NOT NULL,
    FOREIGN KEY (id_dokter) REFERENCES dokter(id_dokter) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 5. TABEL RESERVASI
-- ==========================================================
CREATE TABLE reservasi (
    id_reservasi INT(11) AUTO_INCREMENT PRIMARY KEY,
    id_pasien INT(11) NOT NULL,
    id_jadwal INT(11) NOT NULL,
    tanggal_kunjungan DATE NOT NULL,
    keluhan_awal TEXT NOT NULL,
    status_reservasi ENUM('Menunggu', 'Selesai', 'Batal') DEFAULT 'Menunggu',
    FOREIGN KEY (id_pasien) REFERENCES pasien(id_pasien) ON DELETE CASCADE,
    FOREIGN KEY (id_jadwal) REFERENCES jadwal_praktik(id_jadwal) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 6. TABEL REKAM MEDIS
-- ==========================================================
CREATE TABLE rekam_medis (
    id_rekam_medis INT(11) AUTO_INCREMENT PRIMARY KEY,
    id_reservasi INT(11) NOT NULL UNIQUE, 
    tanggal_pemeriksaan DATETIME DEFAULT CURRENT_TIMESTAMP,
    diagnosis TEXT NOT NULL,
    resep_obat TEXT NOT NULL,
    file_lampiran_lab VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (id_reservasi) REFERENCES reservasi(id_reservasi) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

**2. Persiapan Environment Python**
* Buka Terminal / Command Prompt dan arahkan ke dalam direktori proyek ini.
* Instal konektor MySQL agar Python bisa terhubung ke database:
  pip install mysql-connector-python
* jika menggunakan Python versi 3.13 ke atas, install juga modul pembantu untuk proses file upload:
  pip install legacy-cgi

**3. Menjalankan Server Backend dan Mengakses Frontend**
* Pastikan XAMPP tetap dalam keadaan running.
* Masuk ke dalam vscode, lalu buat folder yang nanti berisi file backend (db_config.py, server.py) dan frontend (index.html) 
* Masuk ke dalam file **server.py**, kemudian buka terminal dan jalankan perintah berikut untuk menghidupkan server API python:
  python server.py
* Biarkan terminal tetap terbuka (running). Terminal akan menampilkan pesan bahwa server berhasil berjalan.
* Selanjutnya buka File Explorer, cari file **index.html**, lalu jalankan file tersebut dengan di klik ganda. Web browser (chrome/Microsoft Edge) akan terbuka dan menampilkan UI Dashboard website.
* Melakukan login dengan input username dan password yang sesuai. 

**4. Pengujian Sistem Website**
* Proses input dan menyimpan data (Create):
  1. Menginput Data Dokter pada form dan mengisi seluruh form, pilih dan unggah foto profil , lalu klik Simpan. Berikut contoh data dokternya:
   * Nama Lengkap: Budi Santoso
   * Spesialisasi: Dokter Umum
   * No. Izin Praktik: IDI-10029384
   * Upload foto: unggah gambar apa saja dari perangkat saat ini
  2. Menginput Data Pasien, mengisi seluruh form, unggah foto, lalu klik simpan. Berikut data pasien yang bisa dijadikan percobaan:
   * NIK: 3171234567890001
   * Nama Lengkap: Ahmad Rizal
   * Tgl Lahir: (bisa diinput secara manual atau bisa menggunakan kalender)
   * No. Telp: 082312648422
   * Alamat: Jl. Kenangan No. 12, Jakarta
   * Upload foto: (unggah gambar apa saja)
  3. Menginput Jadwal Praktik melalui phpMyAdmin (dari backend), kemudian masuk kedalam database **klinikconnect**, masuk ke tab SQL, lalu jalankan kueri menggunakan fungsi INSERT INTO:
    INSERT INTO jadwal_praktik (id_dokter, hari_praktik, jam_mulai, jam_selesai, kuota_pasien) VALUES (1, 'Senin', '08:00:00', '12:00:00', 20);
  Setelah data dimasukkan ke dalam tabel, nantinya form reservasi akan memunculkan nama dokter di UI dashboard.
  4. Setelah ada entitas dokter dan pasien, kita bisa lanjut menggunakan form Reservasi. Nama pasien dan jadwal praktik akan otomatis ditarik dari database ke dalam menu pilihan (dropdown).
  5. Proses Edit Data, dengan klik dengan ikon pensil (edit) pada baris data di tabel mana pun. Form input akan otomatis berubah status menjadi mode edit, lakukan perubahan data yang diinginkan kemudian klik tombol **Update**.
  6. Proses Hapus Data, klik tombol dengan ikon keranjang sampah (hapus) pada baris tabel, akan muncul pop-up konfirmasi. jika disetujui, data akan dihapus dari tabel secara permanen. 