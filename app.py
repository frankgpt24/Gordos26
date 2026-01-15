import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
import extra_streamlit_components as stx
import time

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

# Estilos
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stMetricValue"] { font-size: 40px; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

cookie_manager = stx.CookieManager()

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_con_fuerza():
    # Forzamos la limpieza de la caché interna de Streamlit antes de leer
    st.cache_data.clear()
    
    # Leemos los datos (ttl=0 para no usar caché)
    df_raw = conn.read(ttl=0)
    
    if df_raw is not None and not df_raw.empty:
        # Guardamos una copia en bruto para depuración
        df_debug = df_raw.copy()
        
        df = df_raw.copy()
        # Limpieza de Pesos: comas por puntos y convertir a número
        df['Peso'] = df['Peso'].astype(str).str.replace(',', '.')
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        
        # Limpieza de Fechas: Formato flexible
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        
        # Quitar errores y normalizar
        df = df.dropna(subset=['Fecha', 'Peso'])
        df['Fecha'] = df['Fecha'].dt.normalize()
        df = df.sort_values(by='Fecha')
        
        return df, df_debug
    return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"]), pd.DataFrame()

# --- USUARIOS ---
usuarios = {
    "admin": "valencia", "Alfon": "maquina", "hperis": "admin", 
    "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", 
    "Sergio": "operacion2d", "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"
}

# --- LOGIN ---
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    user_cookie = cookie_manager.get('user_weight_app')
    if user_cookie:
        for u in usuarios:
            if u.lower() == user_cookie.lower():
                st.session_state['logueado'] = True
                st.session_state['usuario_actual'] = u
                st.rerun()

if not st.session_state['logueado']:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.title("🏆 Gordos 2026")
        with st.form("login"):
            u_input = st.text_input("Usuario")
            p_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                user_found = next((u for u in usuarios if u.lower() == u_input.lower()), None)
                if user_found and usuarios[user_found] == p_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user_found
                    cookie_manager.set('user_weight_app', user_found, expires_at=datetime.now() + pd.Timedelta(days=30))
                    st.rerun()
                else:
                    st.error("Error")
else:
    # --- APP PRINCIPAL ---
    st.title("🏆 Gordos 2026")
    if st.button("🔄 Forzar Actualización (Limpiar Caché)"):
        st.cache_data.clear()
        st.rerun()

    # Cargar datos
    df, df_raw_debug = cargar_datos_con_fuerza()

    # Métrica Grupal
    if not df.empty:
        total = 0
        for u in df['Usuario'].unique():
            ud = df[df['Usuario'] == u]
            total += (ud.iloc[0]['Peso'] - ud.iloc[-1]['Peso'])
        st.metric("🔥 KILOS PERDIDOS ENTRE TODOS", f"{round(total, 1)} kg")

    # Registro y Borrado
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Registrar Peso"):
            with st.form("reg"):
                f = st.date_input("Fecha", datetime.now())
                p = st.number_input("Peso", value=80.0, step=0.1)
                if st.form_submit_button("Guardar"):
                    # Formato exacto que pediste
                    nueva = pd.DataFrame({"Fecha": [f.strftime('%Y-%m-%d 0:00')], "Usuario": [st.session_state['usuario_actual']], "Peso": [str(p).replace('.', ',')]})
                    df_ex = conn.read(ttl=0)
                    conn.update(data=pd.concat([df_ex, nueva], ignore_index=True))
                    st.success("OK")
                    time.sleep(1)
                    st.rerun()
    with c2:
        with st.expander("🗑️ Borrar Último"):
            mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
            if not mis_d.empty:
                idx = mis_d.index[-1]
                if st.button("Confirmar Borrado"):
                    df_ex = conn.read(ttl=0)
                    conn.update(data=df_ex.drop(idx))
                    st.rerun()

    # Gráfica
    if not df.empty:
        st.subheader("📊 Evolución")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True)
        fig.update_xaxes(type='date', tickformat="%d/%m")
        st.plotly_chart(fig, use_container_width=True)

    # SECCIÓN DE DEPURACIÓN CRÍTICA
    st.divider()
    with st.expander("🛠️ ZONA DE DIAGNÓSTICO (Si falla, mira aquí)"):
        st.write("### 1. Datos tal cual vienen de Google (RAW):")
        st.write("Si aquí no ves tus datos nuevos, es que Google Sheets no los está enviando.")
        st.dataframe(df_raw_debug)
        
        st.write("### 2. Datos después de limpiar (PROCESADOS):")
        st.write("Si aquí faltan filas respecto a la tabla de arriba, es que el formato de Fecha o Peso está mal.")
        st.dataframe(df)
