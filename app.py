import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import qrcode
import io

# --- CONFIGURACIÓN ---
CLAVE_ADMIN_REAL = "1234"
APP_URL = "https://tu-app-barragan.streamlit.app"

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; padding: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (Actualizada con Teléfono) ---
conn = sqlite3.connect('consultoria.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS contratos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
              telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
              estado TEXT, avances TEXT, fecha TEXT)''')
conn.commit()

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Barragán")
    menu = st.radio("Menú", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MÓDULO SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.container():
        n = st.text_input("Nombre Completo")
        tel = st.text_input("WhatsApp (con +57)")
        s = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Detalles del caso")
        if st.button("Enviar Pedido"):
            msg = f"Hola Francisco! Nuevo pedido de {n}.\n📱 Tel: {tel}\n🛠 {s}\n📝 {d}"
            wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Abrir WhatsApp para Enviar</div></a>', unsafe_allow_html=True)

# --- MÓDULO CONSULTAR ---
elif menu == "🔍 Consultar":
    st.title("Mi Estado")
    cc = st.text_input("Cédula", type="password")
    if st.button("Consultar"):
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        if not df.empty:
            st.success(f"Hola {df['nombre'][0]}")
            st.info(f"**Estado:** {df['estado'][0]}")
            st.warning(f"**Avance:** {df['avances'][0]}")
        else: st.error("No registrado.")

# --- MÓDULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        with st.form("login"):
            pw = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar"):
                if pw == CLAVE_ADMIN_REAL:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Clave Incorrecta")
    else:
        st.title("Panel de Control")
        t1, t2 = st.tabs(["📝 Nuevo", "📈 Seguimiento"])
        
        with t1:
            with st.form("crear"):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre Cliente")
                ced = c1.text_input("Cédula")
                pho = c2.text_input("Teléfono WhatsApp")
                val = c2.number_input("Valor Total")
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                if st.form_submit_button("Registrar"):
                    num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO contratos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    st.success("Registrado.")

        with t2:
            df_admin = pd.read_sql_query("SELECT * FROM contratos", conn)
            st.dataframe(df_admin)
            
            if not df_admin.empty:
                idx = st.selectbox("Seleccionar para actualizar", df_admin.index)
                sel = df_admin.iloc[idx]
                n_est = st.selectbox("Nuevo Estado", ["En Proceso", "Esperando Entidad", "Exitoso"])
                n_av = st.text_area("Detalle el avance")
                
                if st.button("Actualizar y Generar Botón WA"):
                    c.execute("UPDATE contratos SET estado=?, avances=? WHERE numero=?", (n_est, n_av, sel['numero']))
                    conn.commit()
                    st.success("Base de datos actualizada.")
                    
                    # Generar Link de notificación para el cliente
                    notif = f"Hola {sel['nombre']}, te informo que tu trámite de *{sel['tramite']}* contra *{sel['accionado']}* ha tenido un nuevo avance:\n\n✅ *{n_est}*\n📝 {n_av}\n\nPuedes consultar más detalles en: {APP_URL}"
                    wa_notif = f"https://wa.me/{sel['telefono']}?text={urllib.parse.quote(notif)}"
                    st.markdown(f'<a href="{wa_notif}" target="_blank" style="text-decoration:none;"><div style="background-color:#075e54;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">📲 Notificar Avance al Cliente por WhatsApp</div></a>', unsafe_allow_html=True)
