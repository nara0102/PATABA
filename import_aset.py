import os
import django
import openpyxl
from datetime import datetime

# Setup Environment Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pataba_core.settings')
django.setup()

from apps.aset_tanah.models import AsetTanah, MasterOPD

def jalankan_import():
    # --- PERUBAHAN PATH FOLDER DI SINI ---
    file_path = 'dataset/dummy_aset.xlsx'

    if not os.path.exists(file_path):
        print(f"❌ File {file_path} tidak ditemukan! Pastikan file ada di dalam folder 'dataset'.")
        return

    print(f"Membaca file {file_path}...")
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    berhasil = 0
    gagal = 0

    for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        opd_id = row[0]
        
        if not opd_id: 
            break

        # Tarik data dari sel (KEMBALI MENGGUNAKAN 20 KOLOM)
        nama_barang = row[1]
        kode_barang = row[2]
        nibar = row[3]
        nomor_register = row[4]
        status_kepemilikan = row[5]
        luas_m2 = row[6]
        cara_perolehan = row[7]
        tanggal_perolehan = row[8] 
        nilai_aset = row[9]
        latitude = row[10]
        longitude = row[11]
        kecamatan_nama = row[12]
        kelurahan_nama = row[13]
        alamat_lokasi = row[14]
        status_sertifikasi = row[15]
        nomor_sertifikat = row[16]
        kondisi_pemanfaatan = row[17]
        status_penggunaan = row[18]
        status_verifikasi = row[19]

        # Validasi OPD
        try:
            opd_obj = MasterOPD.objects.get(id=opd_id)
        except MasterOPD.DoesNotExist:
            print(f"⚠️ Baris {i}: GAGAL - ID OPD '{opd_id}' tidak ditemukan di Database. (Lewati)")
            gagal += 1
            continue

        # Eksekusi pembuatan aset
        AsetTanah.objects.create(
            opd=opd_obj,
            nama_barang=nama_barang,
            kode_barang=kode_barang,
            nibar=nibar,
            nomor_register=nomor_register,
            status_kepemilikan=status_kepemilikan,
            luas_m2=luas_m2 if luas_m2 else 0,
            cara_perolehan=cara_perolehan,
            tanggal_perolehan=tanggal_perolehan if tanggal_perolehan else None,
            nilai_aset=nilai_aset if nilai_aset else 0,
            latitude=latitude if latitude else 0,
            longitude=longitude if longitude else 0,
            kecamatan_nama=kecamatan_nama,
            kelurahan_nama=kelurahan_nama,
            alamat_lokasi=alamat_lokasi,
            
            # Otomatis jadikan BERSERTIFIKAT jika di Excel kosong
            status_sertifikasi=status_sertifikasi if status_sertifikasi else 'BERSERTIFIKAT',
            nomor_sertifikat=nomor_sertifikat,
            
            kondisi_pemanfaatan=kondisi_pemanfaatan,
            status_penggunaan=status_penggunaan,
            
            # Otomatis jadikan VALID jika di Excel kosong
            status_verifikasi=status_verifikasi if status_verifikasi else 'VALID',
            satuan='m2'
        )
        print(f"✅ Baris {i}: Berhasil menyuntikkan aset '{nama_barang}'")
        berhasil += 1

    print("-" * 30)
    print(f"🎉 Selesai! Berhasil: {berhasil} data, Gagal: {gagal} data.")

if __name__ == '__main__':
    jalankan_import()