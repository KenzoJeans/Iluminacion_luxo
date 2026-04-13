"""
╔══════════════════════════════════════════════════════════════╗
║     DASHBOARD SST - MONITOREO DE ILUMINACIÓN EN ÁREAS       ║
║     Basado en RETILAP y NTC 900 / ISO 8995-1                 ║
╚══════════════════════════════════════════════════════════════╝
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
# ESTILOS CSS PERSONALIZADOS
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
# Los valores corresponden al mínimo de iluminancia mantenida (lux)
# según el tipo de tarea visual que se realiza en cada área.
# ─────────────────────────────────────────────────────────────
NORMA_LUX = {
    # Área                     : (mínimo, recomendado, norma_referencia)
    "Sistemas":                  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Financiero":                (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Comercial":                 (300, 500, "RETILAP T440.1 / ISO 8995"),
    "RRHH":                      (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Inventarios":               (150, 300, "RETILAP T440.1 – Depósito"),
    "Tesoreria":                 (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Diseno":                    (500, 750, "RETILAP T440.1 – Diseño/Detalle fino"),
    "Mercadeo":                  (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Ingenieria":                (300, 500, "RETILAP T440.1 / ISO 8995"),
    "Importados":                (150, 300, "RETILAP T440.1 – Depósito"),
    "Tintoreria":                (300, 500, "RETILAP T440.1 – Industria textil"),
    "PTAR":                      (200, 300, "RETILAP T440.1 – Planta industrial"),
    "Insumos":                   (150, 300, "RETILAP T440.1 – Almacén"),
    "Corte":                     (500, 750, "RETILAP T440.1 – Tarea de precisión"),
    "Bordado":                   (500, 750, "RETILAP T440.1 – Tarea de precisión"),
}
DEFAULT_NORMA = (300, 500, "RETILAP T440.1 – Oficinas generales")

CLIMA_COLORES = {
    "Soleado":            "#ffd166",
    "Mayormente nublado": "#90e0ef",
    "Nublado":            "#8892b0",
    "Lluvioso":           "#00b4d8",
}

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ─────────────────────────────────────────────────────────────
SHEET_ID = "1P3BmLZpGIovaAvN3wep0K-5-NKxjMCBASd03WhHpzgw"
CSV_URL   = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=0)   # ttl=0 → sólo refresca cuando el usuario lo solicita
def cargar_datos() -> pd.DataFrame:
    """Descarga y limpia el Google Sheet."""
    try:
        resp = requests.get(CSV_URL, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
    except Exception as e:
        st.error(f"❌ No se pudo cargar el archivo: {e}")
        return pd.DataFrame()

    # ── Renombrar columnas ────────────────────────────────────
    col_map = {}
    for c in df.columns:
        cl = c.strip()
        if "Marca temporal" in cl:
            col_map[c] = "marca_temporal"
        elif cl.startswith("Fecha"):
            col_map[c] = "fecha"
        elif "clima" in cl.lower():
            col_map[c] = "clima"
        elif "área" in cl.lower() or "area" in cl.lower():
            col_map[c] = "area"
        else:
            for i in range(1, 9):
                if f"(P{i})" in cl:
                    col_map[c] = f"P{i}"
                    break
    df.rename(columns=col_map, inplace=True)

    # ── Parsear fechas ────────────────────────────────────────
    for col in ["marca_temporal", "fecha"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # ── Convertir luxes (N/A → NaN) ───────────────────────────
    puntos = [f"P{i}" for i in range(1, 9)]
    for p in puntos:
        if p in df.columns:
            df[p] = pd.to_numeric(
                df[p].astype(str).str.strip().str.replace(",", ".").replace("N/A", np.nan),
                errors="coerce"
            )

    # ── Calcular promedio e índice de uniformidad por fila ────
    df["lux_promedio"]   = df[[p for p in puntos if p in df.columns]].mean(axis=1)
    df["lux_min"]        = df[[p for p in puntos if p in df.columns]].min(axis=1)
    df["lux_max"]        = df[[p for p in puntos if p in df.columns]].max(axis=1)
    df["n_puntos"]       = df[[p for p in puntos if p in df.columns]].notna().sum(axis=1)

    # Índice de Uniformidad (U₀ = Emin / Eprom) — RETILAP ≥ 0.6
    df["uniformidad"]    = np.where(
        df["lux_promedio"] > 0,
        df["lux_min"] / df["lux_promedio"],
        np.nan
    )

    # ── Cumplimiento normativo ────────────────────────────────
    def check_norma(row):
        area = str(row.get("area", "")).strip()
        norma = NORMA_LUX.get(area, DEFAULT_NORMA)
        minimo = norma[0]
        prom   = row.get("lux_promedio", np.nan)
        u0     = row.get("uniformidad", np.nan)
        cumple_lux = prom >= minimo if not np.isnan(prom) else False
        cumple_u0  = u0 >= 0.6 if not np.isnan(u0) else True   # si 1 punto, no aplica
        return "Cumple" if (cumple_lux and cumple_u0) else "No cumple"

    df["cumplimiento"] = df.apply(check_norma, axis=1)

    return df


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
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    st.markdown("---")

    # Botón de refresco
    if st.button("🔄  Refrescar datos desde Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # Carga inicial
    df_raw = cargar_datos()

    if df_raw.empty:
        st.error("Sin datos disponibles.")
        st.stop()

    st.markdown(f"**📊 Registros cargados:** `{len(df_raw)}`")
    if "marca_temporal" in df_raw.columns:
        ultima = df_raw["marca_temporal"].max()
        st.markdown(f"**🕐 Última entrada:** `{ultima.strftime('%d/%m/%Y %H:%M') if pd.notna(ultima) else 'N/D'}`")

    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    # Filtro área
    areas_disp = sorted(df_raw["area"].dropna().unique().tolist())
    areas_sel  = st.multiselect("Área(s)", areas_disp, default=areas_disp)

    # Filtro clima
    climas_disp = sorted(df_raw["clima"].dropna().unique().tolist())
    climas_sel  = st.multiselect("Condición climática", climas_disp, default=climas_disp)

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
    df = df[df["area"].isin(areas_sel)]
if climas_sel:
    df = df[df["clima"].isin(climas_sel)]
if rango_fecha and len(rango_fecha) == 2:
    f0, f1 = pd.Timestamp(rango_fecha[0]), pd.Timestamp(rango_fecha[1])
    df = df[(df["fecha"] >= f0) & (df["fecha"] <= f1)]

if df.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────
puntos_cols = [f"P{i}" for i in range(1, 9) if f"P{i}" in df.columns]

total_mediciones  = len(df)
areas_evaluadas   = df["area"].nunique()
lux_global_prom   = df["lux_promedio"].mean()
cumplimiento_pct  = (df["cumplimiento"] == "Cumple").mean() * 100
u0_global         = df["uniformidad"].mean()
lux_global_min    = df["lux_min"].min()

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
    color_lux = "#64ffda" if lux_global_prom >= 300 else "#ff6363"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_lux}">{lux_global_prom:.0f}</div>
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
# GRÁFICAS - FILA 1
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

# ── Gráfica 1: Lux promedio por área vs nivel normativo ──────
with col_g1:
    st.markdown("**Iluminancia promedio por área vs. Mínimo RETILAP**")

    area_stats = df.groupby("area")["lux_promedio"].mean().reset_index()
    area_stats.columns = ["area", "lux_promedio"]
    area_stats["lux_minimo_norma"] = area_stats["area"].apply(lambda a: get_norma(a)[0])
    area_stats["lux_recomendado"]  = area_stats["area"].apply(lambda a: get_norma(a)[1])
    area_stats["cumple"] = area_stats["lux_promedio"] >= area_stats["lux_minimo_norma"]
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
    # Línea de mínimo normativo
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

# ── Gráfica 2: Cumplimiento por área ─────────────────────────
with col_g2:
    st.markdown("**Cumplimiento normativo por área (RETILAP + Uniformidad U₀)**")

    cumpl_area = df.groupby(["area", "cumplimiento"]).size().reset_index(name="n")
    cumpl_total = df.groupby("area").size().reset_index(name="total")
    cumpl_area = cumpl_area.merge(cumpl_total, on="area")
    cumpl_area["pct"] = cumpl_area["n"] / cumpl_area["total"] * 100

    cumpl_pivot = cumpl_area.pivot(index="area", columns="cumplimiento", values="pct").fillna(0).reset_index()
    cumpl_pivot = cumpl_pivot.sort_values("Cumple" if "Cumple" in cumpl_pivot.columns else cumpl_pivot.columns[1])

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

# ─────────────────────────────────────────────────────────────
# GRÁFICAS - FILA 2
# ─────────────────────────────────────────────────────────────
col_g3, col_g4 = st.columns(2)

# ── Gráfica 3: Box plot por área ─────────────────────────────
with col_g3:
    st.markdown("**Distribución de luxes por área** *(variabilidad de mediciones)*")
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

# ── Gráfica 4: Distribución climática y luxes ────────────────
with col_g4:
    st.markdown("**Relación entre condición climática e iluminancia**")
    clima_stats = df.groupby("clima")["lux_promedio"].agg(["mean","std","count"]).reset_index()
    clima_stats.columns = ["clima","lux_mean","lux_std","n"]

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

# ─────────────────────────────────────────────────────────────
# GRÁFICAS - FILA 3
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Series de Tiempo y Distribución de Puntos</div>', unsafe_allow_html=True)
col_g5, col_g6 = st.columns([2, 1])

# ── Gráfica 5: Serie de tiempo por área ──────────────────────
with col_g5:
    st.markdown("**Evolución temporal de la iluminancia por área**")
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

# ── Gráfica 6: Pie clima ──────────────────────────────────────
with col_g6:
    st.markdown("**Distribución de condiciones climáticas**")
    clima_count = df["clima"].value_counts().reset_index()
    clima_count.columns = ["clima", "count"]

    fig6 = go.Figure(go.Pie(
        labels=clima_count["clima"],
        values=clima_count["count"],
        hole=0.55,
        marker=dict(colors=[CLIMA_COLORES.get(c, "#8892b0") for c in clima_count["clima"]],
                    line=dict(color="#0a0f1e", width=2)),
        textfont=dict(color="#ccd6f6", size=11),
    ))
    fig6.update_layout(**PLOT_LAYOUT, height=360,
                       legend=dict(orientation="v", x=0.85, y=0.5))
    fig6.add_annotation(
        text=f"<b>{len(df)}</b><br><span style='font-size:10px'>registros</span>",
        x=0.5, y=0.5, font_size=14, font_color="#64ffda",
        showarrow=False, xanchor="center",
    )
    st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# GRÁFICA - MAPA DE CALOR (Área × Punto de medición)
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔥 Mapa de Calor — Iluminancia por Punto de Medición</div>', unsafe_allow_html=True)

df_heat = df.groupby("area")[puntos_cols].mean().round(1)
df_heat = df_heat.dropna(how="all")

if not df_heat.empty:
    fig7 = go.Figure(go.Heatmap(
        z=df_heat.values,
        x=df_heat.columns.tolist(),
        y=df_heat.index.tolist(),
        colorscale=[
            [0,    "#1d0b0b"],
            [0.2,  "#8b1a1a"],
            [0.4,  "#ff6363"],
            [0.6,  "#ffd166"],
            [0.85, "#90e0ef"],
            [1.0,  "#64ffda"],
        ],
        text=df_heat.values.round(0),
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        hovertemplate="Área: %{y}<br>Punto: %{x}<br>Lux promedio: %{z:.1f}<extra></extra>",
        colorbar=dict(
            title="Lux", tickfont=dict(color="#ccd6f6"),
            titlefont=dict(color="#ccd6f6"),
        ),
    ))
    fig7.update_layout(
        **PLOT_LAYOUT, height=350,
        xaxis=dict(showgrid=False, title="Punto de medición"),
        yaxis=dict(showgrid=False, title="Área"),
    )
    st.plotly_chart(fig7, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# GRÁFICA - UNIFORMIDAD (U₀) POR ÁREA
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⚖️ Índice de Uniformidad (U₀ = E_min / E_prom) por Área</div>', unsafe_allow_html=True)

df_u0 = df[df["n_puntos"] > 1].copy()   # U₀ requiere ≥ 2 puntos
if not df_u0.empty:
    u0_area = df_u0.groupby("area")["uniformidad"].mean().reset_index()
    u0_area.columns = ["area", "u0"]
    u0_area = u0_area.sort_values("u0")
    u0_area["color"] = u0_area["u0"].apply(
        lambda v: "#64ffda" if v >= 0.6 else ("#ffd166" if v >= 0.4 else "#ff6363")
    )

    fig8 = go.Figure(go.Bar(
        x=u0_area["area"], y=u0_area["u0"],
        marker_color=u0_area["color"],
        text=[f"{v:.2f}" for v in u0_area["u0"]],
        textposition="outside",
        textfont=dict(color="#ccd6f6", size=10),
    ))
    fig8.add_hline(y=0.6, line_dash="dash", line_color="#ffd166", line_width=2,
                   annotation_text="U₀ ≥ 0.60 (RETILAP mínimo)",
                   annotation_font_color="#ffd166", annotation_position="top right")
    fig8.update_layout(
        **PLOT_LAYOUT, height=300,
        yaxis=dict(range=[0, 1.1], title="U₀", showgrid=True, gridcolor="#1e3a5f"),
        xaxis=dict(showgrid=False, tickangle=-25),
        showlegend=False,
    )
    st.plotly_chart(fig8, use_container_width=True)
else:
    st.info("ℹ️ Se necesitan al menos 2 puntos de medición por área para calcular el índice de uniformidad.")

# ─────────────────────────────────────────────────────────────
# TABLA DE RESUMEN NORMATIVO
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Resumen Normativo por Área</div>', unsafe_allow_html=True)

resumen_rows = []
for area in sorted(df["area"].dropna().unique()):
    sub = df[df["area"] == area]
    norma = get_norma(area)
    lux_m   = sub["lux_promedio"].mean()
    u0_m    = sub["uniformidad"].mean()
    n_reg   = len(sub)
    cumple_lux = lux_m >= norma[0] if pd.notna(lux_m) else False
    cumple_u0  = (u0_m >= 0.6 if pd.notna(u0_m) else True) if sub["n_puntos"].max() > 1 else True
    cumple_tot = "✅ Cumple" if (cumple_lux and cumple_u0) else "❌ No cumple"

    resumen_rows.append({
        "Área":              area,
        "Registros":         n_reg,
        "Lux promedio":      f"{lux_m:.1f}" if pd.notna(lux_m) else "N/D",
        "Mín. RETILAP (lux)":norma[0],
        "Rec. RETILAP (lux)":norma[1],
        "U₀ promedio":       f"{u0_m:.2f}" if pd.notna(u0_m) else "N/A (1 punto)",
        "U₀ ≥ 0.60":         "✅" if cumple_u0 else "❌",
        "Lux ≥ mínimo":      "✅" if cumple_lux else "❌",
        "Estado normativo":  cumple_tot,
        "Referencia":        norma[2],
    })

df_resumen = pd.DataFrame(resumen_rows)
st.dataframe(
    df_resumen,
    use_container_width=True,
    hide_index=True,
)

# ─────────────────────────────────────────────────────────────
# TABLA DE DATOS CRUDOS (EXPANDIBLE)
# ─────────────────────────────────────────────────────────────
with st.expander("🗃️ Ver datos crudos del formulario"):
    cols_mostrar = ["marca_temporal","fecha","clima","area"] + puntos_cols + ["lux_promedio","uniformidad","cumplimiento"]
    cols_mostrar = [c for c in cols_mostrar if c in df.columns]
    st.dataframe(df[cols_mostrar].sort_values("marca_temporal", ascending=False),
                 use_container_width=True, hide_index=True)
    csv_export = df[cols_mostrar].to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=csv_export,
        file_name=f"iluminacion_sst_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; font-family:'Space Mono',monospace; font-size:0.7rem; color:#4a5568; padding: 12px 0;">
    Dashboard SST · Iluminación en Áreas de Trabajo &nbsp;·&nbsp;
    RETILAP 2010 · NTC 900 · ISO 8995-1 · Res. 2400/1979 &nbsp;·&nbsp;
    Desarrollado con Streamlit + Plotly &nbsp;·&nbsp;
    Los datos provienen de Google Sheets en tiempo real
</div>
""", unsafe_allow_html=True)
