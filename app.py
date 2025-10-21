import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Alugandia · Ventas multi-año", layout="wide")
st.title("📊 Alugandia · Dashboard de Ventas")
st.subheader("Análisis de ventas por cliente y año (2020-2025)")
# st.caption("Carga automática de CSVs por año con columnas: client_code, client_name, net_sales, client_code_norm.")
st.caption("Última actualización de datos: 21/10/2025")

# Login / Proteccion con contraseña
def login():
    st.sidebar.subheader("🔐 Acceso privado")
    password = st.sidebar.text_input("Contraseña:", type="password")
    if password != st.secrets["APP_PASSWORD"]:
        st.error("Contraseña incorrecta o falta.")
        st.stop()

login()

# --- Configuración ---
DATA_FOLDER = "data"  # Carpeta donde se guardan los CSVs

# --- Funciones auxiliares ---
def label_segment(amount: float) -> str:
    if amount > 15000:
        return "🟢 >15K"
    elif amount >= 10000:
        return "🟡 10K–15K"
    else:
        return "🔴 <10K"

# --- Cargar todos los CSVs ---
@st.cache_data
def load_all_csvs(path: str):
    frames = []
    if not os.path.exists(path):
        st.warning(f"No se encontró la carpeta '{path}'. Crea una carpeta con tus CSVs dentro del proyecto.")
        return pd.DataFrame()
    for fname in os.listdir(path):
        if fname.lower().endswith(".csv"):
            year_match = re.search(r"(\d{4})", fname)
            if not year_match:
                continue
            year = int(year_match.group(1))
            df = pd.read_csv(os.path.join(path, fname))
            if not {"client_code","client_name","net_sales","client_code_norm"}.issubset(df.columns):
                st.warning(f"⚠️ El archivo {fname} no tiene todas las columnas requeridas.")
                continue
            df["year"] = year
            frames.append(df)
    if not frames:
        st.warning("No se encontraron archivos CSV válidos (por ejemplo: ventas_2024.csv, ventas_2025.csv).")
        return pd.DataFrame()
    df_all = pd.concat(frames, ignore_index=True)
    # Excluir Soleco Traders
    df_all = df_all[df_all["client_code_norm"] != 12334]
    df_all["segment"] = df_all["net_sales"].apply(label_segment)
    return df_all

# --- Cargar datos ---
df_all = load_all_csvs(DATA_FOLDER)
if df_all.empty:
    st.stop()

# --- Filtros ---
st.sidebar.header("🔎 Filtros")
years = sorted(df_all["year"].unique())
year = st.sidebar.selectbox("Año", years, index=len(years)-1)
seg_sel = st.sidebar.selectbox("Segmento", ["Todos", "🟢 >15K", "🟡 10K–15K", "🔴 <10K"], index=0)
show_names = st.sidebar.checkbox("Mostrar nombres de clientes", value=False)

df_year = df_all[df_all["year"] == year].copy()
if seg_sel != "Todos":
    df_year = df_year[df_year["segment"] == seg_sel]

# --- Filtro de exclusión ---
st.sidebar.subheader("🚫 Excluir clientes")
exclude_options = sorted(df_year["client_name"].unique())
exclude_selected = st.sidebar.multiselect(
    "Selecciona clientes a excluir del análisis:",
    options=exclude_options,
    default=[]
)
if exclude_selected:
    df_year = df_year[~df_year["client_name"].isin(exclude_selected)]

# --- Métricas ---
total_sales = df_year["net_sales"].sum()
n_clients = df_year["client_code_norm"].nunique()

c1, c2 = st.columns(2)
c1.metric("Ventas totales", f"{total_sales:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
c2.metric("Nº de clientes", f"{n_clients}")

# --- Gráficos ---
colA, colB = st.columns([1,2])

with colA:
    seg_summary = df_year.groupby("segment", as_index=False)["net_sales"].sum()
    fig_pie = px.pie(seg_summary, names="segment", values="net_sales", hole=0.55,
                     title=f"Distribución por segmento ({year})")
    st.plotly_chart(fig_pie, use_container_width=True)

with colB:
    top_df = df_year.sort_values("net_sales", ascending=False).head(20)
    if show_names:
        top_df["label"] = top_df["client_name"] + " (" + top_df["client_code_norm"].astype(str) + ")"
    else:
        top_df["label"] = top_df["client_code_norm"].astype(str)
    fig_bar = px.bar(top_df, x="net_sales", y="label", orientation="h",
                     title=f"Top 20 clientes · {year}", text="net_sales")
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Facturación (€)", yaxis_title="Cliente")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Evolución anual ---
st.subheader("📈 Evolución anual de ventas totales")
year_summary = df_all.groupby("year", as_index=False)["net_sales"].sum()
fig_year = px.line(year_summary, x="year", y="net_sales", markers=True, title="Evolución anual de ventas")
st.plotly_chart(fig_year, use_container_width=True)

# --- Tabla ---
st.subheader(f"📋 Clientes {year}")
cols = ["client_code", "client_code_norm", "net_sales", "segment"]
rename_map = {
    "client_code": "Código original",
    "client_code_norm": "Código normalizado",
    "net_sales": "Facturación (€)",
    "segment": "Segmento"
}
if show_names:
    cols.insert(1, "client_name")
    rename_map["client_name"] = "Cliente"

df_table = df_year[cols].rename(columns=rename_map)
st.dataframe(df_table, use_container_width=True)
