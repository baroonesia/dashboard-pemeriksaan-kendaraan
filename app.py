import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
from streamlit_option_menu import option_menu
from PIL import Image
import io
import base64
import tempfile
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Pengecekan Kendaraan BMN | BP3MI Jawa Tengah",
  # page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    
    .stCard {
        background-color: #FFFFFF; padding: 20px; border-radius: 10px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .info-box-row {
        background-color: #F8FAFC; padding: 12px 15px; border-radius: 8px;
        border: 1px solid #E2E8F0; display: flex; align-items: center; gap: 10px; height: 100%;
    }
    .info-box-stacked {
        background-color: #F1F5F9; padding: 10px; border-radius: 8px;
        border: 1px solid #E2E8F0; text-align: center;
    }
    
    .label-text { color: #64748B; font-size: 0.9rem; font-weight: 500; }
    .value-text { color: #0F172A; font-size: 1rem; font-weight: 700; }
    
    .info-label-stack { font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;}
    .info-value-stack { font-size: 1.1rem; font-weight: 700; color: #0F172A; }
    .info-value-red { font-size: 1.1rem; font-weight: 700; color: #EF4444; } 
    .info-value-green { font-size: 1.1rem; font-weight: 700; color: #166534; } 

    .badge-baik { background-color: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;}
    .badge-rusak { background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;}
    .badge-hilang { background-color: #FEF9C3; color: #854D0E; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;}
    
    .metric-card { 
        background-color: white; border: 1px solid #E2E8F0; 
        padding: 20px; border-radius: 12px; text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #0F172A; }
    .metric-label { font-size: 0.9rem; color: #64748B; font-weight: 600; }
    
    div.row-widget.stRadio > div { background-color: transparent !important; border: none !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNGSI UTILITIES ---
def compress_image(image_file):
    if image_file is None: return ""
    try:
        image = Image.open(image_file)
        if image.mode != 'RGB': image = image.convert('RGB')
        max_width = 400
        ratio = max_width / float(image.size[0])
        new_height = int((float(image.size[1]) * float(ratio)))
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=40, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e: return ""

def get_users_db():
    try:
        df = conn.read(worksheet="users", ttl=0)
        df['Username'] = df['Username'].astype(str).str.strip(); df['Password'] = df['Password'].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def get_data_mobil():
    try:
        df = conn.read(worksheet="daftar_mobil", ttl=0)
        df.columns = df.columns.str.strip()
        if 'Nama_Mobil' in df.columns and 'Nomor_Polisi' in df.columns: return df[['Nama_Mobil', 'Nomor_Polisi']].dropna()
    except: pass
    return pd.DataFrame()

def get_laporan_cek():
    try: return conn.read(worksheet="data_cek", ttl=0)
    except: return pd.DataFrame()

# --- FUNGSI LOGIN ---
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False; st.session_state['user_role'] = ""; st.session_state['user_fullname'] = ""
    
    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=100)
            st.markdown("### Login Sistem Pengecekan Kendaraan Dinas")
            st.markdown("BP3MI Jawa Tengah")
            username = st.text_input("Username"); password = st.text_input("Password", type="password")
            if st.button("Masuk Sistem", type="primary", use_container_width=True):
                df_users = get_users_db()
                if not df_users.empty:
                    user = df_users[(df_users['Username'] == username) & (df_users['Password'] == password)]
                    if not user.empty:
                        st.session_state['logged_in'] = True; st.session_state['user_role'] = user.iloc[0]['Role']; st.session_state['user_fullname'] = user.iloc[0]['Nama_Lengkap']; st.rerun()
                    else: st.error("Username atau Password salah.")
                else: st.error("Database user error.")
        return False
    return True

# --- FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12); self.cell(0, 10, 'Laporan Pemeriksaan Kendaraan Operasional | BP3MI', 0, 1, 'C'); self.ln(3)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def create_pdf(row):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    
    # A. INFO UMUM
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " A. INFORMASI UMUM", 1, 1, 'L', fill=True); pdf.set_font("Arial", size=10)
    info = [("Tanggal", str(row['Tanggal'])), ("Pemeriksa", str(row['Nama_Security'])), ("Kendaraan", f"{row['Merk_Kendaraan']} ({row['Nomor_Polisi']})"), ("Kilometer", f"{row['Kilometer']} km")]
    for l, v in info: pdf.cell(45, 7, l, 1); pdf.cell(145, 7, v, 1, 1)
    pdf.ln(5)
    
    # B. DETAIL
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " B. DETAIL KONDISI", 1, 1, 'L', fill=True); pdf.set_font("Arial", size=9)
    items = {
        "Kaca & Spion": ['Kaca_Depan', 'Kaca_Kiri', 'Kaca_Kanan', 'Spion_Kanan', 'Spion_Kiri', 'Spion_Dalam'],
        "Ban & Roda": ['Ban_Kanan_Depan', 'Ban_Kiri_Depan', 'Ban_Kanan_Belakang', 'Ban_Kiri_Belakang', 'Ban_Serep'],
        "Eksterior & Body": ['Ext_Talang_Air', 'Ext_Plat_Belakang', 'Ext_Plat_Depan', 'Body_Depan', 'Body_Grill', 'Body_Fender'],
        "Pintu-Pintu": ['Pintu_D_Kanan', 'Pintu_D_Kiri', 'Pintu_B_Kanan', 'Pintu_B_Kiri', 'Pintu_Bagasi'],
        "Interior": ['Int_Jok', 'Int_Stir', 'Int_Karpet', 'Int_Persneling', 'Int_Rem_Tangan', 'Int_Dashboard', 'Int_AC'],
        "Mesin": ['Mesin_Oli', 'Mesin_Minyak_Rem', 'Mesin_Air_Radiator', 'Mesin_Air_Accu', 'Mesin_Air_Wiper'],
        "Lampu & Signal": ['Lampu_Utama', 'Lampu_Kecil', 'Lampu_Rem', 'Sein_Depan', 'Sein_Belakang'],
        "Kelengkapan": ['Kunci_Roda', 'Dongkrak', 'P3K', 'STNK']
    }
    for cat, fields in items.items():
        pdf.set_font("Arial", 'B', 9); pdf.cell(0, 6, cat, 1, 1, 'L'); pdf.set_font("Arial", size=9)
        for i in range(0, len(fields), 2):
            f1 = fields[i]; v1 = str(row.get(f1, '-')); pdf.cell(50, 6, f1.replace('_', ' '), 1)
            pdf.set_text_color(255,0,0) if v1 in ["Rusak","Hilang/Kurang"] else pdf.set_text_color(0,0,0); pdf.cell(45, 6, v1, 1); pdf.set_text_color(0,0,0)
            if i+1 < len(fields):
                f2 = fields[i+1]; v2 = str(row.get(f2, '-')); pdf.cell(50, 6, f2.replace('_', ' '), 1)
                pdf.set_text_color(255,0,0) if v2 in ["Rusak","Hilang/Kurang"] else pdf.set_text_color(0,0,0); pdf.cell(45, 6, v2, 1, 1); pdf.set_text_color(0,0,0)
            else: pdf.cell(95, 6, "", 1, 1)
    pdf.ln(5)
    
    # C. FOTO
    if 'Foto_Bukti' in row and not pd.isna(row['Foto_Bukti']) and len(str(row['Foto_Bukti'])) > 100:
        pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " C. DOKUMENTASI FOTO", 1, 1, 'L', fill=True)
        pdf.ln(2)
        try:
            img_data = base64.b64decode(row['Foto_Bukti'])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(img_data); tmp_path = tmp_file.name
            if pdf.get_y() > 200: pdf.add_page()
            pdf.image(tmp_path, x=10, w=90); pdf.ln(5)
            os.remove(tmp_path)
        except Exception:
            pdf.set_font("Arial", 'I', 9); pdf.cell(0, 10, f"(Gagal memuat foto)", 0, 1)
    pdf.ln(5)
    
    # D. CATATAN
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " D. CATATAN TAMBAHAN", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 6, str(row['Keterangan']), 1)
    pdf.ln(10)
    
    # E. TANDA TANGAN
    if pdf.get_y() > 230: pdf.add_page()
    y_sig = pdf.get_y(); pdf.set_font("Arial", '', 10)
    pdf.set_xy(10, y_sig); pdf.cell(90, 6, "Dibuat Oleh,", 0, 1, 'C'); pdf.set_xy(10, y_sig+6); pdf.cell(90, 6, "Petugas Pemeriksa", 0, 1, 'C')
    pdf.set_xy(110, y_sig); pdf.cell(90, 6, "Diketahui Oleh,", 0, 1, 'C'); pdf.set_xy(110, y_sig+6); pdf.cell(90, 6, "", 0, 1, 'C')
    pdf.ln(25); y_name = pdf.get_y()
    pdf.set_xy(10, y_name); pdf.set_font("Arial", 'B', 10); pdf.cell(90, 6, f"( {row['Nama_Security']} )", 0, 1, 'C')
    pdf.set_xy(110, y_name); pdf.cell(90, 6, "( ................................... )", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def render_item(label, value):
    badge = "badge-baik" if value=="Baik" else ("badge-rusak" if value=="Rusak" else "badge-hilang")
    st.markdown(f"<div><div style='font-size:0.85rem; color:#666;'>{label.replace('_',' ')}</div><span class='{badge}'>{value}</span></div>", unsafe_allow_html=True)

# ================= APLIKASI UTAMA =================
if check_login():
    USER_ROLE = st.session_state['user_role']; USER_NAME = st.session_state['user_fullname']

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=80)
        st.markdown(f"### Halo, {USER_NAME}"); st.caption(f"Role: {USER_ROLE}"); st.write("---")
        opt_list = ["Input Pemeriksaan", "Laporan Data"]
        ico_list = ["pencil-square", "file-earmark-pdf"]
        if USER_ROLE == "Administrator": opt_list.append("Dashboard & Kontrol"); ico_list.append("speedometer2")
        selected = option_menu(menu_title=None, options=opt_list, icons=ico_list, default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"}, "nav-link-selected": {"background-color": "#3B82F6"}})
        st.write("---"); 
        if st.button("🚪 Logout", use_container_width=True): st.session_state['logged_in'] = False; st.rerun()

    # --- INPUT ---
    if selected == "Input Pemeriksaan":
        st.markdown("<div class='header-title'>📝 Input Pemeriksaan Kendaraan</div>", unsafe_allow_html=True)
        df_mobil = get_data_mobil(); df_history = get_laporan_cek()
        nopol_disp = "-"; pilih_mobil = ""; tgl_last = "-"; st_color = "info-value-stack"

        with st.container():
            st.markdown("<div class='stCard'>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            with c1: st.markdown(f"<div class='info-box-row'><span class='label-text'>Pemeriksa :</span><span class='value-text'>{USER_NAME}</span></div>", unsafe_allow_html=True)
            with c2:
                if not df_mobil.empty:
                    pilih_mobil = st.selectbox("Unit", df_mobil['Nama_Mobil'].unique(), label_visibility="collapsed")
                    try:
                        r = df_mobil[df_mobil['Nama_Mobil'] == pilih_mobil]
                        if not r.empty: nopol_disp = r['Nomor_Polisi'].iloc[0]
                        if not df_history.empty:
                            h = df_history[df_history['Merk_Kendaraan'] == pilih_mobil]
                            if not h.empty:
                                h['Tanggal'] = pd.to_datetime(h['Tanggal'])
                                ld = h.sort_values('Tanggal', ascending=False).iloc[0]['Tanggal']
                                tgl_last = ld.strftime("%d-%b-%Y")
                                if (datetime.now() - ld).days > 14: st_color = "info-value-red"
                                else: st_color = "info-value-green"
                            else: tgl_last = "Belum Ada"; st_color = "info-value-red"
                    except: pass
                else: st.error("DB Error")
            with c3: km = st.number_input("KM", min_value=0, step=1, label_visibility="collapsed")
            with c4: tgl = st.date_input("Tanggal", datetime.now(), label_visibility="collapsed")
            st.write("")
            rc1, rc2 = st.columns(2)
            with rc1: st.markdown(f"<div class='info-box-stacked'><div class='info-label-stack'>Terakhir Dicek</div><div class='{st_color}'>{tgl_last}</div></div>", unsafe_allow_html=True)
            with rc2: st.markdown(f"<div class='info-box-stacked'><div class='info-label-stack'>Nomor Polisi</div><div class='info-value-stack'>{nopol_disp}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("#### 📋 Checklist Kondisi")
        with st.form("form_checklist"):
            def opsi(k): return st.radio(k, ["Baik", "Rusak", "Hilang/Kurang"], horizontal=True, label_visibility="collapsed", key=k)
            t1, t2, t3, t4, t5 = st.tabs(["🪟 Eksterior & Pintu", "🚗 Ban & Kaki-kaki", "🛋️ Interior", "⚙️ Mesin", "💡 Lampu & Kelengkapan"])
            
            with t1:
                ca, cb = st.columns(2)
                with ca: st.write("**Kaca Depan**"); kd=opsi("Kaca_Depan"); st.write("**Kaca Kiri**"); kk=opsi("Kaca_Kiri"); st.write("**Kaca Kanan**"); kka=opsi("Kaca_Kanan"); st.write("**Spion Kanan**"); sk=opsi("Spion_Kanan"); st.write("**Spion Kiri**"); ski=opsi("Spion_Kiri"); st.write("**Spion Dalam**"); sd=opsi("Spion_Dalam"); st.divider(); st.write("**Body Depan**"); bod=opsi("Body_Depan"); st.write("**Body Grill**"); bog=opsi("Body_Grill"); st.write("**Body Fender**"); bof=opsi("Body_Fender")
                with cb: st.write("**Talang Air**"); eta=opsi("Ext_Talang_Air"); st.write("**Plat Depan**"); epd=opsi("Ext_Plat_Depan"); st.write("**Plat Belakang**"); epb=opsi("Ext_Plat_Belakang"); st.divider(); st.write("**Pintu Depan Kanan**"); pdk=opsi("Pintu_D_Kanan"); st.write("**Pintu Depan Kiri**"); pdki=opsi("Pintu_D_Kiri"); st.write("**Pintu Belakang Kanan**"); pbk=opsi("Pintu_B_Kanan"); st.write("**Pintu Belakang Kiri**"); pbki=opsi("Pintu_B_Kiri"); st.write("**Pintu Bagasi**"); pbg=opsi("Pintu_Bagasi")
            with t2:
                cc, cd = st.columns(2)
                with cc: st.write("**Ban Kanan Depan**"); bkd=opsi("Ban_Kanan_Depan"); st.write("**Ban Kiri Depan**"); bkid=opsi("Ban_Kiri_Depan"); st.write("**Ban Serep**"); bs=opsi("Ban_Serep")
                with cd: st.write("**Ban Kanan Belakang**"); bkb=opsi("Ban_Kanan_Belakang"); st.write("**Ban Kiri Belakang**"); bkib=opsi("Ban_Kiri_Belakang")
            with t3:
                ce, cf = st.columns(2)
                with ce: st.write("**Jok**"); ij=opsi("Int_Jok"); st.write("**Setir**"); ist=opsi("Int_Stir"); st.write("**Karpet**"); ik=opsi("Int_Karpet"); st.write("**Persneling**"); ip=opsi("Int_Persneling")
                with cf: st.write("**Rem Tangan**"); irt=opsi("Int_Rem_Tangan"); st.write("**Dashboard**"); idb=opsi("Int_Dashboard"); st.write("**AC**"); iac=opsi("Int_AC")
            with t4:
                cg, ch = st.columns(2)
                with cg: st.write("**Oli Mesin**"); mo=opsi("Mesin_Oli"); st.write("**Minyak Rem**"); mmr=opsi("Mesin_Minyak_Rem"); st.write("**Air Radiator**"); mar=opsi("Mesin_Air_Radiator")
                with ch: st.write("**Air Accu**"); maa=opsi("Mesin_Air_Accu"); st.write("**Air Wiper**"); maw=opsi("Mesin_Air_Wiper")
            with t5:
                ci, cj = st.columns(2)
                with ci: st.write("**Lampu Utama**"); lu=opsi("Lampu_Utama"); st.write("**Lampu Kecil**"); lk=opsi("Lampu_Kecil"); st.write("**Lampu Rem**"); lr=opsi("Lampu_Rem"); st.write("**Sein Depan**"); snd=opsi("Sein_Depan"); st.write("**Sein Belakang**"); snb=opsi("Sein_Belakang")
                with cj: st.write("**Kunci Roda**"); kr=opsi("Kunci_Roda"); st.write("**Dongkrak**"); dg=opsi("Dongkrak"); st.write("**P3K**"); p3k=opsi("Kotak P3K"); st.write("**STNK**"); stnk=opsi("STNK")

            st.write("---")
            st.markdown("##### 📸 Dokumentasi Foto")
            up_file = st.file_uploader("Upload Foto Bukti (Max 1 Foto)", type=['jpg','png','jpeg'])
            st.write("---")
            st.warning("📝 CATATAN TAMBAHAN")
            ket = st.text_area("Keterangan", label_visibility="collapsed", height=100)
            
            if st.form_submit_button("💾 SIMPAN DATA", type="primary", use_container_width=True):
                if nopol_disp == "-" or (not df_mobil.empty and pilih_mobil == ""): st.warning("⚠️ Pilih unit kendaraan.")
                else:
                    foto_b64 = compress_image(up_file) if up_file else ""
                    row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Nama_Security": USER_NAME, "Tanggal": tgl.strftime("%Y-%m-%d"),
                        "Merk_Kendaraan": pilih_mobil, "Nomor_Polisi": nopol_disp, "Kilometer": km,
                        "Kaca_Depan": kd, "Kaca_Kiri": kk, "Kaca_Kanan": kka, "Spion_Kanan": sk, "Spion_Kiri": ski, "Spion_Dalam": sd,
                        "Ban_Kanan_Depan": bkd, "Ban_Kiri_Depan": bkid, "Ban_Kanan_Belakang": bkb, "Ban_Kiri_Belakang": bkib, "Ban_Serep": bs,
                        "Ext_Talang_Air": eta, "Ext_Plat_Belakang": epb, "Ext_Plat_Depan": epd, "Body_Depan": bod, "Body_Grill": bog, "Body_Fender": bof,
                        "Pintu_D_Kanan": pdk, "Pintu_D_Kiri": pdki, "Pintu_B_Kanan": pbk, "Pintu_B_Kiri": pbki, "Pintu_Bagasi": pbg,
                        "Int_Jok": ij, "Int_Stir": ist, "Int_Karpet": ik, "Int_Persneling": ip, "Int_Rem_Tangan": irt, "Int_Dashboard": idb, "Int_AC": iac,
                        "Mesin_Oli": mo, "Mesin_Minyak_Rem": mmr, "Mesin_Air_Radiator": mar, "Mesin_Air_Accu": maa, "Mesin_Air_Wiper": maw,
                        "Lampu_Utama": lu, "Lampu_Kecil": lk, "Lampu_Rem": lr, "Sein_Depan": snd, "Sein_Belakang": snb,
                        "Kunci_Roda": kr, "Dongkrak": dg, "P3K": p3k, "STNK": stnk, 
                        "Keterangan": ket, "Foto_Bukti": foto_b64
                    }])
                    try:
                        ex = conn.read(worksheet="data_cek", ttl=0)
                        if 'Foto_Bukti' not in ex.columns: ex['Foto_Bukti'] = ""
                        conn.update(worksheet="data_cek", data=pd.concat([ex, row], ignore_index=True))
                        st.success("✅ Tersimpan!"); st.balloons()
                    except Exception as e: st.error(f"Gagal: {e}")

    # --- LAPORAN ---
    elif selected == "Laporan Data":
        st.markdown("<div class='header-title'>🖨️ Laporan Data</div>", unsafe_allow_html=True)
        df_lap = get_laporan_cek()
        if not df_lap.empty:
            df_lap['Tanggal'] = pd.to_datetime(df_lap['Tanggal']); df_lap = df_lap.sort_values('Timestamp', ascending=False)
            with st.container():
                st.markdown("<div class='stCard'>", unsafe_allow_html=True); fc1, fc2 = st.columns(2)
                with fc1: fm = st.multiselect("Unit Mobil", df_lap['Merk_Kendaraan'].unique())
                with fc2: fb = st.selectbox("Periode", ["Semua"] + sorted(df_lap['Tanggal'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
                st.markdown("</div>", unsafe_allow_html=True)
            v = df_lap.copy()
            if fm: v = v[v['Merk_Kendaraan'].isin(fm)]
            if fb != "Semua": v = v[v['Tanggal'].dt.strftime('%Y-%m') == fb]
            
            if len(v) > 0:
                pid = st.selectbox("Pilih Riwayat:", v.index, format_func=lambda x: f"{v.loc[x,'Tanggal'].date()} | {v.loc[x,'Merk_Kendaraan']} | {v.loc[x,'Nama_Security']}")
                row = v.loc[pid]
                with st.container():
                    st.markdown(f"<div class='stCard' style='border-left:5px solid #3B82F6;'><h3>📑 Detail</h3><p>Tgl: {row['Tanggal'].date()} | Nopol: {row['Nomor_Polisi']} | User: {row['Nama_Security']}</p></div>", unsafe_allow_html=True)
                    if 'Foto_Bukti' in row and row['Foto_Bukti'] and len(str(row['Foto_Bukti'])) > 50:
                        try: st.image(base64.b64decode(row['Foto_Bukti']), width=300, caption="Foto Bukti")
                        except: pass
                    items_map = {"Kaca & Spion":['Kaca_Depan','Kaca_Kiri','Kaca_Kanan','Spion_Kanan','Spion_Kiri','Spion_Dalam'], "Ban & Roda":['Ban_Kanan_Depan','Ban_Kiri_Depan','Ban_Kanan_Belakang','Ban_Kiri_Belakang','Ban_Serep'], "Eksterior":['Ext_Talang_Air','Ext_Plat_Belakang','Ext_Plat_Depan','Body_Depan','Body_Grill','Body_Fender'], "Pintu":['Pintu_D_Kanan','Pintu_D_Kiri','Pintu_B_Kanan','Pintu_B_Kiri','Pintu_Bagasi'], "Interior":['Int_Jok','Int_Stir','Int_Karpet','Int_Persneling','Int_Rem_Tangan','Int_Dashboard','Int_AC'], "Mesin":['Mesin_Oli','Mesin_Minyak_Rem','Mesin_Air_Radiator','Mesin_Air_Accu','Mesin_Air_Wiper'], "Lampu":['Lampu_Utama','Lampu_Kecil','Lampu_Rem','Sein_Depan','Sein_Belakang'], "Kelengkapan":['Kunci_Roda','Dongkrak','P3K','STNK']}
                    for cat, cols in items_map.items():
                        st.markdown(f"##### {cat}"); cl = st.columns(4)
                        for i, cn in enumerate(cols): 
                            with cl[i%4]: render_item(cn, row.get(cn, "-"))
                        st.divider()
                    st.warning(f"📝 NOTE: {row['Keterangan']}")
                    if st.button("📄 DOWNLOAD PDF", type="primary"): st.download_button("⬇️ Unduh", create_pdf(row), f"Laporan Pengecekan Kendaraan.pdf", "application/pdf")
            else: st.info("Data Kosong")
        else: st.info("DB Kosong")
    
    # --- DASHBOARD & KONTROL ---
    elif selected == "Dashboard & Kontrol":
        st.markdown("<div class='header-title'>📊 Dashboard & Kontrol Unit</div>", unsafe_allow_html=True)
        df_history = get_laporan_cek(); df_mobil = get_data_mobil()
        
        if not df_history.empty and not df_mobil.empty:
            df_history['Tanggal'] = pd.to_datetime(df_history['Tanggal'])
            
            # KPI CALCULATION
            total_armada = len(df_mobil); total_history = len(df_history)
            today = datetime.now(); overdue_count = 0; unit_sehat_count = 0; unit_rusak_list = []

            for _, row_m in df_mobil.iterrows():
                nm = row_m['Nama_Mobil']
                h = df_history[df_history['Merk_Kendaraan'] == nm]
                if not h.empty:
                    last_rec = h.sort_values('Tanggal', ascending=False).iloc[0]; last_date = last_rec['Tanggal']
                    if (today - last_date).days > 14: overdue_count += 1
                    
                    cols_check = [c for c in df_history.columns if c not in ['Timestamp','Nama_Security','Tanggal','Merk_Kendaraan','Nomor_Polisi','Kilometer','Keterangan', 'Foto_Bukti']]
                    is_rusak = False
                    for c in cols_check:
                        if last_rec.get(c) in ["Rusak", "Hilang/Kurang"]: is_rusak = True; break
                    
                    if is_rusak: unit_rusak_list.append({"Unit": nm, "Tgl": last_date.strftime("%d-%m-%Y"), "Inspector": last_rec['Nama_Security'], "Note": last_rec['Keterangan']})
                    else: unit_sehat_count += 1
                else: overdue_count += 1
            
            kp1, kp2, kp3, kp4 = st.columns(4)
            with kp1: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_armada}</div><div class='metric-label'>Total Armada</div></div>", unsafe_allow_html=True)
            with kp2: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#166534'>{unit_sehat_count}</div><div class='metric-label'>Unit Sehat</div></div>", unsafe_allow_html=True)
            with kp3: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#DC2626'>{len(unit_rusak_list)}</div><div class='metric-label'>Perlu Perbaikan</div></div>", unsafe_allow_html=True)
            with kp4: st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#D97706'>{overdue_count}</div><div class='metric-label'>Telat Cek (>14 Hr)</div></div>", unsafe_allow_html=True)
            
            st.write("---")
            
            t_jadwal, t_rusak, t_stats = st.tabs(["📅 Kontrol Jadwal", "🛠️ Unit Bermasalah", "📈 Statistik"])
            
            with t_jadwal:
                st.subheader("📋 Status Kepatuhan")
                status_data = []
                for index, row in df_mobil.iterrows():
                    nama_mobil = row['Nama_Mobil']; nopol = row['Nomor_Polisi']
                    hist = df_history[df_history['Merk_Kendaraan'] == nama_mobil]
                    if not hist.empty:
                        last_check = hist.sort_values('Tanggal', ascending=False).iloc[0]['Tanggal']; days_diff = (today - last_check).days
                        if days_diff <= 14: status = "✅ OK"; ket_stat = f"{days_diff} hari lalu"
                        else: status = "⚠️ TELAT"; ket_stat = f"Telat {days_diff} hari"
                        tgl_str = last_check.strftime("%d-%b-%Y")
                    else: status = "❌ BELUM"; tgl_str = "-"; ket_stat = "Belum pernah cek"; days_diff = 999
                    status_data.append({"Unit": nama_mobil, "Plat": nopol, "Terakhir Cek": tgl_str, "Status": status, "Ket": ket_stat, "s": days_diff})
                
                df_stat = pd.DataFrame(status_data).sort_values('s', ascending=False)
                if st.checkbox("Tampilkan Hanya yang Telat"): df_stat = df_stat[df_stat['s'] > 14]
                st.dataframe(df_stat[['Unit', 'Plat', 'Terakhir Cek', 'Status', 'Ket']], use_container_width=True, hide_index=True)
            
            with t_rusak:
                st.subheader("🛠️ Daftar Unit Sedang Bermasalah")
                if unit_rusak_list: st.dataframe(pd.DataFrame(unit_rusak_list), use_container_width=True, hide_index=True)
                else: st.success("🎉 Tidak ada unit yang sedang rusak.")
            
            with t_stats:
                st.subheader("📈 Tren Kerusakan")
                cols_check = [c for c in df_history.columns if c not in ['Timestamp','Nama_Security','Tanggal','Merk_Kendaraan','Nomor_Polisi','Kilometer','Keterangan', 'Foto_Bukti']]
                rusak_per_item = {}
                for idx, r in df_history.iterrows():
                    for c in cols_check:
                        if r[c] in ["Rusak", "Hilang/Kurang"]: rusak_per_item[c] = rusak_per_item.get(c, 0) + 1
                if rusak_per_item: st.bar_chart(pd.DataFrame(list(rusak_per_item.items()), columns=['Komponen', 'Jml']).set_index('Komponen'))
                else: st.info("Belum ada data kerusakan.")

        else: st.info("Database masih kosong.")