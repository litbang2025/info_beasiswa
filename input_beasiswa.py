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
# Fungsi insert data
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

# -------------------------
# Fungsi ambil data
# -------------------------
def fetch_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM beasiswa", conn)
    conn.close()
    return df

# -------------------------
# Fungsi hapus data
# -------------------------
def delete_data_by_id(id_value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM beasiswa WHERE id = ?", (id_value,))
    conn.commit()
    conn.close()

# -------------------------
# Fungsi update data
# -------------------------
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
    page_title="Data Beasiswa",
    page_icon="📚",
    layout="wide",  # Layout wide untuk tampilan desktop yang lebih lebar
    initial_sidebar_state="collapsed"  # Sidebar dalam keadaan tersembunyi secara default
)

# Sidebar navigasi
st.sidebar.title("Navigasi")
selection = st.sidebar.radio("Pilih Menu", ["Upload Data", "Data Tersimpan", "Edit Data", "Hapus Data", "Grafik", "Filter Data", "Laporan", "Reset Data"])

# -------------------------
# Menu Upload Data
# -------------------------
if selection == "Upload Data":
    st.title("📚 Upload Data Beasiswa")
    uploaded_file = st.file_uploader("📤 Upload File CSV atau Excel (Tanpa Header)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file, header=None)
        elif uploaded_file.name.endswith("xlsx"):
            df = pd.read_excel(uploaded_file, header=None)
        
        st.subheader("👀 Preview Data:")
        st.dataframe(df)

        # Konversi ke list dan lewati baris pertama jika header
        data = df.values.tolist()
        if not str(data[0][0]).isdigit() and not str(data[0][0]).startswith("B"):
            data = data[1:]

        if st.button("✅ Simpan ke Database"):
            insert_data(data)
            st.success("Data berhasil disimpan ke database!")

# -------------------------
# Menu Data Tersimpan
# -------------------------
elif selection == "Data Tersimpan":
    st.title("📄 Data Tersimpan")
    df_db = fetch_data()
    st.dataframe(df_db)

    # Filter dan pencarian
    st.subheader("🔍 Cari Beasiswa")
    keyword = st.text_input("Ketik kata kunci (misal: Jepang, S2, Eropa)")
    if keyword:
        filtered_df = df_db[df_db.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
        st.dataframe(filtered_df)

# -------------------------
# Menu Edit Data
# -------------------------
elif selection == "Edit Data":
    st.title("✏️ Edit Data Berdasarkan ID")
    df_db = fetch_data()
    id_edit = st.text_input("Masukkan ID yang akan diedit:")
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
            if st.button("Update Data"):
                update_data_by_id(id_edit, [benua, asal, lembaga, topuniv, program, jenis, link])
                st.success("Data berhasil diperbarui.")

# -------------------------
# Menu Hapus Data
# -------------------------
elif selection == "Hapus Data":
    st.title("🗑️ Hapus Data Berdasarkan ID")
    df_db = fetch_data()
    id_delete = st.text_input("Masukkan ID yang akan dihapus:")
    if st.button("Hapus Data"):
        if id_delete:
            delete_data_by_id(id_delete)
            st.warning(f"Data dengan ID {id_delete} telah dihapus.")

# -------------------------
# Menu Reset Data
# -------------------------
elif selection == "Reset Data":
    st.title("🧹 Reset Seluruh Data Beasiswa")
    if st.button("⚠️ Hapus Semua Data"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM beasiswa")
        conn.commit()
        conn.close()
        st.warning("⚠️ Semua data beasiswa telah dihapus dari database!")

# -------------------------
# Menu Filter DataHapus Semua Data
# -------------------------
elif selection == "Filter Data":
    st.title("🔍 Filter Data Beasiswa")
    df_db = fetch_data()
    
    # Filter berdasarkan benua
    benua_filter = st.selectbox("Pilih Benua", df_db['benua'].unique())

    # Filter berdasarkan program
    program_filter = st.selectbox("Pilih Program Beasiswa", df_db['program_beasiswa'].unique())

    # Menampilkan data berdasarkan filter
    filtered_df = df_db[(df_db['benua'] == benua_filter) & (df_db['program_beasiswa'] == program_filter)]
    st.dataframe(filtered_df)

# -------------------------
# Menu Grafik
# -------------------------
elif selection == "Grafik":
    st.title("📊 Grafik Beasiswa")
    df_db = fetch_data()

    # Pie chart berdasarkan jenis beasiswa
    st.subheader("📊 Distribusi Jenis Beasiswa")
    fig = px.pie(df_db, names='jenis_beasiswa', title='Distribusi Jenis Beasiswa')
    st.plotly_chart(fig)

    # Top universitas berdasarkan jumlah beasiswa
    st.subheader("🏅 Top Universitas dengan Beasiswa Terbanyak")
    top_univ_count = df_db['top_univ'].value_counts().reset_index()
    top_univ_count.columns = ['Universitas', 'Jumlah Beasiswa']
    fig_top_univ = px.bar(top_univ_count, x='Universitas', y='Jumlah Beasiswa', title="Top Universitas dengan Beasiswa Terbanyak")
    st.plotly_chart(fig_top_univ)

# -------------------------
# Menu Laporan PDF
# -------------------------
elif selection == "Laporan":
    st.title("📥 Unduh Data Beasiswa")
    df_db = fetch_data()
    file_format = st.selectbox("Pilih format unduhan", ["CSV", "Excel"])
    
    if file_format == "CSV":
        st.download_button("Download CSV", df_db.to_csv(index=False).encode('utf-8'), "data_beasiswa.csv")
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_db.to_excel(writer, index=False, sheet_name='Beasiswa')
        st.download_button("Download Excel", output.getvalue(), "data_beasiswa.xlsx")

