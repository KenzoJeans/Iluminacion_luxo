```python
"""
app_iluminacion_sst.py
Dashboard SST · Iluminación (corregido y robusto)
Requisitos:
    pip install streamlit pandas plotly gspread google-auth requests openpyxl
Ejecución:
    streamlit run app_iluminacion_sst.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
from io import StringIO
from datetime import datetime
import warnings
import difflib
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
# ESTILOS CSS PERSONALIZADOS (idénticos a tu versión original)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;800&display=swap');

    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%);
        font-family: 'Sora', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b2a 0%, #112240 100%);
        border-right: 1px solid #1e3a5f;
    }
    [data-testid="stSidebar"] * { color: #ccd6f6 !important; }

    /* Título principal */
    .main-title {
        font-family: 'Sora', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #64ffda, #00b4d8, #64ffda);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
        margin: 0;
        padding: 0;
        letter-spacing: -0.5px;
    }
    @keyframes shimmer {
        to { background-position: 200% center; }
    }

    .subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        color: #8892b0;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Métricas KPI */
    .kpi-card {
        background: linear-gradient(135deg, #112240 0%, #0d2137 100%);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #64ffda, #00b4d8);
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(100,255,218,0.15);
    }
    .kpi-value {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #64ffda;
        line-height: 1;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 8px;
    }
    .kpi-sub {
        font-size: 0.7rem;
        color: #64ffda88;
        margin-top: 4px;
        font-family: 'Space Mono', monospace;
    }

    /* Tarjeta de cumplimiento */
    .badge-cumple {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid #64ffda55;
        color: #64ffda;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.7rem;
        font-family: 'Space Mono', monospace;
    }
    .badge-nocumple {
        background: rgba(255, 99, 99, 0.1);
        border: 1px solid #ff636355;
        color: #ff6363;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.7rem;
        font-family: 'Space Mono', monospace;
    }

    /* Secciones */
    .section-header {
        font-family: 'Sora', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #ccd6f6;
        border-left: 3px solid #64ffda;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    /* Norma info box */
    .norma-box {
        background: linear-gradient(135deg, #0a2341 0%, #0d1b2a 100%);
        border: 1px solid #1e3a5f;
        border-left: 3px solid #ffd166;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .norma-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        color: #ffd166;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .norma-text {
        font-size: 0.82rem;
        color: #8892b0;
        margin-top: 6px;
        line-height: 1.6;
    }

    /* Dataframe */
    .dataframe { font-size: 0.8rem !important; }

    /* Refresh button */
    .stButton > button {
        background: linear-gradient(135deg, #64ffda22, #00b4d822);
        border: 1px solid #64ffda55;
        color: #64ffda;
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
        border-radius: 8px;
        padding: 8px 20px;
        transition: all 0.3s;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #64ffda44, #00b4d844);
        border-color: #64ffda;
        box-shadow: 0 0 20px rgba(100,255,218,0.3);
    }

    /* Alert boxes */
    .alert-warning {
        background: rgba(255, 209, 102, 0.08);
        border: 1px solid #ffd16655;
        border-radius: 8px;
        padding: 12px 16px;
        color: #ffd166;
        font-size: 0.82rem;
    }
    .alert-success {
        background: rgba(100, 255, 218, 0.08);
        border: 1px solid #64ffda55;
        border-radius: 8px;
        padding: 12px 16px;
        color: #64ffda;
        font-size: 0.82rem;
    }

    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Plotly charts fondo */
    .js-plotly-plot .plotly .bg { fill: transparent !important; }

    /* Divider */
    hr { border-color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONSTANTES: NIVELES NORMATIVOS POR ÁREA (RETILAP / NTC 900)
# ─────────────────────────────────────────────────────────────
NORMA_LUX = {
    "Sistemas":    (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Financiero":  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Comercial":   (300, 500, "RETILAP T440.1 / ISO 8995"),
    "RRHH":        (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Inventarios": (150, 300, "RETILAP T440.1 – Depósito"),
    "Tesoreria":   (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Diseno":      (500, 750, "RETILAP T440.1 – Diseño/Detalle fino"),
    "Mercadeo":    (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Ingenieria":  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Importados":  (150, 300, "RETILAP T440.1 – Depósito"),
    "Tintoreria":  (300, 500, "RETILAP T440.1 – Industria textil"),
    "PTAR":        (200, 300, "RETILAP T440.1 – Planta industrial"),
    "Insumos":     (150, 300, "RETILAP T440.1 – Almacén"),
    "Corte":       (500, 750, "RETILAP T440.1 – Tarea de precisión"),
    "Bordado":     (500, 750, "RETILAP T440.1 – Tarea de precisión"),
}
DEFAULT_NORMA = (300, 500, "RETILAP T440.1 – Oficinas generales")

CLIMA_COLORES = {
    "Soleado":            "#ffd166",
    "Mayormente nublado": "#90e0ef",
    "Nublado":            "#8892b0",
    "Lluvioso":           "#00b4d8",
}

# ─────────────────────────────────────────────────────────────
# UTILIDADES PARA DETECCIÓN ROBUSTA DE COLUMNAS
# ─────────────────────────────────────────────────────────────
def find_best_column(columns, candidates):
    """
    Busca la mejor columna en 'columns' que coincida con cualquiera de las palabras en 'candidates'.
    Usa coincidencia exacta por substring y, si no hay, usa difflib para coincidencia aproximada.
    Devuelve None si no encuentra nada.
    """
    cols_lower = {c: c.lower() for c in columns}
    # 1) Substring match (prefer exact words)
    for cand in candidates:
        cand_l = cand.lower()
        for c, cl in cols_lower.items():
            if cand_l in cl:
                return c
    # 2) Fuzzy match con difflib
    names = list(columns)
    for cand in candidates:
        matches = difflib.get_close_matches(cand, names, n=1, cutoff=0.6)
        if matches:
            return matches[0]
    return None

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE CARGA Y PROCESAMIENTO (mejoradas)
# ─────────────────────────────────────────────────────────────
# Ajusta SHEET_ID/CSV_URL según tu hoja; se intenta limpiar si el usuario pegó la URL completa.
SHEET_ID_RAW = "1P3BmLZpGIovaAvN3wep0K-5-NKxjMCBASd03WhHpzgw"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_RAW}/export?format=csv&gid=0"

@st.cache_data(ttl=0)
def cargar_datos() -> pd.DataFrame:
    """Descarga y limpia el Google Sheet con detección robusta de columnas."""
    try:
        resp = requests.get(CSV_URL, timeout=20)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
    except Exception as e:
        # No usar st.* dentro de la función para mensajes largos en algunos contextos; devolvemos DataFrame vacío
        return pd.DataFrame(), f"No se pudo descargar CSV: {e}"

    # Normalizar nombres (trim)
    df.columns = [c.strip() for c in df.columns]

    # Intentar mapear columnas conocidas
    col_map = {}
    for c in df.columns:
        cl = c.strip()
        cl_low = cl.lower()
        if "marca" in cl_low and "temporal" in cl_low:
            col_map[c] = "marca_temporal"
        elif cl_low.startswith("fecha") or cl_low == "date":
            col_map[c] = "fecha"
        elif "clima" in cl_low or "weather" in cl_low:
            col_map[c] = "clima"
        # puntos P1..P8: buscar "(P1)" o "P1" o "p1"
        else:
            for i in range(1, 9):
                if f"(p{i})" in cl_low or f" p{i}" in cl_low or cl_low.endswith(f"p{i}") or cl_low == f"p{i}":
                    col_map[c] = f"P{i}"
                    break

    # Aplicar renombrado parcial
    df = df.rename(columns=col_map)

    # Detección robusta de la columna 'area'
    area_col = find_best_column(df.columns, ["area", "área", "áreas", "ubicación", "ubicacion", "zona", "departamento"])
    if area_col and area_col not in df.columns:
        # improbable, pero por seguridad
        area_col = None

    # Si no se detectó, devolver con mensaje de error
    if not area_col:
        # intentar mostrar columnas para depuración
        return df, "No se encontró una columna que represente 'area' (buscar 'area', 'área', 'ubicación', 'zona'). Columnas disponibles: " + ", ".join(df.columns.tolist())

    # Renombrar la columna detectada a 'area' si es distinto
    if area_col != "area":
        df = df.rename(columns={area_col: "area"})

    # Asegurar existencia de 'clima' y 'marca_temporal' si es posible
    clima_col = find_best_column(df.columns, ["clima", "condición", "condicion", "weather"])
    if clima_col and clima_col != "clima":
        df = df.rename(columns={clima_col: "clima"})

    marca_col = find_best_column(df.columns, ["marca_temporal", "marca", "timestamp", "fecha_hora", "fecha hora"])
    if marca_col and marca_col != "marca_temporal":
        df = df.rename(columns={marca_col: "marca_temporal"})

    fecha_col = find_best_column(df.columns, ["fecha", "date"])
    if fecha_col and fecha_col != "fecha":
        df = df.rename(columns={fecha_col: "fecha"})

    # Parsear fechas si existen
    for col in ["marca_temporal", "fecha"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Convertir puntos P1..P8 a numérico
    puntos = [f"P{i}" for i in range(1, 9)]
    for p in puntos:
        if p in df.columns:
            df[p] = pd.to_numeric(
                df[p].astype(str).str.strip().str.replace(",", ".").replace("N/A", np.nan),
                errors="coerce"
            )

    # Calcular métricas por fila (solo con los puntos presentes)
    puntos_presentes = [p for p in puntos if p in df.columns]
    if puntos_presentes:
        df["lux_promedio"] = df[puntos_presentes].mean(axis=1)
        df["lux_min"] = df[puntos_presentes].min(axis=1)
        df["lux_max"] = df[puntos_presentes].max(axis=1)
        df["n_puntos"] = df[puntos_presentes].notna().sum(axis=1)
    else:
        df["lux_promedio"] = np.nan
        df["lux_min"] = np.nan
        df["lux_max"] = np.nan
        df["n_puntos"] = 0

    # Uniformidad U0
    df["uniformidad"] = np.where(
        df["lux_promedio"] > 0,
        df["lux_min"] / df["lux_promedio"],
        np.nan
    )

    # Cumplimiento normativo
    def check_norma(row):
        area = str(row.get("area", "")).strip()
        norma = NORMA_LUX.get(area, DEFAULT_NORMA)
        minimo = norma[0]
        prom = row.get("lux_promedio", np.nan)
        u0 = row.get("uniformidad", np.nan)
        cumple_lux = prom >= minimo if not np.isnan(prom) else False
        cumple_u0 = u0 >= 0.6 if not np.isnan(u0) else True
        return "Cumple" if (cumple_lux and cumple_u0) else "No cumple"

    df["cumplimiento"] = df.apply(check_norma, axis=1)

    return df, None

def get_norma(area: str):
    return NORMA_LUX.get(area.strip(), DEFAULT_NORMA)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 10])
with col_title:
    st.markdown('<p class="main-title">💡 Dashboard SST · Iluminación en Áreas de Trabajo</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">RETILAP · NTC 900 · ISO 8995-1 · Monitoreo en tiempo real</p>', unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    st.markdown("---")

    if st.button("🔄  Refrescar datos desde Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("Cargando datos...")

    df_raw, err = cargar_datos()

    if isinstance(df_raw, pd.DataFrame) and df_raw.empty:
        st.error("❌ No hay datos cargados.")
        if err:
            st.write(err)
        st.stop()

    if err:
        st.error("❌ Problema al detectar columnas.")
        st.write(err)
        st.write("Columnas detectadas:", df_raw.columns.tolist())
        st.stop()

    st.markdown(f"**📊 Registros cargados:** `{len(df_raw)}`")
    if "marca_temporal" in df_raw.columns:
        ultima = df_raw["marca_temporal"].max()
        st.markdown(f"**🕐 Última entrada:** `{ultima.strftime('%d/%m/%Y %H:%M') if pd.notna(ultima) else 'N/D'}`")

    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    # Filtro área (si existe)
    if "area" in df_raw.columns:
        areas_disp = sorted(df_raw["area"].dropna().unique().tolist())
    else:
        areas_disp = []
    areas_sel = st.multiselect("Área(s)", areas_disp, default=areas_disp)

    # Filtro clima
    if "clima" in df_raw.columns:
        climas_disp = sorted(df_raw["clima"].dropna().unique().tolist())
    else:
        climas_disp = []
    climas_sel = st.multiselect("Condición climática", climas_disp, default=climas_disp)

    # Filtro fecha
    if "fecha" in df_raw.columns and df_raw["fecha"].notna().any():
        fmin = df_raw["fecha"].min().date()
        fmax = df_raw["fecha"].max().date()
        rango_fecha = st.date_input("Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax)
    else:
        rango_fecha = None

    st.markdown("---")
    st.markdown("### 📋 Marco Normativo")
    st.markdown("""
    <div class="norma-box">
        <div class="norma-title">🇨🇴 RETILAP 2010</div>
        <div class="norma-text">Tabla 440.1 — Niveles de iluminancia según tipo de tarea. Uniformidad U₀ ≥ 0.6</div>
    </div>
    <div class="norma-box">
        <div class="norma-title">🌐 ISO 8995-1</div>
        <div class="norma-text">Alumbrado de lugares de trabajo interiores. Criterios de cantidad y calidad.</div>
    </div>
    <div class="norma-box">
        <div class="norma-title">🇨🇴 Res. 2400/1979</div>
        <div class="norma-text">Min. de Trabajo Colombia — Art. 79 a 84: Iluminación y visibilidad en puestos de trabajo.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# FILTRAR DATOS
# ─────────────────────────────────────────────────────────────
df = df_raw.copy()

if areas_sel:
    if "area" in df.columns:
        df = df[df["area"].isin(areas_sel)]

if climas_sel:
    if "clima" in df.columns:
        df = df[df["clima"].isin(climas_sel)]

if rango_fecha and len(rango_fecha) == 2 and "fecha" in df.columns:
    f0, f1 = pd.Timestamp(rango_fecha[0]), pd.Timestamp(rango_fecha[1])
    df = df[(df["fecha"] >= f0) & (df["fecha"] <= f1)]

if df.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────
puntos_cols = [f"P{i}" for i in range(1, 9) if f"P{i}" in df.columns]

total_mediciones = len(df)
areas_evaluadas = df["area"].nunique() if "area" in df.columns else 0
lux_global_prom = df["lux_promedio"].mean() if "lux_promedio" in df.columns else np.nan
cumplimiento_pct = (df["cumplimiento"] == "Cumple").mean() * 100 if "cumplimiento" in df.columns else 0
u0_global = df["uniformidad"].mean() if "uniformidad" in df.columns else np.nan
lux_global_min = df["lux_min"].min() if "lux_min" in df.columns else np.nan

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_mediciones}</div>
        <div class="kpi-label">Mediciones totales</div>
        <div class="kpi-sub">registros cargados</div>
    </div>""", unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{areas_evaluadas}</div>
        <div class="kpi-label">Áreas evaluadas</div>
        <div class="kpi-sub">con al menos 1 registro</div>
    </div>""", unsafe_allow_html=True)

with kpi3:
    color_lux = "#64ffda" if (pd.notna(lux_global_prom) and lux_global_prom >= 300) else "#ff6363"
    lux_display = f"{lux_global_prom:.0f}" if pd.notna(lux_global_prom) else "N/D"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_lux}">{lux_display}</div>
        <div class="kpi-label">Lux promedio global</div>
        <div class="kpi-sub">promedio de todos los puntos</div>
    </div>""", unsafe_allow_html=True)

with kpi4:
    color_c = "#64ffda" if cumplimiento_pct >= 80 else ("#ffd166" if cumplimiento_pct >= 60 else "#ff6363")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_c}">{cumplimiento_pct:.0f}%</div>
        <div class="kpi-label">Cumplimiento normativo</div>
        <div class="kpi-sub">mediciones que cumplen RETILAP</div>
    </div>""", unsafe_allow_html=True)

with kpi5:
    color_u = "#64ffda" if (pd.notna(u0_global) and u0_global >= 0.6) else "#ff6363"
    u0_disp = f"{u0_global:.2f}" if pd.notna(u0_global) else "N/D"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_u}">{u0_disp}</div>
        <div class="kpi-label">Uniformidad (U₀) media</div>
        <div class="kpi-sub">mín. aceptable: 0.60</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GRÁFICAS - LAYOUT Y ESTILOS
# ─────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,27,42,0.6)",
    font=dict(family="Sora, sans-serif", color="#ccd6f6", size=11),
    title_font=dict(family="Sora, sans-serif", size=14, color="#ccd6f6"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e3a5f"),
    margin=dict(l=40, r=20, t=50, b=40),
    colorway=["#64ffda","#00b4d8","#ffd166","#ff6363","#a8dadc","#e63946","#457b9d","#1d3557"],
)

st.markdown('<div class="section-header">📊 Análisis por Área</div>', unsafe_allow_html=True)
col_g1, col_g2 = st.columns(2)

# ── Gráfica 1: Lux promedio por área vs nivel normativo
with col_g1:
    st.markdown("**Iluminancia promedio por área vs. Mínimo RETILAP**")
    if "area" in df.columns and "lux_promedio" in df.columns:
        area_stats = df.groupby("area")["lux_promedio"].mean().reset_index()
        area_stats.columns = ["area", "lux_promedio"]
        area_stats["lux_minimo_norma"] = area_stats["area"].apply(lambda a: get_norma(a)[0])
        area_stats["lux_recomendado"] = area_stats["area"].apply(lambda a: get_norma(a)[1])
        area_stats = area_stats.sort_values("lux_promedio", ascending=True)

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=area_stats["lux_promedio"],
            y=area_stats["area"],
            orientation="h",
            name="Lux medido",
            marker=dict(
                color=area_stats["lux_promedio"],
                colorscale=[[0, "#ff6363"], [0.4, "#ffd166"], [1, "#64ffda"]],
                showscale=False,
            ),
            text=[f"{v:.0f} lux" for v in area_stats["lux_promedio"]],
            textposition="outside",
            textfont=dict(size=10, color="#ccd6f6"),
        ))
        for _, row in area_stats.iterrows():
            fig1.add_shape(
                type="line",
                x0=row["lux_minimo_norma"], x1=row["lux_minimo_norma"],
                y0=row["area"], y1=row["area"],
                xref="x", yref="y",
                line=dict(color="#ffd166", width=2, dash="dot"),
            )
        fig1.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            name="Mínimo RETILAP",
            line=dict(color="#ffd166", width=2, dash="dot"),
        ))
        fig1.update_layout(**PLOT_LAYOUT, height=380,
                           xaxis=dict(showgrid=True, gridcolor="#1e3a5f", title="Lux"),
                           yaxis=dict(showgrid=False))
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar por área (falta 'area' o 'lux_promedio').")

# ── Gráfica 2: Cumplimiento por área
with col_g2:
    st.markdown("**Cumplimiento normativo por área (RETILAP + Uniformidad U₀)**")
    if "area" in df.columns and "cumplimiento" in df.columns:
        cumpl_area = df.groupby(["area", "cumplimiento"]).size().reset_index(name="n")
        cumpl_total = df.groupby("area").size().reset_index(name="total")
        cumpl_area = cumpl_area.merge(cumpl_total, on="area")
        cumpl_area["pct"] = cumpl_area["n"] / cumpl_area["total"] * 100

        cumpl_pivot = cumpl_area.pivot(index="area", columns="cumplimiento", values="pct").fillna(0).reset_index()
        sort_col = "Cumple" if "Cumple" in cumpl_pivot.columns else cumpl_pivot.columns[1]
        cumpl_pivot = cumpl_pivot.sort_values(sort_col)

        fig2 = go.Figure()
        if "Cumple" in cumpl_pivot.columns:
            fig2.add_trace(go.Bar(
                y=cumpl_pivot["area"], x=cumpl_pivot["Cumple"],
                orientation="h", name="✅ Cumple",
                marker_color="#64ffda", opacity=0.85,
            ))
        if "No cumple" in cumpl_pivot.columns:
            fig2.add_trace(go.Bar(
                y=cumpl_pivot["area"], x=cumpl_pivot["No cumple"],
                orientation="h", name="❌ No cumple",
                marker_color="#ff6363", opacity=0.85,
            ))
        fig2.update_layout(
            **PLOT_LAYOUT, height=380, barmode="stack",
            xaxis=dict(range=[0, 100], title="%", showgrid=True, gridcolor="#1e3a5f"),
            yaxis=dict(showgrid=False),
        )
        fig2.add_vline(x=80, line_dash="dot", line_color="#ffd166",
                       annotation_text="Meta 80%", annotation_font_color="#ffd166")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar cumplimiento por área (falta 'area' o 'cumplimiento').")

# ─────────────────────────────────────────────────────────────
# GRÁFICAS - FILA 2
# ─────────────────────────────────────────────────────────────
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.markdown("**Distribución de luxes por área** *(variabilidad de mediciones)*")
    if puntos_cols and "area" in df.columns:
        df_melt = df.melt(id_vars=["area"], value_vars=puntos_cols, var_name="Punto", value_name="Lux").dropna()
        fig3 = go.Figure()
        for area in sorted(df_melt["area"].unique()):
            sub = df_melt[df_melt["area"] == area]
            fig3.add_trace(go.Box(
                y=sub["Lux"], name=area, boxpoints="all",
                jitter=0.4, pointpos=0,
                marker=dict(size=4, opacity=0.6),
                line=dict(width=1.5),
            ))
        fig3.update_layout(
            **PLOT_LAYOUT, height=380,
            yaxis=dict(title="Lux", showgrid=True, gridcolor="#1e3a5f"),
            xaxis=dict(showgrid=False, tickangle=-30),
            showlegend=False,
        )
        fig3.add_hline(y=300, line_dash="dash", line_color="#ffd166", line_width=1.5,
                       annotation_text="Mín. general 300 lux", annotation_font_color="#ffd166",
                       annotation_position="top right")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No hay puntos P1..P8 o columna 'area' para mostrar la distribución.")

with col_g4:
    st.markdown("**Relación entre condición climática e iluminancia**")
    if "clima" in df.columns and "lux_promedio" in df.columns:
        clima_stats = df.groupby("clima")["lux_promedio"].agg(["mean", "std", "count"]).reset_index()
        clima_stats.columns = ["clima", "lux_mean", "lux_std", "n"]

        fig4 = go.Figure()
        for _, row in clima_stats.iterrows():
            color = CLIMA_COLORES.get(row["clima"], "#ccd6f6")
            fig4.add_trace(go.Bar(
                x=[row["clima"]],
                y=[row["lux_mean"]],
                name=row["clima"],
                marker_color=color,
                error_y=dict(type="data", array=[row["lux_std"] if pd.notna(row["lux_std"]) else 0],
                             color="#ffffff44", thickness=1.5),
                text=[f"μ={row['lux_mean']:.0f}<br>n={int(row['n'])}"],
                textposition="outside",
                textfont=dict(size=10, color="#ccd6f6"),
            ))
        fig4.add_hline(y=300, line_dash="dot", line_color="#ffd16688",
                       annotation_text="300 lux (mín. general)", annotation_font_color="#ffd166",
                       annotation_position="top right")
        fig4.update_layout(
            **PLOT_LAYOUT, height=380, showlegend=False,
            yaxis=dict(title="Lux promedio", showgrid=True, gridcolor="#1e3a5f"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No hay datos de 'clima' o 'lux_promedio' para analizar la relación climática.")

# ─────────────────────────────────────────────────────────────
# GRÁFICAS - FILA 3: Series de tiempo y pie clima
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Series de Tiempo y Distribución de Puntos</div>', unsafe_allow_html=True)
col_g5, col_g6 = st.columns([2, 1])

with col_g5:
    st.markdown("**Evolución temporal de la iluminancia por área**")
    if "marca_temporal" in df.columns and "lux_promedio" in df.columns and "area" in df.columns:
        df_sorted = df.sort_values("marca_temporal").copy()
        fig5 = px.line(
            df_sorted, x="marca_temporal", y="lux_promedio",
            color="area", markers=True,
            labels={"marca_temporal": "Fecha/Hora", "lux_promedio": "Lux promedio", "area": "Área"},
            color_discrete_sequence=PLOT_LAYOUT["colorway"],
        )
        fig5.add_hline(y=300, line_dash="dash", line_color="#ffd166", line_width=1,
                       annotation_text="Mín. 300 lux", annotation_font_color="#ffd166")
        fig5.update_layout(**PLOT_LAYOUT, height=360,
                           xaxis=dict(showgrid=True, gridcolor="#1e3a5f"),
                           yaxis=dict(showgrid=True, gridcolor="#1e3a5f"))
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No hay datos de marca temporal, lux promedio o área para la serie temporal.")

with col_g6:
    st.markdown("**Distribución de condiciones climáticas**")
    if "clima" in df.columns:
        clima_count = df["clima"].value_counts().reset_index()
        clima_count.columns = ["clima", "count"]
        fig6 = go.Figure(go.Pie(
            labels=clima_count["clima"],
            values=clima_count["count"],
            hole=0.55,
            marker=dict(colors=[CLIMA_COLORES.get(c, "#8892b0") for c in clima_count["clima"]],
                        line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
        ))
        fig6.update_layout(**PLOT_LAYOUT, height=360, showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("No hay columna 'clima' para mostrar la distribución.")

# ─────────────────────────────────────────────────────────────
# TABLA DE DATOS Y RESUMEN
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Datos y Resumen</div>', unsafe_allow_html=True)

# Mostrar primeras filas
st.markdown("**Vista previa de los datos filtrados**")
st.dataframe(df.head(200), use_container_width=True)

# Resumen por área (tabla)
if "area" in df.columns and "lux_promedio" in df.columns:
    resumen_area = df.groupby("area").agg(
        n_mediciones=("lux_promedio", "count"),
        lux_promedio_area=("lux_promedio", "mean"),
        lux_min_area=("lux_min", "min"),
        lux_max_area=("lux_max", "max"),
        uniformidad_media=("uniformidad", "mean"),
        pct_cumplen=("cumplimiento", lambda s: (s == "Cumple").mean() * 100)
    ).reset_index().sort_values("lux_promedio_area", ascending=False)
    st.markdown("**Resumen por área**")
    st.dataframe(resumen_area, use_container_width=True)
else:
    st.info("No hay suficientes columnas para generar el resumen por área.")

st.markdown("---")
st.markdown("Dashboard listo. Si necesitas que detecte automáticamente columnas con otros nombres, o que adapte el mapeo a tu Google Sheet, pega aquí los encabezados de la hoja y lo ajusto.")
```
