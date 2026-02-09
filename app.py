import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Cek Kendaraan Operasional",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Form Pemeriksaan Kendaraan Bulanan")
st.markdown("Pastikan data diisi dengan kondisi riil di lapangan.")

# --- KONEKSI KE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi ambil daftar mobil
def get_daftar_mobil():
    try:
        df = conn.read(worksheet="daftar_mobil", ttl=5)
        return df['Nama_Mobil'].dropna().tolist() # Asumsi kolom di sheet bernama 'Nama_Mobil'
    except Exception as e:
        st.error(f"Gagal mengambil daftar mobil. Pastikan sheet 'daftar_mobil' ada header 'Nama_Mobil'. Error: {e}")
        return []

# --- FORM INPUT ---
with st.form("form_pemeriksaan"):
    # 1. Identitas & Kendaraan
    st.subheader("📝 Data Umum")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        nama_security = st.text_input("Nama Pemeriksa (Security)")
        tanggal = st.date_input("Tanggal Pemeriksaan", datetime.now())
    
    with c2:
        list_mobil = get_daftar_mobil()
        merk_kendaraan = st.selectbox("Pilih Unit Kendaraan", list_mobil if list_mobil else ["Data Kosong"])
        nopol = st.text_input("Nomor Polisi")
    
    with c3:
        kilometer = st.number_input("Kilometer Saat Ini", min_value=0, step=1)

    # Helper function untuk membuat radio button kondisi
    def buat_opsi(label):
        return st.radio(label, ["Baik", "Rusak", "Hilang/Kurang"], horizontal=True, index=0, key=label)

    st.write("---")
    
    # 2. Pengelompokan Item Pemeriksaan (Tabs biar rapi)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🪟 Kaca & Spion", "🚗 Ban & Eksterior", "🛋️ Interior", "⚙️ Mesin", "💡 Lampu & Lainnya"])

    with tab1:
        c_kaca1, c_kaca2 = st.columns(2)
        with c_kaca1:
            kaca_depan = buat_opsi("Kaca Depan")
            kaca_kiri = buat_opsi("Kaca Kiri")
            kaca_kanan = buat_opsi("Kaca Kanan")
        with c_kaca2:
            spion_kanan = buat_opsi("Spion Kanan")
            spion_kiri = buat_opsi("Spion Kiri")
            spion_dalam = buat_opsi("Spion Dalam")

    with tab2:
        c_ban1, c_ban2 = st.columns(2)
        with c_ban1:
            ban_kanan_depan = buat_opsi("Ban Kanan Depan")
            ban_kiri_depan = buat_opsi("Ban Kiri Depan")
            ban_kanan_belakang = buat_opsi("Ban Kanan Belakang")
            ban_kiri_belakang = buat_opsi("Ban Kiri Belakang")
            ban_serep = buat_opsi("Ban Serep")
        with c_ban2:
            ext_talang_air = buat_opsi("Ext. Talang Air")
            ext_plat_blkg = buat_opsi("Ext. Plat Belakang")
            ext_plat_dpn = buat_opsi("Ext. Plat Depan")
            body_depan = buat_opsi("Body Depan")
            body_grill = buat_opsi("Body Grill")
            body_fender = buat_opsi("Body Fender")
            pintu_d_kanan = buat_opsi("Pintu Depan Kanan")
            pintu_d_kiri = buat_opsi("Pintu Depan Kiri")
            pintu_b_kanan = buat_opsi("Pintu Belakang Kanan")
            pintu_b_kiri = buat_opsi("Pintu Belakang Kiri")
            pintu_bagasi = buat_opsi("Pintu Bagasi")

    with tab3:
        c_int1, c_int2 = st.columns(2)
        with c_int1:
            int_jok = buat_opsi("Int. Jok")
            int_stir = buat_opsi("Int. Stir")
            int_karpet = buat_opsi("Int. Karpet")
            int_persneling = buat_opsi("Int. Persneling")
        with c_int2:
            int_rem_tangan = buat_opsi("Int. Rem Tangan")
            int_dashboard = buat_opsi("Int. Dashboard")
            int_ac = buat_opsi("Int. AC")

    with tab4:
        c_mesin1, c_mesin2 = st.columns(2)
        with c_mesin1:
            mesin_oli = buat_opsi("Mesin Oli")
            mesin_minyak_rem = buat_opsi("Mesin Minyak Rem")
            mesin_air_radiator = buat_opsi("Mesin Air Radiator")
        with c_mesin2:
            mesin_air_accu = buat_opsi("Mesin Air Accu")
            mesin_air_wiper = buat_opsi("Mesin Air Wiper")

    with tab5:
        c_lampu1, c_lampu2 = st.columns(2)
        with c_lampu1:
            lampu_utama = buat_opsi("Lampu Utama")
            lampu_kecil = buat_opsi("Lampu Kecil")
            lampu_rem = buat_opsi("Lampu Rem")
            sein_depan = buat_opsi("Sein Depan")
            sein_belakang = buat_opsi("Sein Belakang")
        with c_lampu2:
            kunci_roda = buat_opsi("Kunci Roda")
            dongkrak = buat_opsi("Dongkrak")
            p3k = buat_opsi("P3K")
            stnk = buat_opsi("STNK")

    st.write("---")
    keterangan = st.text_area("Catatan Tambahan / Keterangan Kerusakan")

    # Tombol Submit
    submit_btn = st.form_submit_button("Simpan Data Pemeriksaan", type="primary")

    if submit_btn:
        if not nama_security or not nopol:
            st.warning("Nama Security dan Nomor Polisi wajib diisi!")
        else:
            # Siapkan Data
            data_baru = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nama_Security": nama_security,
                "Tanggal": tanggal.strftime("%Y-%m-%d"),
                "Merk_Kendaraan": merk_kendaraan,
                "Nomor_Polisi": nopol,
                "Kilometer": kilometer,
                "Kaca_Depan": kaca_depan,
                "Kaca_Kiri": kaca_kiri,
                "Kaca_Kanan": kaca_kanan,
                "Spion_Kanan": spion_kanan,
                "Spion_Kiri": spion_kiri,
                "Spion_Dalam": spion_dalam,
                "Ban_Kanan_Depan": ban_kanan_depan,
                "Ban_Kiri_Depan": ban_kiri_depan,
                "Ban_Kanan_Belakang": ban_kanan_belakang,
                "Ban_Kiri_Belakang": ban_kiri_belakang,
                "Ban_Serep": ban_serep,
                "Ext_Talang_Air": ext_talang_air,
                "Ext_Plat_Belakang": ext_plat_blkg,
                "Ext_Plat_Depan": ext_plat_dpn,
                "Int_Jok": int_jok,
                "Int_Stir": int_stir,
                "Int_Karpet": int_karpet,
                "Int_Persneling": int_persneling,
                "Int_Rem_Tangan": int_rem_tangan,
                "Int_Dashboard": int_dashboard,
                "Int_AC": int_ac,
                "Body_Depan": body_depan,
                "Body_Grill": body_grill,
                "Body_Fender": body_fender,
                "Pintu_D_Kanan": pintu_d_kanan,
                "Pintu_D_Kiri": pintu_d_kiri,
                "Pintu_B_Kanan": pintu_b_kanan,
                "Pintu_B_Kiri": pintu_b_kiri,
                "Pintu_Bagasi": pintu_bagasi,
                "Mesin_Oli": mesin_oli,
                "Mesin_Minyak_Rem": mesin_minyak_rem,
                "Mesin_Air_Radiator": mesin_air_radiator,
                "Mesin_Air_Accu": mesin_air_accu,
                "Mesin_Air_Wiper": mesin_air_wiper,
                "Lampu_Utama": lampu_utama,
                "Lampu_Kecil": lampu_kecil,
                "Lampu_Rem": lampu_rem,
                "Sein_Depan": sein_depan,
                "Sein_Belakang": sein_belakang,
                "Kunci_Roda": kunci_roda,
                "Dongkrak": dongkrak,
                "P3K": p3k,
                "STNK": stnk,
                "Keterangan": keterangan
            }])

            try:
                # Baca data lama dulu
                existing_data = conn.read(worksheet="data_cek", ttl=0)
                # Gabungkan
                updated_data = pd.concat([existing_data, data_baru], ignore_index=True)
                # Update ke Sheet
                conn.update(worksheet="data_cek", data=updated_data)
                st.success("✅ Data berhasil disimpan ke Google Sheets!")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menyimpan: {e}")