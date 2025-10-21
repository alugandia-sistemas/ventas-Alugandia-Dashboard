import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Carga las variables desde .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Carpeta donde están los CSV
DATA_FOLDER = "data"

# Recorre todos los archivos ventas_YYYY.csv
for file in os.listdir(DATA_FOLDER):
    if file.startswith("ventas_") and file.endswith(".csv"):
        year = int(file.split("_")[1].split(".")[0])
        path = os.path.join(DATA_FOLDER, file)
        print(f"📦 Importando {file} ({year})...")

        df = pd.read_csv(path)

        # Añadimos el año
        df["year"] = year

        # Normalizamos el código de cliente (sin puntos)
        if "client_code" in df.columns:
            df["client_code_norm"] = df["client_code"].astype(str).str.replace(".", "", regex=False)

        # Convertimos NaN a None para evitar errores al insertar
        df = df.where(pd.notnull(df), None)

        # Insertamos en Supabase en lotes de 500 filas
        rows = df.to_dict(orient="records")
        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            data, count = supabase.table("ventas").insert(batch).execute()
            print(f"   → Insertadas {len(batch)} filas")

print("✅ Importación completa.")
