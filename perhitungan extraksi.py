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
    creds_json = st.secrets["google_credentials"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Database_DAF").get_worksheet(0)

sheet = get_sheet()

# --- MEMBUAT TAB MENU ---
tab1, tab2 = st.tabs(["📝 Input Harian", "📈 Rekap & Tren 24 Jam"])

# ================= TAB 1: INPUT HARIAN =================
with tab1:
    st.markdown("### 📥 Input Data Laboratorium & Waktu Analisa")
    
    # Tanggal pakai Kalender, Jam pakai Ketik Bebas 100%
    col_tgl, col_jam = st.columns(2)
    with col_tgl:
        input_tanggal = st.date_input("📅 Pilih Tanggal Analisa", value=datetime.today())
    with col_jam:
        default_jam = datetime.now().strftime("%H:%M")
        input_jam = st.text_input("⏰ Ketik Jam Analisa (Bebas)", value=default_jam, placeholder="Contoh: 08:14 atau 23:55")

    def calculate_parameters(cawan, cawan_basah, cawan_kering, flask, flask_oil):
        berat_basah = cawan_basah - cawan
        berat_kering = cawan_kering - cawan
        moisture = ((berat_basah - berat_kering) / berat_basah) * 100 if berat_basah > 0 else 0
        oil = flask_oil - flask
        owm = (oil / berat_basah) * 100 if berat_basah > 0 else 0
        nos = 100 - moisture - owm
        return moisture, owm, nos

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

    in_moist, in_owm, in_nos = calculate_parameters(in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil)
    out_moist, out_owm, out_nos = calculate_parameters(out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil)
    selisih_owm = in_owm - out_owm

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("💧 O/WM INLET", f"{in_owm:.3f} %")
    m2.metric("💧 O/WM OUTLET", f"{out_owm:.3f} %")
    m3.metric("⚖️ SELISIH O/WM", f"{selisih_owm:.3f} %", delta=f"{selisih_owm:.3f}%")

    if st.button("💾 SIMPAN KE DATABASE", use_container_width=True):
        try:
            # Menggabungkan tanggal dari kalender dan jam yang diketik bebas
            waktu_gabungan = f"{input_tanggal} {input_jam}"
            
            data_baru = [waktu_gabungan, round(in_moist,3), round(in_owm,3), round(in_nos,3), 
                         round(out_moist,3), round(out_owm,3), round(out_nos,3), round(selisih_owm,3)]
            
            sheet.append_row(data_baru, value_input_option='USER_ENTERED')
            st.success(f"✅ Data berhasil disimpan untuk waktu: {waktu_gabungan}!")
        except Exception as e:
            st.error(f"Gagal menyimpan: {e}")

# ================= TAB 2: REKAP BULANAN =================
with tab2:
    st.markdown("### 📈 Logbook & Riwayat Data")
    
    if st.button("🔄 Segarkan Data"):
        st.rerun()
        
    try:
        records = sheet.get_all_records()
        if len(records) > 0:
            df = pd.DataFrame(records)
            st.markdown("#### Daftar Seluruh Log Pengujian")
            st.dataframe(df, use_container_width=True)
            
            try:
                st.markdown("#### Grafik Tren Pergerakan O/WM")
                kolom_waktu = df.columns[0] 
                df_chart = df.set_index(kolom_waktu)
                
                kolom_inlet = [c for c in df.columns if "Inlet" in c and "O/WM" in c][0]
                kolom_outlet = [c for c in df.columns if "Outlet" in c and "O/WM" in c][0]
                
                st.line_chart(df_chart[[kolom_inlet, kolom_outlet]])
            except Exception:
                st.info("Grafik akan terbentuk otomatis setelah data historis bertambah.")
        else:
            st.info("Belum ada data tersimpan di Google Sheets.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
