import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_option_menu import option_menu
from PIL import Image
import io
import base64

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Vehicle Inspector Pro",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM (CLEAN UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .login-container {
        background-color: white; padding: 40px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
    }
    .stCard {
        background-color: #FFFFFF; padding: 20px; border-radius: 10px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC; border: 1px solid #E2E8F0;
        padding: 15px; border-radius: 10px; text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #3B82F6; }
    .metric-label { font-size: 0.9rem; color: #64748B; }

    /* Info Box Styling */
    .info-box-row {
        background-color: #F8FAFC; padding: 12px 15px; border-radius: 8px;
        border: 1px solid #E2E8F0; display: flex; align-items: center; gap: 10px;
        height: 100%;
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

    div.row-widget.stRadio > div {
        background-color: transparent !important;
        border: none !important;
    }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNGSI UTILITIES ---
def compress_image(image_file):
    """Mengubah file upload menjadi string base64 yang dikompres (agar muat di GSheet)"""
    if image_file is None:
        return ""
    try:
        image = Image.open(image_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize jika terlalu besar (Max lebar 500px)
        max_width = 500
        ratio = max_width / float(image.size[0])
        new_height = int((float(image.size[1]) * float(ratio)))
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Simpan ke buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=50) # Kompresi kualitas 50%
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        return ""

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
    
    # HEADER SECTION
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " A. INFORMASI UMUM", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10)
    
    info = [
        ("Tanggal", str(row['Tanggal'])), ("Pemeriksa", str(row['Nama_Security'])),
        ("Kendaraan", f"{row['Merk_Kendaraan']} ({row['Nomor_Polisi']})"), ("Kilometer", f"{row['Kilometer']} km")
    ]
    for l, v in info: pdf.cell(45, 7, l, 1); pdf.cell(145, 7, v, 1, 1)
    pdf.ln(5)
    
    # DETAIL SECTION
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
    
    pdf.ln(5)
    
    # FOTO DOKUMENTASI (Jika Ada)
    if 'Foto_Bukti' in row and row['Foto_Bukti'] and len(str(row['Foto_Bukti'])) > 10:
        pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " C. DOKUMENTASI FOTO", 1, 1, 'L', fill=True)
        try:
            # Decode Base64 ke Image
            img_data = base64.b64decode(row['Foto_Bukti'])
            img_stream = io.BytesIO(img_data)
            # Simpan sementara di memori PDF
            pdf.image(img_stream, x=10, w=90) # Lebar 90mm
            pdf.ln(5)
        except:
            pdf.cell(0, 10, "(Gagal memuat foto)", 0, 1)
    
    pdf.ln(5)
    
    # CATATAN
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, " D. CATATAN TAMBAHAN", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 6, str(row['Keterangan']), 1)
    
    pdf.ln(10)
    
    # KOLOM TANDA TANGAN (LAYOUT RAPI)
    y_sig = pdf.get_y()
    
    # Cek jika halaman tidak cukup, pindah halaman
    if y_sig > 240: 
        pdf.add_page()
        y_sig = pdf.get_y()

    pdf.set_font("Arial", '', 10)
    
    # Kolom Kiri: Dibuat Oleh
    pdf.set_xy(10, y_sig)
    pdf.cell(90, 6, "Dibuat Oleh,", 0, 1, 'C')
    pdf.set_xy(10, y_sig + 6)
    pdf.cell(90, 6, "Petugas Pemeriksa", 0, 1, 'C')
    
    # Kolom Kanan: Diketahui Oleh
    pdf.set_xy(110, y_sig)
    pdf.cell(90, 6, "Diketahui Oleh,", 0, 1, 'C')
    pdf.set_xy(110, y_sig + 6)
    pdf.cell(90, 6, "Kepala Bagian / Admin", 0, 1, 'C')
    
    # Space Tanda Tangan
    pdf.ln(25)
    y_name = pdf.get_y()
    
    # Nama Penanda Tangan
    pdf.set_xy(10, y_name)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 6, f"( {row['Nama_Security']} )", 0, 1, 'C')
    
    pdf.set_xy(110, y_name)
    pdf.cell(90, 6, "( ................................... )", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

def render_item(label, value):
    badge_class = "badge-baik" if value == "Baik" else ("badge-rusak" if value == "Rusak" else "badge-hilang")
    st.markdown(f"""<div style="margin-bottom: 10px;"><div style="font-size:0.85rem; color:#666;">{label.replace('_', ' ')}</div><span class="{badge_class}">{value}</span></div>""", unsafe_allow_html=True)

# ================= APLIKASI UTAMA =================
if check_login():
    USER_ROLE = st.session_state['user_role']
    USER_NAME = st.session_state['user_fullname']

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
        st.markdown(f"### Halo, {USER_NAME}")
        st.caption(f"Role: {USER_ROLE}")
        st.write("---")
        
        opt_list = ["Input Pemeriksaan", "Laporan Data"]
        ico_list = ["pencil-square", "file-earmark-pdf"]
        
        if USER_ROLE == "Administrator":
            opt_list.append("Dashboard & Kontrol")
            ico_list.append("speedometer2")
            
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

    # --- HALAMAN 1: INPUT ---
    if selected == "Input Pemeriksaan":
        st.markdown("<div class='header-title'>📝 Input Pemeriksaan Kendaraan</div>", unsafe_allow_html=True)
        
        df_mobil = get_data_mobil()
        df_history = get_laporan_cek()
        
        nopol_display = "-"
        pilih_mobil = ""
        tgl_terakhir_display = "-"
        status_color_class = "info-value-stack"

        # --- LAYOUT IDENTITAS (RAAPI) ---
        with st.container():
            st.markdown("<div class='stCard'>", unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            with c1:
                st.markdown(f"""
                <div class='info-box-row' style='margin-top:2px;'>
                    <span class='label-text'>Pemeriksa :</span>
                    <span class='value-text'>{USER_NAME}</span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if not df_mobil.empty:
                    pilih_mobil = st.selectbox("Unit Kendaraan", df_mobil['Nama_Mobil'].unique(), label_visibility="collapsed")
                    try:
                        row_m = df_mobil[df_mobil['Nama_Mobil'] == pilih_mobil]
                        if not row_m.empty: nopol_display = row_m['Nomor_Polisi'].iloc[0]
                        
                        if not df_history.empty:
                            hist_mobil = df_history[df_history['Merk_Kendaraan'] == pilih_mobil]
                            if not hist_mobil.empty:
                                hist_mobil['Tanggal'] = pd.to_datetime(hist_mobil['Tanggal'])
                                last_date = hist_mobil.sort_values('Tanggal', ascending=False).iloc[0]['Tanggal']
                                tgl_terakhir_display = last_date.strftime("%d-%b-%Y")
                                days_diff = (datetime.now() - last_date).days
                                if days_diff > 14: status_color_class = "info-value-red"
                                else: status_color_class = "info-value-green"
                            else:
                                tgl_terakhir_display = "Belum Ada"
                                status_color_class = "info-value-red"
                    except: pass
                else: st.error("DB Error")
            with c3:
                kilometer = st.number_input("KM", min_value=0, step=1, label_visibility="collapsed", placeholder="KM")
            with c4:
                tanggal = st.date_input("Tanggal", datetime.now(), label_visibility="collapsed")

            st.write("") 
            r2_c1, r2_c2 = st.columns(2)
            with r2_c1:
                st.markdown(f"""<div class='info-box-stacked'><div class='info-label-stack'>Terakhir Dicek</div><div class='{status_color_class}'>{tgl_terakhir_display}</div></div>""", unsafe_allow_html=True)
            with r2_c2:
                st.markdown(f"""<div class='info-box-stacked'><div class='info-label-stack'>Nomor Polisi</div><div class='info-value-stack'>{nopol_display}</div></div>""", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("#### 📋 Checklist Kondisi")
        
        with st.form("form_checklist"):
            def opsi(k): return st.radio(k, ["Baik", "Rusak", "Hilang/Kurang"], horizontal=True, label_visibility="collapsed", key=k)
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["🪟 Eksterior & Pintu", "🚗 Ban & Kaki-kaki", "🛋️ Interior", "⚙️ Mesin", "💡 Lampu & Kelengkapan"])

            with tab1:
                ca, cb = st.columns(2)
                with ca: st.write("**Kaca Depan**"); kd=opsi("Kaca_Depan"); st.write("**Kaca Kiri**"); kk=opsi("Kaca_Kiri"); st.write("**Kaca Kanan**"); kka=opsi("Kaca_Kanan"); st.write("**Spion Kanan**"); sk=opsi("Spion_Kanan"); st.write("**Spion Kiri**"); ski=opsi("Spion_Kiri"); st.write("**Spion Dalam**"); sd=opsi("Spion_Dalam"); st.divider(); st.write("**Body Depan**"); bod=opsi("Body_Depan"); st.write("**Body Grill**"); bog=opsi("Body_Grill"); st.write("**Body Fender**"); bof=opsi("Body_Fender")
                with cb: st.write("**Ext. Talang Air**"); eta=opsi("Ext_Talang_Air"); st.write("**Ext. Plat Depan**"); epd=opsi("Ext_Plat_Depan"); st.write("**Ext. Plat Belakang**"); epb=opsi("Ext_Plat_Belakang"); st.divider(); st.write("**Pintu Dpn Kanan**"); pdk=opsi("Pintu_D_Kanan"); st.write("**Pintu Dpn Kiri**"); pdki=opsi("Pintu_D_Kiri"); st.write("**Pintu Blk Kanan**"); pbk=opsi("Pintu_B_Kanan"); st.write("**Pintu Blk Kiri**"); pbki=opsi("Pintu_B_Kiri"); st.write("**Pintu Bagasi**"); pbg=opsi("Pintu_Bagasi")
            with tab2:
                cc, cd = st.columns(2)
                with cc: st.write("**Ban Kanan Depan**"); bkd=opsi("Ban_Kanan_Depan"); st.write("**Ban Kiri Depan**"); bkid=opsi("Ban_Kiri_Depan"); st.write("**Ban Serep**"); bs=opsi("Ban_Serep")
                with cd: st.write("**Ban Kanan Belakang**"); bkb=opsi("Ban_Kanan_Belakang"); st.write("**Ban Kiri Belakang**"); bkib=opsi("Ban_Kiri_Belakang")
            with tab3:
                ce, cf = st.columns(2)
                with ce: st.write("**Jok**"); ij=opsi("Int_Jok"); st.write("**Stir**"); ist=opsi("Int_Stir"); st.write("**Karpet**"); ik=opsi("Int_Karpet"); st.write("**Persneling**"); ip=opsi("Int_Persneling")
                with cf: st.write("**Rem Tangan**"); irt=opsi("Int_Rem_Tangan"); st.write("**Dashboard**"); idb=opsi("Int_Dashboard"); st.write("**AC**"); iac=opsi("Int_AC")
            with tab4:
                cg, ch = st.columns(2)
                with cg: st.write("**Oli Mesin**"); mo=opsi("Mesin_Oli"); st.write("**Minyak Rem**"); mmr=opsi("Mesin_Minyak_Rem"); st.write("**Air Radiator**"); mar=opsi("Mesin_Air_Radiator")
                with ch: st.write("**Air Accu**"); maa=opsi("Mesin_Air_Accu"); st.write("**Air Wiper**"); maw=opsi("Mesin_Air_Wiper")
            with tab5:
                ci, cj = st.columns(2)
                with ci: st.write("**Lampu Utama**"); lu=opsi("Lampu_Utama"); st.write("**Lampu Kecil**"); lk=opsi("Lampu_Kecil"); st.write("**Lampu Rem**"); lr=opsi("Lampu_Rem"); st.write("**Sein Depan**"); snd=opsi("Sein_Depan"); st.write("**Sein Belakang**"); snb=opsi("Sein_Belakang")
                with cj: st.write("**Kunci Roda**"); kr=opsi("Kunci_Roda"); st.write("**Dongkrak**"); dg=opsi("Dongkrak"); st.write("**P3K**"); p3k=opsi("P3K"); st.write("**STNK**"); stnk=opsi("STNK")

            st.write("---")
            
            # --- UPLOAD FOTO (DI DALAM FORM) ---
            st.markdown("##### 📸 Dokumentasi Foto")
            uploaded_file = st.file_uploader("Upload Foto Bukti/Kerusakan (Otomatis Dikecilkan)", type=['jpg', 'jpeg', 'png'])
            
            st.write("---")
            st.warning("📝 CATATAN TAMBAHAN (Wajib diisi jika ada kerusakan)")
            ket = st.text_area("Keterangan", label_visibility="collapsed", height=100)
            
            submit_btn = st.form_submit_button("💾 SIMPAN DATA PEMERIKSAAN", type="primary", use_container_width=True)

            if submit_btn:
                if nopol_display == "-" or not df_mobil.empty and pilih_mobil == "": st.warning("⚠️ Pilih unit kendaraan.")
                else:
                    # PROSES KOMPRESI FOTO
                    foto_b64 = ""
                    if uploaded_file is not None:
                        foto_b64 = compress_image(uploaded_file)
                    
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
                        "Kunci_Roda": kr, "Dongkrak": dg, "P3K": p3k, "STNK": stnk, 
                        "Keterangan": ket,
                        "Foto_Bukti": foto_b64 # KOLOM BARU
                    }])
                    try:
                        exist = conn.read(worksheet="data_cek", ttl=0)
                        # Pastikan kolom Foto_Bukti ada di sheet
                        if 'Foto_Bukti' not in exist.columns:
                            exist['Foto_Bukti'] = ""
                        
                        upd = pd.concat([exist, row], ignore_index=True)
                        conn.update(worksheet="data_cek", data=upd)
                        st.success("✅ Tersimpan!"); st.balloons()
                    except Exception as e: st.error(f"Gagal simpan: {e}")

    # --- HALAMAN 2: LAPORAN ---
    elif selected == "Laporan Data":
        st.markdown("<div class='header-title'>🖨️ Laporan & Kontrol Data</div>", unsafe_allow_html=True)
        
        df_lap = get_laporan_cek()
        if not df_lap.empty:
            df_lap['Tanggal'] = pd.to_datetime(df_lap['Tanggal'])
            df_lap = df_lap.sort_values('Timestamp', ascending=False)
            
            with st.container():
                st.markdown("<div class='stCard'>", unsafe_allow_html=True)
                fc1, fc2 = st.columns(2)
                with fc1: f_mobil = st.multiselect("Unit Mobil", df_lap['Merk_Kendaraan'].unique())
                with fc2: f_bln = st.selectbox("Periode Bulan", ["Semua"] + sorted(df_lap['Tanggal'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
                st.markdown("</div>", unsafe_allow_html=True)
            
            view = df_lap.copy()
            if f_mobil: view = view[view['Merk_Kendaraan'].isin(f_mobil)]
            if f_bln != "Semua": view = view[view['Tanggal'].dt.strftime('%Y-%m') == f_bln]
            
            if len(view) == 0: st.info("Data tidak ditemukan.")
            else:
                st.write("#### 🔍 Pilih Data Pemeriksaan")
                pilihan_list = view.index.tolist()
                label_map = {i: f"{view.loc[i, 'Tanggal'].date()} | {view.loc[i, 'Merk_Kendaraan']} | {view.loc[i, 'Nama_Security']}" for i in pilihan_list}
                selected_id = st.selectbox("Pilih Riwayat:", pilihan_list, format_func=lambda x: label_map[x])
                st.write("---")
                
                row = view.loc[selected_id]
                
                with st.container():
                    st.markdown(f"""<div class='stCard' style='border-left: 5px solid #3B82F6;'><h3>📑 Detail: {row['Merk_Kendaraan']}</h3><p><b>Tanggal:</b> {row['Tanggal'].date()} &nbsp;|&nbsp; <b>Nopol:</b> {row['Nomor_Polisi']} &nbsp;|&nbsp; <b>Inspector:</b> {row['Nama_Security']} &nbsp;|&nbsp; <b>KM:</b> {row['Kilometer']}</p></div>""", unsafe_allow_html=True)
                
                # TAMPILAN FOTO DI PREVIEW
                if 'Foto_Bukti' in row and row['Foto_Bukti'] and len(str(row['Foto_Bukti'])) > 10:
                    try:
                        img_data = base64.b64decode(row['Foto_Bukti'])
                        st.image(img_data, caption="Foto Bukti/Kerusakan", width=300)
                    except: pass
                
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

                for category, cols in items_map.items():
                    st.markdown(f"##### {category}")
                    columns = st.columns(4)
                    for idx, col_name in enumerate(cols):
                        val = row.get(col_name, "-")
                        with columns[idx % 4]: render_item(col_name, val)
                    st.divider()
                
                st.warning(f"📝 CATATAN: {row['Keterangan'] if row['Keterangan'] else '-'}")
                if st.button("📄 DOWNLOAD PDF", type="primary", use_container_width=True):
                    pdf_data = create_pdf(row)
                    st.download_button("⬇️ Unduh File", pdf_data, f"Laporan_{row['Merk_Kendaraan']}.pdf", "application/pdf")

        else: st.info("Belum ada data.")

    # --- HALAMAN 3: DASHBOARD & KONTROL ---
    elif selected == "Dashboard & Kontrol":
        # (Kode Dashboard Sama Seperti Sebelumnya)
        st.markdown("<div class='header-title'>📊 Dashboard & Kontrol Unit</div>", unsafe_allow_html=True)
        
        df_history = get_laporan_cek()
        df_mobil = get_data_mobil()
        
        if not df_history.empty and not df_mobil.empty:
            st.subheader("📋 Status Kontrol Pemeriksaan (Periode 2 Minggu)")
            
            status_data = []
            today = datetime.now()
            
            for index, row in df_mobil.iterrows():
                nama_mobil = row['Nama_Mobil']
                nopol = row['Nomor_Polisi']
                hist = df_history[df_history['Merk_Kendaraan'] == nama_mobil]
                
                if not hist.empty:
                    hist['Tanggal'] = pd.to_datetime(hist['Tanggal'])
                    last_check = hist.sort_values('Tanggal', ascending=False).iloc[0]['Tanggal']
                    days_diff = (today - last_check).days
                    
                    if days_diff <= 14:
                        status = "✅ Sudah Dicek"
                        keterangan_status = f"{days_diff} hari yang lalu"
                    else:
                        status = "⚠️ Perlu Cek"
                        keterangan_status = f"Telat {days_diff} hari"
                    
                    tgl_str = last_check.strftime("%d-%b-%Y")
                else:
                    status = "❌ Belum Pernah"
                    tgl_str = "-"
                    keterangan_status = "Data Kosong"
                    days_diff = 999
                
                status_data.append({
                    "Unit Kendaraan": nama_mobil,
                    "Plat Nomor": nopol,
                    "Terakhir Cek": tgl_str,
                    "Status": status,
                    "Keterangan": keterangan_status,
                    "sort_key": days_diff
                })
            
            df_status = pd.DataFrame(status_data).sort_values('sort_key', ascending=True)
            st.dataframe(df_status[['Unit Kendaraan', 'Plat Nomor', 'Terakhir Cek', 'Status', 'Keterangan']], use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("📈 Analisis Kerusakan")
            
            df_history['Tanggal'] = pd.to_datetime(df_history['Tanggal'])
            bln_dash = st.selectbox("Filter Bulan Grafik", ["Semua"] + sorted(df_history['Tanggal'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
            
            df_dash = df_history.copy()
            if bln_dash != "Semua":
                df_dash = df_dash[df_dash['Tanggal'].dt.strftime('%Y-%m') == bln_dash]

            if not df_dash.empty:
                total_cek = len(df_dash)
                cols_check = [c for c in df_dash.columns if c not in ['Timestamp','Nama_Security','Tanggal','Merk_Kendaraan','Nomor_Polisi','Kilometer','Keterangan', 'Foto_Bukti']]
                
                total_rusak_count = 0
                rusak_per_mobil = {}
                rusak_per_item = {}
                
                for idx, r in df_dash.iterrows():
                    for c in cols_check:
                        val = r[c]
                        if val in ["Rusak", "Hilang/Kurang"]:
                            total_rusak_count += 1
                            mobil = r['Merk_Kendaraan']
                            rusak_per_mobil[mobil] = rusak_per_mobil.get(mobil, 0) + 1
                            rusak_per_item[c] = rusak_per_item.get(c, 0) + 1

                c_k1, c_k2 = st.columns(2)
                with c_k1: st.metric("Total Pemeriksaan", total_cek)
                with c_k2: st.metric("Total Temuan Kerusakan", total_rusak_count)
                
                g1, g2 = st.columns(2)
                with g1:
                    st.write("**Kendaraan Sering Rusak**")
                    if rusak_per_mobil:
                        st.bar_chart(pd.DataFrame(list(rusak_per_mobil.items()), columns=['Mobil', 'Jumlah']).set_index('Mobil'))
                    else: st.info("Tidak ada data.")
                with g2:
                    st.write("**Komponen Sering Rusak**")
                    if rusak_per_item:
                        st.bar_chart(pd.DataFrame(list(rusak_per_item.items()), columns=['Item', 'Jumlah']).set_index('Item'))
                    else: st.info("Tidak ada data.")
            else: st.info("Tidak ada data periode ini.")
            
        else: st.info("Database masih kosong.")