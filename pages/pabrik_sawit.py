import streamlit as st
import datetime

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Pabrik Sawit Monitoring", page_icon="🏭", layout="centered")

# --- Judul dan Header ---
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("Pabrik Sawit 🏭")
    st.caption("Monitoring Dashboard")
with col_date:
    # Input tanggal di sudut kanan
    tanggal_input = st.date_input("Tanggal", datetime.date.today())

# --- Navigasi Tab ---
tab_home, tab_data, tab_summary, tab_grafik = st.tabs(["Home", "Data", "Summary", "Grafik"])

with tab_data:
    st.info("**Keterangan:** **HS** = Hari Sebelumnya | **HI** = Hari Ini | Satuan **MT**")

    # ==========================================
    # BAGIAN 1: TBS & LORY
    # ==========================================
    st.subheader("TBS and Lory")
    
    # 1. Input Data TBS
    col1, col2 = st.columns(2)
    with col1:
        tbs_restan_hs = st.number_input("TBS Restan HS (MT)", value=300000.0, step=1000.0)
        tbs_masuk = st.number_input("TBS Masuk (MT)", value=200000.0, step=1000.0)
    with col2:
        tbs_restan_hi = st.number_input("TBS Restan HI (MT)", value=200000.0, step=1000.0)
    
    # Kalkulasi TBS Olah
    tbs_olah = (tbs_restan_hs + tbs_masuk) - tbs_restan_hi
    st.success(f"**TBS Olah (otomatis):** {tbs_olah:,.0f} MT")
    
    st.markdown("---")
    
    # 2. Input Data Lori
    st.markdown("**Data Posisi Lori**")
    
    # Kapasitas diatur default 10 Ton
    kapasitas_lori = st.number_input("Kapasitas 1 Lori (MT)", value=10.0, step=0.5)
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        lori_masak = st.number_input("Lori Masak (Unit)", value=0, step=1)
        lori_mentah = st.number_input("Lori Mentah (Unit)", value=0, step=1)
        lori_rebusan = st.number_input("Lori di Dalam Rebusan (Unit)", value=0, step=1)
    with col_l2:
        lori_veron = st.number_input("Lori di Veron (Unit)", value=0, step=1)
        lori_lantai = st.number_input("Lori di Lantai (Unit)", value=0, step=1)
        
    # Kalkulasi Total Lori dan Tonase
    total_lori = lori_masak + lori_mentah + lori_rebusan + lori_veron + lori_lantai
    total_tonase_lori = total_lori * kapasitas_lori
    
    # Menampilkan Hasil Kalkulasi Lori
    st.info(f"**Total Keseluruhan Lori:** {total_lori} Unit\n\n**Total Tonase Lori:** {total_tonase_lori:,.2f} MT")
    st.divider()

    # ==========================================
    # BAGIAN 2: Waktu Olah
    # ==========================================
    st.subheader("Waktu Olah")
    col3, col4 = st.columns(2)
    with col3:
        start_olah = st.time_input("Start Olah", datetime.time(8, 0))
    with col4:
        stop_olah = st.time_input("Stop Olah", datetime.time(17, 0))
        
    # Mengubah kotak hijau menjadi kotak input agar bisa diketik bebas
    lama_olah_jam = st.number_input("Lama Olah (Jam)", value=9.0, step=0.5)
    st.divider()

    # ==========================================
    # BAGIAN 3: CPO
    # ==========================================
    st.subheader("CPO")
    cpo_hs = st.number_input("Stok CPO HS (MT)", value=300000.0, step=1000.0)
    cpo_hi = st.number_input("Stok CPO HI (MT)", value=380000.0, step=1000.0)
    dispatch_cpo = st.number_input("Dispatch CPO (MT)", value=0.0, step=1000.0)
    
    cpo_produksi = (cpo_hi + dispatch_cpo) - cpo_hs
    st.success(f"**CPO Produksi (otomatis):** {cpo_produksi:,.0f} MT")
    st.divider()

    # ==========================================
    # BAGIAN 4: PK (Kernel)
    # ==========================================
    st.subheader("PK (Kernel)")
    pk_hs = st.number_input("Stok PK HS (MT)", value=300000.0, step=1000.0)
    pk_hi = st.number_input("Stok PK HI (MT)", value=315000.0, step=1000.0)
    dispatch_pk = st.number_input("Dispatch PK (MT)", value=0.0, step=1000.0)
    
    pk_produksi = (pk_hi + dispatch_pk) - pk_hs
    st.success(f"**PK Produksi (otomatis):** {pk_produksi:,.0f} MT")
    st.divider()

    # ==========================================
    # BAGIAN 5: OER and KER
    # ==========================================
    st.subheader("OER and KER")
    
    oer = (cpo_produksi / tbs_olah * 100) if tbs_olah > 0 else 0.0
    ker = (pk_produksi / tbs_olah * 100) if tbs_olah > 0 else 0.0
    
    col_oer, col_ker = st.columns(2)
    col_oer.metric(label="% OER", value=f"{oer:,.2f} %")
    col_ker.metric(label="% KER (PK / TBS)", value=f"{ker:,.2f} %")
    st.divider()

    # ==========================================
    # TOMBOL AKSI
    # ==========================================
    st.write("### Aksi")
    btn1, btn2, btn3, btn4, btn5 = st.columns(5)
    
    if btn1.button("Reset ke Nol"):
        st.warning("Untuk reset, kita butuh setup session state.")
    if btn2.button("Save Summary", type="primary"): 
        st.toast(f"Data tanggal {tanggal_input} berhasil disimpan!")
    if btn3.button("Export PDF"):
        st.info("Fitur cetak PDF")
    if btn4.button("Kirim WA"):
        st.info("Terhubung ke API WhatsApp")
    if btn5.button("Export CSV"):
        st.info("Fitur unduh CSV")
