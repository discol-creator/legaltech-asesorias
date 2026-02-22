import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- DATOS DEL CONSULTOR (VERIFICADOS) ---
CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
ID_CONSULTOR = "CE 7354548"
CLAVE_ADMIN = "1234"
APP_URL = "https://legaltech-asesorias.streamlit.app"

# --- INICIALIZACIÓN DE VARIABLES ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_contrato' not in st.session_state:
    st.session_state.pdf_contrato = None
if 'nombre_pdf' not in st.session_state:
    st.session_state.nombre_pdf = ""

st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .st-emotion-cache-1r6slb0 { background-color: #fcfcfc; border-radius: 12px; padding: 2.5rem; border: 1px solid #f0f0f0; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #000; color: #fff; font-weight: 600; padding: 0.6rem; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #0066ff; color: #fff; font-weight: 600; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('consultoria_pulcra.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE PDF A4 PULCRO ---
def generar_contrato_pulcro(datos):
    # Configuración A4 estricta con márgenes de 25mm
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=25, top=25, right=25)
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    w_util = pdf.epw # Ancho efectivo tras márgenes

    # Título Principal
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(w_util, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(10)
    
    # Identificación de Partes
    pdf.set_font("Arial", "B", 10)
    pdf.cell(w_util, 6, "PARTES INTERVINIENTES", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, f"CONTRATANTE: {datos['nombre'].upper()}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.ln(2)
    # Variable ID_CONSULTOR corregida aquí
    pdf.multi_cell(w_util, 6, f"CONSULTOR: {CONSULTOR_NOMBRE}, identificado con {ID_CONSULTOR}, profesional con Maestría en Innovación Social y experto en Accesibilidad (RUT 7490).")
    pdf.ln(8)
    
    pdf.multi_cell(w_util, 6, "Las partes acuerdan suscribir el presente contrato bajo las siguientes cláusulas:")
    pdf.ln(4)

    # Bloque de Cláusulas
    clausulas = [
        ("PRIMERA: OBJETO DEL SERVICIO", 
         f"Asesoría técnica y estratégica para la gestión de: {datos['tramite']} ante la entidad {datos['accionado']}."),
        
        ("SEGUNDA: ALCANCE Y NATURALEZA (DISCLAIMER)", 
         "Servicio de naturaleza técnica y administrativa. El CONSULTOR no es abogado titulado y no ofrece defensa jurídica judicial reservada a profesionales del derecho."),
        
        ("TERCERA: VALOR Y FORMA DE PAGO", 
         f"VALOR TOTAL: ${datos['valor']:,.0f} COP\n"
         f"- Anticipo (50%): ${datos['valor']*0.5:,.0f} al inicio de labores.\n"
         f"- Saldo (50%): ${datos['valor']*0.5:,.0f} a la entrega de documentos."),
        
        ("CUARTA: OBLIGACIONES DEL CONSULTOR", 
         "Análisis con rigor técnico, entrega oportuna de documentos y confidencialidad absoluta de los datos suministrados."),
        
        ("QUINTA: OBLIGACIONES DEL CONTRATANTE", 
         "Suministrar información veraz, radicar documentos bajo su responsabilidad y cumplir con los pagos pactados."),
        
        ("SEXTA: PROTECCIÓN DE DATOS", 
         "Tratamiento de datos personales conforme a la Ley 1581 de 2012.")
    ]

    for tit, cont in clausulas:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_util, 7, tit, ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(w_util, 6, cont)
        pdf.ln(4)

    # Cierre
    pdf.ln(6)
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    f = datetime.now()
    pdf.cell(w_util, 10, f"Medellín, a los {f.day} días del mes de {meses[f.month-1]} de 2026.", ln=True)
    
    # Firmas
    pdf.ln(25)
    y_firmas = pdf.get_y()
    pdf.line(25, y_firmas, 95, y_firmas)
    pdf.line(115, y_firmas, 185, y_firmas)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 10, "EL CONTRATANTE", align='C')
    pdf.cell(100, 10, "EL CONSULTOR", align='C')

    # Código QR
    qr = qrcode.make(APP_URL)
    qr_b = io.BytesIO()
    qr.save(qr_b, format="PNG")
    pdf.image(qr_b, x=165, y=255, w=25)

    return bytes(pdf.output())

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Panel")
    menu = st.radio("Ir a:", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state.auth and st.button("Salir"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULOS ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    n_c = st.text_input("Nombre")
    t_c = st.text_input("WhatsApp")
    s_c = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
    if st.button("Enviar"):
        wa = f"https://wa.me/573116651518?text=Hola Francisco! Soy {n_c}, necesito ayuda con {s_c}."
        st.markdown(f'<a href="{wa}" target="_blank">🚀 Enviar WhatsApp</a>', unsafe_allow_html=True)

elif menu == "🔍 Consultar":
    st.title("Mi Estado")
    cc_s = st.text_input("Cédula", type="password")
    if st.button("Consultar"):
        conn
