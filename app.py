import os
import pandas as pd
import streamlit as st
import altair as alt
from supabase import create_client, Client
from dotenv import load_dotenv

# -------------------------------
# CONFIGURACIÓN INICIAL
# -------------------------------
st.set_page_config(page_title="Ventas Alugandia", layout="wide")

# Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# FUNCIONES AUXILIARES
# -------------------------------
@st.cache_data
def cargar_datos():
    """Carga todos los registros de ventas desde Supabase (sin límite)."""
    all_data = []
    batch_size = 1000
    offset = 0

    while True:
        response = (
            supabase.table("ventas")
            .select("*")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        if not response.data:
            break
        all_data.extend(response.data)
        offset += batch_size

    df = pd.DataFrame(all_data)
    if df.empty:
        return pd.DataFrame(columns=["client_code", "client_name", "client_code_norm", "net_sales", "year"])

    df["net_sales"] = df["net_sales"].astype(float)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def clasificar_rango(ventas):
    """Clasifica el cliente según su rango de facturación."""
    if ventas < 10000:
        return "Pequeño (<10k)"
    elif ventas < 20000:
        return "Mediano (10k–20k)"
    else:
        return "Grande (>20k)"


def filtrar_datos(df, year, clientes_excluir, rangos_seleccionados):
    """Filtra por año, exclusión de clientes y rangos."""
    filtrado = df[df["year"] == year].copy()

    if clientes_excluir:
        clientes_excluir_lower = [c.lower() for c in clientes_excluir]
        filtrado = filtrado[~filtrado["client_name"].str.lower().isin(clientes_excluir_lower)]

    if rangos_seleccionados and len(rangos_seleccionados) < 3:
        filtrado = filtrado[filtrado["rango_facturacion"].isin(rangos_seleccionados)]

    return filtrado


def aplicar_estilo(df, color_map):
    """Devuelve un pandas Styler con colores según el rango y formateo de moneda."""
    def color_rango(val):
        color = color_map.get(val, "")
        return f"background-color: {color}; color: white; font-weight: bold; text-align: center;"

    return (
        df.style
        .format({"net_sales": lambda x: f"{x:,.2f} €"})
        .map(lambda v: color_rango(v), subset=["rango_facturacion"])
    )


# -------------------------------
# CONFIGURACIÓN DE COLORES
# -------------------------------
COLOR_RANGOS = {
    "Pequeño (<10k)": "#56B4E9",
    "Mediano (10k–20k)": "#E69F00",
    "Grande (>20k)": "#009E73"
}

# -------------------------------
# CARGA DE DATOS
# -------------------------------
with st.spinner("Cargando datos desde Supabase..."):
    df = cargar_datos()

if df.empty:
    st.warning("No se encontraron datos en la base de datos 'ventas'.")
    st.stop()

# Clasificación de rangos
df["rango_facturacion"] = df["net_sales"].apply(clasificar_rango)
años = sorted(df["year"].dropna().unique())

# -------------------------------
# INTERFAZ DE PESTAÑAS
# -------------------------------
tab1, tab2 = st.tabs(["📊 Ventas por año", "📈 Comparativa anual"])

# ============================================================
# 🟢 TAB 1 – VENTAS POR AÑO
# ============================================================
with tab1:
    st.title("📊 Ventas Alugandia Dashboard")
    st.markdown("Visualización de ventas por cliente, año y rango de facturación. Datos cargados desde Supabase.")

    st.sidebar.header("Filtros (Ventas por año)")
    año_seleccionado = st.sidebar.selectbox("Seleccionar año", años, index=len(años) - 1)

    # Selector múltiple de clientes
    clientes_disponibles = sorted(df["client_name"].dropna().unique())
    clientes_excluir = st.sidebar.multiselect("Excluir clientes", options=clientes_disponibles, default=[])

    rangos_unicos = list(COLOR_RANGOS.keys())
    rangos_seleccionados = st.sidebar.multiselect(
        "Rangos de facturación a mostrar",
        rangos_unicos,
        default=rangos_unicos
    )

    mostrar_nombres = st.sidebar.checkbox("Mostrar nombres de clientes", value=True)

    # Aplicar filtros
    df_filtrado = filtrar_datos(df, año_seleccionado, clientes_excluir, rangos_seleccionados)

    ventas_por_cliente = (
        df_filtrado.groupby(["client_code_norm", "client_name", "rango_facturacion"], as_index=False)["net_sales"]
        .sum()
        .sort_values(by="net_sales", ascending=False)
    )

    # -------------------------------
    # MÉTRICAS GENERALES
    # -------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Ventas totales", f"{ventas_por_cliente['net_sales'].sum():,.2f} €")
    with col2:
        st.metric("👥 Nº de clientes", f"{ventas_por_cliente.shape[0]}")
    with col3:
        st.metric("🗂️ Rangos visibles", f"{len(rangos_seleccionados)}")

    st.divider()

    # -------------------------------
    # DISTRIBUCIÓN POR RANGO
    # -------------------------------
    st.subheader("📦 Distribución por rango de facturación")

    resumen_rangos = (
        ventas_por_cliente.groupby("rango_facturacion", as_index=False)
        .agg(clientes=("client_code_norm", "count"), total_ventas=("net_sales", "sum"))
        .sort_values("total_ventas", ascending=False)
    )

    chart_rangos = (
        alt.Chart(resumen_rangos)
        .mark_bar()
        .encode(
            x=alt.X("rango_facturacion:N", title="Rango de facturación"),
            y=alt.Y("total_ventas:Q", title="Ventas (€)"),
            color=alt.Color(
                "rango_facturacion:N",
                scale=alt.Scale(
                    domain=list(COLOR_RANGOS.keys()),
                    range=list(COLOR_RANGOS.values())
                )
            ),
            tooltip=["rango_facturacion", "total_ventas", "clientes"]
        )
        .properties(height=300)
    )

    colA, colB = st.columns(2)
    with colA:
        # mostrar total_ventas formateado como moneda
        styled_resumen = resumen_rangos.style.format({"total_ventas": lambda x: f"{x:,.2f} €"})
        st.dataframe(styled_resumen, hide_index=True, use_container_width=True)
    with colB:
        st.altair_chart(chart_rangos, use_container_width=True)

    st.divider()

    # -------------------------------
    # TABLA DE CLIENTES
    # -------------------------------
    st.subheader(f"📋 Clientes {año_seleccionado}")

    columnas = ["client_code_norm", "net_sales", "rango_facturacion"]
    if mostrar_nombres:
        columnas.insert(1, "client_name")

    styled_df = aplicar_estilo(ventas_por_cliente[columnas], COLOR_RANGOS)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # -------------------------------
    # GRÁFICO DE CLIENTES TOP
    # -------------------------------
    st.subheader("📈 Ventas por cliente (Top N)")
    top_n = st.slider("Mostrar top N clientes", min_value=5, max_value=50, value=20)
    df_top = ventas_por_cliente.head(top_n)

    chart_top = (
        alt.Chart(df_top)
        .mark_bar()
        .encode(
            x=alt.X("client_code_norm:N", title="Cliente"),
            y=alt.Y("net_sales:Q", title="Ventas (€)"),
            color=alt.Color(
                "rango_facturacion:N",
                scale=alt.Scale(
                    domain=list(COLOR_RANGOS.keys()),
                    range=list(COLOR_RANGOS.values())
                )
            ),
            tooltip=["client_code_norm", "client_name", "net_sales", "rango_facturacion"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart_top, use_container_width=True)

# ============================================================
# 🔵 TAB 2 – COMPARATIVA ANUAL
# ============================================================
with tab2:
    st.title("📈 Comparativa de Ventas entre Años")
    st.markdown("Compara ventas totales o por cliente entre dos años distintos, con análisis por rango de facturación.")

    col_a, col_b = st.columns(2)
    with col_a:
        año_1 = st.selectbox("Año inicial", años, index=max(0, len(años) - 2))
    with col_b:
        año_2 = st.selectbox("Año comparado", años, index=len(años) - 1)

    modo_comparacion = st.radio("Modo de comparación", ["Totales", "Por cliente"], horizontal=True)

    if modo_comparacion == "Totales":
        ventas_totales = df.groupby("year")["net_sales"].sum().reset_index().sort_values("year")

        st.subheader("💰 Ventas Totales por Año")
        st.bar_chart(ventas_totales, x="year", y="net_sales", use_container_width=True)

        total_1 = ventas_totales.loc[ventas_totales["year"] == año_1, "net_sales"].sum()
        total_2 = ventas_totales.loc[ventas_totales["year"] == año_2, "net_sales"].sum()
        variacion = ((total_2 - total_1) / total_1 * 100) if total_1 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"Ventas {año_1}", f"{total_1:,.2f} €")
        with col2:
            st.metric(f"Ventas {año_2}", f"{total_2:,.2f} €")
        with col3:
            st.metric("Variación", f"{variacion:+.1f} %")

        # Evolución por rango
        df_rangos = (
            df.groupby(["year", "client_code_norm", "client_name"], as_index=False)["net_sales"].sum()
        )
        df_rangos["rango_facturacion"] = df_rangos["net_sales"].apply(clasificar_rango)
        resumen = (
            df_rangos.groupby(["year", "rango_facturacion"], as_index=False)
            .agg(total_ventas=("net_sales", "sum"))
        )

        chart_rangos_comp = (
            alt.Chart(resumen)
            .mark_bar()
            .encode(
                x=alt.X("rango_facturacion:N", title="Rango"),
                y=alt.Y("total_ventas:Q", title="Ventas (€)"),
                color=alt.Color(
                    "rango_facturacion:N",
                    scale=alt.Scale(
                        domain=list(COLOR_RANGOS.keys()),
                        range=list(COLOR_RANGOS.values())
                    )
                ),
                column="year:N",
                tooltip=["year", "rango_facturacion", "total_ventas"]
            )
            .properties(height=300)
        )
        st.subheader("📦 Evolución por rango de facturación")
        st.altair_chart(chart_rangos_comp, use_container_width=True)

    else:
        df_1 = df[df["year"] == año_1].groupby(["client_code_norm", "client_name"], as_index=False)["net_sales"].sum()
        df_2 = df[df["year"] == año_2].groupby(["client_code_norm", "client_name"], as_index=False)["net_sales"].sum()

        comparativa = pd.merge(
            df_1, df_2, on=["client_code_norm", "client_name"], how="outer",
            suffixes=(f"_{año_1}", f"_{año_2}")
        ).fillna(0)

        comparativa["diferencia"] = comparativa[f"net_sales_{año_2}"] - comparativa[f"net_sales_{año_1}"]
        comparativa["variacion_%"] = comparativa["diferencia"] / comparativa[f"net_sales_{año_1}"].replace(0, pd.NA) * 100
        comparativa["rango_facturacion"] = comparativa[
            [f"net_sales_{año_1}", f"net_sales_{año_2}"]
        ].mean(axis=1).apply(clasificar_rango)

        st.subheader(f"📊 Comparativa por Cliente: {año_1} vs {año_2}")
        # formatear las columnas de dinero y porcentaje antes de mostrar
        fmt_cols = {
            f"net_sales_{año_1}": lambda x: f"{x:,.2f} €",
            f"net_sales_{año_2}": lambda x: f"{x:,.2f} €",
            "diferencia": lambda x: f"{x:,.2f} €",
            "variacion_%": lambda x: f"{x:.1f} %"
        }
        styled_comparativa = comparativa.sort_values("diferencia", ascending=False).style.format(fmt_cols)
        st.dataframe(styled_comparativa, use_container_width=True, hide_index=True)

        st.subheader("🔝 Principales Incrementos")
        top_inc = comparativa.sort_values("diferencia", ascending=False).head(15)
        st.bar_chart(top_inc, x="client_code_norm", y="diferencia", use_container_width=True)

        st.subheader("🔻 Principales Descensos")
        top_dec = comparativa.sort_values("diferencia", ascending=True).head(15)
        st.bar_chart(top_dec, x="client_code_norm", y="diferencia", use_container_width=True)
