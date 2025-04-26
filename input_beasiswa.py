import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO

# -------------------------
# Fungsi koneksi database
# -------------------------
def get_connection():
    return sqlite3.connect("database_beasiswa.db")

# -------------------------
# Fungsi insert, fetch, delete, update
# -------------------------
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
        SET benua=?, asal_beasiswa=?, nama_lembaga=?, top_univ=?,
            program_beasiswa=?, jenis_beasiswa=?, link=?
        WHERE id=?
    """, (updated_row[0], updated_row[1], updated_row[2], updated_row[3], updated_row[4], updated_row[5], updated_row[6], id_value))
    conn.commit()
    conn.close()

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
# Sidebar Navigasi
# -------------------------
with st.sidebar:
    st.title("🌍 Beasiswa Dashboard")
    st.markdown("---")
    menu = st.radio("Navigasi Menu", 
        ["🏠 Dashboard", "⬆️ Upload Data", "📄 Data Tersimpan", 
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

    st.subheader("Statistik Ringkas")
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Beasiswa", len(df_db))
    col2.metric("Negara Asal Unik", df_db['asal_beasiswa'].nunique())
    col3.metric("Program Beasiswa Unik", df_db['program_beasiswa'].nunique())

    st.markdown("---")
    st.subheader("Visualisasi Singkat")
    fig = px.pie(df_db, names='benua', title="Distribusi Beasiswa berdasarkan Benua")
    st.plotly_chart(fig, use_container_width=True)

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
            df_db = df_db[df_db.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

    st.dataframe(df_db, use_container_width=True)

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
            link = st.text_input("Link", values[7])

            if st.button("💾 Update"):
                update_data_by_id(id_edit, [benua, asal, lembaga, topuniv, program, jenis, link])
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
        fig = px.pie(df_db, names='jenis_beasiswa', title='Distribusi Jenis Beasiswa', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_univ_count = df_db['top_univ'].value_counts().nlargest(10).reset_index()
        top_univ_count.columns = ['Top Universitas', 'Jumlah Beasiswa']
        fig = px.bar(top_univ_count, x='Jumlah Beasiswa', y='Top Universitas', orientation='h', color='Jumlah Beasiswa',
                     title="Top 10 Universitas dengan Beasiswa Terbanyak", color_continuous_scale='Teal')
        st.plotly_chart(fig, use_container_width=True)

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
    if st.button("🚨 Hapus Semua Data"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM beasiswa")
        conn.commit()
        conn.close()
        st.error("Semua data telah dihapus!")

