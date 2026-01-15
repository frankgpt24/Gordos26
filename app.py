import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
import extra_streamlit_components as stx
import time

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .block-container {padding-top: 2rem;}
    /* Estilo para la métrica grupal */
    [data-testid="stMetricValue"] { font-size: 40px; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE COOKIES ---
cookie_manager = stx.CookieManager()

# --- LISTA DE FRASES ---
FRASES = [
    "¡Nunca pierdas la esperanza!",
    "Para adelgazar hay que comer...",
    "Tonto el que lo lea :P",
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

conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(ttl=0)

usuarios = {"admin": "valencia", "Alfon": "maquina", "hperis": "admin", "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", "Sergio": "operacion2d",  "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"}

# --- LÓGICA DE AUTO-LOGIN ---
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    with st.spinner("Cargando sesión..."):
        time.sleep(0.5)
        user_cookie = cookie_manager.get('user_weight_app')
        if user_cookie in usuarios:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = user_cookie
            st.rerun()

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.title("🏆 Gordos 2026")
        st.subheader(st.session_state['frase_dia'])
        st.write("---")
        with st.form("login_form"):
            st.markdown("### Acceso al Reto")
            usuario_input = st.text_input("Username / Usuario", key="user_input")
            password_input = st.text_input("Password / Contraseña", type="password", key="pass_input")
            recordarme = st.checkbox("Recordarme en este equipo", value=True)
            submit = st.form_submit_button("Entrar", use_container_width=True)
            if submit:
                if usuario_input in usuarios and usuarios[usuario_input] == password_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = usuario_input
                    if recordarme:
                        cookie_manager.set('user_weight_app', usuario_input, 
                                         expires_at=datetime.now() + pd.Timedelta(days=30))
                    st.success("¡Bienvenido!")
                    time.sleep(0.5)
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
            cookie_manager.delete('user_weight_app')
            st.rerun()
            
    st.divider()
    
    df = cargar_datos()

    # --- LÓGICA DE DATOS ---
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values(['Usuario', 'Fecha'])

        # 1. MARCADOR GRUPAL (Sugerencia 1)
        total_perdido_grupal = 0
        stats_list = []
        
        for user in df['Usuario'].unique():
            user_data = df[df['Usuario'] == user]
            if len(user_data) > 0:
                peso_inicial = user_data.iloc[0]['Peso']
                peso_actual = user_data.iloc[-1]['Peso']
                perdido_usuario = peso_inicial - peso_actual
                total_perdido_grupal += perdido_usuario
                
                # Para el ranking
                porcentaje_perdido = (perdido_usuario / peso_inicial) * 100 if peso_inicial > 0 else 0
                perdido_semana = user_data.iloc[-2]['Peso'] - peso_actual if len(user_data) >= 2 else 0
                
                stats_list.append({
                    "Usuario": user.capitalize(),
                    "Peso Actual": peso_actual,
                    "Total Perdido (kg)": round(perdido_usuario, 2),
                    "Perdido (%)": f"{round(porcentaje_perdido, 2)}%",
                    "Esta Semana (kg)": round(perdido_semana, 2),
                    "Porcentaje_Num": porcentaje_perdido
                })
        
        # Mostrar el marcador grupal destacado
        st.metric(label="🔥 KILOS PERDIDOS ENTRE TODOS", value=f"{round(total_perdido_grupal, 1)} kg")
        st.write("---")

        df_stats = pd.DataFrame(stats_list)

    # --- REGISTRAR Y BORRAR PESO ---
    col_reg, col_del = st.columns(2)
    
    with col_reg:
        with st.expander("➕ Registrar nuevo peso"):
            peso_defecto = 80.0
            if not df.empty:
                datos_usuario = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not datos_usuario.empty:
                    peso_defecto = float(datos_usuario.iloc[-1]['Peso'])

            with st.form("registro_peso"):
                f_reg = st.date_input("Fecha", datetime.now())
                p_reg = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=peso_defecto, step=0.1)
                if st.form_submit_button("Guardar", use_container_width=True):
                    nueva_fila = pd.DataFrame({"Fecha": [str(f_reg)], "Usuario": [st.session_state['usuario_actual']], "Peso": [p_reg]})
                    df_upd = pd.concat([df, nueva_fila], ignore_index=True)
                    conn.update(data=df_upd)
                    st.success("¡Registrado!")
                    time.sleep(1)
                    st.rerun()

    with col_del:
        with st.expander("🗑️ Borrar último registro"):
            if not df.empty:
                mis_datos = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_datos.empty:
                    ultimo_idx = mis_datos.index[-1]
                    ultimo_val = mis_datos.iloc[-1]
                    st.warning(f"Se borrará: {ultimo_val['Peso']}kg del {ultimo_val['Fecha'].strftime('%d/%m/%Y')}")
                    if st.button("Confirmar Borrado", use_container_width=True):
                        df_upd = df.drop(ultimo_idx)
                        conn.update(data=df_upd)
                        st.error("Registro eliminado")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("No tienes registros todavía.")

    # --- VISUALIZACIÓN ---
    if not df.empty:
        st.subheader("📊 Evolución Temporal")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🏆 Salón de la Fama")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🔥 Esta Semana")
            st.dataframe(df_stats[['Usuario', 'Esta Semana (kg)']].sort_values(by="Esta Semana (kg)", ascending=False), hide_index=True, use_container_width=True)
        with c2:
            st.markdown("#### 🥇 Total Kilos")
            st.dataframe(df_stats[['Usuario', 'Total Perdido (kg)']].sort_values(by="Total Perdido (kg)", ascending=False), hide_index=True, use_container_width=True)
        with c3:
            st.markdown("#### 📉 Total %")
            ranking_pct = df_stats[['Usuario', 'Perdido (%)', 'Porcentaje_Num']].sort_values(by="Porcentaje_Num", ascending=False)
            st.dataframe(ranking_pct[['Usuario', 'Perdido (%)']], hide_index=True, use_container_width=True)

        with st.expander("Ver historial completo"):
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos registrados.")
