import pandas as pd
import os
import django
from django.utils import timezone

# Setup lingkungan Django agar script bisa membaca model
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pataba_core.settings') # nama project
django.setup()

from apps.aset_tanah.models import MasterOPD

def import_opd():
    # file path mac
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'dataset', 'daftar_opd.xlsx')
    
    # Membaca file Excel
    df = pd.read_excel(file_path)
    
    # Menghapus baris yang kosong atau tidak memiliki Kode OPD
    df = df.dropna(subset=['Kode OPD'])

    count = 0
    for index, row in df.iterrows():
        try:
            # Update atau Create data baru
            obj, created = MasterOPD.objects.update_or_create(
                kode_opd=row['Kode OPD'],
                defaults={
                    'nama_opd': row['Nama OPD'],
                    'kode_lokasi': row['Kode Lokasi'],
                    'singkatan': row['Singkatan'],
                    'kategori_opd': row['Kategori OPD'],
                    'alamat_kantor': row['Alamat Kantor'],
                    'kepala_opd': row['Kepala OPD'],
                    'is_active': 1 if str(row['Status Aktif']).strip() == 'Aktif' else 0,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )
            count += 1
            print(f"Berhasil mengimport: {row['Nama OPD']}")
        except Exception as e:
            print(f"Gagal mengimport {row['Nama OPD']}: {e}")
            
    print(f"\nSelesai! Total {count} OPD telah diimport ke database.")

if __name__ == "__main__":
    import_opd()