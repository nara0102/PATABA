import re
from decimal import Decimal

def bersihkan_angka(val, ke_integer=False):
    """
    Fungsi cerdas penormalisasi angka kacau bawaan staf dinas.
    Dapat mendeteksi format US (1,234.56) maupun format ID (1.234,56).
    """
    if val is None:
        return 0
    # Jika sudah bertipe numerik murni dari openpyxl
    if isinstance(val, (int, float)):
        return int(val) if ke_integer else Decimal(str(val))
    
    # Konversi ke string dan buang spasi hantu
    s = str(val).strip()
    if not s:
        return 0
        
    # Kasus 1: Memiliki titik DAN koma sekaligus (Contoh: 1.234,56 atau 1,234.56)
    if '.' in s and ',' in s:
        if s.rfind('.') > s.rfind(','):
            s = s.replace(',', '') # Gaya US, buang koma ribuan
        else:
            s = s.replace('.', '').replace(',', '.') # Gaya ID, buang titik ribuan, ubah koma desimal ke titik
            
    # Kasus 2: Hanya memiliki karakter KOMA saja (Contoh: 658,98 atau 756,947)
    elif ',' in s:
        parts = s.split(',')
        if len(parts[-1]) in [1, 2]: 
            s = s.replace(',', '.') # Berarti koma desimal (658,98 -> 658.98)
        else:
            s = s.replace(',', '') # Berarti koma ribuan (1,234 -> 1234)
            
    # Kasus 3: Hanya memiliki karakter TITIK saja (Contoh: 658.98 atau 75.800)
    elif '.' in s:
        parts = s.split('.')
        # Jika titik tunggal diikuti 3 digit, di Indonesia itu hampir pasti ribuan (75.800 -> 75800)
        if len(parts[-1]) == 3 and len(parts) == 2:
            s = s.replace('.', '')
        elif len(parts[-1]) in [1, 2]:
            pass # Berarti titik desimal (658.98), biarkan utuh
        else:
            s = s.replace('.', '') # Titik ribuan berganda (1.234.567)

    # Bersihkan sisa karakter non-numerik (seperti huruf Rp, spasi, atau simbol m2)
    s = re.sub(pattern=r'[^\d.]', repl='', string=s)
    if not s:
        return 0
        
    # Kembalikan tipe data sesuai kebutuhan kolom database
    if ke_integer:
        return int(float(s)) # Memotong sen rupiah (,89) secara aman agar BigIntegerField tidak crash!
    else:
        return Decimal(s)