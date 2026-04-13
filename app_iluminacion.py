"""
app_iluminacion_sst.py
Dashboard SST · Iluminación (versión completa, corregida y con exportación a Excel)

Requisitos:
    pip install streamlit pandas plotly requests openpyxl

Ejecución:
    streamlit run app_iluminacion_sst.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO, BytesIO
import requests
import warnings
import difflib
from datetime import datetime

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard · Iluminación",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# ESTILOS CSS (resumen para mantener legibilidad)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;800&display=swap');
    .main-title { font-family: 'Sora', sans-serif; font-size: 2.0rem; font-weight:800; color: #64ffda; margin:0; }
    .subtitle { font-family: 'Space Mono', monospace; color:#8892b0; font-size:0.8rem; margin-top:4px; }
    .kpi-card { background: linear-gradient(135deg, #112240 0%, #0d2137 100%); border-radius:10px; padding:14px; color:#ccd6f6; text-align:center; }
    .kpi-value { font-family: 'Space Mono', monospace; font-size:1.6rem; color:#64ffda; font-weight:700; }
    .kpi-label { font-size:0.8rem; color:#8892b0; text-transform:uppercase; letter-spacing:1px; }
    .section-header { font-family: 'Sora', sans-serif; font-size:1.05rem; font-weight:600; color:#ccd6f6; border-left:3px solid #64ffda; padding-left:10px; margin-top:18px; margin-bottom:8px; }
    .norma-box { background:#0a2341; border-left:3px solid #ffd166; padding:10px; border-radius:6px; color:#8892b0; }
    hr { border-color:#1e3a5f; }
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
    cols_lower = {c: c.lower() for c in columns}
    for cand in candidates:
        cand_l = cand.lower()
        for c, cl in cols_lower.items():
            if cand_l in cl:
                return c
    names = list(columns)
    for cand in candidates:
        matches = difflib.get_close_matches(cand, names, n=1, cutoff=0.6)
        if matches:
            return matches[0]
    return None

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
            if text.strip().lower().startswith("<!doctype html") or ("error" in text.lower() and "google" in text.lower()):
                last_err = f"Respuesta no es CSV válida desde {u}"
                continue
            return text, None
        except requests.HTTPError as he:
            code = he.response.status_code if he.response is not None else "HTTPError"
            last_err = f"HTTP {code} desde {u}"
        except Exception as e:
            last_err = f"Error descargando {u}: {e}"
    return None, last_err

# ─────────────────────────────────────────────────────────────
# PARSEO Y LIMPIEZA DE CSV
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=0)
def parse_csv_text_to_df(csv_text: str):
    df = pd.read_csv(StringIO(csv_text))
    df.columns = [c.strip() for c in df.columns]

    # Intentar renombrar columnas conocidas
    col_map = {}
    for c in df.columns:
        cl_low = c.lower()
        if "marca" in cl_low and "temporal" in cl_low:
            col_map[c] = "marca_temporal"
        elif cl_low.startswith("fecha") or cl_low == "date":
            col_map[c] = "fecha"
        elif "clima" in cl_low or "weather" in cl_low:
            col_map[c] = "clima"
        else:
            for i in range(1, 9):
                if f"(p{i})" in cl_low or f" p{i}" in cl_low or cl_low.endswith(f"p{i}") or cl_low == f"p{i}":
                    col_map[c] = f"P{i}"
                    break
    df = df.rename(columns=col_map)

    # Detectar columna area de forma robusta
    area_col = find_best_column(df.columns, ["area", "área", "ubicación", "ubicacion", "zona", "departamento", "sede"])
    if area_col and area_col != "area":
        df = df.rename(columns={area_col: "area"})

    # Detectar clima, marca_temporal, fecha
    clima_col = find_best_column(df.columns, ["clima", "condición", "condicion", "weather"])
    if clima_col and clima_col != "clima":
        df = df.rename(columns={clima_col: "clima"})
    marca_col = find_best_column(df.columns, ["marca_temporal", "marca", "timestamp", "fecha_hora", "fecha hora"])
    if marca_col and marca_col != "marca_temporal":
        df = df.rename(columns={marca_col: "marca_temporal"})
    fecha_col = find_best_column(df.columns, ["fecha", "date"])
    if fecha_col and fecha_col != "fecha":
        df = df.rename(columns={fecha_col: "fecha"})

    # Parsear fechas
    for col in ["marca_temporal", "fecha"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Convertir puntos P1..P8
    puntos = [f"P{i}" for i in range(1, 9)]
    for p in puntos:
        if p in df.columns:
            df[p] = pd.to_numeric(df[p].astype(str).str.strip().str.replace(",", ".").replace("N/A", np.nan), errors="coerce")

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

    df["uniformidad"] = np.where(df["lux_promedio"] > 0, df["lux_min"] / df["lux_promedio"], np.nan)

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

    return df

def get_norma(area: str):
    return NORMA_LUX.get(area.strip(), DEFAULT_NORMA)

# ─────────────────────────────────────────────────────────────
# INTERFAZ: entrada de URL/ID y fallback por carga manual
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">💡 Dashboard · Iluminación en Áreas de Trabajo</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">RETILAP · Monitoreo</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    st.markdown("---")
    st.markdown("Introduce el ID o la URL de Google Sheets (opcional). Si la descarga falla, puedes subir el CSV manualmente.")
    sheet_input = st.text_input("ID o URL de Google Sheets", value="1P3BmLZpGIovaAvN3wep0K-5-NKxjMCBASd03WhHpzgw")
    if st.button("🔄 Intentar descargar desde Google Sheets", use_container_width=True):
        st.session_state["_try_download"] = True
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("O sube un archivo CSV exportado desde Google Sheets")
    uploaded_file = st.file_uploader("Subir CSV (opcional)", type=["csv"], accept_multiple_files=False)

    st.markdown("---")
    st.markdown("### 📋 Marco Normativo")
    st.markdown("""
    <div class="norma-box">
        <div style="font-weight:700; color:#ffd166;">🇨🇴 RETILAP 2010</div>
        <div style="margin-top:6px;">Tabla 440.1 — Niveles de iluminancia según tipo de tarea. Uniformidad U₀ ≥ 0.6</div>
    </div>
    <div class="norma-box" style="margin-top:8px;">
        <div style="font-weight:700; color:#ffd166;">🌐 ISO 8995-1</div>
        <div style="margin-top:6px;">Alumbrado de lugares de trabajo interiores. Criterios de cantidad y calidad.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Intentar obtener CSV: prioridad
# 1) Si usuario subió archivo -> usarlo
# 2) Si pidió descargar -> intentar descargar con varias URLs
# 3) Si no, intentar descargar con valor por defecto (si hay)
# 4) Si todo falla -> pedir carga manual
# ─────────────────────────────────────────────────────────────
csv_text = None
download_error = None

# 1) archivo subido
if uploaded_file is not None:
    try:
        csv_text = uploaded_file.getvalue().decode("utf-8")
    except Exception:
        try:
            csv_text = uploaded_file.getvalue().decode("latin-1")
        except Exception as e:
            st.error(f"No se pudo leer el archivo subido: {e}")
            st.stop()

# 2) intento de descarga si el usuario pulsó el botón o si no hay archivo pero hay input
elif st.session_state.get("_try_download", False) or sheet_input:
    urls = build_possible_csv_urls(sheet_input)
    if urls:
        csv_text, download_error = try_download_csv(urls, timeout=15)
    else:
        download_error = "No se pudo construir una URL válida desde la entrada proporcionada."

# Si no se obtuvo CSV, mostrar mensaje y permitir pegar CSV manualmente
if csv_text is None:
    st.warning("No se pudo descargar el CSV automáticamente o no se subió archivo. Puedes pegar el contenido CSV aquí o subir un archivo.")
    pasted = st.text_area("Pega aquí el contenido CSV (opcional)", height=200)
    if pasted and not csv_text:
        csv_text = pasted

    if download_error:
        st.error(f"No se pudo descargar CSV: {download_error}")

    if csv_text is None:
        st.info("Sube un CSV o pega su contenido para continuar.")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Parsear CSV y validar columnas
# ─────────────────────────────────────────────────────────────
try:
    df_raw = parse_csv_text_to_df(csv_text)
except Exception as e:
    st.error(f"Error al parsear CSV: {e}")
    st.stop()

# Validaciones básicas
if df_raw.empty:
    st.error("El CSV fue leído pero no contiene filas.")
    st.write("Columnas detectadas:", df_raw.columns.tolist())
    st.stop()

if "area" not in df_raw.columns:
    st.error("No se detectó una columna que represente 'area'. Revisa los encabezados del CSV.")
    st.write("Columnas detectadas:", df_raw.columns.tolist())
    st.stop()

# ─────────────────────────────────────────────────────────────
# SIDEBAR: mostrar resumen y filtros (continuación)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**📊 Registros cargados:** `{len(df_raw)}`")
    if "marca_temporal" in df_raw.columns:
        ultima = df_raw["marca_temporal"].max()
        st.markdown(f"**🕐 Última entrada:** `{ultima.strftime('%d/%m/%Y %H:%M') if pd.notna(ultima) else 'N/D'}`")

    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    areas_disp = sorted(df_raw["area"].dropna().unique().tolist()) if "area" in df_raw.columns else []
    areas_sel = st.multiselect("Área(s)", areas_disp, default=areas_disp)

    climas_disp = sorted(df_raw["clima"].dropna().unique().tolist()) if "clima" in df_raw.columns else []
    climas_sel = st.multiselect("Condición climática", climas_disp, default=climas_disp)

    if "fecha" in df_raw.columns and df_raw["fecha"].notna().any():
        fmin = df_raw["fecha"].min().date()
        fmax = df_raw["fecha"].max().date()
        rango_fecha = st.date_input("Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax)
    else:
        rango_fecha = None

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

total_mediciones  = len(df)
areas_evaluadas   = df["area"].nunique() if "area" in df.columns else 0
lux_global_prom   = df["lux_promedio"].mean() if "lux_promedio" in df.columns else np.nan
cumplimiento_pct  = (df["cumplimiento"] == "Cumple").mean() * 100 if "cumplimiento" in df.columns else 0
u0_global         = df["uniformidad"].mean() if "uniformidad" in df.columns else np.nan
lux_global_min    = df["lux_min"].min() if "lux_min" in df.columns else np.nan

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_mediciones}</div>
        <div class="kpi-label">Mediciones totales</div>
    </div>""", unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{areas_evaluadas}</div>
        <div class="kpi-label">Áreas evaluadas</div>
    </div>""", unsafe_allow_html=True)

with kpi3:
    color_lux = "#64ffda" if (pd.notna(lux_global_prom) and lux_global_prom >= 300) else "#ff6363"
    lux_display = f"{lux_global_prom:.0f}" if pd.notna(lux_global_prom) else "N/D"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_lux}">{lux_display}</div>
        <div class="kpi-label">Lux promedio global</div>
    </div>""", unsafe_allow_html=True)

with kpi4:
    color_c = "#64ffda" if cumplimiento_pct >= 80 else ("#ffd166" if cumplimiento_pct >= 60 else "#ff6363")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_c}">{cumplimiento_pct:.0f}%</div>
        <div class="kpi-label">Cumplimiento normativo</div>
    </div>""", unsafe_allow_html=True)

with kpi5:
    color_u = "#64ffda" if (pd.notna(u0_global) and u0_global >= 0.6) else "#ff6363"
    u0_disp = f"{u0_global:.2f}" if pd.notna(u0_global) else "N/D"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{color_u}">{u0_disp}</div>
        <div class="kpi-label">Uniformidad (U₀) media</div>
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
        fig1.update_layout(**PLOT_LAYOUT, height=380,
                           xaxis=dict(showgrid=True, gridcolor="#1e3a5f", title="Lux"),
                           yaxis=dict(showgrid=False))
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar por área (falta 'area' o 'lux_promedio').")

# ── Gráfica 2: Cumplimiento por área
with col_g2:
    st.markdown("**Cumplimiento normativo por área**")
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
                       annotation_text="Mín. general 300 lux", annotation_font_color="#ffd166")
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
            err_color = "rgba(255,255,255,0.27)"
            err_array = [row["lux_std"] if pd.notna(row["lux_std"]) else 0]
            fig4.add_trace(go.Bar(
                x=[row["clima"]],
                y=[row["lux_mean"]],
                name=row["clima"],
                marker_color=color,
                error_y=dict(type="data", array=err_array, color=err_color, thickness=1.5),
                text=[f"μ={row['lux_mean']:.0f}<br>n={int(row['n'])}"],
                textposition="outside",
                textfont=dict(size=10, color="#ccd6f6"),
            ))
        fig4.add_hline(y=300, line_dash="dot", line_color="rgba(255,209,102,0.35)",
                       annotation_text="300 lux (mín. general)", annotation_font_color="#ffd166")
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

st.markdown("**Vista previa de los datos filtrados**")
st.dataframe(df.head(200), use_container_width=True)

resumen_area = None
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

# ─────────────────────────────────────────────────────────────
# EXPORTAR A EXCEL: botón para descargar datos filtrados y resumen
# ─────────────────────────────────────────────────────────────
def to_excel_bytes(df_main, df_summary=None):
    """
    Crea un archivo Excel en memoria con:
      - Hoja 'Datos' -> df_main (datos filtrados)
      - Hoja 'Resumen por area' -> df_summary (si existe)
      - Hoja 'Meta' -> metadatos básicos
    Devuelve bytes listos para descarga.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="Datos", index=False)
        if df_summary is not None:
            df_summary.to_excel(writer, sheet_name="Resumen por area", index=False)
        meta = pd.DataFrame({
            "Generado el": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Registros exportados": [len(df_main)],
            "Áreas incluidas": [df_main["area"].nunique() if "area" in df_main.columns else 0]
        })
        meta.to_excel(writer, sheet_name="Meta", index=False)
        # NO llamar writer.save() ni writer.close(); el context manager se encarga de guardar
    return output.getvalue()

st.markdown("### 📥 Exportar resultados")
col_e1, col_e2 = st.columns([3, 1])
with col_e1:
    st.markdown("Descarga los datos filtrados y el resumen por área en un archivo Excel.")
with col_e2:
    if st.button("Generar archivo Excel"):
        try:
            excel_bytes = to_excel_bytes(df, resumen_area)
            filename = f"iluminacion_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.success("Archivo generado. Haz clic en descargar.")
            st.download_button(
                label="📥 Descargar .xlsx",
                data=excel_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"No se pudo generar el archivo Excel: {e}")

st.markdown("### ✅ Listo")
st.markdown("Dashboard listo. Si quieres que el Excel incluya hojas adicionales (por ejemplo: estadísticas por clima, gráficos embebidos, o formato condicional), dime qué hojas necesitas y lo adapto.")
