# =========================================================
# APP STREAMLIT - EXTRAER DATOS Y RENOMBRAR PDFs
# =========================================================
#
# INSTALAR:
# pip install streamlit pdfplumber pandas openpyxl
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

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Renombrador de PDFs",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Renombrador Automático de PDFs")

st.write("""
Sube varios archivos PDF y la aplicación:

✅ Extraerá DNI y nombre  
✅ Renombrará los PDFs automáticamente  
✅ Generará un Excel resumen  
✅ Creará un ZIP descargable con TODOS los PDFs
""")

# =========================================================
# SUBIR ARCHIVOS
# =========================================================

uploaded_files = st.file_uploader(
    "Selecciona PDFs",
    type=["pdf"],
    accept_multiple_files=True
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

        match = re.search(
            patron,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            nombre = match.group(1).strip()
            dni = match.group(2).strip()

            # Limpiar espacios múltiples
            nombre = " ".join(nombre.split())

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

if uploaded_files:

    st.success(f"✅ {len(uploaded_files)} PDFs cargados")

    if st.button("🚀 Procesar PDFs"):

        resultados = []

        zip_buffer = io.BytesIO()

        total_ok = 0
        total_error = 0

        # =====================================================
        # CREAR ZIP
        # =====================================================

        with zipfile.ZipFile(zip_buffer, "w") as zipf:

            for archivo in uploaded_files:

                try:

                    texto_completo = ""

                    # =================================================
                    # LEER PDF
                    # =================================================

                    with pdfplumber.open(archivo) as pdf:

                        for pagina in pdf.pages:

                            texto = pagina.extract_text()

                            if texto:
                                texto_completo += texto + "\n"

                    # =================================================
                    # EXTRAER DATOS
                    # =================================================

                    dni, nombre = extraer_datos(texto_completo)

                    # =================================================
                    # SI ENCUENTRA DATOS
                    # =================================================

                    if dni and nombre:

                        nombre_limpio = limpiar_nombre(nombre)

                        nuevo_nombre = f"{dni} - {nombre_limpio}.pdf"

                        # Agregar PDF renombrado al ZIP
                        zipf.writestr(
                            nuevo_nombre,
                            archivo.getvalue()
                        )

                        resultados.append({
                            "PDF Original": archivo.name,
                            "DNI": dni,
                            "Nombre": nombre,
                            "Nuevo Nombre": nuevo_nombre,
                            "Estado": "OK"
                        })

                        total_ok += 1

                    # =================================================
                    # SI NO ENCUENTRA DATOS
                    # =================================================

                    else:

                        # Guardar PDF original
                        zipf.writestr(
                            archivo.name,
                            archivo.getvalue()
                        )

                        resultados.append({
                            "PDF Original": archivo.name,
                            "DNI": "",
                            "Nombre": "",
                            "Nuevo Nombre": archivo.name,
                            "Estado": "NO ENCONTRADO"
                        })

                        total_error += 1

                # =====================================================
                # SI OCURRE ERROR
                # =====================================================

                except Exception as e:

                    # Guardar PDF original aunque falle
                    zipf.writestr(
                        archivo.name,
                        archivo.getvalue()
                    )

                    resultados.append({
                        "PDF Original": archivo.name,
                        "DNI": "",
                        "Nombre": "",
                        "Nuevo Nombre": archivo.name,
                        "Estado": f"ERROR: {str(e)}"
                    })

                    total_error += 1

        # =========================================================
        # CREAR DATAFRAME
        # =========================================================

        df = pd.DataFrame(resultados)

        # =========================================================
        # MOSTRAR RESULTADOS
        # =========================================================

        st.subheader("📋 Resultados")

        st.dataframe(
            df,
            use_container_width=True
        )

        # =========================================================
        # MÉTRICAS
        # =========================================================

        col1, col2 = st.columns(2)

        col1.metric(
            "✅ Procesados Correctamente",
            total_ok
        )

        col2.metric(
            "⚠️ No encontrados / errores",
            total_error
        )

        # =========================================================
        # CREAR EXCEL
        # =========================================================

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Resultados"
            )

        excel_buffer.seek(0)

        # =========================================================
        # BOTÓN DESCARGAR EXCEL
        # =========================================================

        st.download_button(
            label="📥 Descargar Excel",
            data=excel_buffer,
            file_name="resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # =========================================================
        # BOTÓN DESCARGAR ZIP
        # =========================================================

        zip_buffer.seek(0)

        st.download_button(
            label="📦 Descargar ZIP con TODOS los PDFs",
            data=zip_buffer,
            file_name="PDFs_Procesados.zip",
            mime="application/zip"
        )

        st.success("✅ Proceso finalizado")
