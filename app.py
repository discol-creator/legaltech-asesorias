import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import qrcode
import io
from PIL import Image

# --- CONFIGURACIÓN DE SEGURIDAD ---
CLAVE_ADMIN_REAL = "1234" 
APP_URL = "https://legaltech-asesorias.streamlit.app" 

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS MODERNO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #0f172a; color: white; border: none; padding: 0.7rem; }
    .stButton>button:hover { background-color: #334155; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE PDF MINIMALISTA ---
class MinimalPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(15, 23, 42)
        self.cell(0, 10, "FRANCISCO BARRAGÁN", ln=True, align="L")
        self.set_font("Arial", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, "Consultoría Técnica | RUT Actividad 7490", ln=True, align="L")
        self.ln(10)
        self.set_draw_color(226, 232, 240)
        self.line(10, 32, 200, 32)
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font("Arial", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "Este documento es una consultoría técnica. No constituye representación jurídica.", align="C")

def generar_contrato_pdf(datos):
    pdf = MinimalPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO No. {datos['numero']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    
    items = [
        ("CLIENTE", datos['nombre']),
        ("DOCUMENTO", datos['cedula']),
        ("TRÁMITE", datos['tramite']),
        ("VALOR TOTAL", f"${datos['valor']:,.0f} COP")
    ]
    
    for label, val in items:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, f"{label}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, str(val), ln=1)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "ACUERDO Y SEGUIMIENTO", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 7, f"Se acuerda la gestión técnica de {datos['tramite']} ante {datos['accionado']}. "
                         f"El cliente podrá seguir los avances escaneando el código QR adjunto.")

    # Generación de QR
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(APP_URL)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format="PNG")
    qr_io.seek(0)
    pdf.image(qr_io, x=155, y=180, w=35)
    
    pdf.ln(40)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.line(120, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(2)
    pdf.cell(90, 10, "EL CONSULTOR", align="C")
    pdf.cell(90, 10, "EL CLIENTE", align="C")
    return pdf.output(dest='S')

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('consultoria.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Barragán")
    menu = st.radio("Menú", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MÓDULOS ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    n = st.text_input("Nombre")
    t = st.text_input("WhatsApp")
    s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
    if st.button("Preparar Pedido"):
        msg = f"Hola Francisco! Nuevo pedido de {n}. Servicio: {s}."
        st.markdown(f'<a href="https://wa.me/573116651518?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Enviar por WhatsApp</div></a>', unsafe_allow_html=True)

elif menu == "🔍 Consultar":
    st.title("Mi Estado")
    cc = st.text_input("Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('consultoria.db')
        df = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Estado: {df['estado'].iloc[0]}")
            st.info(f"Avance: {df['avances'].iloc[0]}")
        else: st.error("No registrado.")

elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        pw = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if pw == CLAVE_ADMIN_REAL:
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("Incorrecta")
    else:
        st.title("Panel Admin")
        with st.form("nuevo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nom, ced = c1.text_input("Nombre"), c1.text_input("Cédula")
            pho, val = c2.text_input("WhatsApp"), c2.number_input("Valor")
            tra, acc = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"]), st.text_input("Entidad")
            
            if st.form_submit_button("Registrar Proceso"):
                num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                fec = datetime.now().strftime("%Y-%m-%d")
                conn = sqlite3.connect('consultoria.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (num, nom, ced, pho, tra, acc, val, "Abierto", "Iniciado", fec))
                conn.commit()
                conn.close()
                st.success("Guardado.")
                pdf = generar_contrato_pdf({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val})
                st.download_button("📥 Descargar Contrato", pdf, f"Contrato_{nom}.pdf", "application/pdf")
