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

# --- KONFIGURASI HALAMAN & SEMBUNYIKAN MANAGE APP TOTAL ---
st.set_page_config(page_title="DAF Dashboard", layout="wide", page_icon="🛢️")

hide_streamlit_style = """
<style>
[data-testid="stStatusWidget"] {visibility: hidden;}
.viewerBadge_container__1QSob {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
div[data-testid="stToolbar"] {visibility: hidden; height: 0px; position: fixed;}
/* Tambahan untuk menghilangkan tombol Manage App di pojok kanan bawah */
button[kind="header"] {visibility: hidden;}
.manage-app-button {display: none !important;}
iframe[src*="streamlit.app"] ~ div {display: none;}
section[data-testid="stSidebarNav"] + div {display: none;}
.css-1544g2n {display: none;}
div.css-1q1n0ol {display: none;}
[class*="manage-app"] {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
