import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO
from fuzzywuzzy import process
import requests
from datetime import datetime, timedelta
import base64
from fpdf import FPDF
import warnings
warnings.filterwarnings('ignore')

# -------------------------
# Fungsi koneksi database
# -------------------------
def get_connection():
    return sqlite3.connect("beasiswa.db")

# -------------------------
# Fungsi insert, fetch, delete, update
# -------------------------
def insert_data(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO beasiswa 
        (id, benua, asal_beasiswa, nama_lembaga, top_univ, program_beasiswa, jenis_beasiswa, persyaratan, benefit, waktu_pendaftaran, link, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def fetch_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM beasiswa", conn)
    conn.close()
    return df

def delete_data_by_id(id_value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM beasiswa WHERE id = ?", (id_value,))
    conn.commit()
    conn.close()

def update_data_by_id(id_value, updated_row):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE beasiswa
        SET benua=?, asal_beasiswa=?, nama_lembaga=?, top_univ=?,
            program_beasiswa=?, jenis_beasiswa=?, persyaratan=?, benefit=?, waktu_pendaftaran=?, link=?
        WHERE id=?
    """, (updated_row[0], updated_row[1], updated_row[2], updated_row[3], updated_row[4], updated_row[5], updated_row[6], updated_row[7], updated_row[8], updated_row[9], id_value))
    conn.commit()
    conn.close()

# -------------------------
# Fungsi untuk membaca username dan password dari file Excel
# -------------------------
def read_credentials():
    try:
        df = pd.read_excel("credentials.xlsx", engine='openpyxl')  
        credentials = df.set_index('user')['password'].to_dict()
        return credentials
    except:
        # Default credentials jika file tidak ada
        return {"admin": "admin123"}

# -------------------------
# Fungsi untuk generate PDF
# -------------------------
def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Data Beasiswa Global", ln=1, align='C')
    pdf.ln(10)
    
    # Header tabel
    headers = df.columns.tolist()
    for header in headers:
        pdf.cell(40, 10, txt=header, border=1)
    pdf.ln()
    
    # Data tabel
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(40, 10, txt=str(item)[:20], border=1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# -------------------------
# Fungsi untuk notifikasi beasiswa yang akan tutup
# -------------------------
def check_closing_scholarships():
    df = fetch_data()
    today = datetime.now()
    closing_soon = []
    
    for _, row in df.iterrows():
        if pd.notna(row['waktu_pendaftaran']):
            try:
                # Parse tanggal (format: "Januari - Februari" atau "1-15 Januari")
                if '-' in row['waktu_pendaftaran']:
                    parts = row['waktu_pendaftaran'].split('-')
                    if len(parts) == 2:
                        month = parts[1].strip()
                        # Cek jika bulan depan adalah bulan sekarang atau bulan depan
                        if month.lower() in [today.strftime("%B").lower(), 
                                           (today + timedelta(days=30)).strftime("%B").lower()]:
                            closing_soon.append(row['nama_lembaga'])
            except:
                pass
    
    return closing_soon

# -------------------------
# Fungsi untuk integrasi API sederhana
# -------------------------
def fetch_external_scholarships():
    try:
        # Contoh API (ganti dengan API real)
        response = requests.get("https://api.example.com/scholarships", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
    except:
        pass
    return pd.DataFrame()

# -------------------------
# UI Streamlit
# -------------------------
st.set_page_config(
    page_title="🎓 Portal Beasiswa Global",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS yang ditingkatkan dengan mobile responsiveness
# -------------------------
st.markdown("""
<style>
    :root {
        --primary: #1e88e5;
        --secondary: #43a047;
        --accent: #8e24aa;
        --background: rgba(255, 255, 255, 0.85);
        --card-bg: #ffffff;
        --text: #263238;
    }
    
    body {
        background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), 
                          url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1');
        background-size: cover;
        background-attachment: fixed;
        color: var(--text);
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.3s, box-shadow 0.3s;
        border-left: 5px solid var(--primary);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    
    .chart-container {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .sidebar-content {
        background: var(--background);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background-color: var(--primary);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        transition: all 0.3s;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        background-color: #1565c0;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .data-frame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .login-container {
        background: var(--card-bg);
        border-radius: 15px;
        padding: 2.5rem;
        max-width: 450px;
        margin: 8rem auto;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .chart-container {
            padding: 1rem;
        }
        
        .sidebar-content {
            padding: 1rem;
        }
    }
    
    /* Notification styles */
    .notification {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    
    .notification-warning {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .notification-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Atur session state
# -------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'notifications' not in st.session_state:
    st.session_state.notifications = []

# -------------------------
# Halaman Login
# -------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div class="login-container">
        <div style="text-align: center; margin-bottom: 2rem;">
            <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="100" style="margin-bottom: 1rem;">
            <h1 style="margin-bottom: 0.5rem;">Portal Beasiswa Global</h1>
            <p style="color: #666;">Masuk untuk mengakses database beasiswa</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Membaca kredensial dari file Excel
    credentials = read_credentials()
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Masukkan username")
        password = st.text_input("Password", type="password", placeholder="Masukkan password")
        
        if st.form_submit_button("Login"):
            if username in credentials:
                if credentials[username] == password:
                    st.session_state.logged_in = True
                    st.success("Login berhasil! Mengalihkan ke dashboard...")
                    st.rerun()
                else:
                    st.error("Password salah. Silakan coba lagi.")
            else:
                st.error("Username tidak ditemukan.")
    
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.9rem;">
            <p>Hubungi admin untuk mendapatkan akses</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# -------------------------
# Sidebar Navigasi
# -------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.title("🌍 Beasiswa Dashboard")
    st.caption("Platform informasi beasiswa global")
    st.markdown("---")
    
    menu = st.selectbox(
        "Navigasi Menu", 
        ["🏠 Dashboard", "⬆️ Upload Data", "➕ Tambah Data Manual", "📄 Data Tersimpan", 
         "✏️ Edit Data", "🗑️ Hapus Data", "📊 Grafik", 
         "🔎 Filter Data", "📥 Download Data", "⚠️ Reset Database", "🔗 Integrasi API"],
         index=0
    )
    
    st.markdown("---")
    st.markdown("### 📈 Statistik Cepat")
    df_db = fetch_data()
    st.metric("Total Beasiswa", len(df_db))
    st.metric("Negara", df_db['asal_beasiswa'].nunique())
    
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Notifikasi Beasiswa yang Akan Tutup
# -------------------------
closing_soon = check_closing_scholarships()
if closing_soon:
    for scholarship in closing_soon:
        st.markdown(f"""
        <div class="notification notification-warning">
            <strong>⏰ Peringatan:</strong> Pendaftaran beasiswa dari {scholarship} akan segera ditutup!
        </div>
        """, unsafe_allow_html=True)

# -------------------------
# Tampilan Dashboard
# -------------------------
if menu == "🏠 Dashboard":
    st.markdown('<div class="main-header"><h1>🌍 Portal Beasiswa Global</h1><p>Platform informasi beasiswa internasional terlengkap</p></div>', unsafe_allow_html=True)
    
    df_db = fetch_data()
    
    # Statistik dengan kartu yang lebih menarik
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card"><h3>📚 Total Beasiswa</h3><h2>{}</h2></div>'.format(len(df_db)), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><h3>🌏 Negara</h3><h2>{}</h2></div>'.format(df_db['asal_beasiswa'].nunique()), unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><h3>🏛️ Universitas</h3><h2>{}</h2></div>'.format(df_db['top_univ'].nunique()), unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><h3>🎓 Program</h3><h2>{}</h2></div>'.format(df_db['program_beasiswa'].nunique()), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Visualisasi dengan container yang lebih baik
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container"><h3>📊 Distribusi Beasiswa per Benua</h3>', unsafe_allow_html=True)
        fig = px.pie(df_db, names='benua', hole=0.4, color_discrete_sequence=px.colors.qualitative.Plotly)
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container"><h3>📈 Jenis Beasiswa Populer</h3>', unsafe_allow_html=True)
        jenis_counts = df_db['jenis_beasiswa'].value_counts().nlargest(5)
        fig = px.bar(x=jenis_counts.values, y=jenis_counts.index, orientation='h', 
                     color=jenis_counts.values, color_continuous_scale='Blues')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabel data terbaru
    st.markdown('<div class="chart-container"><h3>📋 Beasiswa Terbaru</h3>', unsafe_allow_html=True)
    st.dataframe(df_db.sort_values('id', ascending=False).head(10), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Upload Data
# -------------------------
elif menu == "⬆️ Upload Data":
    st.title("⬆️ Upload Data Beasiswa Baru")
    uploaded_file = st.file_uploader("Upload file CSV atau Excel", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file, header=None)
        else:
            df = pd.read_excel(uploaded_file, header=None)

        with st.expander("📖 Preview Data Upload"):
            st.dataframe(df)

        data = df.values.tolist()
        if not str(data[0][0]).isdigit() and not str(data[0][0]).startswith("B"):
            data = data[1:]

        if st.button("✅ Simpan ke Database"):
            # Tambahkan timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_with_time = [row + [current_time] for row in data]
            insert_data(data_with_time)
            st.success("Data berhasil disimpan!")
            st.balloons()

# -------------------------
# Data Tersimpan
# -------------------------
elif menu == "📄 Data Tersimpan":
    st.title("📄 Database Beasiswa")
    df_db = fetch_data()

    with st.expander("🔍 Cari Data"):
        keyword = st.text_input("Masukkan kata kunci pencarian")
        if keyword:
            # Mencocokkan nama lembaga dengan fuzzy matching
            df_db['match_score'] = df_db['nama_lembaga'].apply(lambda x: process.extractOne(keyword, [x])[1])
            df_db = df_db[df_db['match_score'] > 70].drop(columns='match_score')  # Ambil yang match score > 70

    st.dataframe(df_db, use_container_width=True)

# -------------------------
# Tambah Data Manual
# -------------------------
elif menu == "➕ Tambah Data Manual":
    st.title("➕ Tambah Data Beasiswa Manual")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    with st.form("form_tambah_manual"):
        st.markdown("### 📝 Informasi Beasiswa")
        
        col1, col2 = st.columns(2)
        with col1:
            id_beasiswa = st.text_input("ID Beasiswa *", placeholder="Contoh: B001", help="ID unik untuk identifikasi beasiswa")
            benua = st.selectbox("Benua *", ["Asia", "Eropa", "Amerika", "Afrika", "Oseania"])
            asal_beasiswa = st.text_input("Asal Beasiswa *", placeholder="Contoh: Jepang")
            nama_lembaga = st.text_input("Nama Lembaga *", placeholder="Contoh: MEXT")
        
        with col2:
            top_univ = st.text_input("Top Universitas", placeholder="Contoh: University of Tokyo")
            program_beasiswa = st.selectbox("Program Beasiswa *", ["S1", "S2", "S3", "Non-Gelar"])
            jenis_beasiswa = st.selectbox("Jenis Beasiswa *", ["Fully Funded", "Partial", "Tuition Only"])
            waktu_pendaftaran = st.text_input("Waktu Pendaftaran", placeholder="Contoh: Januari - Februari")
        
        st.markdown("### 📄 Detail Beasiswa")
        col1, col2 = st.columns(2)
        with col1:
            persyaratan = st.text_area("Persyaratan *", placeholder="Contoh: IPK minimal 3.5", height=150)
        with col2:
            benefit = st.text_area("Benefit *", placeholder="Contoh: Beasiswa penuh", height=150)
        
        link = st.text_input("Link Informasi *", placeholder="https://example.com")
        
        submitted = st.form_submit_button("💾 Simpan Data")
        if submitted:
            if not all([id_beasiswa, benua, asal_beasiswa, nama_lembaga, program_beasiswa, jenis_beasiswa, persyaratan, benefit, link]):
                st.error("Harap isi semua field yang ditandai dengan *")
            else:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_data = [(id_beasiswa, benua, asal_beasiswa, nama_lembaga, top_univ, program_beasiswa, jenis_beasiswa, persyaratan, benefit, waktu_pendaftaran, link, current_time)]
                insert_data(new_data)
                st.success(f"Data Beasiswa {id_beasiswa} berhasil ditambahkan!")
                st.balloons()
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Edit Data
# -------------------------
elif menu == "✏️ Edit Data":
    st.title("✏️ Edit Data Beasiswa")
    df_db = fetch_data()
    id_edit = st.text_input("Masukkan ID Beasiswa yang akan diedit:")

    if id_edit:
        record = df_db[df_db['id'] == id_edit]
        if not record.empty:
            values = record.values[0].tolist()
            benua = st.text_input("Benua", values[1])
            asal = st.text_input("Asal Beasiswa", values[2])
            lembaga = st.text_input("Nama Lembaga", values[3])
            topuniv = st.text_input("Top Univ", values[4])
            program = st.text_input("Program", values[5])
            jenis = st.text_input("Jenis", values[6])
            persyaratan = st.text_area("Persyaratan", values[7])
            benefit = st.text_area("Benefit", values[8])
            waktu_pendaftaran = st.text_input("Waktu Pendaftaran", values[9])
            link = st.text_input("Link", values[10])

            if st.button("💾 Update"):
                update_data_by_id(id_edit, [benua, asal, lembaga, topuniv, program, jenis, persyaratan, benefit, waktu_pendaftaran, link])
                st.success("Data berhasil diupdate.")
                st.balloons()

# -------------------------
# Hapus Data
# -------------------------
elif menu == "🗑️ Hapus Data":
    st.title("🗑️ Hapus Data Beasiswa")
    id_delete = st.text_input("Masukkan ID Beasiswa yang akan dihapus:")
    if st.button("⚡ Hapus Data"):
        delete_data_by_id(id_delete)
        st.warning(f"Data dengan ID {id_delete} telah dihapus.")
        st.balloons()

# -------------------------
# Grafik
# -------------------------
elif menu == "📊 Grafik":
    st.title("📊 Analisis Data Beasiswa")
    df_db = fetch_data()
    
    tab1, tab2, tab3 = st.tabs(["📊 Jenis Beasiswa", "🏛️ Universitas", "🌍 Distribusi Geografis"])
    
    with tab1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Distribusi Jenis Beasiswa")
        
        jenis_counts = df_db['jenis_beasiswa'].value_counts().reset_index()
        jenis_counts.columns = ['Jenis Beasiswa', 'Jumlah']
        
        fig = px.bar(
            jenis_counts,
            x='Jenis Beasiswa',
            y='Jumlah',
            color='Jumlah',
            color_continuous_scale='Blues',
            text='Jumlah'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)
        
        # Analisis otomatis
        most_common = jenis_counts.iloc[0]['Jenis Beasiswa']
        most_common_pct = jenis_counts.iloc[0]['Jumlah'] / jenis_counts['Jumlah'].sum() * 100
        
        st.markdown(f"""
        <div style="background:#e3f2fd; padding:15px; border-radius:10px; margin-top:20px;">
            <h4>🔍 Analisis:</h4>
            <p>Jenis beasiswa paling banyak adalah <b>{most_common}</b> dengan proporsi <b>{most_common_pct:.1f}%</b> 
            dari total beasiswa. Ini menunjukkan bahwa sebagian besar penyedia beasiswa menawarkan 
            pendanaan penuh kepada penerima.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Top 15 Universitas Tujuan Beasiswa")
        top_univ_count = df_db['top_univ'].value_counts().nlargest(15).reset_index()
        top_univ_count.columns = ['Universitas', 'Jumlah Beasiswa']
        
        fig = px.treemap(
            top_univ_count,
            path=['Universitas'],
            values='Jumlah Beasiswa',
            color='Jumlah Beasiswa',
            color_continuous_scale='RdYlGn',
            title="Universitas dengan Beasiswa Terbanyak"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Analisis otomatis
        top_univ = top_univ_count.iloc[0]
        st.markdown(f"""
        <div style="background:#e8f5e9; padding:15px; border-radius:10px; margin-top:20px;">
            <h4>🔍 Analisis:</h4>
            <p><b>{top_univ['Universitas']}</b> adalah universitas dengan beasiswa terbanyak 
            ({top_univ['Jumlah Beasiswa']} beasiswa). Universitas ini menjadi tujuan utama 
            bagi para pelamar beasiswa internasional.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Distribusi Geografis Beasiswa")
        
        # Hitung data per negara
        country_counts = df_db['asal_beasiswa'].value_counts().reset_index()
        country_counts.columns = ['Negara', 'Jumlah Beasiswa']
        
        # Peta dunia
        fig = px.choropleth(
            country_counts,
            locations="Negara",
            locationmode='country names',
            color="Jumlah Beasiswa",
            hover_name="Negara",
            color_continuous_scale=px.colors.sequential.Plasma,
            title="Distribusi Beasiswa per Negara"
        )
        fig.update_geos(showcountries=True, showcoastlines=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Analisis otomatis
        top_country = country_counts.iloc[0]
        st.markdown(f"""
        <div style="background:#fff3e0; padding:15px; border-radius:10px; margin-top:20px;">
            <h4>🔍 Analisis:</h4>
            <p><b>{top_country['Negara']}</b> adalah negara dengan beasiswa terbanyak 
            ({top_country['Jumlah Beasiswa']} beasiswa). Negara ini menjadi pusat utama 
            pendidikan internasional dengan berbagai program beasiswa.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Filter Data
# -------------------------
elif menu == "🔎 Filter Data":
    st.title("🔎 Filter & Pencarian Data Beasiswa")
    df_db = fetch_data()
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Pencarian dengan fuzzy matching
    st.subheader("🔍 Pencarian Cerdas")
    keyword = st.text_input("Masukkan kata kunci pencarian", placeholder="Cari berdasarkan nama lembaga, universitas, atau program")
    
    if keyword:
        # Mencocokkan dengan fuzzy matching
        df_db['match_score'] = df_db['nama_lembaga'].apply(lambda x: process.extractOne(keyword, [x])[1])
        df_db = df_db[df_db['match_score'] > 70].drop(columns='match_score')
        st.info(f"Ditemukan {len(df_db)} beasiswa yang cocok dengan kata kunci '{keyword}'")
    
    st.markdown("---")
    
    # Filter multi-kriteria
    st.subheader("🎯 Filter Berdasarkan Kriteria")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        benua_filter = st.multiselect("Benua", df_db['benua'].unique())
    with col2:
        negara_filter = st.multiselect("Negara", df_db['asal_beasiswa'].unique())
    with col3:
        program_filter = st.multiselect("Program", df_db['program_beasiswa'].unique())
    with col4:
        jenis_filter = st.multiselect("Jenis Beasiswa", df_db['jenis_beasiswa'].unique())
    
    # Terapkan filter
    if benua_filter:
        df_db = df_db[df_db['benua'].isin(benua_filter)]
    if negara_filter:
        df_db = df_db[df_db['asal_beasiswa'].isin(negara_filter)]
    if program_filter:
        df_db = df_db[df_db['program_beasiswa'].isin(program_filter)]
    if jenis_filter:
        df_db = df_db[df_db['jenis_beasiswa'].isin(jenis_filter)]
    
    # Tampilkan hasil
    st.subheader(f"📋 Hasil Pencarian ({len(df_db)} beasiswa ditemukan)")
    st.dataframe(df_db, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Download Data dengan Format Lebih Lengkap
# -------------------------
elif menu == "📥 Download Data":
    st.title("📥 Download Database")
    df_db = fetch_data()
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Pilih kolom untuk di-download
    st.subheader("Pilih Kolom yang Akan Diunduh")
    selected_columns = st.multiselect(
        "Pilih kolom:", 
        df_db.columns.tolist(),
        default=df_db.columns.tolist()
    )
    
    if not selected_columns:
        st.error("Harap pilih minimal satu kolom")
        st.stop()
    
    df_selected = df_db[selected_columns]
    
    # Pilih format file
    file_format = st.selectbox("Pilih format file", ["CSV", "Excel", "PDF"])
    
    if file_format == "CSV":
        csv = df_selected.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='data_beasiswa.csv',
            mime='text/csv'
        )
    elif file_format == "Excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_selected.to_excel(writer, index=False, sheet_name='Beasiswa')
        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name='data_beasiswa.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    elif file_format == "PDF":
        pdf_data = create_pdf(df_selected)
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name='data_beasiswa.pdf',
            mime='application/pdf'
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Reset Database
# -------------------------
elif menu == "⚠️ Reset Database":
    st.title("⚠️ Reset Seluruh Database Beasiswa")

    st.warning("PERINGATAN: Tindakan ini akan menghapus **SELURUH data beasiswa** secara permanen. Harap berhati-hati!")

    kode_verifikasi = st.text_input("Masukkan kode verifikasi admin untuk melanjutkan (ketik: 6464):", type="password")

    if kode_verifikasi == "6464":
        if st.button("🚨 Hapus Semua Data"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM beasiswa")
            conn.commit()
            conn.close()
            st.success("✅ Semua data telah berhasil dihapus!")
            st.balloons()
    elif kode_verifikasi != "":
        st.error("❌ Kode verifikasi salah. Silakan coba lagi.")

# -------------------------
# Integrasi API
# -------------------------
elif menu == "🔗 Integrasi API":
    st.title("🔗 Integrasi API Beasiswa Eksternal")
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    st.subheader("Ambil Data dari Sumber Eksternal")
    
    if st.button("🔄 Ambil Data dari API"):
        with st.spinner("Mengambil data dari API..."):
            external_data = fetch_external_scholarships()
            
            if not external_data.empty:
                st.success(f"Berhasil mengambil {len(external_data)} beasiswa dari API!")
                
                # Tampilkan preview data
                st.subheader("Preview Data dari API")
                st.dataframe(external_data.head())
                
                # Konfirmasi import
                if st.button("✅ Import ke Database"):
                    # Tambahkan ID unik dan timestamp
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    external_data['id'] = ['API' + str(i) for i in range(len(external_data))]
                    external_data['created_at'] = current_time
                    
                    # Sesuaikan kolom dengan database
                    required_columns = ['id', 'benua', 'asal_beasiswa', 'nama_lembaga', 'top_univ', 
                                      'program_beasiswa', 'jenis_beasiswa', 'persyaratan', 
                                      'benefit', 'waktu_pendaftaran', 'link', 'created_at']
                    
                    # Isi kolom yang kosong dengan nilai default
                    for col in required_columns:
                        if col not in external_data.columns:
                            external_data[col] = '-'
                    
                    # Insert ke database
                    data_to_insert = external_data[required_columns].values.tolist()
                    insert_data(data_to_insert)
                    
                    st.success("Data berhasil diimpor ke database!")
                    st.balloons()
            else:
                st.error("Gagal mengambil data dari API. Silakan coba lagi nanti.")
    
    st.markdown('</div>', unsafe_allow_html=True)
