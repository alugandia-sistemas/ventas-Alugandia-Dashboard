import streamlit as st
from auth import logout, approve_user
from supabase_client import get_supabase_client
from utils import redirect

supabase = get_supabase_client()

if "user" not in st.session_state or not st.session_state["user"]:
    redirect("../Home.py")

user_email = st.session_state["user"].email
if user_email != "jmgomez@alugandia.es":
    st.warning("⚠️ No tienes permisos para acceder a esta página.")
    redirect("../Home.py")

st.sidebar.success(f"👋 Admin: {user_email}")
if st.sidebar.button("Cerrar sesión"):
    logout()

st.title("👤 Panel de Administración de usuarios")

pending = supabase.table("pending_users").select("*").eq("approved", False).execute()
if not pending.data:
    st.info("✅ No hay usuarios pendientes.")
else:
    for user in pending.data:
        col1, col2 = st.columns([3, 1])
        col1.write(user["email"])
        if col2.button("Aprobar", key=user["email"]):
            approve_user(user["email"])
