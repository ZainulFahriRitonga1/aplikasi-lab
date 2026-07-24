import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import io

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DAF Dashboard", layout="wide", page_icon="🛢️")

# --- SISTEM LOGIN SEDERHANA ---
def check_password():
    """Mengembalikan True jika user berhasil login."""
    
    def password_entered():
        # Masukkan Username & Password rahasia di sini
        if st.session_state["username"] == "zainul" and st.session_state["password"] == "sawit12345":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Hapus password dari memori demi keamanan
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Tampilkan kotak login jika belum login
        st.title("🔐 Login Sistem Informasi Lab - DAF")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Username atau Password salah. Silakan coba lagi.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Login Sistem Informasi Lab - DAF")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 Username atau Password salah. Silakan coba lagi.")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Hentikan eksekusi halaman jika belum login

# ================= KODE UTAMA SETELAH LOGIN BERHASIL =================
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

# --- FUNGSI PEMBUAT PDF LAPORAN LAB ---
def create_pdf_report(waktu, in_raw, in_res, out_raw, out_res, selisih):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor("#1b4332")
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#555555")
    )
    
    story.append(Paragraph("LAPORAN ANALISA LABORATORIUM - DAF EXTRACTION", title_style))
    story.append(Paragraph(f"Waktu Analisa: {waktu}", subtitle_style))
    story.append(Spacer(1, 15))
    
    data_table = [
        ["Parameter Pengujian", "INLET DAF", "OUTLET DAF", "SELISIH (In - Out)"],
        ["Cawan Kosong (gr)", f"{in_raw[0]:.4f}", f"{out_raw[0]:.4f}", "-"],
        ["Cawan + Sampel Basah (gr)", f"{in_raw[1]:.4f}", f"{out_raw[1]:.4f}", "-"],
        ["Cawan + Sampel Kering (gr)", f"{in_raw[2]:.4f}", f"{out_raw[2]:.4f}", "-"],
        ["Bottom Flask Kosong (gr)", f"{in_raw[3]:.4f}", f"{out_raw[3]:.4f}", "-"],
        ["Bottom Flask + Oil (gr)", f"{in_raw[4]:.4f}", f"{out_raw[4]:.4f}", "-"],
        ["Berat Sampel Basah (gr)", f"{in_res[0]:.4f}", f"{out_res[0]:.4f}", "-"],
        ["Berat Sampel Kering (gr)", f"{in_res[1]:.4f}", f"{out_res[1]:.4f}", "-"],
        ["Minyak / Oil (gr)", f"{in_res[2]:.4f}", f"{out_res[2]:.4f}", f"{selisih[0]:.4f} gr"],
        ["Moisture (%)", f"{in_res[3]:.2f} %", f"{out_res[3]:.2f} %", "-"],
        ["O/WM (%)", f"{in_res[4]:.3f} %", f"{out_res[4]:.3f} %", f"{selisih[1]:.3f} %"],
        ["O/DM (%)", f"{in_res[5]:.2f} %", f"{out_res[5]:.2f} %", f"{selisih[2]:.2f} %"],
        ["NOS (%)", f"{in_res[6]:.2f} %", f"{out_res[6]:.2f} %", f"{selisih[3]:.2f} %"],
    ]
    
    t = Table(data_table, colWidths=[180, 110, 110, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2d6a4f")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f3f5")]),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- MEMBUAT TAB MENU ---
tab1, tab2 = st.tabs(["📝 Input Harian", "📈 Rekap & Tren 24 Jam"])

# ================= TAB 1: INPUT HARIAN =================
with tab1:
    st.markdown("### 📥 Input Data Laboratorium & Waktu Analisa")
    st.info("💡 Tip: Anda bisa mengetik angka dengan bebas (bisa menggunakan titik . atau koma ,).")
    
    col_tgl, col_jam = st.columns(2)
    with col_tgl:
        input_tanggal = st.date_input("📅 Pilih Tanggal Analisa", value=datetime.today())
    with col_jam:
        default_jam = datetime.now().strftime("%H:%M")
        input_jam = st.text_input("⏰ Ketik Jam Analisa (Bebas)", value=default_jam)

    def parse_angka(teks):
        try:
            if not teks:
                return 0.0
            teks_bersih = str(teks).strip().replace(',', '.')
            return float(teks_bersih)
        except:
            return 0.0

    def calculate_parameters(cawan, cawan_basah, cawan_kering, flask, flask_oil):
        berat_basah = cawan_basah - cawan
        berat_kering = cawan_kering - cawan
        moisture = ((berat_basah - berat_kering) / berat_basah) * 100 if berat_basah > 0 else 0
        
        oil = flask_oil - flask
        owm = (oil / berat_basah) * 100 if berat_basah > 0 else 0
        odm = (oil / berat_kering) * 100 if berat_kering > 0 else 0
        nos = 100 - moisture - owm
        return berat_basah, berat_kering, oil, moisture, owm, odm, nos

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 INLET (DAF)")
        in_cawan_str = st.text_input("Cawan Kosong (gr)", value="88.1707", key="in_1")
        in_cawan_basah_str = st.text_input("Cawan + Sampel Basah (gr)", value="113.5584", key="in_2")
        in_cawan_kering_str = st.text_input("Cawan + Sampel Kering (gr)", value="89.9324", key="in_3")
        in_flask_str = st.text_input("Bottom Flask Kosong (gr)", value="80.8070", key="in_4")
        in_flask_oil_str = st.text_input("Bottom + Oil (gr)", value="105.9338", key="in_5")

    with col2:
        st.subheader("📤 OUTLET (DAF)")
        out_cawan_str = st.text_input("Cawan Kosong (gr)", value="61.3822", key="out_1")
        out_cawan_basah_str = st.text_input("Cawan + Sampel Basah (gr)", value="86.7600", key="out_2")
        out_cawan_kering_str = st.text_input("Cawan + Sampel Kering (gr)", value="62.8219", key="out_3")
        out_flask_str = st.text_input("Bottom Flask Kosong (gr)", value="94.7254", key="out_4")
        out_flask_oil_str = st.text_input("Bottom + Oil (gr)", value="94.9274", key="out_5")

    in_cawan = parse_angka(in_cawan_str)
    in_cawan_basah = parse_angka(in_cawan_basah_str)
    in_cawan_kering = parse_angka(in_cawan_kering_str)
    in_flask = parse_angka(in_flask_str)
    in_flask_oil = parse_angka(in_flask_oil_str)

    out_cawan = parse_angka(out_cawan_str)
    out_cawan_basah = parse_angka(out_cawan_basah_str)
    out_cawan_kering = parse_angka(out_cawan_kering_str)
    out_flask = parse_angka(out_flask_str)
    out_flask_oil = parse_angka(out_flask_oil_str)

    in_bb, in_bk, in_oil, in_moist, in_owm, in_odm, in_nos = calculate_parameters(in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil)
    out_bb, out_bk, out_oil, out_moist, out_owm, out_odm, out_nos = calculate_parameters(out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil)
    
    selisih_oil = in_oil - out_oil
    selisih_owm = in_owm - out_owm
    selisih_odm = in_odm - out_odm
    selisih_nos = in_nos - out_nos

    st.markdown("---")
    st.markdown("### 📊 Hasil Perhitungan Laboratorium")
    
    st.text("INLET DAF:")
    mi1, mi2, mi3, mi4 = st.columns(4)
    mi1.metric("💧 Moisture", f"{in_moist:.2f} %")
    mi2.metric("🛢️ O/WM", f"{in_owm:.3f} %")
    mi3.metric("🛢️ O/DM", f"{in_odm:.2f} %")
    mi4.metric("⚖️ NOS", f"{in_nos:.2f} %")

    st.text("OUTLET DAF:")
    mo1, mo2, mo3, mo4 = st.columns(4)
    mo1.metric("💧 Moisture", f"{out_moist:.2f} %")
    mo2.metric("🛢️ O/WM", f"{out_owm:.3f} %")
    mo3.metric("🛢️ O/DM", f"{out_odm:.2f} %")
    mo4.metric("⚖️ NOS", f"{out_nos:.2f} %")

    st.markdown("---")
    st.markdown("### 📉 Selisih (Inlet - Outlet)")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("⚖️ Selisih Oil", f"{selisih_oil:.4f} gr")
    s2.metric("⚖️ Selisih O/WM", f"{selisih_owm:.3f} %")
    s3.metric("⚖️ Selisih O/DM", f"{selisih_odm:.2f} %")
    s4.metric("⚖️ Selisih NOS", f"{selisih_nos:.2f} %")

    st.markdown("---")
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("💾 SIMPAN KE DATABASE", use_container_width=True):
            try:
                waktu_gabungan = f"{input_tanggal} {input_jam}"
                data_baru = [
                    waktu_gabungan,
                    in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil,
                    round(in_bb,4), round(in_bk,4), round(in_oil,4), round(in_moist,2), round(in_owm,3), round(in_odm,2), round(in_nos,2),
                    out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil,
                    round(out_bb,4), round(out_bk,4), round(out_oil,4), round(out_moist,2), round(out_owm,3), round(out_odm,2), round(out_nos,2),
                    round(selisih_oil,4), round(selisih_owm,3), round(selisih_odm,2), round(selisih_nos,2)
                ]
                sheet.append_row(data_baru, value_input_option='USER_ENTERED')
                st.success(f"✅ Data lengkap berhasil disimpan ke Google Sheets!")
            except Exception as e:
                st.error(f"Gagal menyimpan: {e}")

    with col_act2:
        waktu_gabungan = f"{input_tanggal} {input_jam}"
        in_raw_list = [in_cawan, in_cawan_basah, in_cawan_kering, in_flask, in_flask_oil]
        in_res_list = [in_bb, in_bk, in_oil, in_moist, in_owm, in_odm, in_nos]
        out_raw_list = [out_cawan, out_cawan_basah, out_cawan_kering, out_flask, out_flask_oil]
        out_res_list = [out_bb, out_bk, out_oil, out_moist, out_owm, out_odm, out_nos]
        selisih_list = [selisih_oil, selisih_owm, selisih_odm, selisih_nos]
        
        pdf_bytes = create_pdf_report(waktu_gabungan, in_raw_list, in_res_list, out_raw_list, out_res_list, selisih_list)
        
        st.download_button(
            label="📄 DOWNLOAD LAPORAN PDF",
            data=pdf_bytes,
            file_name=f"Laporan_Lab_DAF_{input_tanggal}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ================= TAB 2: REKAP BULANAN =================
with tab2:
    st.markdown("### 📈 Logbook & Riwayat Data Lab")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
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
                
                kolom_inlet = [c for c in df.columns if "In -" in c and "O/WM" in c][0]
                kolom_outlet = [c for c in df.columns if "Out -" in c and "O/WM" in c][0]
                
                st.line_chart(df_chart[[kolom_inlet, kolom_outlet]])
            except Exception as e_grafik:
                st.info(f"Grafik menyesuaikan data: {e_grafik}")
        else:
            st.info("Belum ada data tersimpan di Google Sheets.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
