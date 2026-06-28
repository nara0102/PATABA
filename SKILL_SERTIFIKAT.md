# TRANSPARA - DOKTRIN LOGIKA SERTIFIKASI (SKILL_SERTIFIKAT.MD)
**Fokus:** Relasi Master Aset Tanah & Detail Sertifikat Tanah

## 1. Arsitektur Dua Tabel (The Twin-Table Architecture)
Data sertifikat dipecah menjadi dua bagian untuk menjaga performa filter Dasbor dan kelengkapan dokumen BPN:
* **Tabel Master (`AsetTanah`):** Menyimpan status singkatan untuk kebutuhan Filter/Pencarian cepat (Dashboard).
* **Tabel Detail (`SertifikatTanah`):** Menyimpan wujud fisik dokumen BPN secara mendetail untuk kebutuhan Cetak Profil/PDF.

## 2. Kunci Sinkronisasi (The Sync Key)
Setiap kali `SertifikatTanah` DIBUAT atau DIEDIT, ia WAJIB melemparkan dua data kembali ke `AsetTanah`:
1. `nomor_sertifikat`
2. `nama_pemegang_hak`

## 3. Logika 5 Kategori Bukti Fisik (The 5-Pillars of Evidence)
Aturan baku Dinas BPKAD yang membagi bukti sertifikat menjadi 5 kondisi absolut:

**A. KELOMPOK SUDAH BERSERTIFIKAT (Sertifikat Telah Terbit)**
Disimpan di kolom `keterangan_sertifikasi_lainnya` pada Master Aset.
1. **`ASLI_PEMKOT`** - Bukti Fisik: ASLI
   - Kepemilikan: PEMKOT
   - *Tindakan Sistem:* Paksa `nama_pemegang_hak` menjadi "Pemerintah Kota Palu".
2. **`FOTOKOPI_PEMKOT`**
   - Bukti Fisik: FOTOKOPI
   - Kepemilikan: PEMKOT
   - *Tindakan Sistem:* Paksa `nama_pemegang_hak` menjadi "Pemerintah Kota Palu".
3. **`ASLI_NON_PEMKOT`**
   - Bukti Fisik: ASLI
   - Kepemilikan: LAINNYA
   - *Tindakan Sistem:* Simpan teks nama yang diketik manual oleh user (Misal: "Kementerian Agama").
4. **`FOTOKOPI_NON_PEMKOT`**
   - Bukti Fisik: FOTOKOPI
   - Kepemilikan: LAINNYA
   - *Tindakan Sistem:* Simpan teks nama yang diketik manual oleh user.

**B. KELOMPOK BELUM BERSERTIFIKAT (Sertifikat Dalam Proses/Kosong)**
5. **Belum Bersertifikat / Dalam Proses**
   - Wajib mendefinisikan `status_hak_sementara` (HAK_PAKAI / HAK_MILIK).
   - Wajib mengisi `nomor_hak` sementara.
   - Kolom `keterangan_sertifikasi_lainnya` diisi keterangan proses.
   - *Tindakan Sistem:* Kosongkan absolut `nama_pemegang_hak`.

## 4. Pengaman Ganda Lapis Backend (Double Safety Net)
Karena JavaScript terkadang gagal mengirimkan data dari form HTML yang tersembunyi (`display: none`), fungsi `views.py` WAJIB mengintervensi dengan membaca *string* 'PEMKOT'. Jika terdeteksi, Python yang akan mengisi paksa string "Pemerintah Kota Palu" ke database.