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
    
    /* Estilo para las tarjetas de medallas - ALTO CONTRASTE */
    .medal-card {
        background-color: #1e293b; /* Azul muy oscuro */
        color: #ffffff !important; /* Texto blanco puro */
        padding: 20px;
        border-radius: 12px;
        border-top: 5px solid #ffd700; /* Borde superior dorado */
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .medal-card b {
        color: #ffd700; /* Nombres de medalla en dorado */
        font-size: 1.1em;
    }
    .medal-card small {
        color: #cbd5e1; /* Texto secundario en gris claro */
    }
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

def cargar_datos():
    df = conn.read(ttl=0)
    if df is not None and not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Fecha', 'Peso'])
        
        if df['Peso'].dtype == object:
            df['Peso'] = df['Peso'].astype(str).str.replace(',', '.')
            
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        df = df.dropna(subset=['Peso'])
        df['Fecha'] = df['Fecha'].dt.normalize()
        return df.sort_values(['Usuario', 'Fecha'])
    return pd.DataFrame(columns=["Fecha", "Usuario", "Peso"])

# --- LISTA DE USUARIOS ---
usuarios = {
    "admin": "valencia", "Alfon": "maquina", "hperis": "admin", 
    "Josete": "weman", "Julian": "pilotas", "Mberengu": "vividor", 
    "Sergio": "operacion2d", "Alberto": "gorriki", "Fran": "flaco", "Rubo": "chamador"
}

# --- LÓGICA DE AUTO-LOGIN ---
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

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.title("🏆 Gordos 2026")
        st.subheader(st.session_state['frase_dia'])
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
                    st.error("Usuario o contraseña incorrectos")
else:
    # --- APP PRINCIPAL ---
    st.title("🏆 Gordos 2026")
    st.markdown(f"### *{st.session_state['frase_dia']}* 💪")
    
    col_user, col_logout = st.columns([4, 1])
    col_user.write(f"Conectado como: **{st.session_state['usuario_actual']}**")
    if col_logout.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        cookie_manager.delete('user_weight_app')
        st.rerun()
            
    st.divider()
    df = cargar_datos()

    if not df.empty:
        # Procesar estadísticas
        total_perdido_grupal = 0
        stats_list = []
        for user in df['Usuario'].unique():
            user_data = df[df['Usuario'] == user]
            if len(user_data) > 0:
                p_ini, p_act = user_data.iloc[0]['Peso'], user_data.iloc[-1]['Peso']
                perdido = p_ini - p_act
                total_perdido_grupal += perdido
                pct = (perdido / p_ini) * 100 if p_ini > 0 else 0
                sem = user_data.iloc[-2]['Peso'] - p_act if len(user_data) >= 2 else 0
                stats_list.append({
                    "Usuario": user, "Peso Actual": p_act, "Total Perdido (kg)": round(perdido, 2),
                    "Perdido (%)": round(pct, 2), "Esta Semana (kg)": round(sem, 2), 
                    "Entradas": len(user_data)
                })
        df_stats = pd.DataFrame(stats_list)

        # 1. MARCADOR GRUPAL
        st.metric(label="🔥 KILOS PERDIDOS ENTRE TODOS", value=f"{round(total_perdido_grupal, 1)} kg")

        # 2. TARJETA PERSONAL
        st.subheader(f"👤 Tu Resumen: {st.session_state['usuario_actual']}")
        mi_stat = df_stats[df_stats['Usuario'] == st.session_state['usuario_actual']]
        if not mi_stat.empty:
            ms = mi_stat.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tu Peso", f"{ms['Peso Actual']} kg")
            c2.metric("Total Perdido", f"{ms['Total Perdido (kg)']} kg")
            c3.metric("Esta Semana", f"{ms['Esta Semana (kg)']} kg", delta=ms['Esta Semana (kg)'])
            c4.metric("Progreso", f"{ms['Perdido (%)']}%")
        else:
            st.info("Registra tu primer peso para activar tu tarjeta.")

    st.divider()

    # --- REGISTRAR Y BORRAR ---
    col_reg, col_del = st.columns(2)
    with col_reg:
        with st.expander("➕ Registrar nuevo peso"):
            peso_def = 80.0
            if not df.empty:
                mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_d.empty: peso_def = float(mis_d.iloc[-1]['Peso'])
            with st.form("registro_peso"):
                f_reg = st.date_input("Fecha", datetime.now())
                p_reg = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=peso_def, step=0.1)
                if st.form_submit_button("Guardar", use_container_width=True):
                    fecha_sql = f_reg.strftime('%Y-%m-%d 00:00:00')
                    peso_str = str(p_reg).replace('.', ',')
                    nueva_fila = pd.DataFrame({"Fecha": [fecha_sql], "Usuario": [st.session_state['usuario_actual']], "Peso": [peso_str]})
                    df_raw = conn.read(ttl=0)
                    conn.update(data=pd.concat([df_raw, nueva_fila], ignore_index=True))
                    st.success("¡Registrado!")
                    time.sleep(1)
                    st.rerun()

    with col_del:
        with st.expander("🗑️ Borrar último registro"):
            if not df.empty:
                mis_d = df[df['Usuario'] == st.session_state['usuario_actual']]
                if not mis_d.empty:
                    ultimo_idx = mis_d.index[-1]
                    st.warning(f"Se borrará el peso de {mis_d.iloc[-1]['Peso']}kg")
                    if st.button("Confirmar Borrado", use_container_width=True):
                        df_raw = conn.read(ttl=0)
                        conn.update(data=df_raw.drop(ultimo_idx))
                        st.error("Eliminado")
                        time.sleep(1)
                        st.rerun()

    # --- VISUALIZACIÓN ---
    if not df.empty:
        st.subheader("📊 Evolución Temporal")
        fig = px.line(df, x="Fecha", y="Peso", color="Usuario", markers=True, template="plotly_white")
        fig.update_xaxes(type='date', tickformat="%d/%m/%y")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🏆 Rankings de la Liga")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🔥 Esta Semana")
            st.dataframe(df_stats[['Usuario', 'Esta Semana (kg)']].sort_values(by="Esta Semana (kg)", ascending=False), hide_index=True)
        with c2:
            st.markdown("#### 🥇 Total Kilos")
            st.dataframe(df_stats[['Usuario', 'Total Perdido (kg)']].sort_values(by="Total Perdido (kg)", ascending=False), hide_index=True)
        with c3:
            st.markdown("#### 📉 Total %")
            st.dataframe(df_stats[['Usuario', 'Perdido (%)']].sort_values(by="Perdido (%)", ascending=False), hide_index=True)

        # --- CUADRO DE HONOR AL FINAL ---
        st.divider()
        st.subheader("🎖️ Cuadro de Honor")
        m1, m2, m3, m4 = st.columns(4)
        
        rey_semana = df_stats.sort_values("Esta Semana (kg)", ascending=False).iloc[0]
        lider_abs = df_stats.sort_values("Total Perdido (kg)", ascending=False).iloc[0]
        mas_constante = df_stats.sort_values("Entradas", ascending=False).iloc[0]
        mejor_pct = df_stats.sort_values("Perdido (%)", ascending=False).iloc[0]

        with m1:
            st.markdown(f"<div class='medal-card'>🥇 <b>Rey de la Semana</b><br>{rey_semana['Usuario']}<br><small>{rey_semana['Esta Semana (kg)']} kg perdidos</small></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='medal-card'>🏆 <b>Líder Absoluto</b><br>{lider_abs['Usuario']}<br><small>{lider_abs['Total Perdido (kg)']} kg totales</small></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='medal-card'>📉 <b>Mejor %</b><br>{mejor_pct['Usuario']}<br><small>{mejor_pct['Perdido (%)']}% del peso</small></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='medal-card'>📅 <b>Más Constante</b><br>{mas_constante['Usuario']}<br><small>{mas_constante['Entradas']} pesajes</small></div>", unsafe_allow_html=True)

        with st.expander("Ver historial completo"):
            df_display = df.copy()
            df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_display.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay datos registrados.")
