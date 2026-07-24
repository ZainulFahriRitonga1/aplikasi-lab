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
st.set_page_config(page_title="DAF & Losses Dashboard", layout="wide", page_icon="🛢️")

# CSS untuk menyembunyikan menu atas & footer bawaan Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
div[data-testid="stStatusWidget"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- KONEKSI KE GOOGLE SHEETS ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_sheets():
    creds_json = st.secrets["google_credentials"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Database_DAF")
    
    sheet_daf = spreadsheet.get_worksheet(0) 
    
    try:
        sheet_users = spreadsheet.worksheet("Users")
    except:
        sheet_users = spreadsheet.add_worksheet(title="Users", rows="100", cols="2")
        sheet_users.append_row(["Username", "Password"], value_input_option='USER_ENTERED')
        
    try:
        sheet_losses = spreadsheet.worksheet("Losses")
    except:
        sheet_losses = spreadsheet.add_worksheet(title="Losses", rows="100", cols="10")
        sheet_losses.append_row([
            "Waktu", "Stasiun", "Berat Basah", "Berat Kering", 
            "Berat Minyak", "Ratio (%)", "Moisture (%)", "Losses (%)", "Petugas"
        ], value_input_option='USER_ENTERED')
        
    return sheet_daf, sheet_users, sheet_losses

sheet, sheet_users, sheet_losses = get_sheets()

# --- SISTEM LOGIN DENGAN TAB MENU DI DEPAN ---
def auth_system():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.title("🔐 Sistem Informasi Lab - Palm Oil Mill")
        
        role_login = st.radio("Pilih Masuk Sebagai:", ["👤 Anggota (Staff Lab)", "🛠️ Administrator (Admin)"], horizontal=True)
        st.markdown("---")
        
        tab_login, tab_reg, tab_reset = st.tabs(["🔑 Masuk (Login)", "📝 Daftar Akun Baru", "🔄 Lupa / Ubah Password"])
        
        with tab_login:
            st.subheader("Silakan Masuk")
            u_login = st.text_input("Username", key="u_log_input")
            p_login = st.text_input("Password", type="password", key="p_log_input")
            
            if st.button("Masuk Sekarang", use_container_width=True):
                try:
                    if role_login == "🛠️ Administrator (Admin)":
                        if u_login == "admin" and p_login == "admin123":
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = u_login
                            st.session_state["role"] = "Admin"
                            st.rerun()
                        else:
                            st.error("❌ Username atau Password Admin salah!")
                    else:
                        users_data = sheet_users.get_all_records()
                        df_users = pd.DataFrame(users_data)
                        
                        if not df_users.empty and "Username" in df_users.columns:
                            df_users["Username"] = df_users["Username"].astype(str).str.strip()
                            df_users["Password"] = df_users["Password"].astype(str).str.strip()
                            
                            match = df_users[(df_users["Username"] == u_login.strip()) & (df_users["Password"] == p_login.strip())]
                            if not match.empty:
                                st.session_state["logged_in"] = True
                                st.session_state["username"] = u_login
                                st.session_state["role"] = "Anggota"
                                st.rerun()
                            else:
                                st.error("❌ Username atau Password Anggota salah!")
                        else:
                            st.error("❌ Belum ada akun terdaftar di database.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat login: {e}")

        with tab_reg:
            st.subheader("Buat Akun Anggota Baru")
            u_reg = st.text_input("Buat Username Baru", key="u_reg_input")
            p_reg = st.text_input("Buat Password Baru", type="password", key="p_reg_input")
            
            if st.button("Daftar Akun Baru", use_container_width=True):
                if not u_reg or not p_reg:
                    st.warning("⚠️ Username dan Password tidak boleh kosong!")
                else:
                    try:
                        users_data = sheet_users.get_all_records()
                        df_users = pd.DataFrame(users_data)
                        
                        if not df_users.empty and "Username" in df_users.columns:
                            existing_users = df_users["Username"].astype(str).str.strip().values
                            if u_reg.strip() in existing_users:
                                st.error("❌ Username sudah terdaftar! Gunakan username lain.")
                                return False
                                
                        sheet_users.append_row([u_reg.strip(), p_reg.strip()], value_input_option='USER_ENTERED')
                        st.success("✅ Pendaftaran berhasil! Silakan pindah ke tab 'Masuk (Login)' untuk masuk.")
                    except Exception as e:
                        st.error(f"Gagal mendaftar: {e}")

        with tab_reset:
            st.subheader("Ubah Password Akun")
            u_reset = st.text_input("Masukkan Username Anda", key="u_reset_input")
            p_reset = st.text_input("Masukkan Password Baru", type="password", key="p_reset_input")
            
            if st.button("Perbarui Password", use_container_width=True):
                if not u_reset or not p_reset:
                    st.warning("⚠️ Username dan Password baru tidak boleh kosong!")
                else:
                    try:
                        cell = sheet_users.find(u_reset.strip())
                        if cell:
                            row_idx = cell.row
                            sheet_users.update_cell(row_idx, 2, p_reset.strip())
                            st.success("✅ Password berhasil diubah! Silakan login menggunakan password baru Anda.")
                        else:
                            st.error("❌ Username tidak ditemukan di database!")
                    except Exception as e:
                        st.error(f"Gagal merubah password: {e}")
                        
        return False
    else:
        return True

if not auth_system():
    st.stop()

# --- SIDEBAR NAVIGASI & MENU MULTI-HALAMAN ---
with st.sidebar:
    st.write(f"👤 User: **{st.session_state.get('username')}**")
    st.write(f"🛡️ Hak Akses: **{st.session_state.get('role')}**")
    st.markdown("---")
    
    st.subheader("📌 Dashboard")
    pilih_halaman = st.radio(
        "Pilih Halaman:", 
        [
            "🛢️ Input DAF Extraction", 
            "📈 Rekap & Tren DAF",
            "📊 Perhitungan Losses & TOL"
        ]
    )
    
    st.markdown("---")
    if st.button("🚪 Keluar (Logout)", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- FUNGSI PEMBUAT PDF LAPORAN LAB DAF ---
def create_pdf_report(waktu, in_raw, in_res, out_raw, out_res, selisih):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, alignment=1, textColor=colors.HexColor("#1b4332"))
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.HexColor("#555555"))
    
    story.append(Paragraph("LAPORAN ANALISA LABORATORIUM - DAF EXTRACTION", title_style))
    story.append(Paragraph(f"Waktu Analisa: {waktu} | Oleh: {st.session_state.get('username')} ({st.session_state.get('role')})", subtitle_style))
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
        ["O/DM (%)", f"{in_res[5]:.2f} %", f"{out_res[5]:.2f} %", f"{selisih[2]:.3f} %"],
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


# ================= KONDISI HALAMAN (MULTI-PAGE) =================

# 1. HALAMAN: INPUT DAF EXTRACTION
if pilih_halaman == "🛢️ Input DAF Extraction":
    st.title("🛢️ Sistem Informasi Lab - DAF Extraction")
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
    mi3.metric("🛢️ O/DM", f"{in_odm:.3f} %")
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
    s3.metric("⚖️ Selisih O/DM", f"{selisih_odm:.3f} %")
    s4.metric("⚖️ Selisih NOS", f"{selisih_nos:.3f} %")

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
                st.success(f"✅ Data lengkap berhasil disimpan ke Google Sheets oleh {st.session_state.get('username')}!")
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

# 2. HALAMAN: REKAP & TREN 24 JAM
elif pilih_halaman == "📈 Rekap & Tren DAF":
    st.title("📈 Logbook & Riwayat Data Lab DAF")
    
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
                kolom_wakun = df.columns[0] 
                df_chart = df.set_index(kolom_wakun)
                
                kolom_inlet = [c for c in df.columns if "In -" in c and "O/WM" in c][0]
                kolom_outlet = [c for c in df.columns if "Out -" in c and "O/WM" in c][0]
                
                st.line_chart(df_chart[[kolom_inlet, kolom_outlet]])
            except Exception as e_grafik:
                st.info(f"Grafik menyesuaikan data: {e_grafik}")
        else:
            st.info("Belum ada data tersimpan di Google Sheets.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")

# 3. HALAMAN: PERHITUNGAN LOSSES & TOL (TOTAL OIL LOSSES)
elif pilih_halaman == "📊 Perhitungan Losses & TOL":
    st.title("📊 Perhitungan Losses & Total Oil Losses (TOL)")
    st.markdown("### 📥 Form Input Analisa Losses per Stasiun Pabrik")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.date_input("📅 Tanggal Analisa", value=datetime.today(), key="loss_tgl")
        st.selectbox(
            "🏭 Pilih Stasiun / Sample", 
            [
                "Ampas Press (Pressed Fibre)", 
                "Tandan Kosong (Empty Bunch)", 
                "Sebelum Bunch Press", 
                "Sesudah Bunch Press", 
                "Decanter Solid", 
                "Sludge Centrifuge", 
                "Sludge Waste", 
                "Biji / Nut"
            ], 
            key="loss_stasiun"
        )
        berat_basah_loss = st.text_input("Berat Sampel Basah (gr)", value="100.0", key="lb_1")
        ratio_terolah = st.slider("📊 Ratio Tandan Terolah (%)", min_value=0.0, max_value=100.0, value=100.0, step=0.1, help="Persentase proporsi yang terolah vs tidak terolah")
    with col_l2:
        st.text_input("⏰ Jam Analisa", value=datetime.now().strftime("%H:%M"), key="loss_jam")
        berat_kering_loss = st.text_input("Berat Sampel Kering / Residu (gr)", value="35.0", key="lb_2")
        berat_minyak_loss = st.text_input("Berat Minyak / Ekstrak (gr)", value="0.5", key="lb_3")

    def parse_num(t):
        try:
            return float(str(t).strip().replace(',', '.'))
        except:
            return 0.0

    b_basah = parse_num(berat_basah_loss)
    b_kering = parse_num(berat_kering_loss)
    b_minyak = parse_num(berat_minyak_loss)

    moisture_loss = ((b_basah - b_kering) / b_basah) * 100 if b_basah > 0 else 0
    raw_losses = (b_minyak / b_basah) * 100 if b_basah > 0 else 0
    persen_losses = raw_losses * (ratio_terolah / 100.0)

    st.markdown("---")
    st.markdown("### 📈 Hasil Perhitungan Stasiun Ini")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💧 Kadar Air (Moisture)", f"{moisture_loss:.2f} %")
    m2.metric("⚙️ Ratio Terolah", f"{ratio_terolah:.1f} %")
    m3.metric("📉 Losses Akhir", f"{persen_losses:.3f} %", delta_color="inverse")

    st.markdown("---")
    if st.button("💾 SIMPAN LOSSES KE DATABASE", use_container_width=True):
        try:
            waktu_loss = f"{st.session_state.get('loss_tgl')} {st.session_state.get('loss_jam')}"
            stasiun_pilih = st.session_state.get('loss_stasiun')
            user_pembuat = st.session_state.get('username')
            
            data_row = [
                waktu_loss, stasiun_pilih, 
                round(b_basah, 4), round(b_kering, 4), round(b_minyak, 4), 
                round(ratio_terolah, 2), round(moisture_loss, 2), round(persen_losses, 3), user_pembuat
            ]
            sheet_losses.append_row(data_row, value_input_option='USER_ENTERED')
            st.success(f"✅ Data Losses stasiun '{stasiun_pilih}' berhasil disimpan ke database!")
        except Exception as e:
            st.error(f"Gagal menyimpan data losses: {e}")

    st.markdown("---")
    st.markdown("### 🧮 Rekapitulasi Total Oil Losses (TOL)")
    st.info("💡 TOL (Total Oil Losses) otomatis mengakumulasi seluruh data losses stasiun termasuk *Sludge Waste*.")

    if st.button("🔄 Hitung & Refresh Total TOL", use_container_width=True):
        st.rerun()

    try:
        # Perbaikan aman menggunakan get_all_values() agar bebas dari error duplikat header
        rows = sheet_losses.get_all_values()
        if len(rows) > 1:
            header = rows[0]
            data = rows[1:]
            df_loss = pd.DataFrame(data, columns=header[:len(data[0])])
            
            st.dataframe(df_loss, use_container_width=True)
            
            # Cari kolom losses secara dinamis berdasarkan kata kunci
            matched_cols = [c for c in df_loss.columns if "Losses" in c]
            if matched_cols:
                col_target = matched_cols[0]
                total_tol = pd.to_numeric(df_loss[col_target].astype(str).str.replace(',', '.'), errors='coerce').sum()
                
                st.markdown("---")
                st.metric(
                    label="🌟 **TOTAL OIL LOSSES (TOL) Keseluruhan**", 
                    value=f"{total_tol:.3f} %",
                    help="Akumulasi seluruh losses stasiun termasuk sludge waste"
                )
        else:
            st.info("Belum ada data losses tersimpan di database untuk dikalkulasi menjadi TOL.")
    except Exception as e:
        st.info(f"Memuat tabel rekapitulasi losses... ({e})")
