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
    [data-testid="stMetricValue"] { font-size: 40px; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE COOKIES ---
cookie_manager = stx.CookieManager()

# --- FRASES ---
FRASES = ["¡Nunca pierdas la esperanza!", "Cada gramo cuenta.", "La disciplina es la clave.", "Tu yo del futuro te lo agradecerá."]
if 'frase_dia' not in st.session_state:
    st.session_state['frase_dia'] = random.choice(FRASES)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN DE CARGA DEFINITIVA (FECHAS Y COMAS) ---
def cargar_datos():
    df = conn.read(ttl=0)
    if df is not None and not df.empty:
        # 1. Limpieza de Pesos (Cambiar comas por puntos si existen)
        if df['Peso'].dtype == object:
            df['Peso'] = df['Peso'].str.replace(',', '.')
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        
        # 2. Limpieza de Fechas (Formato flexible)
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        
        # 3. Quitar filas con errores
        df = df.dropna(subset=['Fecha', 'Peso'])
        
        # 4. Normalizar y Ordenar
        df['Fecha'] = df['Fecha'].dt.normalize()
        return df.sort_values(by='Fecha')
    return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])

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
    with st.spinner("Cargando sesión..."):
        time.sleep(0.5)
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
        with st.form("login_form"):
            u_input = st.text_input("Usuario")
            p_input = st.text_input("Contraseña", type="password")
            recordarme = st.checkbox("Recordarme", value=True)
            if st.form_submit_button("Entrar", use_container_width=True):
                usuario_encontrado = next((u for u in usuarios if u.lower() == u_input.lower()), None)
                if usuario_encontrado and usuarios[usuario_encontrado] == p_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = usuario_encontrado
                    if recordarme:
                        cookie_manager.set('user_weight_app', usuario_encontrado, expires_at=datetime.now() + pd.Timedelta(days=30))
                    st.rerun()
                else:
                    st.error("Error de acceso")
else:
    # --- APP PRINCIPAL ---
    st.title("🏆 Gordos 2026")
    col_u, col_l = st.columns([4, 1])
    col_u.write(f"Usuario: **{st.session_state['usuario_actual']}**")
    if col_l.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        cookie_manager.delete('user_weight_app')
        st.rerun()

    df = cargar_datos()

    # Marcador Grupal
    if not df.empty:
        total = sum([df[df['Usuario']==u].iloc[0]['Peso'] - df[df['Usuario']==u].iloc[-1]['Peso'] for u in df['Usuario'].unique() if len(df[df['Usuario']==u]) > 0])
        st.metric("🔥 KILOS PERDIDOS ENTRE TODOS", f"{round(total, 1)} kg")

    # Registro
    with st.expander("➕ Registrar Peso"):
        peso_ult = 80.0
        if not df.empty:
            mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
            if not mis_d.empty: peso_ult = float(mis_d.iloc[-1]['Peso'])
        
        with st.form("nuevo_peso"):
            f_reg = st.date_input("Fecha", datetime.now())
            p_reg = st.number_input("Peso (kg)", value=peso_ult, step=0.1)
            if st.form_submit_button("Guardar"):
                # Formato solicitado: AAAA-MM-DD 0:00
                nueva_fila = pd.DataFrame({
                    "Fecha": [f_reg.strftime('%Y-%m-%d 0:00')],
                    "Usuario": [st.session_state['usuario_actual']],
                    "Peso": [str(p_reg).replace('.', ',')] # Guardamos con coma para mantener tu estilo de hoja
                })
                df_orig = conn.read(ttl=0)
                df_upd = pd.concat([df_orig, nueva_fila], ignore_index=True)
                conn.update(data=df_upd)
                st.success("¡Guardado!")
                time.sleep(1)
                st.rerun()

    # Gráfica y Rankings
    if not df.empty:
        st.subheader("📊 Evolución")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        fig.update_xaxes(type='date', tickformat="%d/%m/%y")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        # Rankings simplificados para evitar errores de cálculo
        st.subheader("🏆 Salón de la Fama")
        resumen = []
        for u in df['Usuario'].unique():
            ud = df[df['Usuario'] == u]
            p_i, p_a = ud.iloc[0]['Peso'], ud.iloc[-1]['Peso']
            resumen.append({"Usuario": u, "Kilos Perdidos": round(p_i - p_a, 2), "Peso Actual": p_a})
        
        st.table(pd.DataFrame(resumen).sort_values("Kilos Perdidos", ascending=False))
