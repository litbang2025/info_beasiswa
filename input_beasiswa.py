import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO

# -------------------------------
# Database Connection
# -------------------------------
def get_connection():
    return sqlite3.connect("database_beasiswa.db")

def insert_data(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO beasiswa (id, benua, asal_beasiswa, nama_lembaga, top_univ, program_beasiswa, jenis_beasiswa, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        SET benua=?, asal_beasiswa=?, nama_lembaga=?, top_univ=?, program_beasiswa=?, jenis_beasiswa=?, link=?
        WHERE id=?
    """, (updated_row[0], updated_row[1], updated_row[2], updated_row[3], updated_row[4], updated_row[5], updated_row[6], id_value))
    conn.commit()
    conn.close()

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="🎓 Beasiswa Global Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS Styling
# -------------------------------
st.markdown("""
    <style>
    /* Background App */
    body, .stApp {
        background-color: #f4f6f8;
        font-family: 'Arial', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #2c3e50, #4ca1af);
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
        padding-top: 20px;
        color: white;
    }

    /* Logo */
    .sidebar-logo {
        text-align: center;
        margin-bottom: 20px;
    }
    .sidebar-logo img {
        width: 100px;
        border-radius: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }

    /* Menu styling */
    [data-testid="stSidebar"] .st-radio {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
    }
    [data-testid="stSidebar"] .st-radio label {
        color: white;
        font-size: 18px;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #4ca1af;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
    }

    /* Table */
    .css-1d391kg {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Session Login
# -------------------------------
st.session_state.logged_in = st.session_state.get('logged_in', False)

if not st.session_state.logged_in:
    st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:80vh;">
            <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="120"/>
            <h1 style="color:#2c3e50;">Login Beasiswa</h1>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("🔐 Login"):
        if username == "litbang" and password == "12345":
            st.session_state.logged_in = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau Password salah.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo"><img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png"></div>', unsafe_allow_html=True)
    st.title("🌍 Beasiswa Dashboard")
    st.markdown("---")

    menu = st.radio("Navigasi Menu", 
        ["🏠 Dashboard", "⬆️ Upload Data", "➕ Tambah Manual", "📄 Lihat Data", 
         "✏️ Edit Data", "🗑️ Hapus Data", "📊 Grafik", 
         "🔎 Filter", "📥 Download", "⚠️ Reset Database"]
    )
    st.markdown("---")
    st.caption("Made by Tim Beasiswa Global")

# -------------------------------
# Pages
# -------------------------------
if menu == "🏠 Dashboard":
    st.title("🎯 Dashboard Beasiswa Global")
    df = fetch_data()

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Beasiswa", len(df))
    col2.metric("Negara Asal Unik", df['asal_beasiswa'].nunique())
    col3.metric("Program Unik", df['program_beasiswa'].nunique())

    st.markdown("---")
    st.subheader("Distribusi Beasiswa Berdasarkan Benua")
    fig = px.pie(df, names='benua', title="Distribusi Beasiswa")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "⬆️ Upload Data":
    st.title("⬆️ Upload Data Beasiswa")
    uploaded_file = st.file_uploader("Upload File CSV atau Excel", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith("csv"):
            df_upload = pd.read_csv(uploaded_file, header=None)
        else:
            df_upload = pd.read_excel(uploaded_file, header=None)

        st.dataframe(df_upload, use_container_width=True)

        data = df_upload.values.tolist()
        if not str(data[0][0]).isdigit() and not str(data[0][0]).startswith("B"):
            data = data[1:]

        if st.button("✅ Simpan"):
            insert_data(data)
            st.success("Data berhasil disimpan!")

elif menu == "➕ Tambah Manual":
    st.title("➕ Tambah Data Manual")
    with st.form("form_tambah"):
        idb = st.text_input("ID Beasiswa (unik)", placeholder="B001")
        benua = st.text_input("Benua", placeholder="Asia")
        asal = st.text_input("Asal Beasiswa", placeholder="Jepang")
        lembaga = st.text_input("Nama Lembaga", placeholder="MEXT")
        topuniv = st.text_input("Top Universitas", placeholder="University of Tokyo")
        program = st.text_input("Program", placeholder="S2")
        jenis = st.text_input("Jenis", placeholder="Fully Funded")
        link = st.text_input("Link", placeholder="https://example.com")

        submit = st.form_submit_button("💾 Simpan")
        if submit:
            insert_data([(idb, benua, asal, lembaga, topuniv, program, jenis, link)])
            st.success(f"Data {idb} berhasil ditambahkan!")

elif menu == "📄 Lihat Data":
    st.title("📄 Data Beasiswa")
    df = fetch_data()

    keyword = st.text_input("🔎 Cari", "")
    if keyword:
        df = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

    st.dataframe(df, use_container_width=True)

elif menu == "✏️ Edit Data":
    st.title("✏️ Edit Data Beasiswa")
    df = fetch_data()
    id_edit = st.text_input("Masukkan ID yang mau diedit:")

    if id_edit:
        record = df[df['id'] == id_edit]
        if not record.empty:
            values = record.values[0]
            benua = st.text_input("Benua", values[1])
            asal = st.text_input("Asal", values[2])
            lembaga = st.text_input("Lembaga", values[3])
            topuniv = st.text_input("Top Univ", values[4])
            program = st.text_input("Program", values[5])
            jenis = st.text_input("Jenis", values[6])
            link = st.text_input("Link", values[7])

            if st.button("💾 Update"):
                update_data_by_id(id_edit, [benua, asal, lembaga, topuniv, program, jenis, link])
                st.success("Data berhasil diupdate!")

elif menu == "🗑️ Hapus Data":
    st.title("🗑️ Hapus Data")
    id_delete = st.text_input("Masukkan ID Beasiswa untuk dihapus:")
    if st.button("⚡ Hapus"):
        delete_data_by_id(id_delete)
        st.warning(f"Data {id_delete} telah dihapus!")

elif menu == "📊 Grafik":
    st.title("📊 Visualisasi Data")
    df = fetch_data()

    tab1, tab2 = st.tabs(["Jenis Beasiswa", "Top Universitas"])

    with tab1:
        fig1 = px.pie(df, names='jenis_beasiswa', title='Distribusi Jenis Beasiswa', hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        top10 = df['top_univ'].value_counts().nlargest(10).reset_index()
        top10.columns = ['Universitas', 'Jumlah']
        fig2 = px.bar(top10, x='Jumlah', y='Universitas', orientation='h', title="Top 10 Universitas", color='Jumlah')
        st.plotly_chart(fig2, use_container_width=True)

elif menu == "🔎 Filter":
    st.title("🔎 Filter Data Beasiswa")
    df = fetch_data()

    col1, col2 = st.columns(2)
    benua_filter = col1.selectbox("Pilih Benua", df['benua'].unique())
    program_filter = col2.selectbox("Pilih Program", df['program_beasiswa'].unique())

    filtered = df[(df['benua'] == benua_filter) & (df['program_beasiswa'] == program_filter)]
    st.dataframe(filtered, use_container_width=True)

elif menu == "📥 Download":
    st.title("📥 Download Data")
    df = fetch_data()

    format = st.selectbox("Pilih Format", ["CSV", "Excel"])
    if format == "CSV":
        st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "data_beasiswa.csv")
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", output.getvalue(), "data_beasiswa.xlsx")

elif menu == "⚠️ Reset Database":
    st.title("⚠️ Reset Semua Data")
    if st.button("🚨 Hapus Semua Data"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM beasiswa")
        conn.commit()
        conn.close()
        st.error("Semua data telah dihapus!")
