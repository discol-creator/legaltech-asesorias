import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import io

# --- CONFIGURACIÓN DE SEGURIDAD ---
CLAVE_ADMIN_REAL = "1234" 
# URL de tu app (se usa para el QR o links)
APP_URL = "https://legaltech-asesorias.streamlit.app" 

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #0f172a; color: white; border: none; padding: 0.7rem; }
    .stButton>button:hover { background-color: #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (NUEVA TABLA PARA EVITAR CONFLICTOS) ---
def init_db():
    conn = sqlite3.connect('consultoria.db', check_same_thread=False)
    c = conn.cursor()
    # Usamos un nombre de tabla nuevo: 'gestion_procesos'
    # Esto garantiza que se cree con las 11 columnas exactas que necesitamos
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, 
                  valor REAL, estado TEXT, avances TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Panel")
    menu = st.radio("Ir a:", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MÓDULO SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.container():
        n = st.text_input("Nombre Completo")
        tel_c = st.text_input("WhatsApp (con +57)")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Cuéntanos tu caso")
        
        if st.button("Generar Solicitud"):
            if n and tel_c:
                msg = f"¡Hola Francisco! 👋\nNuevo pedido de servicio:\n\n👤 *{n}*\n📱 WhatsApp: {tel_c}\n🛠 Servicio: {s}\n📝 Detalles: {d}"
                wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
                st.markdown(f'''<a href="{wa_link}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">
                    🚀 ENVIAR POR WHATSAPP AHORA
                    </button></a>''', unsafe_allow_html=True)
            else:
                st.error("Nombre y teléfono son obligatorios.")

# --- MÓDULO CONSULTAR ---
elif menu == "🔍 Consultar":
    st.title("Estado de tu Proceso")
    cc = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('consultoria.db')
        # Buscamos en la nueva tabla
        df = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Hola {df['nombre'].iloc[0]}")
            st.info(f"**Estado:** {df['estado'].iloc[0]}")
            st.write(f"**Último Avance:** {df['avances'].iloc[0]}")
        else: st.error("No se encontró ningún registro.")

# --- MÓDULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        with st.form("login_admin"):
            pw = st.text_input("Clave Admin", type="password")
            if st.form_submit_button("Entrar"):
                if pw == CLAVE_ADMIN_REAL:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Clave Incorrecta")
    else:
        st.title("Administración")
        t1, t2 = st.tabs(["📝 Crear Caso", "📊 Seguimiento"])
        
        with t1:
            with st.form("nuevo_caso", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre")
                ced = c1.text_input("Cédula")
                pho = c2.text_input("WhatsApp (con +57)")
                val = c2.number_input("Valor", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                
                if st.form_submit_button("Registrar Proceso"):
                    num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    # Insertamos en la nueva tabla 'gestion_procesos'
                    cur.execute("""INSERT INTO gestion_procesos 
                                   (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (num, nom, ced, pho, tra, acc, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    st.success(f"Caso {num} guardado correctamente.")

        with t2:
            conn = sqlite3.connect('consultoria.db')
            df_admin = pd.read_sql_query("SELECT * FROM gestion_procesos", conn)
            conn.close()
            if not df_admin.empty:
                st.dataframe(df_admin)
                idx = st.selectbox("ID del proceso", df_admin['id'])
                n_est = st.selectbox("Nuevo Estado", ["En Proceso", "Esperando Entidad", "Exitoso"])
                n_av = st.text_area("Detalle del avance")
                
                if st.button("Actualizar y Notificar"):
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    cur.execute("UPDATE gestion_procesos SET estado=?, avances=? WHERE id=?", (n_est, n_av, idx))
                    conn.commit()
                    conn.close()
                    
                    sel = df_admin[df_admin['id'] == idx].iloc[0]
                    notif = f"Hola {sel['nombre']}, hay un avance en tu proceso de {sel['tramite']}:\n*Estado:* {n_est}\n*Detalle:* {n_av}"
                    wa_not = f"https://wa.me/{sel['telefono']}?text={urllib.parse.quote(notif)}"
                    st.markdown(f'<a href="{wa_not}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#075e54; color:white; padding:10px; border-radius:10px; border:none; cursor:pointer; font-weight:bold;">📲 NOTIFICAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
