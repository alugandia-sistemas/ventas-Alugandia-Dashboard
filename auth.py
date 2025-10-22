import streamlit as st
from supabase_client import get_supabase_client
from utils import redirect

supabase = get_supabase_client()
ADMIN_EMAIL = "jmgomez@alugandia.es"

def get_user_approval(email: str) -> bool:
    try:
        res = supabase.table("pending_users").select("approved").eq("email", email).execute()
        if res.data:
            return bool(res.data[0]["approved"])
        return False
    except Exception as e:
        print("Error al comprobar aprobación:", e)
        return False

def login(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        approved = get_user_approval(email)
        if not approved:
            st.warning("⏳ Tu cuenta aún no ha sido aprobada por el administrador.")
            supabase.auth.sign_out()
            return
        st.session_state["user"] = user
        st.success("✅ Sesión iniciada correctamente.")
        if email == ADMIN_EMAIL:
            redirect("pages/admin.py")
        else:
            redirect("pages/dashboard.py")
    except Exception as e:
        st.error("❌ Error de autenticación. Verifica tus credenciales.")
        print(e)

def register(email: str, password: str):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        supabase.table("pending_users").insert({"email": email, "approved": False}).execute()
        st.success("✅ Registro completado. Espera la aprobación del administrador.")
        redirect("Home.py")
    except Exception as e:
        st.error("❌ No se pudo crear la cuenta.")
        print(e)

def logout():
    try:
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.success("👋 Sesión cerrada correctamente.")
        redirect("Home.py")
    except Exception as e:
        st.error("❌ Error al cerrar sesión.")
        print(e)

def approve_user(email: str):
    try:
        supabase.table("pending_users").update({"approved": True}).eq("email", email).execute()
        st.success(f"✅ Usuario {email} aprobado.")
        st.experimental_rerun()
    except Exception as e:
        st.error("❌ Error al aprobar usuario.")
        print(e)
