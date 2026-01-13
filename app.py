import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Control de Peso Grupal", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(ttl=0) # ttl=0 para que no use caché y lea datos frescos

# --- LOGIN (Igual que antes) ---
usuarios = {"admin": "1234", "juan": "peso01", "maria": "peso02"}

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.title("Bienvenido al Reto de Peso")
    usuario = st.sidebar.text_input("Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == password:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = usuario
            st.rerun()
else:
    st.title(f"Hola, {st.session_state['usuario_actual']} 👋")
    
    # Leer datos actuales
    df = cargar_datos()

    # --- REGISTRAR PESO ---
    with st.expander("Registrar nuevo peso"):
        fecha = st.date_input("Fecha", datetime.now())
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1)
        
        if st.button("Guardar en Google Sheets"):
            # Crear nueva fila
            nueva_fila = pd.DataFrame({"Fecha": [str(fecha)], 
                                       "Usuario": [st.session_state['usuario_actual']], 
                                       "Peso": [peso]})
            # Combinar y actualizar
            df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_actualizado)
            st.success("¡Datos guardados!")
            st.rerun()

    # --- GRÁFICA ---
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.sort_values(by="Fecha", ascending=False))

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()
