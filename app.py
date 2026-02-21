import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- CONFIGURACIÓN DE SEGURIDAD ---
CLAVE_ADMIN = "1234"
APP_URL = "https://legaltech-asesorias.streamlit.app" # Ajusta con tu URL real

if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_ready' not in st.session_state:
    st.session_state.pdf_ready = None

# --- ESTILO CSS MINIMALISTA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .st-emotion-cache-1r6slb0 { background-color: white; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #eee; }
    h1 { color: #1a1a1a; font-weight: 600; letter-spacing: -1.2px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #000; color: white; border: none; padding: 0.6rem; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #0066ff; color: white; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('barragan_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "FRANCISCO BARRAGÁN - CONSULTORÍA TÉCNICA", ln=True)
        self.ln(10)

def create_pdf(datos):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO No. {datos['numero']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for k, v in [("Cliente", datos['nombre']), ("Cédula", datos['cedula']), ("Trámite", datos['tramite']), ("Valor", f"${datos['valor']:,.0f} COP")]:
        pdf.cell(40, 8, f"{k}:", ln=0)
        pdf.cell(0, 8, str(v), ln=1)
    
    # QR simplificado
    qr = qrcode.make(APP_URL)
    qr_img = io.BytesIO()
    qr.save(qr_img, format="PNG")
    qr_img.seek(0)
    pdf.image(qr_img, x=150, y=200, w=40)
    
    return pdf.output(dest='S')

# --- MENÚ LATERAL ---
with st.sidebar:
    st.title("⚖️ Barragán Tech")
    opt = st.radio("Sección", ["✨ Solicitar", "🔍 Mi Proceso", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO SOLICITAR ---
if opt == "✨ Solicitar":
    st.title("Solicita tu Asesoría")
    with st.container():
        n = st.text_input("Nombre")
        c = st.text_input("Cédula")
        t = st.text_input("WhatsApp")
        if st.button("Enviar Solicitud"):
            msg = f"Hola Francisco! Nuevo caso de {n}. WhatsApp: {t}"
            wa = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Enviar a WhatsApp</div></a>', unsafe_allow_html=True)

# --- MÓDULO CONSULTA ---
elif opt == "🔍 Mi Proceso":
    st.title("Consulta de Estado")
    search = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('barragan_final.db')
        df = pd.read_sql_query("SELECT * FROM procesos WHERE cedula=?", conn, params=(search,))
        conn.close()
        if not df.empty:
            st.success(f"Estado: {df['estado'].iloc[0]}")
            st.info(f"Avance: {df['avances'].iloc[0]}")
        else: st.error("No se encontró el proceso.")

# --- MÓDULO ADMIN (EL FIX ESTÁ AQUÍ) ---
elif opt == "🔒 Admin":
    if not st.session_state.auth:
        pw = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if pw == CLAVE_ADMIN:
                st.session_state.auth = True
                st.rerun()
    else:
        st.title("Panel Administrativo")
        t1, t2 = st.tabs(["📝 Registrar Caso", "📂 Gestión / Firmados"])
        
        with t1:
            with st.form("registro_admin", clear_on_submit=False):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre")
                ced = col1.text_input("Cédula")
                pho = col2.text_input("WhatsApp")
                val = col2.number_input("Valor", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Accionado")
                
                submitted = st.form_submit_button("Guardar y Preparar Contrato")
                
                if submitted:
                    num = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_final.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Abierto", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    
                    # Generamos el PDF y lo guardamos en el estado de la sesión
                    st.session_state.pdf_ready = {
                        "bytes": create_pdf({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val}),
                        "filename": f"Contrato_{nom}.pdf"
                    }
                    st.success("✅ Registro exitoso. El contrato está listo abajo.")

            # ESTO ESTÁ FUERA DEL FORMULARIO - Así no da error
            if st.session_state.pdf_ready:
                st.download_button(
                    label="📥 DESCARGAR CONTRATO AHORA",
                    data=st.session_state.pdf_ready["bytes"],
                    file_name=st.session_state.pdf_ready["filename"],
                    mime="application/pdf"
                )

        with t2:
            st.subheader("Subir Contrato Firmado")
            conn = sqlite3.connect('barragan_final.db')
            df_admin = pd.read_sql_query("SELECT id, nombre, estado FROM procesos", conn)
            st.dataframe(df_admin, use_container_width=True)
            
            sel_id = st.selectbox("ID del Proceso", df_admin['id'])
            archivo = st.file_uploader("Contrato firmado (PDF)", type="pdf")
            if st.button("Finalizar y Guardar PDF Firmado"):
                if archivo:
                    blob = archivo.read()
                    conn = sqlite3.connect('barragan_final.db')
                    cur = conn.cursor()
                    cur.execute("UPDATE procesos SET firmado=?, estado='Firmado' WHERE id=?", (blob, sel_id))
                    conn.commit()
                    conn.close()
                    st.success("Archivo firmado guardado en la base de datos.")
