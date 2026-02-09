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
import requests

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Pengecekan Kendaraan | BP3MI Jawa Tengah",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. KONFIGURASI API (Ganti API KEY DISINI) ---
IMGBB_API_KEY = "PASTE_API_KEY_IMGBB_ANDA_DISINI"

# --- 3. CSS CUSTOM (ELEGANT THEME DARI REV.PY) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    :root { 
        --bg-card: #ffffff; 
        --text-main: #0F172A; 
        --accent: #2563EB; /* Biru Royal */
    }

    /* Login Container Styling */
    .login-box {
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #F1F5F9;
        text-align: center;
    }
    
    .header-title {
        color: var(--accent);
        font-weight: 800;
        font-size: 26px;
        letter-spacing: -0.5px;
        margin-bottom: 5px;
    }

    .stCard {
        background-color: #FFFFFF; padding: 20px; border-radius: 12px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    .info-box-stacked {
        background-color: #F8FAFC; padding: 12px; border-radius: 10px;
        border: 1px solid #E2E8F0; text-align: center;
    }
    
    .info-label-stack { font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;}
    .info-value-stack { font-size: 1.1rem; font-weight: 700; color: #0F172A; }
    .info-value-red { font-size: 1.1rem; font-weight: 700; color: #EF4444; } 
    .info-value-green { font-size: 1.1rem; font-weight: 700; color: #166534; } 

    .badge-baik { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 8px; font-weight: 600; font-size: 0.85rem;}
    .badge-rusak { background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 8px; font-weight: 600; font-size: 0.85rem;}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }

    div.row-widget.stRadio > div { background-color: transparent !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. FUNGSI UTILITIES ---
def upload_to_imgbb(uploaded_files, api_key):
    if not uploaded_files: return ""
    links = []
    for file in uploaded_files:
        try:
            file_bytes = file.read()
            payload = {"key": api_key, "image": base64.b64encode(file_bytes)}
            response = requests.post("https://api.imgbb.com/1/upload", payload)
            res_json = response.json()
            if res_json['success']: links.append(res_json['data']['url'])
            file.seek(0)
        except Exception as e: st.error(f"Gagal upload: {e}")
    return "\n".join(links)

def get_users_db():
    try:
        df = conn.read(worksheet="users", ttl=0)
        df['Username'] = df['Username'].astype(str).str.strip()
        df['Password'] = df['Password'].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def get_data_mobil():
    try:
        df = conn.read(worksheet="daftar_mobil", ttl=0)
        df.columns = df.columns.str.strip()
        return df[['Nama_Mobil', 'Nomor_Polisi']].dropna()
    except: return pd.DataFrame()

def get_laporan_cek():
    try: return conn.read(worksheet="data_cek", ttl=0)
    except: return pd.DataFrame()

# --- 6. HALAMAN LOGIN (DESAIN REV.PY) ---
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = ""
        st.session_state['user_fullname'] = ""

    if not st.session_state['logged_in']:
        _, col2, _ = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
                <div class='login-box'>
                    <div class='header-title'>KENDARAAN BMN</div>
                    <div style='color: #64748B; font-weight: 400; margin-bottom: 20px;'>BP3MI Jawa Tengah</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown("<div style='margin-top:-15px'>", unsafe_allow_html=True)
                user_input = st.text_input("Username", placeholder="Masukkan ID")
                pass_input = st.text_input("Password", type="password", placeholder="••••••••")
                if st.button("MASUK SISTEM", type="primary", use_container_width=True):
                    df_users = get_users_db()
                    user = df_users[(df_users['Username'] == user_input) & (df_users['Password'] == pass_input)]
                    if not user.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = user.iloc[0]['Role']
                        st.session_state['user_fullname'] = user.iloc[0]['Nama_Lengkap']
                        st.rerun()
                    else:
                        st.error("Kredensial salah.")
                st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

# --- 7. FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Laporan Pemeriksaan Kendaraan Operasional | BP3MI Jawa Tengah', 0, 1, 'C')
        self.ln(3)

def create_pdf(row, image_files=None):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    # Detail Section
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " A. INFORMASI UMUM", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10)
    info = [("Tanggal", str(row['Tanggal'])), ("Pemeriksa", str(row['Nama_Security'])), ("Kendaraan", f"{row['Merk_Kendaraan']} ({row['Nomor_Polisi']})"), ("Kilometer", f"{row['Kilometer']} km")]
    for l, v in info: pdf.cell(45, 7, l, 1); pdf.cell(145, 7, v, 1, 1)
    
    # Foto Section
    if image_files:
        pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " C. DOKUMENTASI FOTO", 1, 1, 'L', fill=True); pdf.ln(2)
        for img_file in image_files:
            img = Image.open(img_file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp, format='JPEG', quality=70)
                if pdf.get_y() > 220: pdf.add_page()
                pdf.image(tmp.name, x=10, w=80); pdf.ln(60)
                os.remove(tmp.name)
    return pdf.output(dest='S').encode('latin-1')

def render_item(label, value):
    badge = "badge-baik" if value=="Baik" else "badge-rusak"
    st.markdown(f"<div><div style='font-size:0.85rem; color:#666;'>{label.replace('_',' ')}</div><span class='{badge}'>{value}</span></div>", unsafe_allow_html=True)

# ================= APLIKASI UTAMA =================
if check_login():
    USER_ROLE = st.session_state['user_role']
    USER_NAME = st.session_state['user_fullname']

    # --- SIDEBAR (DESAIN REV.PY) ---
    with st.sidebar:
        st.markdown(f"""
            <div style='text-align: center; padding: 10px;'>
                <div style='font-size: 20px; font-weight: 800; color: #2563EB;'>V-INSPECTOR</div>
                <div style='font-size: 12px; color: #64748B;'>BP3MI Jawa Tengah</div>
            </div>
            <hr style='margin: 10px 0;'>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**👤 {USER_NAME}**")
        st.caption(f"Role: {USER_ROLE}")
        
        # Menu Navigasi
        menu_options = ["Input Pemeriksaan", "Laporan Data"]
        menu_icons = ["pencil-square", "file-earmark-text"]
        
        if USER_ROLE == "Administrator":
            menu_options.append("Dashboard & Kontrol")
            menu_icons.append("speedometer2")
            
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#EFF6FF"},
                "nav-link-selected": {"background-color": "#2563EB", "font-weight": "600"},
            }
        )
        
        st.write("---")
        if st.button("Keluar Sistem", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- HALAMAN 1: INPUT ---
    if selected == "Input Pemeriksaan":
        st.markdown(f"<h2 style='color:#2563EB'>📝 Input Pemeriksaan</h2>", unsafe_allow_html=True)
        df_mobil = get_data_mobil(); df_history = get_laporan_cek()
        nopol_disp = "-"; tgl_last = "-"; st_color = "info-value-stack"

        with st.container():
            st.markdown("<div class='stCard'>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            with c1: st.markdown(f"<div class='info-box-row'><span class='label-text'>Pemeriksa :</span><span class='value-text'>{USER_NAME}</span></div>", unsafe_allow_html=True)
            with c2:
                pilih_mobil = st.selectbox("Unit", df_mobil['Nama_Mobil'].unique(), label_visibility="collapsed")
                r_mob = df_mobil[df_mobil['Nama_Mobil'] == pilih_mobil]
                nopol_disp = r_mob['Nomor_Polisi'].iloc[0] if not r_mob.empty else "-"
                if not df_history.empty:
                    h = df_history[df_history['Merk_Kendaraan'] == pilih_mobil]
                    if not h.empty:
                        ld = pd.to_datetime(h.sort_values('Tanggal', ascending=False).iloc[0]['Tanggal'])
                        tgl_last = ld.strftime("%d-%b-%Y")
                        st_color = "info-value-red" if (datetime.now() - ld).days > 14 else "info-value-green"
                    else: tgl_last = "Belum Ada"; st_color = "info-value-red"
            with c3: km = st.number_input("KM", min_value=0, step=1, label_visibility="collapsed")
            with c4: tgl = st.date_input("Tgl", datetime.now(), label_visibility="collapsed")
            
            st.write(""); rc1, rc2 = st.columns(2)
            with rc1: st.markdown(f"<div class='info-box-stacked'><div class='info-label-stack'>Terakhir Cek</div><div class='{st_color}'>{tgl_last}</div></div>", unsafe_allow_html=True)
            with rc2: st.markdown(f"<div class='info-box-stacked'><div class='info-label-stack'>Nopol</div><div class='info-value-stack'>{nopol_disp}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with st.form("form_inspection"):
            def opsi(k): return st.radio(k, ["Baik", "Rusak"], horizontal=True, label_visibility="collapsed", key=k)
            t1, t2, t3, t4, t5 = st.tabs(["🪟 Eksterior", "🚗 Ban", "🛋️ Interior", "⚙️ Mesin", "💡 Lampu"])
            # (Tab details remain the same as your app.py functional code)
            with t1:
                col_a, col_b = st.columns(2)
                with col_a: st.write("**Kaca Depan**"); kd=opsi("Kaca_Depan"); st.write("**Body Depan**"); bd=opsi("Body_Depan")
                with col_b: st.write("**Pintu Kanan**"); pk=opsi("Pintu_Kanan"); st.write("**Pintu Kiri**"); pki=opsi("Pintu_Kiri")
            # ... (Lengkapi tab lainnya sesuai kebutuhan parameter Anda)
            
            st.markdown("##### 📸 Foto Dokumentasi")
            up_files = st.file_uploader("Upload Foto (Multiple)", accept_multiple_files=True)
            ket = st.text_area("Catatan Tambahan")
            
            if st.form_submit_button("SIMPAN DATA", type="primary", use_container_width=True):
                with st.spinner("Proses simpan..."):
                    links = upload_to_imgbb(up_files, IMGBB_API_KEY)
                    # Logika Append ke GSheet (Sesuai kolom database Anda)
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Nama_Security": USER_NAME, "Tanggal": tgl.strftime("%Y-%m-%d"),
                        "Merk_Kendaraan": pilih_mobil, "Nomor_Polisi": nopol_disp, "Kilometer": km,
                        "Kaca_Depan": kd, "Body_Depan": bd, "Pintu_Kanan": pk, "Pintu_Kiri": pki,
                        "Keterangan": ket, "Foto_Bukti": links
                    }])
                    ex = get_laporan_cek()
                    conn.update(worksheet="data_cek", data=pd.concat([ex, new_data], ignore_index=True))
                    st.success("Data Tersimpan!")
                    st.download_button("Download PDF", create_pdf(new_data.iloc[0], up_files), f"Cek_{nopol_disp}.pdf")

    # --- HALAMAN 2: LAPORAN ---
    elif selected == "Laporan Data":
        st.markdown(f"<h2 style='color:#2563EB'>📋 Riwayat Pemeriksaan</h2>", unsafe_allow_html=True)
        df_lap = get_laporan_cek()
        if not df_lap.empty:
            df_lap['Tanggal'] = pd.to_datetime(df_lap['Tanggal'])
            df_lap = df_lap.sort_values('Timestamp', ascending=False)
            
            # Filter bar
            st.markdown("<div class='stCard'>", unsafe_allow_html=True)
            f1, f2 = st.columns(2)
            with f1: f_mob = st.multiselect("Filter Unit", df_lap['Merk_Kendaraan'].unique())
            with f2: f_bln = st.selectbox("Periode", ["Semua"] + sorted(df_lap['Tanggal'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
            st.markdown("</div>", unsafe_allow_html=True)
            
            v = df_lap.copy()
            if f_mob: v = v[v['Merk_Kendaraan'].isin(f_mob)]
            if f_bln != "Semua": v = v[v['Tanggal'].dt.strftime('%Y-%m') == f_bln]
            
            st.dataframe(v[['Tanggal', 'Merk_Kendaraan', 'Nomor_Polisi', 'Nama_Security', 'Kilometer']], use_container_width=True, hide_index=True)

    # --- HALAMAN 3: DASHBOARD ---
    elif selected == "Dashboard & Kontrol":
        st.markdown(f"<h2 style='color:#2563EB'>📊 Monitoring Armada</h2>", unsafe_allow_html=True)
        # Tambahkan statistik metric seperti di rev.py
        st.info("Dashboard analisis kerusakan unit.")