import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(ttl=0)

# --- LOGIN ---
usuarios = {"admin": "1234", "juan": "peso01", "hperis": "admin"}

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.title("🏆 Gordos 2026")
    st.subheader("¡Nunca pierdas la esperanza!")
    st.divider()
    
    with st.sidebar:
        st.title("Acceso")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario in usuarios and usuarios[usuario] == password:
                st.session_state['logueado'] = True
                st.session_state['usuario_actual'] = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
else:
    # --- CABECERA PERSONALIZADA ---
    st.title("🏆 Gordos 2026")
    st.markdown("### *¡Nunca pierdas la esperanza!* 💪")
    st.write(f"Bienvenido/a de nuevo, **{st.session_state['usuario_actual'].capitalize()}**")
    st.divider()
    
    # Leer datos actuales
    df = cargar_datos()

    # --- REGISTRAR PESO ---
    with st.expander("➕ Registrar nuevo peso"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha del pesaje", datetime.now())
        with col2:
            peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1)
        
        if st.button("Guardar peso"):
            nueva_fila = pd.DataFrame({"Fecha": [str(fecha)], 
                                       "Usuario": [st.session_state['usuario_actual']], 
                                       "Peso": [peso]})
            df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_actualizado)
            st.success("¡Peso registrado con éxito!")
            st.rerun()

    # --- GRÁFICA ---
    if not df.empty:
        st.subheader("📊 Evolución del grupo")
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        # Ordenamos por fecha para que la gráfica no salga desordenada
        df = df.sort_values('Fecha')
        
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", 
                      markers=True, template="plotly_white")
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Ver historial de datos"):
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos. ¡Sé el primero en inaugurar la báscula!")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()
