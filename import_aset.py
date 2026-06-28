import os
import django
import openpyxl
from datetime import datetime

# Setup Environment Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pataba_core.settings')
django.setup()

from apps.aset_tanah.models import AsetTanah, MasterOPD, RefKelurahan

def jalankan_import():
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
        # Amankan baris jika kosong
        if not row or not row[0]: 
            break

        opd_id = row[0]

        # --- MAPPING 26 KOLOM EXCEL ---
        nama_barang = row[1]
        kode_barang = row[2]
        nibar = row[3]
        nomor_register_raw = row[4]
        nomor_register_raw = row[4]
        if nomor_register_raw is not None:
            # 1. Jika excel membaca sebagai float (ex: 1.0) atau int (ex: 1)
            if isinstance(nomor_register_raw, (int, float)):
                nomor_register = str(int(nomor_register_raw)).strip().zfill(4)
            else:
                # 2. Jika dibaca sebagai teks string biasa
                nomor_register = str(nomor_register_raw).strip().zfill(4)
        else:
            nomor_register = "0000"
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
        
        # pencarian id kel.
        kel_obj = None
        if kelurahan_nama:
            kel_obj = RefKelurahan.objects.filter(nama_kelurahan__iexact=kelurahan_nama).first()
        
        # Kolom Status Sertifikasi Utama
        status_sertifikasi = row[15] if row[15] else 'BELUM_BERSERTIFIKAT'
        nomor_sertifikat = row[16]
        
        kondisi_pemanfaatan = row[17]
        status_penggunaan = row[18]
        status_verifikasi = row[19] if row[19] else 'VALID'

        # --- KOLOM BARU (Penyesuaian Data Integrity) ---
        # Pastikan Excel memiliki kolom ini agar tidak IndexError
        spesifikasi_nama_barang = row[20] if len(row) > 20 else None
        spesifikasi_lainnya = row[21] if len(row) > 21 else None
        
        # Logika Sertifikat Terpadu
        status_hak_sementara = row[22] if len(row) > 22 else None
        nomor_hak = row[23] if len(row) > 23 else None
        nama_pemegang_hak = row[24] if len(row) > 24 else None
        keterangan_sertifikasi_lainnya = row[25] if len(row) > 25 else None

        # Validasi OPD
        try:
            opd_obj = MasterOPD.objects.get(id=opd_id)
        except MasterOPD.DoesNotExist:
            print(f"⚠️ Baris {i}: GAGAL - ID OPD '{opd_id}' tidak ditemukan di Database. (Lewati)")
            gagal += 1
            continue

        # Eksekusi pembuatan aset
        try:
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
                kelurahan=kel_obj,
                kelurahan_nama=kelurahan_nama,
                alamat_lokasi=alamat_lokasi,
                
                status_sertifikasi=status_sertifikasi,
                nomor_sertifikat=nomor_sertifikat,
                
                kondisi_pemanfaatan=kondisi_pemanfaatan,
                status_penggunaan=status_penggunaan,
                status_verifikasi=status_verifikasi,
                satuan='m2',

                # Field Baru
                spesifikasi_nama_barang=spesifikasi_nama_barang,
                spesifikasi_lainnya=spesifikasi_lainnya,
                status_hak_sementara=status_hak_sementara,
                nomor_hak=nomor_hak,
                nama_pemegang_hak=nama_pemegang_hak,
                keterangan_sertifikasi_lainnya=keterangan_sertifikasi_lainnya
            )
            print(f"✅ Baris {i}: Berhasil menyuntikkan aset '{nama_barang}'")
            berhasil += 1
        except Exception as e:
            print(f"❌ Baris {i}: GAGAL menyimpan '{nama_barang}'. Error: {e}")
            gagal += 1

    print("-" * 30)
    print(f"🎉 Selesai! Berhasil: {berhasil} data, Gagal: {gagal} data.")

if __name__ == '__main__':
    jalankan_import()