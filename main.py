import streamlit as st
from auth import login, register, logout
from dashboard import render_dashboard

st.set_page_config(page_title="Dashboard Ventas", page_icon="🔐")

if "user" not in st.session_state:
    st.session_state["user"] = None

st.title("Acceso - Dashboard Ventas")

if not st.session_state["user"]:
    tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab1:
        st.subheader("Inicio de sesión")
        email = st.text_input("Correo electrónico", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Entrar"):
            if email and password:
                login(email, password)
            else:
                st.warning("Introduce correo y contraseña.")

    with tab2:
        st.subheader("Crear cuenta nueva")
        new_email = st.text_input("Correo nuevo", key="register_email")
        new_pass = st.text_input("Contraseña nueva", type="password", key="register_pass")
        if st.button("Registrarse"):
            if new_email and new_pass:
                register(new_email, new_pass)
            else:
                st.warning("Introduce correo y contraseña.")

else:
    st.sidebar.success(f"👋 Hola, {st.session_state['user'].email}")
    if st.sidebar.button("Cerrar sesión"):
        logout()

    render_dashboard()
