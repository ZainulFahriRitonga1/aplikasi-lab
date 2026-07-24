import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DAF Dashboard", layout="wide", page_icon="🛢️")
st.title("🛢️ Sistem Informasi Lab - DAF Extraction")

# --- KONEKSI KE GOOGLE SHEETS ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_sheet():
    # Mengambil kunci rahasia dari Streamlit Secrets
    creds_json = st.secrets["google_credentials"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    # Membuka file berdasarkan nama dan memilih Sheet1
    return client.open("Database_DAF").sheet1

sheet = get_sheet()

# --- MEMBUAT TAB MENU ---
# Aplikasi sekarang memiliki 2 Halaman/Tab
tab1, tab2 = st.tabs(["📝 Input Harian", "📈 Rekap & Grafik Bulanan"])

# ================= TAB 1: INPUT HARIAN =================
with tab1:
    st.markdown("### Kalkulator & Input Data Baru")
    
    # Fungsi Kalkulasi
    def calculate_parameters(cawan, cawan_basah, cawan_kering, flask, flask_oil):
        berat_basah = cawan_basah - cawan
        berat_kering = cawan_kering - cawan
        moisture = ((berat_basah - berat_kering) / berat_basah) * 100 if berat_basah > 0 else 0
        oil = flask_oil - flask
        owm = (oil / berat_basah) * 100 if berat_basah > 0 else 0
        nos = 100 - moisture - owm
        return moisture, owm, nos

    # Tampilan Input
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 INLET (DAF)")
        in_cawan = st.number_input("Cawan Kosong (gr)", value=62.3370, format="%.4f", key="in_1")
        in_cawan_basah = st.number_input("Cawan + Sampel Basah (gr)", value=88.0031, format="%.4f", key="in_2")
        in_cawan_kering = st.number_input("Cawan + Sampel Kering (gr)", value=63.9199, format="%.4f", key="in_3")
        in_flask = st.number_input("Bottom Flask Kosong (gr)", value=105.7184, format="%.4f", key="in_4")
        in_flask_oil = st.number_input("Bottom + Oil (gr)", value=105.9338, format="%.4f", key="in_5")

    with col2:
        st.subheader("📤 OUTLET (DAF)")
        out_cawan = st.number_input("Cawan Kosong (gr)", value=61.3822, format="%.4f", key="out_1")
        out_cawan_basah = st.number_input("Cawan + Sampel Basah (gr)", value=86.7600, format="%.4f", key="out_2")
        out_cawan_kering = st.number_input("Cawan + Sampel Kering (gr)", value=62.8219, format="%.4f", key="out_3")
        out_flask = st.number_input("Bottom Flask Kosong (gr)", value=94.7254, format="%.4f", key="out_4")
        out_flask_oil = st.number_input("Bottom + Oil (gr)", value=94.9274, format="%.4f", key="out_5")

    # Perhitungan Otomatis
    in_moist, in_owm, in_nos = calculate_parameters(in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil)
    out_moist, out_owm, out_nos = calculate_parameters(out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil)
    selisih_owm = in_owm - out_owm

    st.markdown("---")
    # Kotak Hasil
    m1, m2, m3 = st.columns(3)
    m1.metric("💧 O/WM INLET", f"{in_owm:.3f} %")
    m2.metric("💧 O/WM OUTLET", f"{out_owm:.3f} %")
    m3.metric("⚖️ SELISIH O/WM", f"{selisih_owm:.3f} %", delta=f"{selisih_owm:.3f}%")

    # TOMBOL SIMPAN KE GOOGLE SHEETS
    if st.button("💾 SIMPAN DATA HARI INI KE DATABASE", use_container_width=True):
        try:
            # Ambil Waktu Saat Ini
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Susun data agar berurutan sesuai kolom Google Sheets Bapak
            data_baru = [now, round(in_moist,3), round(in_owm,3), round(in_nos,3), 
                         round(out_moist,3), round(out_owm,3), round(out_nos,3), round(selisih_owm,3)]
            
            # Kirim data ke Sheets
            sheet.append_row(data_baru)
            st.success(f"✅ Data berhasil disimpan ke Google Sheets pada {now}!")
        except Exception as e:
            st.error(f"Gagal menyimpan: {e}")

# ================= TAB 2: REKAP BULANAN =================
with tab2:
    st.markdown("### 📈 Database & Tren Ekstraksi")
    st.info("💡 Data di bawah ini ditarik secara otomatis dan real-time dari Google Sheets.")
    
    if st.button("🔄 Segarkan Data (Refresh)"):
        st.rerun()
        
    try:
        # Menarik data dari Google Sheets
        records = sheet.get_all_records()
        if len(records) > 0:
            df = pd.DataFrame(records)
            
            # 1. Tampilkan Tabel
            st.dataframe(df, use_container_width=True)
            
            # 2. Tampilkan Grafik
            st.markdown("#### Grafik Tren O/WM (Inlet vs Outlet)")
            # Menggunakan Tanggal sebagai dasar grafik
            df_chart = df.set_index("Tanggal & Jam")
            st.line_chart(df_chart[["Inlet - O/WM (%)", "Outlet - O/WM (%)"]])
        else:
            st.warning("Belum ada data di Google Sheets. Silakan input dan simpan data pada tab 'Input Harian'.")
    except Exception as e:
        st.error("Data tidak dapat dimuat. Pastikan Bapak sudah mengetikkan Judul Kolom di baris pertama Google Sheets.")
