# =========================================================
# APP STREAMLIT - EXTRAER DATOS Y RENOMBRAR PDFs
# =========================================================
#
# INSTALAR LOCAL:
# pip install -r requirements.txt
#
# En Streamlit Cloud, asegúrate de tener también packages.txt
#
# EJECUTAR:
# streamlit run app.py
#
# =========================================================

import streamlit as st
import pdfplumber
import pandas as pd
import re
import zipfile
import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

# ----------------------------
# LOGO
# ----------------------------
logo = Image.open("logo.png")
st.image(logo, width=400)

# ----------------------------
# ESTILOS
# ----------------------------
page_bg_style = '''
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom right, #eaeaea, #ffffff);
    background-attachment: fixed;
}
[data-testid="stSidebar"] {
    background-color: #eaeaea;
}
h1, h2, h3, h4, h5, h6, p, label {
    color: #a81e35;
}
.stButton > button {
    background-color: #a81e35 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 8px 16px !important;
    font-weight: bold !important;
    color: white !important;
}
.stButton > button * {
    color: white !important;
    fill: white !important;
}
.stButton > button:hover {
    background-color: #000000 !important;
    color: white !important;
}
.stButton > button:hover * {
    color: white !important;
}
</style>
'''
st.markdown(page_bg_style, unsafe_allow_html=True)

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Renombrador de PDFs",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Renombrador Masivo de CLA")

# =========================================================
# SUBIR ZIP
# =========================================================

uploaded_zip = st.file_uploader(
    "Selecciona el archivo ZIP con PDFs",
    type=["zip"]
)

# =========================================================
# FUNCIÓN EXTRAER DATOS
# =========================================================

def extraer_datos(texto):
    patrones = [
        r"estudiante\s+(.*?)\s*,?\s*con\s+DNI\s+N.?°?\s*(\d{8})",
        r"estudiante\s+(.*?)\s*,?\s*con\s+DNI\s*N.?°?\s*(\d{8})",
        r"([A-ZÁÉÍÓÚÑ ]+)\s*,?\s*con\s+DNI\s*N.?°?\s*(\d{8})"
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            nombre = match.group(1).strip()
            dni = match.group(2).strip()
            nombre = " ".join(nombre.split())  # limpiar espacios múltiples
            return dni, nombre
    return None, None

# =========================================================
# LIMPIAR NOMBRES
# =========================================================

def limpiar_nombre(nombre):
    return re.sub(r'[\\/:*?"<>|]', '', nombre)

# =========================================================
# PROCESAR PDFs
# =========================================================

if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_in:
        archivos_pdf = [f for f in zip_in.namelist() if f.lower().
