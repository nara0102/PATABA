# 🏛️ PATABA - Portal Aset Tanah Pemerintah Daerah

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap_5-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=leaflet&logoColor=white)

**PATABA** adalah platform tata kelola aset dan barang milik daerah yang dikembangkan khusus untuk Badan Pengelola Keuangan dan Aset Daerah (BPKAD) Kota Palu. Sistem ini mendigitalisasi proses inventarisasi, sertifikasi, dan validasi aset tanah secara *real-time* dan transparan.

---

## 🎯 Tujuan & Latar Belakang
Sistem ini dibangun untuk menyelesaikan tantangan dalam manajemen aset daerah, dengan tujuan:
1. **Transparansi & Akuntabilitas:** Mencatat setiap perubahan, usulan, dan validasi aset dengan *Audit Log* yang ketat.
2. **Digitalisasi Arsip (Paperless):** Mengelola dokumen sertifikat (Asli/Fotokopi) dan foto profil pengguna menggunakan penyimpanan *Cloud* (Supabase S3).
3. **SOP Terstruktur (Ping-Pong System):** Memastikan usulan aset dari Operator OPD harus melewati proses verifikasi (Valid/Perlu Review/Sengketa) oleh Admin BPKAD sebelum masuk ke Master Data.
4. **Pemetaan Spasial (GIS):** Memvisualisasikan titik koordinat lokasi aset tanah milik Pemerintah Kota Palu kepada publik.

---

## 🏗️ Arsitektur Sistem (Domain-Driven Design)
Proyek ini memisahkan logika bisnis ke dalam tiga aplikasi utama (*Separation of Concerns*) agar kode tetap rapi dan *scalable*:

1. 📂 **`aset_tanah` (Core Domain):** Menangani logika utama inventarisasi aset, sertifikasi tanah, relasi dengan Master OPD, dan pemetaan kelurahan/kecamatan.
2. 📂 **`manajemen_pengguna` (HR & Security Domain):** Mengelola autentikasi, level akses (*Role-Based Access Control*), profil pengguna, pengaturan akun, dan perekaman jejak (*Audit Log*).
3. 📂 **`portal_publik` (Public & Media Domain):** Menangani portal informasi untuk warga, GIS publik, kontak pesan, serta manajemen publikasi instansi (Berita, Pengumuman, Galeri).

---

## 🚀 Fitur Utama
1. **Role-Based Access Control (RBAC):** Pemisahan hak akses antara Superadmin (HR System), Admin BPKAD (Verifikator Utama), dan Operator OPD (Pengusul Aset).
2. **Alur Kerja Usulan Aset:** Sistem tiket "Ping-Pong" dengan kewajiban mengisi **Catatan Revisi** jika usulan aset ditolak/dikembalikan ke OPD.
3. **Manajemen Sertifikat Berjenjang:** Pendataan detail sertifikat (Hak Pakai/Hak Milik) dengan sinkronisasi otomatis ke status master aset.
4. **Integrasi Cloud Storage:** Pemisahan *bucket* Supabase S3 secara logis untuk `Publikasi` (Publik) dan `User Profiles` (Privat).
5. **Export Laporan:** Pembuatan laporan Excel maupun PDF dinamis yang menyesuaikan dengan parameter filter.

---

## 💻 Panduan Setup Lokal (Developer Notes)

Langkah-langkah untuk menjalankan *environment* PATABA di mesin lokal:

1. **Clone & Virtual Environment:**
   ```bash
   git clone <url-repo-kamu>
   cd PATABA
   python3 -m venv venv
   source venv/bin/activate
   ```  
(Mac/Linux) atau venv\Scripts\activate (Windows)

2. **Install Dependensi:**
```bash
pip install -r requirements.txt
```
(Pastikan django-storages dan boto3 sudah terinstall untuk fitur Supabase)

3. **Konfigurasi Environment:**

5. **Jalankan Migrasi dan Server:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
---
## ⚠️ Notes
1. Trik Nama Tabel (Supabase):
   Setiap menambahkan model baru, WAJIB menambahkan `db_table = 'nama_tabel'` di dalam `class Meta:` agar nama tabel di PostgreSQL tetap sinkron dan tidak berantakan.
2. Aturan Migrasi Ulang:
Jika terjadi error bentrok antar tabel akibat perombakan, gunakan trik `python manage.py migrate --fake` agar Django mendata migrasi tanpa menimpa/menghapus data asli di database.
3. Upload File / Gambar HTML:
Setiap tag `<form>` yang memiliki fitur upload file/foto WAJIB memiliki atribut `enctype="multipart/form-data"`. Jika tidak, file tidak akan pernah terkirim ke backend.
4. Manajemen Cloud Storage:
File dilarang disimpan di lokal untuk versi Production. Selalu gunakan file `pataba_core/storages.py` untuk mengarahkan pengunggahan gambar ke bucket Supabase yang terpisah (contoh: `PublikasiStorage()` dan `ProfileStorage()`).

---

🫶🏻🐈‍⬛
