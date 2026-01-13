import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Control de Peso Grupal", layout="wide")

# 2. Base de datos simple (Para este ejemplo usaremos un archivo CSV local)
# En el futuro, esto se conectará a tu Google Sheets
DB_FILE = "datos_peso.csv"

def cargar_datos():
    try:
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])

# 3. Sistema de Login muy básico
usuarios = {"admin": "1234", "juan": "peso01", "maria": "peso02"} # Puedes añadir los 8 aquí

def login():
    st.sidebar.title("Acceso Usuarios")
    usuario = st.sidebar.text_input("Nombre de usuario")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == password:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = usuario
        else:
            st.sidebar.error("Usuario o contraseña incorrectos")

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

# --- LÓGICA DE LA APP ---
if not st.session_state['logueado']:
    st.title("Bienvenido al Reto de Peso")
    st.info("Por favor, inicia sesión en la barra lateral.")
    login()
else:
    st.title(f"Hola, {st.session_state['usuario_actual']} 👋")
    
    # Cargar datos existentes
    df = cargar_datos()

    # --- SECCIÓN 1: REGISTRAR PESO ---
    st.subheader("Registrar nuevo peso")
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", datetime.now())
    with col2:
        peso = st.number_input("Tu peso (kg)", min_value=30.0, max_value=200.0, step=0.1)
    
    if st.button("Guardar peso"):
        nueva_fila = pd.DataFrame({"Fecha": [fecha], "Usuario": [st.session_state['usuario_actual']], "Peso": [peso]})
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("¡Peso guardado correctamente!")
        st.rerun()

    # --- SECCIÓN 2: GRÁFICA DE EVOLUCIÓN ---
    st.divider()
    st.subheader("Evolución del grupo")
    
    if not df.empty:
        # Convertir fecha a formato que entienda la gráfica
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Crear la gráfica con Plotly
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", 
                      title="Progreso de todos los miembros",
                      markers=True)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla con los últimos datos
        st.subheader("Últimos registros")
        st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
    else:
        st.write("Aún no hay datos registrados.")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()
