import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

def get_supabase_client() -> Client:
    # Cargar .env una sola vez
    if not st.session_state.get("_dotenv_loaded"):
        load_dotenv(override=False)
        st.session_state["_dotenv_loaded"] = True

    # Prioridad: st.secrets -> variables de entorno -> .env (cargado arriba)
    url = st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None
    key = st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None

    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "⚠️ Faltan credenciales de Supabase. Define `SUPABASE_URL` y `SUPABASE_KEY` "
            "en *[Settings → Secrets]* (Streamlit) o como variables de entorno (.env/host)."
        )
        st.stop()

    return create_client(url, key)