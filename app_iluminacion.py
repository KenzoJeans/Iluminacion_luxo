import re
from datetime import datetime
from io import StringIO
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ───────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Iluminación RETILAP",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Reemplaza por tu ID de Google Sheet
SHEET_ID = "1Rh7MbE07hMgeyFH4vvuNNpDzRVAXU0LateoBPbwg_78"
CSV_URLS = [
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0",
]
SHEET_LINK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

NUM_PUNTOS = 8

RETILAP = {
    "oficinas": 300,
    "comedores": 200,
    "zonas de descanso": 200,
    "operación": 200,
    "operacion": 200,
    "detalles finos": 500,
    "detalles moderados": 150,
    "lavado": 300,
}

RETILAP_DISPLAY = {
    "Oficinas": 300,
    "Comedores / zonas de descanso": 200,
    "Operación": 200,
    "Detalles finos": 500,
    "Detalles moderados": 150,
    "Lavado": 300,
}

# ───────────────────────────────────────────────────────────────
# UTILIDADES DE CARGA
# ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=0, show_spinner=False)
def descargar_csv_desde_urls(urls: list[str], timeout: int = 20) -> Tuple[pd.DataFrame | None, str | None]:
    """
    Intenta descargar CSV desde una lista de URLs (ordenadas por preferencia).
    Retorna (df, error_message). No lanza excepción al llamador.
    """
    last_err = None
    headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
    for url in urls:
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            # Intentar leer como CSV
            df = pd.read_csv(StringIO(resp.text))
            return df, None
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            continue
    return None, last_err or "No se pudo descargar desde las URLs provistas."


def cargar_datos_interactivo() -> Tuple[pd.DataFrame | None, str | None]:
    """
    Flujo de carga robusto:
      1) Intenta descargar desde Google Sheets (dos endpoints).
      2) Si falla, permite al usuario subir un archivo CSV o pegar el CSV.
    """
    df, err = descargar_csv_desde_urls(CSV_URLS)
    if df is not None:
        return df, None

    # Si llegamos aquí, la descarga falló: ofrecer uploader/paste
    st.warning(
        "No se pudo descargar el CSV desde Google Sheets automáticamente.\n"
        "Esto puede deberse a que la hoja no es pública o a restricciones del enlace."
    )
    st.info("Opciones: 1) Subir un archivo CSV exportado del Google Sheet. 2) Pegar el contenido CSV en el cuadro de texto.")

    uploaded = st.file_uploader("Sube el CSV exportado (opción recomendada)", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            return df, None
        except Exception as exc:
            return None, f"Error leyendo el CSV subido: {exc}"

    pasted = st.text_area("O pega aquí el contenido CSV (si no subiste archivo)", height=200)
    if pasted and pasted.strip():
        try:
            df = pd.read_csv(StringIO(pasted))
            return df, None
        except Exception as exc:
            return None, f"Error leyendo el CSV pegado: {exc}"

    # Si no se subió ni pegó nada, devolver el error original de descarga
    return None, err or "No se proporcionó CSV manualmente."


# ───────────────────────────────────────────────────────────────
# NORMALIZACIÓN DE ENCABEZADOS Y DATOS
# ───────────────────────────────────────────────────────────────
def _buscar_col_por_patron(cols, patrones):
    for pat in patrones:
        for c in cols:
            try:
                if re.search(pat, str(c), flags=re.IGNORECASE):
                    return c
            except re.error:
                continue
    return None


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza encabezados largos del formulario a nombres cortos:
      Fecha, Area, Cumple_P1..P8, Lux_P1..P8
    """
    original_cols = df.columns.tolist()
    mapping: dict[str, str] = {}

    # Detectar Fecha
    col_fecha = _buscar_col_por_patron(original_cols, [r"\bfecha\b", r"\bdate\b"])
    if col_fecha:
        mapping[col_fecha] = "Fecha"

    # Detectar Area
    col_area = _buscar_col_por_patron(
        original_cols,
        [r"seleccione.*area", r"\barea\b", r"\bárea\b", r"ubicaci", r"depart"]
    )
    if col_area:
        mapping[col_area] = "Area"

    # Detectar columnas de Cumple y Lux por patrón
    for col in original_cols:
        col_l = str(col).lower()

        # Cumple: contiene "cumple" o "indique si"
        if ("cumple" in col_l or "indique si" in col_l) and "lux" not in col_l and "valor" not in col_l:
            m = re.search(r"punto\s*(\d+)", col_l) or re.search(r"\(p(\d+)\)", col_l) or re.search(r"p(\d+)", col_l)
            p = m.group(1) if m else None
            if p:
                mapping[col] = f"Cumple_P{p}"
            else:
                for i in range(1, NUM_PUNTOS + 1):
                    key = f"Cumple_P{i}"
                    if key not in mapping.values():
                        mapping[col] = key
                        break

        # Lux: buscar "lux" o "luxómetro" o "valor dado"
        elif "lux" in col_l or "luxómetro" in col_l or "valor dado" in col_l or "luxometro" in col_l:
            m = re.search(r"punto\s*(\d+)", col_l) or re.search(r"\(p(\d+)\)", col_l) or re.search(r"p(\d+)", col_l)
            p = m.group(1) if m else None
            if p:
                mapping[col] = f"Lux_P{p}"
            else:
                for i in range(1, NUM_PUNTOS + 1):
                    key = f"Lux_P{i}"
                    if key not in mapping.values():
                        mapping[col] = key
                        break

    # Renombrar
    if mapping:
        df = df.rename(columns=mapping)

    # Fecha
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

    # Si no existe 'Area', intentar inferir o crear con 'Desconocida'
    if "Area" not in df.columns:
        inferred = _buscar_col_por_patron(original_cols, [r"\bubicaci", r"\bdepart", r"\barea\b", r"\bárea\b"])
        if inferred:
            df = df.rename(columns={inferred: "Area"})
        else:
            df["Area"] = "Desconocida"

    df["Area"] = df["Area"].astype(str).str.strip()

    # Lux → numérico
    for p in range(1, NUM_PUNTOS + 1):
        col = f"Lux_P{p}"
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Cumple → normalizar Sí/No/N/A a "Cumple"/"No cumple"/NaN
    cumple_true = {"sí", "si", "s", "cumple", "yes", "y"}
    cumple_false = {"no", "n", "no cumple", "nocumple"}
    na_vals = {"n/a", "na", "-", "—", "sin dato", "s/d", ""}

    for p in range(1, NUM_PUNTOS + 1):
        col = f"Cumple_P{p}"
        if col in df.columns:
            def _norm_val(x):
                if pd.isna(x):
                    return np.nan
                s = str(x).strip().lower()
                s = re.sub(r"\s+", " ", s)
                if s in cumple_true:
                    return "Cumple"
                if s in cumple_false:
                    return "No cumple"
                if s in na_vals:
                    return np.nan
                if "no" in s and "cumple" in s:
                    return "No cumple"
                if "cumple" in s:
                    return "Cumple"
                return np.nan
            df[col] = df[col].apply(_norm_val)

    return df


def lux_referencia(area: str) -> int | None:
    area_l = str(area).lower()
    for clave, val in RETILAP.items():
        if clave in area_l:
            return val
    return None


# ───────────────────────────────────────────────────────────────
# COLUMNAS AUXILIARES
# ───────────────────────────────────────────────────────────────
LUX_COLS = [f"Lux_P{p}" for p in range(1, NUM_PUNTOS + 1)]
CUMPLE_COLS = [f"Cumple_P{p}" for p in range(1, NUM_PUNTOS + 1)]


# ───────────────────────────────────────────────────────────────
# APP PRINCIPAL
# ───────────────────────────────────────────────────────────────
def main() -> None:
    st.markdown(
        """
        <style>
        .sec-title { font-size:1.05rem; font-weight:700; margin:12px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='text-align:center;padding:8px 0'><h1>💡 Dashboard Iluminación RETILAP</h1></div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## ⚙️ Panel de control")
        if st.button("🔄  Refrescar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption(f"Última carga: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        st.divider()
        st.markdown("### 📋 Normas RETILAP")
        for area, lux in RETILAP_DISPLAY.items():
            st.markdown(f"- **{area}:** {lux} lux")
        st.divider()
        st.markdown(f"🔗 [Ver Google Sheet]({SHEET_LINK})")

    # Cargar datos (robusto)
    with st.spinner("⏳ Cargando datos (intento automático y opciones manuales)…"):
        df_raw, error = cargar_datos_interactivo()

    if error:
        st.error(f"❌ No se pudo cargar la hoja: {error}")
        st.info("Si la hoja no es pública, exporta el CSV desde Google Sheets (Archivo → Descargar → Valores separados por comas) y súbelo aquí.")
        return

    if df_raw is None or df_raw.empty:
        st.warning("⚠️ No hay datos en el CSV proporcionado.")
        return

    df_full = limpiar_columnas(df_raw.copy())

    # Sólo columnas que existen
    lux_cols = [c for c in LUX_COLS if c in df_full.columns]
    cumple_cols = [c for c in CUMPLE_COLS if c in df_full.columns]

    # Filtros en sidebar
    with st.sidebar:
        st.divider()
        st.markdown("### 🔍 Filtros")
        areas = sorted(df_full["Area"].dropna().unique().tolist())
        areas_sel = st.multiselect("Área(s)", areas, default=areas)
        fechas_validas = df_full["Fecha"].dropna() if "Fecha" in df_full.columns else pd.Series(dtype="datetime64[ns]")
        if not fechas_validas.empty:
            f_min, f_max = fechas_validas.min().date(), fechas_validas.max().date()
            rango = st.date_input("Rango de fechas", value=(f_min, f_max))
        else:
            rango = None

    # Aplicar filtros
    df = df_full.copy()
    if areas_sel:
        df = df[df["Area"].isin(areas_sel)]
    if rango and len(rango) == 2 and "Fecha" in df.columns:
        df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]

    if df.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

    # KPIs
    st.markdown('<div class="sec-title">📊 Indicadores Generales</div>', unsafe_allow_html=True)

    todos_lux = df[lux_cols].values.flatten() if lux_cols else np.array([])
    todos_lux = pd.to_numeric(pd.Series(todos_lux), errors="coerce").dropna().values

    todos_cumple = df[cumple_cols].values.flatten() if cumple_cols else np.array([])
    todos_cumple = [v for v in todos_cumple if v in ("Cumple", "No cumple")]
    pct_cumple = (sum(v == "Cumple" for v in todos_cumple) / len(todos_cumple) * 100) if len(todos_cumple) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Registros totales", len(df))
    c2.metric("✅ Cumplimiento RETILAP", f"{pct_cumple:.1f}%")
    c3.metric("💡 Promedio lux general", f"{np.nanmean(todos_lux):.0f}" if len(todos_lux) else "—")
    try:
        areas_n = int(df["Area"].nunique())
    except Exception:
        areas_n = 0
    c4.metric("🏢 Áreas evaluadas", areas_n)

    # Pestañas con gráficas básicas
    tab1, tab2 = st.tabs(["📊 Cumplimiento por Área", "💡 Valores de Lux"])

    with tab1:
        st.markdown('<div class="sec-title">Cumplimiento RETILAP por Área</div>', unsafe_allow_html=True)
        if not cumple_cols:
            st.info("No hay columnas de cumplimiento detectadas.")
        else:
            df_melt = df.melt(id_vars=["Fecha", "Area"], value_vars=cumple_cols, var_name="Punto", value_name="Estado").dropna(subset=["Estado"])
            df_melt = df_melt[df_melt["Estado"].isin(["Cumple", "No cumple"])]
            if df_melt.empty:
                st.info("Sin datos de cumplimiento para mostrar.")
            else:
                resumen = df_melt.groupby(["Area", "Estado"]).size().reset_index(name="Cantidad")
                total_area = resumen.groupby("Area")["Cantidad"].sum().reset_index(name="Total")
                resumen = resumen.merge(total_area, on="Area")
                resumen["Porcentaje"] = resumen["Cantidad"] / resumen["Total"] * 100

                fig = px.bar(
                    resumen,
                    x="Area",
                    y="Porcentaje",
                    color="Estado",
                    barmode="stack",
                    color_discrete_map={"Cumple": "#2ecc71", "No cumple": "#e74c3c"},
                    title="% Cumplimiento por Área (todos los puntos)",
                    text_auto=".1f",
                )
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis_range=[0, 105])
                fig.update_xaxes(tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<div class="sec-title">Valores de Lux vs. Norma RETILAP</div>', unsafe_allow_html=True)
        if not lux_cols:
            st.info("No hay columnas de lux detectadas.")
        else:
            df_lux = df.melt(id_vars=["Fecha", "Area"], value_vars=lux_cols, var_name="Punto", value_name="Lux").dropna(subset=["Lux"])
            if df_lux.empty:
                st.info("Sin valores de lux para mostrar.")
            else:
                fig3 = px.box(df_lux, x="Area", y="Lux", color="Area", points="all", title="Distribución de Lux por Área")
                areas_unicas = df_lux["Area"].unique().tolist()
                for area in areas_unicas:
                    ref = lux_referencia(area)
                    if ref:
                        fig3.add_hline(y=ref, line_dash="dash", line_color="yellow", annotation_text=f"Ref {ref} lux", annotation_position="top left")
                fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                fig3.update_xaxes(tickangle=-30)
                st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
