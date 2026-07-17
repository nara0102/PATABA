import re
from decimal import Decimal

# pataba_core/utils.py

def bersihkan_angka(value, ke_integer=False):
    """
    SOP Pembersih Angka Pintar (PATABA Engine).
    Kebal terhadap format ribuan/desimal Indonesia (dots) maupun Inggris (commas).
    """
    if value is None:
        return 0 if ke_integer else 0.0
    
    # Bersihkan simbol mata uang, spasi, dan satuan luas
    val_str = str(value).replace('Rp', '').replace('m²', '').replace(' ', '').strip()
    if not val_str:
        return 0 if ke_integer else 0.0

    # KASUS 1: Mengandung kedua separator (Koma dan Titik)
    # Contoh: "129.870.000,50" (ID) atau "129,870,000.50" (EN)
    if ',' in val_str and '.' in val_str:
        if val_str.rfind('.') > val_str.rfind(','):
            # Titik berada di akhir -> Format Inggris (Koma adalah ribuan, hapus!)
            val_str = val_str.replace(',', '')
        else:
            # Koma berada di akhir -> Format Indonesia (Titik ribuan hapus, koma jadi titik desimal)
            val_str = val_str.replace('.', '').replace(',', '.')
    
    # KASUS 2: Hanya mengandung Koma (Contoh: "129,870,000" atau "23,718")
    elif ',' in val_str and '.' not in val_str:
        parts = val_str.split(',')
        if ke_integer:
            # Untuk Rupiah, koma pasti ribuan Inggris atau desimal sen (,00) yang bisa dibuang
            if len(parts[-1]) == 2 or parts[-1] == '00': 
                val_str = "".join(parts[:-1]).replace(',', '')
            else:
                val_str = val_str.replace(',', '')
        else:
            # Untuk Luas, jika hanya ada 1 koma dengan 3 digit di belakang (e.g. "23,718") -> itu ribuan
            if len(parts) == 2 and len(parts[1]) == 3:
                val_str = val_str.replace(',', '')
            # Jika koma tunggal desimal (e.g. "23,7" atau "23,72") -> ubah jadi desimal titik
            elif len(parts) == 2:
                val_str = val_str.replace(',', '.')
            else:
                val_str = val_str.replace(',', '')

    # KASUS 3: Hanya mengandung Titik (Contoh: "129.870.000" atau "23.718")
    elif '.' in val_str and ',' not in val_str:
        parts = val_str.split('.')
        if ke_integer:
            # Untuk Rupiah, titik murni pembatas ribuan
            val_str = val_str.replace('.', '')
        else:
            # Untuk Luas, jika hanya ada 1 titik dengan 3 digit di belakang (e.g. "23.718") -> itu ribuan
            if len(parts) == 2 and len(parts[1]) == 3:
                val_str = val_str.replace('.', '')
            # Jika titik tunggal desimal (e.g. "23.7" atau "23.72") -> biarkan saja
            elif len(parts) == 2:
                pass
            else:
                val_str = val_str.replace('.', '')

    # Eksekusi konversi aman
    try:
        if ke_integer:
            return int(float(val_str))
        else:
            return float(val_str)
    except (ValueError, TypeError):
        return 0 if ke_integer else 0.0