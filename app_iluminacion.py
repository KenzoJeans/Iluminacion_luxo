import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import requests
import warnings
import difflib
from datetime import datetime

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard SST · Iluminación",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CONSTANTES: NIVELES NORMATIVOS POR ÁREA
# ─────────────────────────────────────────────────────────────
NORMA_LUX = {
    "Sistemas":    (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Financiero":  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Comercial":   (300, 500, "RETILAP T440.1 / ISO 8995"),
    "RRHH":        (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Inventarios": (300, 500, "RETILAP T440.1 – Depósito"),
    "Tesoreria":   (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Diseno":      (500, 750, "RETILAP T440.1 – Diseño/Detalle fino"),
    "Mercadeo":    (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Ingenieria":  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Importados":  (100, 300, "RETILAP T440.1 – Depósito"),
    "Tintoreria":  (200, 500, "RETILAP T440.1 – Industria textil"),
    "PTAR":        (200, 300, "RETILAP T440.1 – Planta industrial"),
    "Insumos":     (100, 300, "RETILAP T440.1 – Almacén"),
    "Corte":       (500, 750, "RETILAP T440.1 – Tarea de precisión"),
    "Bordado":     (500, 750, "RETILAP T440.1 – Tarea de precisión"),
}
DEFAULT_NORMA = (300, 500, "RETILAP T440.1 – Oficinas generales")

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE DESCARGA Y PARSEO
# ─────────────────────────────────────────────────────────────
def build_possible_csv_urls(sheet_input: str):
    s = sheet_input.strip()
    urls = []
    sheet_id = None
    if "docs.google.com" in s:
        try:
            part = s.split("/d/")[1]
            sheet_id = part.split("/")[0]
        except Exception:
            sheet_id = None
    else:
        sheet_id = s if s else None

    if sheet_id:
        urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0")
        urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=0")
        urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
    return urls

def try_download_csv(urls, timeout=15):
    last_err = None
    for u in urls:
        try:
            resp = requests.get(u, timeout=timeout)
            resp.raise_for_status()
            text = resp.text
            if text.strip().lower().startswith("<!doctype html"):
                last_err = f"Respuesta no es CSV válida desde {u}"
                continue
            return text, None
        except Exception as e:
            last_err = f"Error descargando {u}: {e}"
    return None, last_err

@st.cache_data(ttl=0)
def parse_csv_text_to_df(csv_text: str):
    df = pd.read_csv(StringIO(csv_text))
    df.columns = [c.strip() for c in df.columns]
    # Normalización básica
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
    return df

# ─────────────────────────────────────────────────────────────
# INTERFAZ PRINCIPAL
# ─────────────────────────────────────────────────────────────
st.markdown('<h1 style="color:#64ffda">💡 Dashboard SST · Iluminación</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    sheet_input = st.text_input("ID o URL de Google Sheets", value="1P3BmLZpGIovaAvN3wep0K-5-NKxjMCBASd03WhHpzgw")

    # 🔄 BOTÓN DE RECARGAR CORREGIDO
    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    uploaded_file = st.file_uploader("Subir CSV (opcional)", type=["csv"])

# ─────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────
csv_text = None
download_error = None

if uploaded_file is not None:
    csv_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
else:
    urls = build_possible_csv_urls(sheet_input)
    if urls:
        csv_text, download_error = try_download_csv(urls)

if csv_text is None:
    st.error("No se pudo cargar datos. Sube un CSV o revisa el ID/URL.")
    st.stop()

df = parse_csv_text_to_df(csv_text)

if df.empty:
    st.error("El CSV está vacío o no tiene datos válidos.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# KPI DE EJEMPLO
# ─────────────────────────────────────────────────────────────
st.metric("📅 Registros totales", len(df))
if "Area" in df.columns:
    st.metric("🏢 Áreas evaluadas", df["Area"].nunique())
