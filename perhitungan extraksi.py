import streamlit as st

# Konfigurasi Halaman Web (Dibuat lebih lebar dan diberi ikon)
st.set_page_config(page_title="DAF Extraction Dashboard", layout="wide", page_icon="🛢️")

# Judul dengan gaya Dashboard
st.title("🛢️ Dashboard Analisa Lab - DAF Extraction")
st.markdown("---")

# Fungsi Kalkulasi
def calculate_parameters(cawan, cawan_basah, cawan_kering, flask, flask_oil):
    berat_basah = cawan_basah - cawan
    berat_kering = cawan_kering - cawan
    moisture = ((berat_basah - berat_kering) / berat_basah) * 100 if berat_basah > 0 else 0
    oil = flask_oil - flask
    owm = (oil / berat_basah) * 100 if berat_basah > 0 else 0
    odm = (oil / berat_kering) * 100 if berat_kering > 0 else 0
    nos = 100 - moisture - owm
    return berat_basah, berat_kering, moisture, oil, owm, odm, nos

# Fitur Expander: Input data bisa dilipat agar tampilan rapi
with st.expander("📝 BUKA UNTUK INPUT DATA TIMBANGAN", expanded=True):
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

# Eksekusi Perhitungan
in_res = calculate_parameters(in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil)
out_res = calculate_parameters(out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil)

st.markdown("---")
st.subheader("📊 Laporan Hasil Analisa")

# Menampilkan Metric Cards (Tampilan Visual Profesional)
st.markdown("#### 1. Perbandingan O/WM (Oil to Wet Matter)")
m1, m2, m3 = st.columns(3)
m1.metric(label="💧 O/WM INLET", value=f"{in_res[4]:.3f} %")
m2.metric(label="💧 O/WM OUTLET", value=f"{out_res[4]:.3f} %")
selisih_owm = in_res[4] - out_res[4]
# Indikator Delta otomatis
m3.metric(label="⚖️ SELISIH O/WM", value=f"{selisih_owm:.3f} %", delta=f"{selisih_owm:.3f}%")

st.markdown("#### 2. Perbandingan Moisture (Kadar Air)")
m4, m5, m6 = st.columns(3)
m4.metric(label="💨 Moisture INLET", value=f"{in_res[2]:.2f} %")
m5.metric(label="💨 Moisture OUTLET", value=f"{out_res[2]:.2f} %")
selisih_moist = in_res[2] - out_res[2]
m6.metric(label="⚖️ SELISIH Moisture", value=f"{selisih_moist:.2f} %", delta=f"{selisih_moist:.2f}%")

st.markdown("#### 3. Tabel Rincian Parameter Ekstraksi")
st.markdown(f"""
| Parameter Analisa | INLET DAF | OUTLET DAF |
| :--- | :--- | :--- |
| **Berat Sampel Basah (gr)** | {in_res[0]:.4f} | {out_res[0]:.4f} |
| **Berat Kering (gr)** | {in_res[1]:.4f} | {out_res[1]:.4f} |
| **Oil (gr)** | {in_res[3]:.4f} | {out_res[3]:.4f} |
| **O/DM (%)** | {in_res[5]:.4f} | {out_res[5]:.4f} |
| **NOS (%)** | {in_res[6]:.4f} | {out_res[6]:.4f} |
""")