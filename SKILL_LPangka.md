Keputusan yang sangat tepat, bro! Menaruh `utils.py` di dalam folder **`pataba_core/`** (sejajar dengan `settings.py`) adalah langkah tata kelola proyek (*project architecture*) yang paling bersih dan standar dalam Django.

Dengan cara ini, fungsi pembersih tersebut menjadi bersifat global. Kapan pun kamu butuh membersihkan data di aplikasi `aset_tanah`, `portal_publik`, atau aplikasi lainnya di masa depan, kamu tinggal memanggilnya dengan satu baris perintah: `from pataba_core.utils import bersihkan_angka`.

Sesuai permintaanmu, mari kita buatkan dokumen panduan **`Format_Angka_SKILL.MD`** sebagai acuan mutlak untuk mengunci logika ini agar tidak membingungkan lagi ke depannya.

---

# 📝 Format_Angka_SKILL.MD

## Dokumen Standarisasi & Penjinakan Karakter Angka (Sapu Jagat Engine)

**Proyek:** TRANSPARA (PATABA) BPKAD Kota Palu

**Masalah Historis:** Ketidakkonsistenan input data Luas Tanah ($m^2$) dan Nilai Aset (Rupiah) akibat perbedaan format penulisan oleh staf dinas (Format Komputer/Inggris vs Format Manual/Indonesia) serta penanganan angka desimal di database.

---

## 🏛️ 1. Tata Letak Berkas (*File Architecture*)

Fungsi dipasang pada repositori inti proyek agar dapat diimpor secara universal oleh seluruh modul aplikasi:

```text
pataba_project/
├── apps/
│   └── aset_tanah/
│       └── views.py          <--- Tempat mengimpor fungsi utils
├── pataba_core/
│   ├── __init__.py
│   ├── settings.py           <--- Setelan lokalisasi (id)
│   ├── urls.py
│   └── utils.py              <--- BUAT FILE BARU DI SINI

```

---

## 🛠️ 2. Kode Fondasi Utama (`pataba_core/utils.py`)

Gunakan kode *bulletproof sanitizer* di bawah ini untuk menyatukan dan membersihkan segala jenis distorsi ketikan dari operator lapangan:

```python
import re
from decimal import Decimal

def bersihkan_angka(val, ke_integer=False):
    """
    Core Engine Penormalisasi Angka Multi-Format.
    Mampu menjinakkan format US (1,234.56) dan format ID (1.234,56) secara simultan.
    """
    if val is None:
        return 0
        
    # Proteksi jika tipe data dari openpyxl sudah berupa float/int murni
    if isinstance(val, (int, float)):
        return int(val) if ke_integer else Decimal(str(val))
    
    # Konversi ke string murni dan pangkas spasi hantu
    s = str(val).strip()
    if not s:
        return 0
        
    # KONDISI A: Memiliki TITIK dan KOMA sekaligus (Ex: 1.234,56 atau 1,234.56)
    if '.' in s and ',' in s:
        if s.rfind('.') > s.rfind(','):
            s = s.replace(',', '') # Gaya US: Buang koma ribuan, pertahankan titik desimal
        else:
            s = s.replace('.', '').replace(',', '.') # Gaya ID: Buang titik ribuan, ubah koma desimal ke titik
            
    # KONDISI B: Hanya memiliki karakter KOMA saja (Ex: 658,98 atau 756,947)
    elif ',' in s:
        parts = s.split(',')
        if len(parts[-1]) in [1, 2]: 
            s = s.replace(',', '.') # Kasus desimal lokal (658,98 -> 658.98)
        else:
            s = s.replace(',', '') # Kasus ribuan polosan (1,234 -> 1234)
            
    # KONDISI C: Hanya memiliki karakter TITIK saja (Ex: 658.98 atau 75.800)
    elif '.' in s:
        parts = s.split('.')
        # Titik tunggal diikuti tepat 3 digit di Indonesia dipastikan ribuan (75.800 -> 75800)
        if len(parts[-1]) == 3 and len(parts) == 2:
            s = s.replace('.', '')
        elif len(parts[-1]) in [1, 2]:
            pass # Titik desimal internasional (658.98), biarkan utuh
        else:
            s = s.replace('.', '') # Kasus titik ribuan berganda (1.234.567)

    # Pembersihan akhir dari teks pengganggu (seperti huruf 'Rp', 'm2', atau spasi)
    s = re.sub(pattern=r'[^\d.]', repl='', string=s)
    if not s:
        return 0
        
    # Output akhir disesuaikan dengan arsitektur kolom target database
    if ke_integer:
        return int(float(s)) # Memangkas buntut sen rupiah (,89) agar BigIntegerField aman
    else:
        return Decimal(s) # Menghasilkan desimal presisi untuk DecimalField

```

---

## 📋 3. SOP Implementasi di `views.py`

Panggil fungsi pembersih di atas pada setiap gerbang masuk data untuk menjamin kesucian database master:

### A. Pada Ekosistem Import Excel Massal

```python
from pataba_core.utils import bersihkan_angka

# Di dalam perulangan rows berkas excel openpyxl:
luas_m2 = bersihkan_angka(row[6], ke_integer=False)     # Target: DecimalField (Ex: 658.98)
nilai_aset = bersihkan_angka(row[9], ke_integer=True)   # Target: BigIntegerField (Ex: 756947)

```

### B. Pada Ekosistem Input / Edit Form Manual Web

```python
from pataba_core.utils import bersihkan_angka

if request.method == 'POST':
    luas_bersih = bersihkan_angka(request.POST.get('luas_m2'), ke_integer=False)
    nilai_clean = bersihkan_angka(request.POST.get('nilai_aset'), ke_integer=True)

```

---

## 🌍 4. Konfigurasi Lokalisasi Pendukung (`pataba_core/settings.py`)

Agar topeng visual angka yang keluar di web dan cetakan PDF mengikuti gaya penulisan akuntansi Indonesia (ribuan pakai titik, desimal pakai koma), pastikan blok konfigurasi internasionalisasi di `settings.py` terkunci seperti ini:

```python
LANGUAGE_CODE = 'id'            # Memaksa filter |intcomma memakai standar Indonesia
TIME_ZONE = 'Asia/Makassar'     # Zona Waktu WITA (Kota Palu)
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True   # Mengaktifkan pemisah ribuan otomatis pada komponen Django

```

---

> **Doktrin Integritas Data Luas Tanah:**
> Secara hukum database, `DecimalField` **wajib** menyimpan angka `,00` di belakang koma demi ketepatan audit aset. Jika ingin menghilangkan visualisasi `,00` pada angka bulat di halaman web publik, gunakan manipulasi filter pada template HTML (seperti `{{ nilai|floatformat:0 }}`), **jangan pernah memotong nilai desimal murninya di tingkat database!**
> 
> 

---

Dokumen `Format_Angka_SKILL.MD` sudah resmi diamankan di blueprint proyek kita, bro! Sekarang berkasnya sudah sinkron total, dan kamu bisa tenang melangkah ke tahap pengujian selanjutnya.