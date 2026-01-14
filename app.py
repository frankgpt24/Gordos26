import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import random

# 1. CONFIGURACIÓN Y ESTILOS PARA OCULTAR MENÚS
st.set_page_config(page_title="Gordos 2026", layout="wide", page_icon="⚖️")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- LISTA DE FRASES MOTIVADORAS ---
FRASES = [
    "¡Nunca pierdas la esperanza!",
    "Para adelgazar hay que comer...",
    "El éxito es la suma de pequeños esfuerzos repetidos día tras día.",
    "Tu cuerpo escucha todo lo que tu mente dice. ¡Mantente positivo!",
    "No te detengas hasta que te sientas orgulloso.",
    "Comer bien es una forma de respetarte a ti mismo.",
    "La disciplina es hacer lo que hay que hacer, incluso cuando no quieres.",
    "No es una dieta, es un estilo de vida.",
    "Cada gramo cuenta, cada paso suma. ¡Tú puedes!",
    "Tu yo del futuro te agradecerá lo que hagas hoy.",
    "La paciencia es amarga, pero su fruto es muy dulce.",
    "Transforma tu cuerpo, transforma tu vida.",
    "Si te cansas, aprende a descansar, no a rendirte.",
    "La meta es ser mejor de lo que fuiste ayer."
]

if 'frase_dia' not in st.session_state:
    st.session_state['frase_dia'] = random.choice(FRASES)

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(ttl=0)

# --- LOGIN ---
usuarios = {"admin": "valencia", "Alfon": "maquina", "hperis": "admin", "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", "Sergio": "operacion2d",  "Alberto": "gorriki", "Fran": "flaco"}

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.title("🏆 Gordos 2026")
    st.subheader(st.session_state['frase_dia'])
    st.divider()
    
    with st.sidebar:
        st.title("Acceso")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario in usuarios and usuarios[usuario] == password:
                st.session_state['logueado'] = True
                st.session_state['usuario_actual'] = usuario
                st.session_state['frase_dia'] = random.choice(FRASES)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
else:
    # --- CABECERA ---
    st.title("🏆 Gordos 2026")
    st.markdown(f"### *{st.session_state['frase_dia']}* 💪")
    st.write(f"Conectado como: **{st.session_state['usuario_actual'].capitalize()}**")
    st.divider()
    
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
                
                if len(user_data) >= 2:
                    perdido_semana = user_data.iloc[-2]['Peso'] - peso_actual
                else:
                    perdido_semana = 0
                
                stats_list.append({
                    "Usuario": user.capitalize(),
                    "Peso Actual": peso_actual,
                    "Total Perdido (kg)": round(total_perdido, 2),
                    "Esta Semana (kg)": round(perdido_semana, 2)
                })
        
        df_stats = pd.DataFrame(stats_list)

        # --- GRÁFICA ---
        st.subheader("📊 Evolución Temporal")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLAS DE RANKING ---
        st.divider()
        st.subheader("🏆 Salón de la Fama")
        
        col_rank1, col_rank2 = st.columns(2)
        
        with col_rank1:
            st.markdown("#### 🔥 Ganadores de la Semana")
            ranking_semanal = df_stats[['Usuario', 'Esta Semana (kg)']].sort_values(by="Esta Semana (kg)", ascending=False)
            st.dataframe(ranking_semanal, hide_index=True, use_container_width=True)
            
        with col_rank2:
            st.markdown("#### 🥇 Ranking Histórico Total")
            ranking_total = df_stats[['Usuario', 'Total Perdido (kg)']].sort_values(by="Total Perdido (kg)", ascending=False)
            st.dataframe(ranking_total, hide_index=True, use_container_width=True)

        with st.expander("Ver todos los registros"):
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos registrados.")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        if 'frase_dia' in st.session_state:
            del st.session_state['frase_dia']
        st.rerun()
