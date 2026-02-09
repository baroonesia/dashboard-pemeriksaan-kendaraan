import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_option_menu import option_menu

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Vehicle Inspector Pro",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM (UI MODERN & STATUS BADGE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Login & Card Styling */
    .login-container {
        background-color: white; padding: 40px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
    }
    .stCard {
        background-color: #FFFFFF; padding: 20px; border-radius: 10px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #EFF6FF; border-left: 5px solid #3B82F6;
        padding: 15px; border-radius: 5px; color: #1E3A8A; font-weight: 600;
    }
    .warning-box {
        background-color: #FEF2F2; border-left: 5px solid #EF4444;
        padding: 15px; border-radius: 5px; color: #991B1B; font-weight: 600;
        margin-top: 20px;
    }
    .header-title { font-size: 1.5rem; font-weight: 700; color: #1E293B; }
    
    /* STATUS BADGES (Indikator Warna) */
    .badge-baik {
        background-color: #DCFCE7; color: #166534; 
        padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;
        border: 1px solid #BBF7D0;
    }
    .badge-rusak {
        background-color: #FEE2E2; color: #991B1B; 
        padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;
        border: 1px solid #FECACA;
    }
    .badge-hilang {
        background-color: #FEF9C3; color: #854D0E; 
        padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;
        border: 1px solid #FEF08A;
    }
    .item-label {
        font-size: 0.9rem; color: #64748B; margin-bottom: 2px;
    }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    div.row-widget.stRadio > div {flex-direction: row;}
</style>
""", unsafe_allow_html=True)

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNGSI LOAD DATA ---
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
        if 'Nama_Mobil' in df.columns and 'Nomor_Polisi' in df.columns:
            return df[['Nama_Mobil', 'Nomor_Polisi']].dropna()
    except: pass
    return pd.DataFrame()

def get_laporan_cek():
    try: return conn.read(worksheet="data_cek", ttl=0)
    except: return pd.DataFrame()

# --- FUNGSI LOGIN ---
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = ""
        st.session_state['user_fullname'] = ""
    
    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""<div class='login-container'><h2>🚘 Vehicle Inspector</h2><p style='color:gray;'>Silakan masuk untuk melanjutkan</p></div>""", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            if st.button("Masuk Sistem", type="primary", use_container_width=True):
                df_users = get_users_db()
                if not df_users.empty:
                    user = df_users[(df_users['Username'] == username) & (df_users['Password'] == password)]
                    if not user.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = user.iloc[0]['Role']
                        st.session_state['user_fullname'] = user.iloc[0]['Nama_Lengkap']
                        st.rerun()
                    else: st.error("Username atau Password salah.")
                else: st.error("Database user error.")
        return False
    return True

# --- FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'LAPORAN PEMERIKSAAN KENDARAAN', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def create_pdf(row):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    
    # A. INFO UMUM
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " A. INFORMASI UMUM", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10)
    
    info = [
        ("Tanggal", str(row['Tanggal'])), ("Pemeriksa", str(row['Nama_Security'])),
        ("Kendaraan", f"{row['Merk_Kendaraan']} ({row['Nomor_Polisi']})"), ("Kilometer", f"{row['Kilometer']} km")
    ]
    for l, v in info: pdf.cell(45, 7, l, 1); pdf.cell(145, 7, v, 1, 1)
    pdf.ln(5)
    
    # B. DETAIL KONDISI
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " B. DETAIL KONDISI", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=9)
    
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
        pdf.set_font("Arial", 'B', 9); pdf.cell(0, 6, cat, 1, 1, 'L')
        pdf.set_font("Arial", size=9)
        for i in range(0, len(fields), 2):
            f1 = fields[i]; v1 = str(row.get(f1, '-'))
            pdf.cell(50, 6, f1.replace('_', ' '), 1)
            pdf.set_text_color(255,0,0) if v1 in ["Rusak","Hilang/Kurang"] else pdf.set_text_color(0,0,0)
            pdf.cell(45, 6, v1, 1)
            pdf.set_text_color(0,0,0)
            
            if i+1 < len(fields):
                f2 = fields[i+1]; v2 = str(row.get(f2, '-'))
                pdf.cell(50, 6, f2.replace('_', ' '), 1)
                pdf.set_text_color(255,0,0) if v2 in ["Rusak","Hilang/Kurang"] else pdf.set_text_color(0,0,0)
                pdf.cell(45, 6, v2, 1, 1)
                pdf.set_text_color(0,0,0)
            else: pdf.cell(95, 6, "", 1, 1)
            
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " C. CATATAN TAMBAHAN", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 6, str(row['Keterangan']), 1)
    return pdf.output(dest='S').encode('latin-1')

# --- HELPER VIEW ---
def render_item(label, value):
    # Tentukan Warna Badge
    if value == "Baik":
        badge_class = "badge-baik"
    elif value == "Rusak":
        badge_class = "badge-rusak"
    else:
        badge_class = "badge-hilang"
    
    st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div class="item-label">{label.replace('_', ' ')}</div>
            <span class="{badge_class}">{value}</span>
        </div>
    """, unsafe_allow_html=True)

# ================= APLIKASI UTAMA =================
if check_login():
    USER_ROLE = st.session_state['user_role']
    USER_NAME = st.session_state['user_fullname']

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
        st.markdown(f"### Halo, {USER_NAME}")
        st.caption(f"Role: {USER_ROLE}")
        st.write("---")
        
        opt_list = ["Input Pemeriksaan"]
        ico_list = ["pencil-square"]
        if USER_ROLE == "Administrator":
            opt_list.append("Laporan Data")
            ico_list.append("file-earmark-pdf")
            
        selected = option_menu(
            menu_title=None, options=opt_list, icons=ico_list, default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#3B82F6", "font-size": "18px"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#EFF6FF"},
                "nav-link-selected": {"background-color": "#3B82F6"},
            }
        )
        st.write("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

    # --- HALAMAN 1: INPUT PEMERIKSAAN ---
    if selected == "Input Pemeriksaan":
        st.markdown("<div class='header-title'>📝 Input Pemeriksaan Kendaraan</div>", unsafe_allow_html=True)
        st.markdown("Isi checklist kondisi di bawah.", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='stCard'>", unsafe_allow_html=True)
            df_mobil = get_data_mobil()
            c1, c2, c3 = st.columns([1, 1.5, 1])
            with c1:
                st.text_input("👮 Pemeriksa", value=USER_NAME, disabled=True)
                tanggal = st.date_input("📅 Tanggal", datetime.now())
            with c2:
                nopol_display = "-"
                pilih_mobil = ""
                if not df_mobil.empty:
                    pilih_mobil = st.selectbox("🚘 Pilih Unit", df_mobil['Nama_Mobil'].unique())
                    try:
                        row = df_mobil[df_mobil['Nama_Mobil'] == pilih_mobil]
                        if not row.empty: nopol_display = row['Nomor_Polisi'].iloc[0]
                    except: pass
                else: pilih_mobil = st.text_input("Nama Mobil")
                st.markdown(f"<div class='info-box'>Plat Nomor: {nopol_display}</div>", unsafe_allow_html=True)
            with c3:
                kilometer = st.number_input("📟 KM Saat Ini", min_value=0, step=1)
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("#### 📋 Checklist Kondisi")
        def opsi(k): return st.radio(k, ["Baik", "Rusak", "Hilang/Kurang"], horizontal=True, label_visibility="collapsed", key=k)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🪟 Eksterior & Pintu", "🚗 Ban & Kaki-kaki", "🛋️ Interior", "⚙️ Mesin", "💡 Lampu & Kelengkapan"])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Kaca Depan**"); kd = opsi("Kaca_Depan")
                st.write("**Kaca Kiri**"); kk = opsi("Kaca_Kiri")
                st.write("**Kaca Kanan**"); kka = opsi("Kaca_Kanan")
                st.write("**Spion Kanan**"); sk = opsi("Spion_Kanan")
                st.write("**Spion Kiri**"); ski = opsi("Spion_Kiri")
                st.write("**Spion Dalam**"); sd = opsi("Spion_Dalam")
                st.divider()
                st.write("**Body Depan**"); bod = opsi("Body_Depan")
                st.write("**Body Grill**"); bog = opsi("Body_Grill")
                st.write("**Body Fender**"); bof = opsi("Body_Fender")
            with col_b:
                st.write("**Ext. Talang Air**"); eta = opsi("Ext_Talang_Air")
                st.write("**Ext. Plat Depan**"); epd = opsi("Ext_Plat_Depan")
                st.write("**Ext. Plat Belakang**"); epb = opsi("Ext_Plat_Belakang")
                st.divider()
                st.write("**Pintu Depan Kanan**"); pdk = opsi("Pintu_D_Kanan")
                st.write("**Pintu Depan Kiri**"); pdki = opsi("Pintu_D_Kiri")
                st.write("**Pintu Blkg Kanan**"); pbk = opsi("Pintu_B_Kanan")
                st.write("**Pintu Blkg Kiri**"); pbki = opsi("Pintu_B_Kiri")
                st.write("**Pintu Bagasi**"); pbg = opsi("Pintu_Bagasi")

        with tab2:
            col_c, col_d = st.columns(2)
            with col_c:
                st.write("**Ban Kanan Depan**"); bkd = opsi("Ban_Kanan_Depan")
                st.write("**Ban Kiri Depan**"); bkid = opsi("Ban_Kiri_Depan")
                st.write("**Ban Serep**"); bs = opsi("Ban_Serep")
            with col_d:
                st.write("**Ban Kanan Belakang**"); bkb = opsi("Ban_Kanan_Belakang")
                st.write("**Ban Kiri Belakang**"); bkib = opsi("Ban_Kiri_Belakang")

        with tab3:
            col_e, col_f = st.columns(2)
            with col_e:
                st.write("**Jok**"); ij = opsi("Int_Jok")
                st.write("**Stir**"); ist = opsi("Int_Stir")
                st.write("**Karpet**"); ik = opsi("Int_Karpet")
                st.write("**Persneling**"); ip = opsi("Int_Persneling")
            with col_f:
                st.write("**Rem Tangan**"); irt = opsi("Int_Rem_Tangan")
                st.write("**Dashboard**"); idb = opsi("Int_Dashboard")
                st.write("**AC**"); iac = opsi("Int_AC")

        with tab4:
            col_g, col_h = st.columns(2)
            with col_g:
                st.write("**Oli Mesin**"); mo = opsi("Mesin_Oli")
                st.write("**Minyak Rem**"); mmr = opsi("Mesin_Minyak_Rem")
                st.write("**Air Radiator**"); mar = opsi("Mesin_Air_Radiator")
            with col_h:
                st.write("**Air Accu**"); maa = opsi("Mesin_Air_Accu")
                st.write("**Air Wiper**"); maw = opsi("Mesin_Air_Wiper")

        with tab5:
            col_i, col_j = st.columns(2)
            with col_i:
                st.write("**Lampu Utama**"); lu = opsi("Lampu_Utama")
                st.write("**Lampu Kecil**"); lk = opsi("Lampu_Kecil")
                st.write("**Lampu Rem**"); lr = opsi("Lampu_Rem")
                st.write("**Sein Depan**"); snd = opsi("Sein_Depan")
                st.write("**Sein Belakang**"); snb = opsi("Sein_Belakang")
            with col_j:
                st.write("**Kunci Roda**"); kr = opsi("Kunci_Roda")
                st.write("**Dongkrak**"); dg = opsi("Dongkrak")
                st.write("**P3K**"); p3k = opsi("P3K")
                st.write("**STNK**"); stnk = opsi("STNK")

        st.write("---")
        with st.container():
            st.markdown("""<div class='warning-box'>📝 CATATAN TAMBAHAN<br><span style='font-weight:400; font-size:0.9rem'>Jelaskan kerusakan detail di sini.</span></div>""", unsafe_allow_html=True)
            ket = st.text_area("Keterangan", label_visibility="collapsed", height=100)
        
        st.write("")
        if st.button("💾 SIMPAN DATA", type="primary", use_container_width=True):
            if nopol_display == "-": st.warning("⚠️ Pilih unit kendaraan.")
            else:
                row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Nama_Security": USER_NAME, "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Merk_Kendaraan": pilih_mobil, "Nomor_Polisi": nopol_display, "Kilometer": kilometer,
                    "Kaca_Depan": kd, "Kaca_Kiri": kk, "Kaca_Kanan": kka, "Spion_Kanan": sk, "Spion_Kiri": ski, "Spion_Dalam": sd,
                    "Ban_Kanan_Depan": bkd, "Ban_Kiri_Depan": bkid, "Ban_Kanan_Belakang": bkb, "Ban_Kiri_Belakang": bkib, "Ban_Serep": bs,
                    "Ext_Talang_Air": eta, "Ext_Plat_Belakang": epb, "Ext_Plat_Depan": epd, "Body_Depan": bod, "Body_Grill": bog, "Body_Fender": bof,
                    "Pintu_D_Kanan": pdk, "Pintu_D_Kiri": pdki, "Pintu_B_Kanan": pbk, "Pintu_B_Kiri": pbki, "Pintu_Bagasi": pbg,
                    "Int_Jok": ij, "Int_Stir": ist, "Int_Karpet": ik, "Int_Persneling": ip, "Int_Rem_Tangan": irt, "Int_Dashboard": idb, "Int_AC": iac,
                    "Mesin_Oli": mo, "Mesin_Minyak_Rem": mmr, "Mesin_Air_Radiator": mar, "Mesin_Air_Accu": maa, "Mesin_Air_Wiper": maw,
                    "Lampu_Utama": lu, "Lampu_Kecil": lk, "Lampu_Rem": lr, "Sein_Depan": snd, "Sein_Belakang": snb,
                    "Kunci_Roda": kr, "Dongkrak": dg, "P3K": p3k, "STNK": stnk, "Keterangan": ket
                }])
                try:
                    exist = conn.read(worksheet="data_cek", ttl=0)
                    upd = pd.concat([exist, row], ignore_index=True)
                    conn.update(worksheet="data_cek", data=upd)
                    st.success("✅ Tersimpan!"); st.balloons()
                except Exception as e: st.error(f"Gagal simpan: {e}")

    # --- HALAMAN 2: LAPORAN & DETAIL VIEW ---
    elif selected == "Laporan Data":
        st.markdown("<div class='header-title'>🖨️ Laporan & Kontrol Data</div>", unsafe_allow_html=True)
        
        df_lap = get_laporan_cek()
        if not df_lap.empty:
            df_lap['Tanggal'] = pd.to_datetime(df_lap['Tanggal'])
            df_lap = df_lap.sort_values('Timestamp', ascending=False)
            
            # --- 1. FILTER AREA ---
            with st.container():
                st.markdown("<div class='stCard'>", unsafe_allow_html=True)
                fc1, fc2 = st.columns(2)
                with fc1: f_mobil = st.multiselect("Unit Mobil", df_lap['Merk_Kendaraan'].unique())
                with fc2: f_bln = st.selectbox("Periode Bulan", ["Semua"] + sorted(df_lap['Tanggal'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Filter Logic
            view = df_lap.copy()
            if f_mobil: view = view[view['Merk_Kendaraan'].isin(f_mobil)]
            if f_bln != "Semua": view = view[view['Tanggal'].dt.strftime('%Y-%m') == f_bln]
            
            if len(view) == 0:
                st.info("Data tidak ditemukan.")
            else:
                # --- 2. SELECTOR (PILIH DATA) ---
                st.write("#### 🔍 Pilih Data Pemeriksaan")
                
                # Buat Label Dropdown yang Informatif
                pilihan_list = view.index.tolist()
                label_map = {i: f"{view.loc[i, 'Tanggal'].date()} | {view.loc[i, 'Merk_Kendaraan']} | {view.loc[i, 'Nama_Security']}" for i in pilihan_list}
                
                selected_id = st.selectbox("Pilih Riwayat:", pilihan_list, format_func=lambda x: label_map[x])
                
                st.write("---")
                
                # --- 3. DETAIL VIEW (FORM MODE) ---
                # Ambil satu baris data
                row = view.loc[selected_id]
                
                # Tampilkan Header Info
                with st.container():
                    st.markdown(f"""
                    <div class='stCard' style='border-left: 5px solid #3B82F6;'>
                        <h3>📑 Detail Pemeriksaan: {row['Merk_Kendaraan']}</h3>
                        <p>
                            <b>Tanggal:</b> {row['Tanggal'].date()} &nbsp;|&nbsp; 
                            <b>Nopol:</b> {row['Nomor_Polisi']} &nbsp;|&nbsp; 
                            <b>Inspector:</b> {row['Nama_Security']} &nbsp;|&nbsp; 
                            <b>KM:</b> {row['Kilometer']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Tampilkan Item per Kategori (Dengan Warna)
                items_map = {
                    "Kaca & Spion": ['Kaca_Depan', 'Kaca_Kiri', 'Kaca_Kanan', 'Spion_Kanan', 'Spion_Kiri', 'Spion_Dalam'],
                    "Ban & Roda": ['Ban_Kanan_Depan', 'Ban_Kiri_Depan', 'Ban_Kanan_Belakang', 'Ban_Kiri_Belakang', 'Ban_Serep'],
                    "Eksterior & Body": ['Ext_Talang_Air', 'Ext_Plat_Belakang', 'Ext_Plat_Depan', 'Body_Depan', 'Body_Grill', 'Body_Fender'],
                    "Pintu-Pintu": ['Pintu_D_Kanan', 'Pintu_D_Kiri', 'Pintu_B_Kanan', 'Pintu_B_Kiri', 'Pintu_Bagasi'],
                    "Interior": ['Int_Jok', 'Int_Stir', 'Int_Karpet', 'Int_Persneling', 'Int_Rem_Tangan', 'Int_Dashboard', 'Int_AC'],
                    "Mesin": ['Mesin_Oli', 'Mesin_Minyak_Rem', 'Mesin_Air_Radiator', 'Mesin_Air_Accu', 'Mesin_Air_Wiper'],
                    "Lampu & Signal": ['Lampu_Utama', 'Lampu_Kecil', 'Lampu_Rem', 'Sein_Depan', 'Sein_Belakang'],
                    "Kelengkapan": ['Kunci_Roda', 'Dongkrak', 'P3K', 'STNK']
                }

                # Looping Layout Grid
                for category, cols in items_map.items():
                    st.markdown(f"##### {category}")
                    columns = st.columns(4) # 4 Kolom per baris agar rapi
                    for idx, col_name in enumerate(cols):
                        val = row.get(col_name, "-")
                        with columns[idx % 4]:
                            render_item(col_name, val)
                    st.divider()
                
                # Catatan
                st.markdown(f"""
                <div class='warning-box'>
                    📝 CATATAN TAMBAHAN:<br>
                    {row['Keterangan'] if row['Keterangan'] else "-"}
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                # Tombol Download PDF untuk Data TERPILIH INI
                if st.button("📄 DOWNLOAD PDF LAPORAN INI", type="primary", use_container_width=True):
                    pdf_data = create_pdf(row)
                    st.download_button("⬇️ Klik Disini untuk Unduh", pdf_data, f"Laporan_{row['Merk_Kendaraan']}.pdf", "application/pdf")

        else: st.info("Belum ada data.")