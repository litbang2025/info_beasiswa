import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO
from fuzzywuzzy import process

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
        (id, benua, asal_beasiswa, nama_lembaga, top_univ, program_beasiswa, jenis_beasiswa, persyaratan, benefit, waktu_pendaftaran, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    df = pd.read_excel("credentials.xlsx", engine='openpyxl')  
    credentials = df.set_index('user')['password'].to_dict()
    print(credentials)  # Debugging: Tampilkan kredensial yang dibaca
    return credentials

# -------------------------
# UI Streamlit
# -------------------------
st.set_page_config(
    page_title="🎓 Data Beasiswa Global",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
st.markdown("""
    <style>
    body {
        background-image: url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1');
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        color: #333;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        animation: fadeIn 0.5s;
    }
    .login-container h1 {
        margin-bottom: 1.5rem;
        font-size: 2rem;
        color: #333;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    .header {
        background-color: #2a3f54;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

# Atur session
st.session_state.logged_in = st.session_state.get('logged_in', False)

if not st.session_state.logged_in:
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)  # Gambar icon user kecil
        st.markdown("<h1>Login ke Sistem</h1>", unsafe_allow_html=True)

        # Membaca kredensial dari file Excel
        credentials = read_credentials()

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username in credentials:
                if credentials[username] == password:
                    st.session_state.logged_in = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Password salah.")
            else:
                st.error("Username tidak ditemukan.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# -------------------------
# Sidebar Navigasi
# -------------------------
with st.sidebar:
    st.title("🌍 Beasiswa Dashboard")
    st.markdown("---")
    menu = st.radio("Navigasi Menu", 
    ["🏠 Dashboard", "⬆️ Upload Data", "➕ Tambah Data Manual", "📄 Data Tersimpan", 
     "✏️ Edit Data", "🗑️ Hapus Data", "📊 Grafik", 
     "🔎 Filter Data", "📥 Download Data", "⚠️ Reset Database"]
)

    st.markdown("---")
    st.caption("Dibuat oleh: Tim Beasiswa Global")

# -------------------------
# Tampilan Dashboard
# -------------------------
if menu == "🏠 Dashboard":
    st.title("🎯 Dashboard Beasiswa Global")
    df_db = fetch_data()

    st.markdown('<div class="header"><h2>Statistik Ringkas</h2></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Beasiswa", len(df_db))
    col2.metric("Negara Asal Unik", df_db['asal_beasiswa'].nunique())
    col3.metric("Program Beasiswa Unik", df_db['program_beasiswa'].nunique())

    st.markdown("---")
    st.subheader("Visualisasi Singkat")
    fig = px.pie(df_db, names='benua', title="Distribusi Beasiswa berdasarkan Benua")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tambahkan filter untuk program beasiswa, nama lembaga, dan persyaratan
    st.markdown("---")
    st.subheader("Filter Data Beasiswa")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    with filter_col1:
        program_filter = st.selectbox("Pilih Program Beasiswa:", ["Semua Program"] + df_db['program_beasiswa'].unique().tolist())
    with filter_col2:
        lembaga_filter = st.selectbox("Pilih Nama Lembaga:", ["Semua Lembaga"] + df_db['nama_lembaga'].unique().tolist())
    with filter_col3:
        persyaratan_filter = st.selectbox("Pilih Persyaratan:", ["Semua Persyaratan"] + df_db['persyaratan'].unique().tolist())
    with filter_col4:
        top_univ_filter = st.selectbox("Pilih Top Universitas:", ["Semua Universitas"] + df_db['top_univ'].unique().tolist())

    # Filter data berdasarkan pilihan
    if program_filter != "Semua Program":
        df_db = df_db[df_db['program_beasiswa'] == program_filter]
    
    if lembaga_filter != "Semua Lembaga":
        df_db = df_db[df_db['nama_lembaga'] == lembaga_filter]
    
    if persyaratan_filter != "Semua Persyaratan":
        df_db = df_db[df_db['persyaratan'] == persyaratan_filter]
    
    if top_univ_filter != "Semua Universitas":
        df_db = df_db[df_db['top_univ'] == top_univ_filter]
    
    # Menampilkan data yang ter-filter
    st.markdown("---")
    st.subheader("Data Beasiswa yang Terfilter")
    st.dataframe(df_db)

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
            insert_data(data)
            st.success("Data berhasil disimpan!")

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

    st.info("Isi form di bawah ini untuk menambah data beasiswa ke database:")

    with st.form("form_tambah_manual"):
        id_beasiswa = st.text_input("ID Beasiswa (harus unik)", placeholder="Contoh: B001")
        benua = st.text_input("Benua", placeholder="Contoh: Asia")
        asal_beasiswa = st.text_input("Asal Beasiswa", placeholder="Contoh: Jepang")
        nama_lembaga = st.text_input("Nama Lembaga", placeholder="Contoh: MEXT")
        top_univ = st.text_input("Top Universitas (opsional)", placeholder="Contoh: University of Tokyo")
        program_beasiswa = st.text_input("Program Beasiswa", placeholder="Contoh: S2")
        jenis_beasiswa = st.text_input("Jenis Beasiswa", placeholder="Contoh: Fully Funded")
        persyaratan = st.text_area("Persyaratan", placeholder="Contoh: IPK minimal 3.5")
        benefit = st.text_area("Benefit", placeholder="Contoh: Beasiswa penuh")
        waktu_pendaftaran = st.text_input("Waktu Pendaftaran", placeholder="Contoh: Januari - Februari")
        link = st.text_input("Link Informasi", placeholder="Contoh: https://example.com")

        submitted = st.form_submit_button("💾 Simpan Data")
        if submitted:
            if not id_beasiswa:
                st.error("ID Beasiswa wajib diisi!")
            else:
                new_data = [(id_beasiswa, benua, asal_beasiswa, nama_lembaga, top_univ, program_beasiswa, jenis_beasiswa, persyaratan, benefit, waktu_pendaftaran, link)]
                insert_data(new_data)
                st.success(f"Data Beasiswa {id_beasiswa} berhasil ditambahkan!")

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

# -------------------------
# Hapus Data
# -------------------------
elif menu == "🗑️ Hapus Data":
    st.title("🗑️ Hapus Data Beasiswa")
    id_delete = st.text_input("Masukkan ID Beasiswa yang akan dihapus:")
    if st.button("⚡ Hapus Data"):
        delete_data_by_id(id_delete)
        st.warning(f"Data dengan ID {id_delete} telah dihapus.")

# -------------------------
# Grafik
# -------------------------
elif menu == "📊 Grafik":
    st.title("📊 Visualisasi Data Beasiswa")
    df_db = fetch_data()

    tab1, tab2 = st.tabs(["📊 Jenis Beasiswa", "🏛️ Top Universitas"])

    with tab1:
        st.subheader("📊 Distribusi Jenis Beasiswa")
        
        jenis_counts = df_db['jenis_beasiswa'].value_counts().reset_index()
        jenis_counts.columns = ['Jenis Beasiswa', 'Jumlah']

        fig = px.bar(
            jenis_counts,
            x='Jumlah',
            y='Jenis Beasiswa',
            orientation='h',
            color='Jumlah',
            title="Jumlah Beasiswa Berdasarkan Jenis",
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_jenis_beasiswa")

        # Penjelasan otomatis
        most_common = jenis_counts.iloc[0]['Jenis Beasiswa']
        most_common_pct = jenis_counts.iloc[0]['Jumlah'] / jenis_counts['Jumlah'].sum() * 100

        st.markdown(f"""
        ℹ️ **Penjelasan:**
        Jenis beasiswa paling banyak adalah **{most_common}** dengan proporsi sekitar **{most_common_pct:.1f}%**
        dari total jenis beasiswa. Ini menunjukkan fokus utama lembaga penyedia beasiswa saat ini.
        """)

    with tab2:
        st.subheader("🏛️ Top 10 Universitas Tujuan Beasiswa")
        top_univ_count = df_db['top_univ'].value_counts().nlargest(10).reset_index()
        top_univ_count.columns = ['Top Universitas', 'Jumlah Beasiswa']

        fig = px.bar(
            top_univ_count,
            x='Jumlah Beasiswa',
            y='Top Universitas',
            orientation='h',
            color='Jumlah Beasiswa',
            title="Top 10 Universitas dengan Beasiswa Terbanyak",
            color_continuous_scale='Teal'
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_top_univ")

        # Penjelasan otomatis
        top_univ = top_univ_count.iloc[0]
        st.markdown(f"""
        ℹ️ **Penjelasan:**
        Universitas dengan penerimaan beasiswa terbanyak adalah **{top_univ['Top Universitas']}**
        dengan total **{top_univ['Jumlah Beasiswa']}** beasiswa tercatat dalam database.
        Ini menunjukkan bahwa universitas ini menjadi salah satu tujuan favorit atau mitra utama dalam program-program beasiswa.
        """)

# -------------------------
# Filter Data
# -------------------------
elif menu == "🔎 Filter Data":
    st.title("🔎 Filter Data Beasiswa")
    df_db = fetch_data()

    col1, col2 = st.columns(2)
    benua_filter = col1.selectbox("Pilih Benua", df_db['benua'].unique())
    program_filter = col2.selectbox("Pilih Program Beasiswa", df_db['program_beasiswa'].unique())

    filtered_df = df_db[(df_db['benua'] == benua_filter) & (df_db['program_beasiswa'] == program_filter)]
    st.dataframe(filtered_df, use_container_width=True)

# -------------------------
# Download Data
# -------------------------
elif menu == "📥 Download Data":
    st.title("📥 Download Database")
    df_db = fetch_data()
    file_format = st.selectbox("Pilih format file", ["CSV", "Excel"])

    if file_format == "CSV":
        st.download_button("Download CSV", df_db.to_csv(index=False).encode('utf-8'), "data_beasiswa.csv")
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_db.to_excel(writer, index=False, sheet_name='Beasiswa')
        st.download_button("Download Excel", output.getvalue(), "data_beasiswa.xlsx")

# -------------------------
# Reset Database
# -------------------------
elif menu == "⚠️ Reset Database":
    st.title("⚠️ Reset Seluruh Database Beasiswa")

    st.warning("PERINGATAN: Tindakan ini akan menghapus **SELURUH data beasiswa** secara permanen. Harap berhati-hati!")

    kode_verifikasi = st.text_input("Masukkan kode verifikasi admin untuk melanjutkan (ketik: xxx4):", type="password")

    if kode_verifikasi == "6464":
        if st.button("🚨 Hapus Semua Data"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM beasiswa")
            conn.commit()
            conn.close()
            st.success("✅ Semua data telah berhasil dihapus!")
    elif kode_verifikasi != "":
        st.error("❌ Kode verifikasi salah. Silakan coba lagi.")
