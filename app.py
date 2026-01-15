import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
import extra_streamlit_components as stx # Nueva librería para cookies

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

# CSS para limpieza visual e inyección de etiquetas para el navegador
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            .block-container {padding-top: 2rem;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- GESTIÓN DE COOKIES (RECORDAR SESIÓN) ---
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- LISTA DE FRASES ---
FRASES = [
    "¡Nunca pierdas la esperanza!",
    "El éxito es la suma de pequeños esfuerzos repetidos día tras día.",
    "No te detengas hasta que te sientas orgulloso.",
    "Comer bien es una forma de respetarte a ti mismo.",
    "La disciplina es hacer lo que hay que hacer, incluso cuando no quieres.",
    "Cada gramo cuenta, cada paso suma. ¡Tú puedes!",
    "Tu yo del futuro te agradecerá lo que hagas hoy.",
    "La meta es ser mejor de lo que fuiste ayer."
]

if 'frase_dia' not in st.session_state:
    st.session_state['frase_dia'] = random.choice(FRASES)

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(ttl=0)

# --- SISTEMA DE LOGIN ---
usuarios = {"admin": "valencia", "Alfon": "maquina", "hperis": "admin", "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", "Sergio": "operacion2d",  "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"}

# Intentar auto-login con cookie
saved_user = cookie_manager.get('user_weight_app')

if 'logueado' not in st.session_state:
    if saved_user in usuarios:
        st.session_state['logueado'] = True
        st.session_state['usuario_actual'] = saved_user
    else:
        st.session_state['logueado'] = False

if not st.session_state['logueado']:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.title("🏆 Gordos 2026")
        st.subheader(st.session_state['frase_dia'])
        st.write("---")
        
        # Formulario de Login
        with st.form("login_form"):
            st.markdown("### Acceso")
            # Usamos etiquetas estándar para que el navegador las detecte
            usuario_input = st.text_input("Username", placeholder="Usuario")
            password_input = st.text_input("Password", type="password", placeholder="Contraseña")
            recordarme = st.checkbox("Recordarme en este equipo")
            
            submit_button = st.form_submit_button("Entrar al Reto", use_container_width=True)
            
            if submit_button:
                if usuario_input in usuarios and usuarios[usuario_input] == password_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = usuario_input
                    
                    # Si marca "Recordarme", guardamos una cookie por 30 días
                    if recordarme:
                        cookie_manager.set('user_weight_app', usuario_input, expires_at=datetime.now() + pd.Timedelta(days=30))
                    
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
else:
    # --- CONTENIDO DE LA APP ---
    st.title("🏆 Gordos 2026")
    st.markdown(f"### *{st.session_state['frase_dia']}* 💪")
    
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.write(f"Conectado como: **{st.session_state['usuario_actual'].capitalize()}**")
    with col_logout:
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state['logueado'] = False
            cookie_manager.delete('user_weight_app') # Borramos la cookie al salir
            st.rerun()
            
    st.divider()
    
    df = cargar_datos()

    # --- REGISTRAR PESO ---
    with st.expander("➕ Registrar nuevo peso"):
        with st.form("registro_peso"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.now())
            with col2:
                peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1)
            
            if st.form_submit_button("Guardar peso", use_container_width=True):
                nueva_fila = pd.DataFrame({"Fecha": [str(fecha)], 
                                           "Usuario": [st.session_state['usuario_actual']], 
                                           "Peso": [peso]})
                df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
                conn.update(data=df_actualizado)
                st.success("¡Peso registrado!")
                st.rerun()

    # --- LÓGICA DE ESTADÍSTICAS ---
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values(['Usuario', 'Fecha'])

        stats_list = []
        for user in df['Usuario'].unique():
            user_data = df[df['Usuario'] == user]
            if len(user_data) > 0:
                peso_inicial = user_data.iloc[0]['Peso']
                peso_actual = user_data.iloc[-1]['Peso']
                total_perdido = peso_inicial - peso_actual
                porcentaje_perdido = (total_perdido / peso_inicial) * 100 if peso_inicial > 0 else 0
                
                if len(user_data) >= 2:
                    perdido_semana = user_data.iloc[-2]['Peso'] - peso_actual
                else:
                    perdido_semana = 0
                
                stats_list.append({
                    "Usuario": user.capitalize(),
                    "Peso Actual": peso_actual,
                    "Total Perdido (kg)": round(total_perdido, 2),
                    "Perdido (%)": f"{round(porcentaje_perdido, 2)}%",
                    "Esta Semana (kg)": round(perdido_semana, 2),
                    "Porcentaje_Num": porcentaje_perdido
                })
        
        df_stats = pd.DataFrame(stats_list)

        # --- GRÁFICA ---
        st.subheader("📊 Evolución Temporal")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLAS DE RANKING ---
        st.divider()
        st.subheader("🏆 Salón de la Fama")
        col_rank1, col_rank2, col_rank3 = st.columns(3)
        with col_rank1:
            st.markdown("#### 🔥 Esta Semana")
            st.dataframe(df_stats[['Usuario', 'Esta Semana (kg)']].sort_values(by="Esta Semana (kg)", ascending=False), hide_index=True, use_container_width=True)
        with col_rank2:
            st.markdown("#### 🥇 Total Kilos")
            st.dataframe(df_stats[['Usuario', 'Total Perdido (kg)']].sort_values(by="Total Perdido (kg)", ascending=False), hide_index=True, use_container_width=True)
        with col_rank3:
            st.markdown("#### 📉 Total %")
            ranking_pct = df_stats[['Usuario', 'Perdido (%)', 'Porcentaje_Num']].sort_values(by="Porcentaje_Num", ascending=False)
            st.dataframe(ranking_pct[['Usuario', 'Perdido (%)']], hide_index=True, use_container_width=True)

        with st.expander("Ver todos los registros"):
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos registrados.")
