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

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN DE CARGA "ULTRA-ROBUSTA" ---
def cargar_datos():
    df = conn.read(ttl=0)
    if df is not None and not df.empty:
        # Paso 1: Convertir todo a texto para evitar conflictos de tipos
        df['Fecha'] = df['Fecha'].astype(str)
        
        # Paso 2: Intento de conversión inteligente
        # Probamos primero con formato europeo (DD/MM/AAAA) que es el que te está dando problemas
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        
        # Paso 3: Limpieza de datos fallidos
        df = df.dropna(subset=['Fecha', 'Peso'])
        
        # Paso 4: Normalizar (quitar horas) y asegurar que el peso sea número
        df['Fecha'] = df['Fecha'].dt.normalize()
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        df = df.dropna(subset=['Peso'])
        
        # Paso 5: ORDENAR CRONOLÓGICAMENTE (Vital para que la línea de la gráfica no desaparezca)
        df = df.sort_values(by='Fecha', ascending=True)
        return df
    return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])

# --- USUARIOS ---
usuarios = {
    "admin": "valencia", "Alfon": "maquina", "hperis": "admin", 
    "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", 
    "Sergio": "operacion2d", "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"
}

# --- LÓGICA DE AUTO-LOGIN ---
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

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.title("🏆 Gordos 2026")
        st.subheader(st.session_state['frase_dia'])
        st.write("---")
        with st.form("login_form"):
            st.markdown("### Acceso al Reto")
            u_input = st.text_input("Usuario", key="user_input")
            p_input = st.text_input("Contraseña", type="password", key="pass_input")
            recordarme = st.checkbox("Recordarme en este equipo", value=True)
            submit = st.form_submit_button("Entrar", use_container_width=True)
            if submit:
                usuario_encontrado = next((u for u in usuarios if u.lower() == u_input.lower()), None)
                if usuario_encontrado and usuarios[usuario_encontrado] == p_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = usuario_encontrado
                    if recordarme:
                        cookie_manager.set('user_weight_app', usuario_encontrado, 
                                         expires_at=datetime.now() + pd.Timedelta(days=30))
                    st.success(f"¡Hola {usuario_encontrado}!")
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
        st.write(f"Conectado como: **{st.session_state['usuario_actual']}**")
    with col_logout:
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state['logueado'] = False
            cookie_manager.delete('user_weight_app')
            st.rerun()
            
    st.divider()
    
    df = cargar_datos()

    # --- MÉTRICA GRUPAL ---
    if not df.empty:
        total_perdido_grupal = 0
        stats_list = []
        # Calculamos stats sobre el DF ya limpio y ordenado
        for user in df['Usuario'].unique():
            user_data = df[df['Usuario'] == user]
            if len(user_data) > 0:
                p_ini = user_data.iloc[0]['Peso']
                p_act = user_data.iloc[-1]['Peso']
                perdido = p_ini - p_act
                total_perdido_grupal += perdido
                pct = (perdido / p_ini) * 100 if p_ini > 0 else 0
                sem = user_data.iloc[-2]['Peso'] - p_act if len(user_data) >= 2 else 0
                stats_list.append({
                    "Usuario": user, "Peso Actual": p_act, "Total Perdido (kg)": round(perdido, 2),
                    "Perdido (%)": f"{round(pct, 2)}%", "Esta Semana (kg)": round(sem, 2), "Porcentaje_Num": pct
                })
        
        st.metric(label="🔥 KILOS PERDIDOS ENTRE TODOS", value=f"{round(total_perdido_grupal, 1)} kg")
        st.write("---")
        df_stats = pd.DataFrame(stats_list)

    # --- REGISTRAR Y BORRAR ---
    col_reg, col_del = st.columns(2)
    with col_reg:
        with st.expander("➕ Registrar nuevo peso"):
            peso_defecto = 80.0
            if not df.empty:
                mis_datos = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_datos.empty:
                    peso_defecto = float(mis_datos.iloc[-1]['Peso'])
            with st.form("registro_peso"):
                f_reg = st.date_input("Fecha", datetime.now())
                p_reg = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=peso_defecto, step=0.1)
                if st.form_submit_button("Guardar", use_container_width=True):
                    # GUARDADO EN FORMATO ISO (El que mejor entiende Google)
                    nueva_fila = pd.DataFrame({
                        "Fecha": [f_reg.strftime('%Y-%m-%d')], 
                        "Usuario": [st.session_state['usuario_actual']], 
                        "Peso": [p_reg]
                    })
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
                        # Leemos el original para borrar el índice exacto
                        df_original = conn.read(ttl=0)
                        df_upd = df_original.drop(ultimo_idx)
                        conn.update(data=df_upd)
                        st.error("Registro eliminado")
                        time.sleep(1)
                        st.rerun()

    # --- VISUALIZACIÓN ---
    if not df.empty:
        st.subheader("📊 Evolución Temporal")
        # Forzamos a Plotly a tratar el eje X como fechas
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        fig.update_xaxes(type='date', tickformat="%d/%m/%y")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🏆 Salón de la Fama")
        c1, c2, c3 = st.columns(3)
        if not df_stats.empty:
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
            df_display = df.copy()
            df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_display.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay datos registrados.")
