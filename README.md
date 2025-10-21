
# Alugandia · Dashboard de Ventas (2020–2025)

## Ejecución local

0. Instalar environment
```bash
python -m venv /path/to/new/virtual/environment
```

Ejecutar env en PowerhSell
```bash
<venv>\Scripts\Activate.ps1
```

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicia el dashboard:
   ```bash
   streamlit run app.py
   ```
3. Se abrirá en tu navegador en `http://localhost:8501`.

## Segmentos de facturación
- 🟢 > 15.000 €
- 🟡 10.000–15.000 €
- 🔴 < 10.000 €



## ⚙️ Comportamiento actualizado

- Lee todos los archivos CSV del directorio /data (por ejemplo: ventas_2024.csv, ventas_2025.csv, etc.).
- Extrae automáticamente el año del nombre del archivo.
- Permite filtrar por:

   - Año

   - Segmento de facturación

   - Código de artículo (code_norm)

- Muestra métricas, gráficos y una tabla detallada.
- Calcula los segmentos según net_sales:

   - 🟢 > 20K

   - 🟡 10K–20K

   - 🔴 <10K

   ## Deployment in Render

[Secrets management in Render](https://discuss.streamlit.io/t/secrets-management-in-render/39736/3)

```bash
mkdir .streamlit; cp /etc/secrets/secrets.toml ./.streamlit/; pip install --upgrade pip && pip install -r requirements.txt
```
