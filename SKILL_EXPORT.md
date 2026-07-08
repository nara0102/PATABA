# TRANSPARA - DOKTRIN LOGIKA EKSPOR DATA & LAPORAN (SKILL_EXPORT.MD)
**Fokus:** Konfigurasi Mesin Ekspor Dinamis Excel (OpenPyXL) & Dokumen Fisik Audit Eksekutif PDF (xhtml2pdf)

---

## 1. Filter Cerdas & Konsolidasi Anti-Duplikasi (Data Deduplication)
Untuk mencegah admin BPKAD kebingungan akibat kolom ganda antara Tabel Master (`AsetTanah`) dan Tabel Detail (`SertifikatTanah`), mesin ekspor wajib menggunakan gerbang logika satu pintu:
* **Status Hak & Nomor Hak:** Jika aset berstatus `BERSERTIFIKAT`, data otomatis ditarik dari tabel detail BPN (`SertifikatTanah`)[cite: 3]. Jika statusnya `BELUM_BERSERTIFIKAT`, data ditarik dari data sementara di tabel master (`AsetTanah`)[cite: 3].
* **Kondisi Fisik Dokumen:** Dipetakan menjadi string bersih ("Dokumen Asli" / "Hanya Fotokopi") dengan membaca prioritas utama pada tabel detail BPN, kemudian melakukan fallback ke kode sinkronisasi 5 pilar (`ASLI_PEMKOT`, `FOTOKOPI_NON_PEMKOT`, dll) pada tabel master[cite: 3].

---

## 2. Aturan Format Akuntansi & Numerik Excel (OpenPyXL Engine)
Jangan pernah mengubah angka menjadi string teks di level Python (seperti menambahkan simbol "Rp" manual), karena akan merusak fungsi aritmatika (`SUM`, grafik) di Microsoft Excel. 
* **Solusi:** Kirimkan data berupa angka mentah (*float/int*), lalu injeksikan properti `number_format` bawaan openpyxl:
  * **Kolom Luas Tanah:** Gunakan format mask `#,##0 "m²"` (Visual otomatis: `1.500 m²`).
  * **Kolom Nilai Aset:** Gunakan format mask `"Rp"#,##0` (Visual otomatis: `Rp150.000.000`).

---

## 3. Interceptor Latar Belakang & Animasi Loading (Fetch Blob Tech)
Untuk menghindari lonjakan beban request browser dan memberikan UX yang responsif, proses submit form unduhan dibajak oleh JavaScript Fetch API:
1. Tahan submit konvensional via `e.preventDefault()`.
2. Kunci tombol utama, sembunyikan teks normal, dan hidupkan kelas `.spinner-border` (`d-none` di-toggle).
3. Jalankan `fetch()` secara background, konversi *stream tracking* menjadi `response.blob()`, lalu tembak link dummy otomatis menggunakan `URL.createObjectURL(blob)`.
4. Kembalikan sakelar tombol ke kondisi semula di dalam blok `.finally()`.

---

## 4. Arsitektur PDF Rekapitulasi 40 OPD Global (Landscape F4)
* **Doktrin Keutuhan Baris:** Laporan wajib menggunakan query basis data dari `MasterOPD.objects.filter(is_active=1)` agar seluruh 40 instansi aktif Kota Palu tercetak utuh[cite: 4]. OPD yang belum memiliki aset tervalidasi tidak boleh hilang dari baris tabel, melainkan wajib diisi dengan angka `0` atau tanda strip `-` secara otomatis.
* **Redistribusi Lebar Kolom:** Menggunakan properti CSS `table-layout: fixed;` pada `xhtml2pdf`. Alokasikan lebar kolom sekecil mungkin untuk data ringkas (dengan memaksimalkan untuk kolom nomor atau lainnya yang berkemungkinan isi data nya kecil atau sedikit karakter), lalu berikan sisa ruang terbesar untuk kolom nilai rupiah agar angka ratusan miliar tidak melipat ke bawah.

---

## 5. Arsitektur PDF Buku Inventaris Individu OPD (Landscape F4 & String Chunker)
* **Sinkronisasi Kepala Instansi Dinamis:** Nama kepala dinas dan NIP dilarang keras menggunakan input teks statis. Cari data secara silang melalui relasi `UserProfile` yang memiliki `opd_id` sama, lalu peras datanya dari `auth_user` (`first_name`, `last_name`) dan `user_profile` (`nip`)[cite: 4].
* **Defensive Programming Kode Lokasi:** Jika database mengirimkan nilai mentah transisi berupa `"0.0"` atau `"0"`, Python *backend view* wajib mencegatnya dan memaksa nilainya kembali ke kode regulasi acuan utama BPKAD yaitu `-`.
* **Strategi Anti-Jebol Sel (String Chunker):** Karena `xhtml2pdf` tidak bisa memotong string angka beruntun tanpa spasi (NIBAR, Kode Barang, Koordinat raksasa), Python wajib memecah teks tersebut dengan menyisipkan spasi halus setiap 10-14 karakter menggunakan fungsi:
  `" ".join(teks[i:i+batas] for i in range(0, len(teks), batas))`
  Hal ini memaksa browser seluler/PDF melakukan *wrap down* (patah baris ke bawah) dengan aman di dalam kotak.

---

## 6. Standarisasi Balanced Executive Footer
Setiap laporan PDF resmi aplikasi PATABA wajib mengimplementasikan struktur dwi-bingkai seimbang pada bagian kaki halaman:
* **Sisi Kiri (60% Width):** Menampilkan URL otentikasi verifikasi sistem enkripsi absolut (`request.build_absolute_uri`).
* **Sisi Kanan (40% Width):** Menampilkan indeks penomoran halaman dinamis menggunakan tag ReportLab native: `Halaman <pdf:pagenumber> dari <pdf:pagecount>`.