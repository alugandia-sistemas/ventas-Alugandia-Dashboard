import streamlit as st
from supabase_client import get_supabase_client

supabase = get_supabase_client()

def login(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.success("✅ Sesión iniciada correctamente.")
    except Exception as e:
        st.error("❌ Error de autenticación: verifica tus credenciales.")
        print(e)

def register(email: str, password: str):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.success("✅ Usuario creado. Revisa tu correo para confirmar la cuenta.")
        st.sleep(2)
        st.switch_page("main")
    except Exception as e:
        st.error("❌ No se pudo crear la cuenta.")
        print(e)

def logout():
    try:
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.success("👋 Sesión cerrada correctamente.")
    except Exception as e:
        st.error("❌ Error al cerrar sesión.")
        print(e)
