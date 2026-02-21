import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import qrcode
import io
from PIL import Image

# --- CONFIGURACIÓN ---
APP_URL = "https://tu-app-barragan.streamlit.app" # Cambia esto cuando la publiques
CLAVE_ADMIN = "1234" # CAMBIA ESTA CLAVE PARA TU SEGURIDAD

st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9; }
    h1 { color: #0f172a; font-weight: 600; letter-spacing: -1.5px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #0f172a; color: white; border: none; padding: 0.7rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN PDF CON QR ---
class MinimalPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(15, 23, 42)
        self.cell(0, 10, "FRANCISCO BARRAGÁN", ln=True, align="L")
        self.set_font("Arial", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, "Consultoría Técnica en Innovación Social & Accesibilidad", ln=True, align="L")
        self.ln(15)

def generar_pdf_premium(datos):
    pdf = MinimalPDF()
    pdf.add_page()
    
    # Datos del contrato
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO No. {datos['numero']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(51, 65, 85)
    for k, v in [("CLIENTE", datos['nombre']), ("CÉDULA", datos['cedula']), ("TRÁMITE", datos['tramite']), ("VALOR", f"${datos['valor']:,.0f} COP")]:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, f"{k}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, str(v), ln=1)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "CLÁUSULA DE SEGUIMIENTO DIGITAL", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 7, "Para su comodidad, puede escanear el código QR adjunto para consultar el estado de su proceso en tiempo real desde nuestro portal digital.")

    # GENERAR QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(APP_URL)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar QR temporalmente en memoria
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    # Insertar QR en PDF
    pdf.image(qr_buffer, x=150, y=180, w=40)
    
    # Firmas
    pdf.set_y(220)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.line(120, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(2)
    pdf.cell(90, 10, "EL CONSULTOR", ln=0, align="C")
    pdf.cell(90, 10, "EL CLIENTE", ln=1, align="C")
    
    return pdf.output(dest='S')

# --- DB E INTERFAZ (Igual que antes pero optimizado) ---
conn = sqlite3.connect('consultoria.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS contratos (numero TEXT, nombre TEXT, cedula TEXT, tramite TEXT, accionado TEXT, valor REAL, estado TEXT, avances TEXT, fecha TEXT)')
conn.commit()

with st.sidebar:
    st.title("⚖️ Barragán Admin")
    menu = st.radio("Ir a:", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])

if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.container():
        n = st.text_input("Nombre")
        w = st.text_input("WhatsApp")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        if st.button("Enviar Pedido"):
            msg = f"Hola Francisco! Pedido de {n} para {s}."
            st.markdown(f'<a href="https://wa.me/573116651518?text={urllib.parse.quote(msg)}" target="_blank">🚀 Enviar</a>', unsafe_allow_html=True)

elif menu == "🔍 Consultar":
    st.title("Mi Estado")
    cc = st.text_input("Cédula", type="password")
    if st.button("Buscar"):
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        if not df.empty:
            st.success(f"Estado: {df['estado'][0]}")
            st.info(f"Último Avance: {df['avances'][0]}")
        else: st.error("No encontrado.")

elif menu == "🔒 Admin":
    if st.sidebar.text_input("Clave", type="password") == CLAVE_ADMIN:
        st.title("Panel Admin")
        with st.form("nuevo"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre")
            ced = c1.text_input("Cédula")
            tra = c2.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
            val = c2.number_input("Valor")
            acc = st.text_input("Entidad")
            if st.form_submit_button("Registrar"):
                fec = datetime.now().strftime("%Y-%m-%d")
                num = f"FB-{datetime.now().strftime('%y%m%d%H')}"
                c.execute("INSERT INTO contratos VALUES (?,?,?,?,?,?,?,?,?)", (num, nom, ced, tra, acc, val, "Abierto", "Iniciado", fec))
                conn.commit()
                pdf = generar_pdf_premium({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val, "fecha":fec})
                st.download_button("📥 Descargar Contrato con QR", pdf, f"Contrato_{nom}.pdf", "application/pdf")
