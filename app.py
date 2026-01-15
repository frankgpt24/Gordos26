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

# --- FUNCIÓN DE CARGA "ULTRA-ROBUSTA" ---
def cargar_datos():
    # Forzamos ttl=0 para que no use caché y lea siempre lo último de Google
    df_raw = conn.read(ttl=0)
    
    if df_raw is not None and not df_raw.empty:
        df = df_raw.copy()
        
        # 1. Limpieza de Fechas: Usamos 'mixed' para que entienda DD/MM y AAAA-MM-DD a la vez
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        
        # 2. Limpieza de Pesos: Quitamos espacios, cambiamos comas por puntos y forzamos número
        df['Peso'] = df['Peso'].astype(str).str.replace(' ', '').str.replace(',', '.')
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        
        # 3. Eliminamos filas que hayan quedado vacías tras la limpieza
        df = df.dropna(subset=['Fecha', 'Peso'])
        
        # 4. Normalizamos (sin horas para la gráfica) y ordenamos
        df['Fecha'] = df['Fecha'].dt.normalize()
        df = df.sort_values(by=['Fecha', 'Usuario'])
        return df
    return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])

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
    with st.spinner("Iniciando..."):
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
                user_found = next((u for u in usuarios if u.lower() == u_input.lower()), None)
                if user_found and usuarios[user_found] == p_input:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user_found
                    if recordarme:
                        cookie_manager.set('user_weight_app', user_found, expires_at=datetime.now() + pd.Timedelta(days=30))
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
else:
    # --- APP PRINCIPAL ---
    st.title("🏆 Gordos 2026")
    col_u, col_l = st.columns([4, 1])
    col_u.markdown(f"Hola, **{st.session_state['usuario_actual']}** 👋")
    if col_l.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        cookie_manager.delete('user_weight_app')
        st.rerun()

    st.divider()
    
    # CARGAR DATOS
    df = cargar_datos()

    # --- MÉTRICA GRUPAL ---
    if not df.empty:
        total_perdido = 0
        stats_list = []
        for u in df['Usuario'].unique():
            ud = df[df['Usuario'] == u]
            if not ud.empty:
                p_ini, p_act = ud.iloc[0]['Peso'], ud.iloc[-1]['Peso']
                perdido = p_ini - p_act
                total_perdido += perdido
                pct = (perdido / p_ini) * 100 if p_ini > 0 else 0
                sem = ud.iloc[-2]['Peso'] - p_act if len(ud) >= 2 else 0
                stats_list.append({
                    "Usuario": u, "Peso Actual": p_act, "Total Perdido (kg)": round(perdido, 2),
                    "Perdido (%)": f"{round(pct, 2)}%", "Esta Semana (kg)": round(sem, 2), "pct_num": pct
                })
        st.metric(label="🔥 KILOS PERDIDOS ENTRE TODOS", value=f"{round(total_perdido, 1)} kg")
        df_stats = pd.DataFrame(stats_list)

    # --- REGISTRAR Y BORRAR ---
    c_reg, c_del = st.columns(2)
    
    with c_reg:
        with st.expander("➕ Registrar Peso"):
            peso_def = 80.0
            if not df.empty:
                mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_d.empty: peso_def = float(mis_d.iloc[-1]['Peso'])
            
            with st.form("form_reg"):
                f_reg = st.date_input("Fecha", datetime.now())
                p_reg = st.number_input("Peso (kg)", value=peso_def, step=0.1)
                if st.form_submit_button("Guardar"):
                    # Enviamos con el formato AAAA-MM-DD 0:00 y coma decimal
                    nueva_fila = pd.DataFrame({
                        "Fecha": [f_reg.strftime('%Y-%m-%d 0:00')],
                        "Usuario": [st.session_state['usuario_actual']],
                        "Peso": [str(p_reg).replace('.', ',')]
                    })
                    df_orig = conn.read(ttl=0)
                    df_final = pd.concat([df_orig, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.success("¡Enviado!")
                    time.sleep(1)
                    st.rerun()

    with c_del:
        with st.expander("🗑️ Borrar registro"):
            if not df.empty:
                mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_d.empty:
                    idx_borrar = mis_d.index[-1]
                    val_borrar = mis_d.iloc[-1]
                    st.warning(f"Borrar: {val_borrar['Peso']}kg ({val_borrar['Fecha'].strftime('%d/%m')})")
                    if st.button("Confirmar Borrado"):
                        df_orig = conn.read(ttl=0)
                        df_final = df_orig.drop(idx_borrar)
                        conn.update(data=df_final)
                        st.error("Borrado")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("No hay datos.")

    # --- GRÁFICA ---
    if not df.empty:
        st.subheader("📊 Evolución Temporal")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        fig.update_xaxes(type='date', tickformat="%d/%m/%y")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🏆 Salón de la Fama")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("#### 🔥 Semana")
            st.dataframe(df_stats[['Usuario', 'Esta Semana (kg)']].sort_values("Esta Semana (kg)", ascending=False), hide_index=True)
        with r2:
            st.markdown("#### 🥇 Total Kilos")
            st.dataframe(df_stats[['Usuario', 'Total Perdido (kg)']].sort_values("Total Perdido (kg)", ascending=False), hide_index=True)
        with r3:
            st.markdown("#### 📉 Total %")
            st.dataframe(df_stats[['Usuario', 'Perdido (%)', 'pct_num']].sort_values("pct_num", ascending=False)[['Usuario', 'Perdido (%)']], hide_index=True)
    
    # --- DEPURACIÓN (Solo visible si quieres) ---
    with st.expander("🛠️ Depuración de Datos (Si la gráfica falla, mira aquí)"):
        st.write("Datos procesados por la App:")
        st.dataframe(df)
        if st.button("Limpiar Caché manualmente"):
            st.cache_data.clear()
            st.rerun()
