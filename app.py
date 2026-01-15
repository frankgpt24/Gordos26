import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
import extra_streamlit_components as stx
import time
import re

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

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
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MOTOR DE LIMPIEZA REFORZADO ---
def limpiar_datos_invencible(df_raw):
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])
    
    df = df_raw.copy()
    
    # 1. LIMPIEZA DE PESO (Rescata números aunque tengan comas, espacios o texto)
    def extraer_peso(valor):
        try:
            # Convertir a string y limpiar
            s = str(valor).replace(',', '.').strip()
            # Extraer solo el primer número que encuentre (ej: "94.6 kg" -> "94.6")
            match = re.search(r"[-+]?\d*\.\d+|\d+", s)
            return float(match.group()) if match else None
        except:
            return None

    df['Peso'] = df['Peso'].apply(extraer_peso)
    
    # 2. LIMPIEZA DE FECHA (Prueba varios formatos para no perder nada)
    # Primero intentamos el estándar, si falla usamos 'coerce'
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    
    # 3. ELIMINAR FILAS REALMENTE CORRUPTAS (Sin fecha o sin peso)
    df = df.dropna(subset=['Fecha', 'Peso'])
    
    # 4. NORMALIZAR Y ORDENAR
    df['Fecha'] = df['Fecha'].dt.normalize()
    df = df.sort_values(by=['Fecha', 'Usuario'])
    
    return df

# --- USUARIOS ---
usuarios = {
    "admin": "valencia", "Alfon": "maquina", "hperis": "admin", 
    "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", 
    "Sergio": "operacion2d", "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"
}

# --- LÓGICA DE LOGIN ---
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
    
    # Botón de refresco manual
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

    # CARGA DE DATOS
    df_raw = conn.read(ttl=0)
    df = limpiar_datos_invencible(df_raw)

    # Marcador Grupal
    if not df.empty:
        total = 0
        for u in df['Usuario'].unique():
            ud = df[df['Usuario'] == u]
            if len(ud) >= 1:
                total += (ud.iloc[0]['Peso'] - ud.iloc[-1]['Peso'])
        st.metric("🔥 KILOS PERDIDOS ENTRE TODOS", f"{round(total, 1)} kg")

    # Registro y Borrado
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Registrar Peso"):
            with st.form("reg"):
                f = st.date_input("Fecha", datetime.now())
                p = st.number_input("Peso (kg)", value=80.0, step=0.1)
                if st.form_submit_button("Guardar"):
                    # Formato exacto solicitado
                    nueva = pd.DataFrame({
                        "Fecha": [f.strftime('%Y-%m-%d 0:00')], 
                        "Usuario": [st.session_state['usuario_actual']], 
                        "Peso": [str(p).replace('.', ',')]
                    })
                    df_actual = conn.read(ttl=0)
                    conn.update(data=pd.concat([df_actual, nueva], ignore_index=True))
                    st.success("Guardado en Google Sheets")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
    with c2:
        with st.expander("🗑️ Borrar Último"):
            mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
            if not mis_d.empty:
                idx_original = mis_d.index[-1]
                st.warning(f"Borrar registro de {mis_d.iloc[-1]['Peso']} kg")
                if st.button("Confirmar Borrado"):
                    df_actual = conn.read(ttl=0)
                    conn.update(data=df_actual.drop(idx_original))
                    st.cache_data.clear()
                    st.rerun()

    # Gráfica
    if not df.empty:
        st.subheader("📊 Evolución")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        fig.update_xaxes(type='date', tickformat="%d/%m")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🏆 Rankings")
        # Generar tabla de rankings
        rank_data = []
        for u in df['Usuario'].unique():
            ud = df[df['Usuario'] == u]
            p_i, p_a = ud.iloc[0]['Peso'], ud.iloc[-1]['Peso']
            rank_data.append({"Usuario": u, "Total Perdido (kg)": round(p_i - p_a, 2), "Peso Actual": p_a})
        st.table(pd.DataFrame(rank_data).sort_values("Total Perdido (kg)", ascending=False))

    # ZONA DE DIAGNÓSTICO
    with st.expander("🛠️ ZONA DE DIAGNÓSTICO"):
        st.write("Datos RAW (Lo que viene de Google):")
        st.dataframe(df_raw)
        st.write("Datos PROCESADOS (Lo que va a la gráfica):")
        st.dataframe(df)
