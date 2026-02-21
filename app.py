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
# IMPORTANTE: Reemplaza con la URL real cuando la publiques en Streamlit Cloud
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

# --- BASE DE DATOS (AUTO-REPARABLE) ---
def get_db_connection():
    conn = sqlite3.connect('consultoria.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Crear tabla si no existe
    c.execute('''CREATE TABLE IF NOT EXISTS contratos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT)''')
    
    # MIGRACIÓN: Verificar si falta la columna 'telefono' (para evitar el OperationalError)
    c.execute("PRAGMA table_info(contratos)")
    columns = [column[1] for column in c.fetchall()]
    if 'telefono' not in columns:
        c.execute("ALTER TABLE contratos ADD COLUMN telefono TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- MÓDULO PDF ---
class MinimalPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "FRANCISCO BARRAGÁN", ln=True)
        self.ln(10)

def generar_pdf(datos):
    pdf = MinimalPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO: {datos['numero']}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 10, f"Cliente: {datos['nombre']}\nCédula: {datos['cedula']}\nTrámite: {datos['tramite']}\nValor: ${datos['valor']:,.0f}")
    return pdf.output(dest='S')

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Gestión")
    menu = st.radio("Menú", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Salir"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MÓDULOS ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.form("pedido_cliente"):
        n = st.text_input("Nombre Completo")
        tel = st.text_input("WhatsApp (ej: +573001234567)")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Detalles")
        enviar = st.form_submit_button("Generar Solicitud")
        
        if enviar:
            msg = f"¡Hola Francisco! 👋\nNuevo pedido de *{n}*.\n📱 WhatsApp: {tel}\n🛠 Servicio: {s}\n📝 Caso: {d}"
            wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
            st.success("✅ ¡Solicitud lista!")
            st.link_button("🚀 ENVIAR A WHATSAPP AHORA", wa_link)

elif menu == "🔍 Consultar":
    st.title("Consulta de Estado")
    cc = st.text_input("Tu Cédula", type="password")
    if st.button("Buscar"):
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Hola {df['nombre'].iloc[0]}")
            st.info(f"**Estado:** {df['estado'].iloc[0]}")
            st.markdown(f"**Avance técnico:**\n{df['avances'].iloc[0]}")
        else: st.error("No se encontró el registro.")

elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        with st.form("login"):
            pw = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar"):
                if pw == CLAVE_ADMIN_REAL:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Clave incorrecta")
    else:
        st.title("Panel Administrador")
        t1, t2 = st.tabs(["📝 Crear Caso", "📈 Seguimiento"])
        
        with t1:
            with st.form("nuevo_caso"):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre")
                ced = c1.text_input("Cédula")
                pho = c2.text_input("WhatsApp Cliente")
                val = c2.number_input("Valor", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                if st.form_submit_button("Registrar Proceso"):
                    num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO contratos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    st.success("Caso Guardado.")
                    pdf = generar_pdf({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "valor":val})
                    st.download_button("📥 Descargar PDF", pdf, f"Contrato_{nom}.pdf", "application/pdf")

        with t2:
            conn = get_db_connection()
            df_admin = pd.read_sql_query("SELECT * FROM contratos", conn)
            conn.close()
            if not df_admin.empty:
                st.dataframe(df_admin)
                idx = st.selectbox("Actualizar ID", df_admin['id'])
                n_est = st.selectbox("Estado", ["En Proceso", "Esperando Entidad", "Exitoso"])
                n_av = st.text_area("Nuevo Avance")
                if st.button("Guardar y Notificar"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE contratos SET estado=?, avances=? WHERE id=?", (n_est, n_av, idx))
                    conn.commit()
                    conn.close()
                    # Notificación WhatsApp
                    sel = df_admin[df_admin['id'] == idx].iloc[0]
                    notif = f"Hola {sel['nombre']}, tu trámite de {sel['tramite']} ha cambiado a: *{n_est}*.\nDetalle: {n_av}"
                    wa_notif = f"https://wa.me/{sel['telefono']}?text={urllib.parse.quote(notif)}"
                    st.link_button("📲 NOTIFICAR POR WHATSAPP", wa_notif)
