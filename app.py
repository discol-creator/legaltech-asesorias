import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import io

# --- CONFIGURACIÓN DE SEGURIDAD ---
CLAVE_ADMIN_REAL = "1234" 
APP_URL = "https://tu-app-barragan.streamlit.app" # Cambia esto por tu URL real

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
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #0f172a; color: white; border: none; }
    .stButton>button:hover { background-color: #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (REPARACIÓN DEFINITIVA) ---
def init_db():
    conn = sqlite3.connect('consultoria.db', check_same_thread=False)
    c = conn.cursor()
    
    # Verificamos si la tabla existe y qué columnas tiene
    c.execute("PRAGMA table_info(contratos)")
    columnas = [col[1] for col in c.fetchall()]
    
    # SI LA TABLA NO TIENE 'telefono', LA BORRAMOS PARA RECREARLA (BORRADO DE EMERGENCIA)
    if columnas and 'telefono' not in columnas:
        c.execute("DROP TABLE contratos")
        conn.commit()
        columnas = [] # Forzamos la recreación

    # Crear tabla con la estructura completa
    c.execute('''CREATE TABLE IF NOT EXISTS contratos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, 
                  valor REAL, estado TEXT, avances TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- MÓDULOS ---
with st.sidebar:
    st.title("⚖️ Panel")
    menu = st.radio("Menú", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MODULO CLIENTE: SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Solicita tu Asesoría")
    with st.container():
        n = st.text_input("Nombre Completo")
        tel_cliente = st.text_input("Tu WhatsApp (Ej: +57311...)")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Cuéntanos tu caso")
        
        if st.button("Preparar Pedido"):
            if n and tel_cliente:
                msg = f"¡Hola Francisco! 👋\nNuevo pedido de servicio:\n\n👤 *{n}*\n📱 WhatsApp: {tel_cliente}\n🛠 Servicio: {s}\n📝 Detalles: {d}"
                # Aquí va TU número donde recibes los pedidos
                wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
                st.success("✅ Resumen generado.")
                # Botón de envío directo
                st.markdown(f'''<a href="{wa_link}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">
                    🚀 ENVIAR AHORA POR WHATSAPP
                    </button></a>''', unsafe_allow_html=True)
            else:
                st.error("Falta nombre o teléfono.")

# --- MODULO CLIENTE: CONSULTAR ---
elif menu == "🔍 Consultar":
    st.title("Estado de tu Proceso")
    cc = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('consultoria.db')
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Hola {df['nombre'].iloc[0]}")
            st.info(f"**Estado:** {df['estado'].iloc[0]}")
            st.write(f"**Último Avance:** {df['avances'].iloc[0]}")
        else: st.error("No se encontró registro.")

# --- MODULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        with st.form("login"):
            pw = st.text_input("Clave Admin", type="password")
            if st.form_submit_button("Entrar"):
                if pw == CLAVE_ADMIN_REAL:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Clave Incorrecta")
    else:
        st.title("Administración")
        tab1, tab2 = st.tabs(["📝 Crear Caso", "📊 Seguimiento"])
        
        with tab1:
            with st.form("nuevo_caso", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre")
                ced = c1.text_input("Cédula")
                pho = c2.text_input("Teléfono Cliente (con +57)")
                val = c2.number_input("Valor", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                
                if st.form_submit_button("Guardar"):
                    num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO contratos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    st.success(f"Caso {num} guardado.")

        with tab2:
            conn = sqlite3.connect('consultoria.db')
            df_admin = pd.read_sql_query("SELECT * FROM contratos", conn)
            conn.close()
            if not df_admin.empty:
                st.dataframe(df_admin)
                idx = st.selectbox("Seleccione ID", df_admin['id'])
                n_est = st.selectbox("Estado", ["En Proceso", "Pendiente Entidad", "Exitoso"])
                n_av = st.text_area("Avance")
                
                if st.button("Actualizar y Notificar"):
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    cur.execute("UPDATE contratos SET estado=?, avances=? WHERE id=?", (n_est, n_av, idx))
                    conn.commit()
                    conn.close()
                    
                    sel = df_admin[df_admin['id'] == idx].iloc[0]
                    notif = f"Hola {sel['nombre']}, tu proceso tiene un avance:\n*Estado:* {n_est}\n*Detalle:* {n_av}"
                    wa_notif = f"https://wa.me/{sel['telefono']}?text={urllib.parse.quote(notif)}"
                    st
