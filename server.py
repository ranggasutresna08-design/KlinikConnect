from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import cgi
import os
import urllib.parse
from db_config import get_db_connection

HOST_NAME = 'localhost'
PORT_NUMBER = 8000
UPLOAD_DIR = 'uploads'

class KlinikAPIHandler(BaseHTTPRequestHandler):

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, ngrok-skip-browser-warning')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    # ==========================================
    # MIDDLEWARE: PENJAGA AUTENTIKASI & ROLE
    # ==========================================
    def cek_autentikasi(self):
        auth_header = self.headers.get('Authorization')
        if auth_header == 'Bearer token-admin-123':
            return 'admin'
        elif auth_header == 'Bearer token-petugas-123':
            return 'petugas'
        
        self.send_response(401)
        self.send_header('Content-type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"pesan": "Akses Ditolak! Sesi tidak valid."}).encode('utf-8'))
        return None

    # ==========================================
    # 1. READ (GET)
    # ==========================================
    def do_GET(self):
        role = self.cek_autentikasi()
        if not role: return
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            if self.path == '/api/dokter':
                cursor.execute("SELECT * FROM dokter")
                data = cursor.fetchall()
            elif self.path == '/api/pasien':
                cursor.execute("SELECT * FROM pasien")
                data = cursor.fetchall()
            elif self.path == '/api/jadwal':
                cursor.execute("""
                    SELECT j.id_jadwal, d.nama_dokter, j.hari_praktik, j.jam_mulai, j.jam_selesai, j.kuota_pasien 
                    FROM jadwal_praktik j JOIN dokter d ON j.id_dokter = d.id_dokter
                """)
                data = cursor.fetchall()
            elif self.path == '/api/reservasi':
                cursor.execute("""
                    SELECT r.id_reservasi, r.id_pasien, r.id_jadwal, p.nama_lengkap AS nama_pasien, 
                           d.nama_dokter, j.hari_praktik, r.tanggal_kunjungan, r.keluhan_awal, r.status_reservasi
                    FROM reservasi r
                    JOIN pasien p ON r.id_pasien = p.id_pasien
                    JOIN jadwal_praktik j ON r.id_jadwal = j.id_jadwal
                    JOIN dokter d ON j.id_dokter = d.id_dokter
                """)
                data = cursor.fetchall()
            else:
                self.send_error(404)
                return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
        finally:
            db.close()

    # ==========================================
    # 2. CREATE (POST) & LOGIN
    # ==========================================
    def do_POST(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
        
        # --- ENDPOINT LOGIN ---
        if self.path == '/api/login':
            username = form.getvalue("username")
            password = form.getvalue("password")
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
            role = "admin"
            token = "token-admin-123"
            
            if not user:
                cursor.execute("SELECT * FROM petugas WHERE username=%s AND password=%s", (username, password))
                user = cursor.fetchone()
                role = "petugas"
                token = "token-petugas-123"
                
            db.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            
            if user:
                self.wfile.write(json.dumps({"sukses": True, "token": token, "role": role}).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"sukses": False, "pesan": "Username atau Password salah!"}).encode('utf-8'))
            return

        # --- ENDPOINT CREATE DATA ---
        role = self.cek_autentikasi()
        if not role: return 
        
        # Aturan: Petugas tidak boleh menambah dokter
        if role == 'petugas' and self.path == '/api/dokter':
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Hak akses ditolak!"}).encode('utf-8'))
            return
            
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            if self.path == '/api/dokter':
                foto_path = ""
                if "foto_profil" in form and form["foto_profil"].filename:
                    filepath = os.path.join(UPLOAD_DIR, os.path.basename(form["foto_profil"].filename))
                    with open(filepath, 'wb') as f: f.write(form["foto_profil"].file.read())
                    foto_path = filepath
                cursor.execute("INSERT INTO dokter (nama_dokter, spesialisasi, no_izin_praktik, foto_profil) VALUES (%s, %s, %s, %s)", 
                               (form.getvalue("nama_dokter"), form.getvalue("spesialisasi"), form.getvalue("no_izin_praktik"), foto_path))
                db.commit()
                
            elif self.path == '/api/pasien':
                foto_path = ""
                if "foto_pasien" in form and form["foto_pasien"].filename:
                    filepath = os.path.join(UPLOAD_DIR, os.path.basename(form["foto_pasien"].filename))
                    with open(filepath, 'wb') as f: f.write(form["foto_pasien"].file.read())
                    foto_path = filepath
                cursor.execute("INSERT INTO pasien (nik, nama_lengkap, tanggal_lahir, no_telepon, alamat, foto_pasien) VALUES (%s, %s, %s, %s, %s, %s)",
                               (form.getvalue("nik"), form.getvalue("nama_lengkap"), form.getvalue("tanggal_lahir"), form.getvalue("no_telepon"), form.getvalue("alamat"), foto_path))
                db.commit()
                
            elif self.path == '/api/reservasi':
                cursor.execute("INSERT INTO reservasi (id_pasien, id_jadwal, tanggal_kunjungan, keluhan_awal) VALUES (%s, %s, %s, %s)",
                               (form.getvalue("id_pasien"), form.getvalue("id_jadwal"), form.getvalue("tanggal_kunjungan"), form.getvalue("keluhan_awal")))
                db.commit()

            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Sukses!"}).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
        finally:
            db.close()

    # ==========================================
    # 3. UPDATE (PUT)
    # ==========================================
    def do_PUT(self):
        role = self.cek_autentikasi()
        if not role: return

        # Aturan: Petugas tidak boleh mengedit dokter
        if role == 'petugas' and '/api/dokter' in self.path:
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Hak akses ditolak!"}).encode('utf-8'))
            return

        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        record_id = query['id'][0]
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
        db = get_db_connection()
        cursor = db.cursor()

        try:
            if parsed_path.path == '/api/dokter':
                if "foto_profil" in form and form["foto_profil"].filename:
                    filepath = os.path.join(UPLOAD_DIR, os.path.basename(form["foto_profil"].filename))
                    with open(filepath, 'wb') as f: f.write(form["foto_profil"].file.read())
                    cursor.execute("UPDATE dokter SET nama_dokter=%s, spesialisasi=%s, no_izin_praktik=%s, foto_profil=%s WHERE id_dokter=%s",
                                   (form.getvalue("nama_dokter"), form.getvalue("spesialisasi"), form.getvalue("no_izin_praktik"), filepath, record_id))
                else:
                    cursor.execute("UPDATE dokter SET nama_dokter=%s, spesialisasi=%s, no_izin_praktik=%s WHERE id_dokter=%s",
                                   (form.getvalue("nama_dokter"), form.getvalue("spesialisasi"), form.getvalue("no_izin_praktik"), record_id))
                
            elif parsed_path.path == '/api/pasien':
                if "foto_pasien" in form and form["foto_pasien"].filename:
                    filepath = os.path.join(UPLOAD_DIR, os.path.basename(form["foto_pasien"].filename))
                    with open(filepath, 'wb') as f: f.write(form["foto_pasien"].file.read())
                    cursor.execute("UPDATE pasien SET nik=%s, nama_lengkap=%s, tanggal_lahir=%s, no_telepon=%s, alamat=%s, foto_pasien=%s WHERE id_pasien=%s",
                                   (form.getvalue("nik"), form.getvalue("nama_lengkap"), form.getvalue("tanggal_lahir"), form.getvalue("no_telepon"), form.getvalue("alamat"), filepath, record_id))
                else:
                    cursor.execute("UPDATE pasien SET nik=%s, nama_lengkap=%s, tanggal_lahir=%s, no_telepon=%s, alamat=%s WHERE id_pasien=%s",
                                   (form.getvalue("nik"), form.getvalue("nama_lengkap"), form.getvalue("tanggal_lahir"), form.getvalue("no_telepon"), form.getvalue("alamat"), record_id))
                                   
            elif parsed_path.path == '/api/reservasi':
                cursor.execute("UPDATE reservasi SET id_pasien=%s, id_jadwal=%s, tanggal_kunjungan=%s, keluhan_awal=%s, status_reservasi=%s WHERE id_reservasi=%s",
                               (form.getvalue("id_pasien"), form.getvalue("id_jadwal"), form.getvalue("tanggal_kunjungan"), form.getvalue("keluhan_awal"), form.getvalue("status_reservasi"), record_id))
            
            db.commit()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Update Sukses!"}).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
        finally:
            db.close()

    # ==========================================
    # 4. DELETE
    # ==========================================
    def do_DELETE(self):
        role = self.cek_autentikasi()
        if not role: return

        # Aturan: Petugas sama sekali tidak boleh menghapus data
        if role == 'petugas':
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Hak akses ditolak! Petugas tidak boleh menghapus data."}).encode('utf-8'))
            return

        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        record_id = query['id'][0]
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            if parsed_path.path == '/api/dokter':
                cursor.execute("DELETE FROM dokter WHERE id_dokter = %s", (record_id,))
            elif parsed_path.path == '/api/pasien':
                cursor.execute("DELETE FROM pasien WHERE id_pasien = %s", (record_id,))
            elif parsed_path.path == '/api/reservasi':
                cursor.execute("DELETE FROM reservasi WHERE id_reservasi = %s", (record_id,))
                
            db.commit()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"pesan": "Hapus Sukses!"}).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
        finally:
            db.close()

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), KlinikAPIHandler)
    print(f"Server Backend Berjalan di http://{HOST_NAME}:{PORT_NUMBER}")
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    httpd.server_close()