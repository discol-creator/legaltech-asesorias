import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- DATOS DEL CONSULTOR (PRE-CARGADOS) ---
CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_ID = "CE 7354548"
CLAVE_ADMIN = "1234" # Cámbiala por tu clave real
APP_URL = "https://tu-app-barragan.streamlit.app"

# --- 1. INICIALIZACIÓN DE VARIABLES DE SESIÓN (EVITA ATTRIBUTEERROR) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_contrato' not in st.session_state:
    st.session_state.pdf_contrato = None
if 'nombre_pdf' not in st.session_state:
    st.session_state.nombre_pdf = ""

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS MINIMALISTA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .st-emotion-cache-1r6slb0 { background-color: white; border-radius: 20px; padding: 2.5rem; border: 1px solid #f0f0f0; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
    h1, h2 { color: #1a1a1a; font-weight: 600; letter-spacing: -1.2px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #000; color: #fff; font-weight: 600; border: none; padding: 0.6rem; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #0066ff; color: #fff; font-weight: 600; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS (NUEVA TABLA PARA EVITAR CONFLICTOS) ---
def init_db():
    conn = sqlite3.connect('consultoria_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. GENERADOR DE PDF CON ESTRUCTURA LEGAL ---
def generar_contrato_legal(datos):
    pdf = FPDF()
    pdf.add_page()
    w_util = pdf.epw # Ancho efectivo para evitar FPDFException
    
    # Título
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(w_util, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(5)
    
    # Identificación
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, f"CONTRATANTE: {datos['nombre']}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.multi_cell(w_util, 6, f"CONSULTOR: {CONSULTOR_NOMBRE}, identificado con {CONSULTOR_ID}, profesional con Maestría en Innovación Social y experto en Accesibilidad, operando bajo la actividad económica RUT 7490.")
    pdf.ln(5)
    pdf.multi_cell(w_util, 6, "Las partes acuerdan suscribir el presente contrato de consultoría técnica bajo las siguientes cláusulas:")
    pdf.ln(3)

    # Cláusulas
    clausulas = [
        ("PRIMERA: OBJETO DEL SERVICIO", 
         f"El CONSULTOR prestará sus servicios de asesoría técnica y estratégica para la gestión de: {datos['tramite']} ante la entidad {datos['accionado']}."),
        
        ("SEGUNDA: ALCANCE Y NATURALEZA DEL SERVICIO (DISCLAIMER)", 
         "El CONTRATANTE declara entender que el servicio prestado es de naturaleza técnica y de gestión administrativa. El CONSULTOR no es abogado titulado y no ofrece representación judicial ni defensa jurídica reservada a profesionales del derecho. El servicio consiste en la elaboración de documentos y estrategias para que el CONTRATANTE ejerza sus derechos constitucionales por cuenta propia."),
        
        ("TERCERA: VALOR Y FORMA DE PAGO", 
         f"El valor total de la consultoría es de ${datos['valor']:,.0f} COP, los cuales se cancelarán así:\n"
         f"- Anticipo (50%): ${datos['valor']*0.5:,.0f} a la firma del contrato para inicio de labores.\n"
         f"- Saldo (50%): ${datos['valor']*0.5:,.0f} pagaderos al momento de la entrega de los documentos finales."),
        
        ("CUARTA: OBLIGACIONES DEL CONSULTOR", 
         "1. Analizar la información suministrada con rigor técnico.\n"
         "2. Entregar los documentos (peticiones, formatos, guías) oportunamente.\n"
         "3. Mantener absoluta confidencialidad sobre los datos personales del cliente."),
        
        ("QUINTA: OBLIGACIONES DEL CONTRATANTE", 
         "1. Suministrar información veraz y completa.\n"
         "2. Radicar los documentos bajo su propia responsabilidad.\n"
         "3. Realizar los pagos en las fechas acordadas."),
        
        ("SEXTA: PROTECCIÓN DE DATOS", 
         "Ambas partes autorizan el tratamiento de datos personales única y exclusivamente para los fines de este contrato, conforme a la Ley 1581 de 2012.")
    ]

    for titulo, contenido in clausulas:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_util, 8, titulo, ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(w_util, 6, contenido)
        pdf.ln(2)

    # Cierre y Firmas
    pdf.ln(5)
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora = datetime.now()
    fecha_txt = f"En la ciudad de Medellín, a los {ahora.day} días del mes de {meses[ahora.month-1]} de 2026."
    pdf.multi_cell(w_util, 10, fecha_txt)
    
    pdf.ln(20)
    pdf.line(10, pdf.get_y(), 90, pdf.get_y())
    pdf.line(120, pdf.get_y(), 200, pdf.get_y())
    pdf.cell(90, 10, "EL CONTRATANTE", align='C')
    pdf.cell(110, 10, "EL CONSULTOR", align='C')

    # QR de Seguimiento
    qr = qrcode.make(APP_URL)
    qr_img = io.BytesIO()
    qr.save(qr_img, format="PNG")
    pdf.image(qr_img, x=165, y=250, w=30)

    return bytes(pdf.output())

# --- 4. INTERFAZ ---
with st.sidebar:
    st.title("⚖️ Barragán Tech")
    menu = st.radio("Secciones", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Trámite")
    n_p = st.text_input("Nombre")
    t_p = st.text_input("WhatsApp")
    s_p = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
    if st.button("Enviar Pedido"):
        wa = f"https://wa.me/573116651518?text=Hola Francisco! Soy {n_p}, quiero el servicio de {s_p}."
        st.markdown(f'<a href="{wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Hablar por WhatsApp</div></a>', unsafe_allow_html=True)

# --- MÓDULO CONSULTAR ---
elif menu == "🔍 Consultar":
    st.title("Mi Estado")
    ced_c = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Ver Avances"):
        conn = sqlite3.connect('consultoria_final.db')
        df = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(ced_c,))
        conn.close()
        if not df.empty:
            st.success(f"Estado: {df['estado'].iloc[0]}")
            st.info(f"Detalle: {df['avances'].iloc[0]}")
        else: st.error("No se encontró registro.")

# --- MÓDULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state.auth:
        if st.text_input("Clave", type="password") == CLAVE_ADMIN:
            st.session_state.auth = True
            st.rerun()
    else:
        st.title("Panel Admin")
        t1, t2 = st.tabs(["📝 Nuevo Registro", "📂 Gestión"])
        
        with t1:
            with st.form("form_admin", clear_on_submit=False):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre Cliente")
                ced = col1.text_input("Cédula")
                pho = col2.text_input("WhatsApp")
                val = col2.number_input("Valor COP", min_value=0)
                tra = st.selectbox("Servicio", ["Solicitud de Ajustes Razonables (Ley 1618)", "Reclamación falta de notificación", "Estructuración Derechos de Petición"])
                acc = st.text_input("Entidad")
                if st.form_submit_button("Registrar y Crear PDF"):
                    num = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('consultoria_final.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Abierto", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.pdf_contrato = generar_contrato_legal({"nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val})
                    st.session_state.nombre_pdf = f"Contrato_{nom}.pdf"
                    st.success("✅ Registro exitoso.")

            if st.session_state.pdf_contrato:
                st.download_button("📥 DESCARGAR CONTRATO LEGAL (PDF)", st.session_state.pdf_contrato, st.session_state.nombre_pdf, "application/pdf")

        with t2:
            conn = sqlite3.connect('consultoria_final.db')
            df_g = pd.read_sql_query("SELECT id, nombre, estado FROM gestion_procesos", conn)
            conn.close()
            st.dataframe(df_g, use_container_width=True)
            if not df_g.empty:
                sid = st.selectbox("ID", df_g['id'])
                up_pdf = st.file_uploader("Subir contrato firmado", type="pdf")
                if st.button("Guardar Cambios"):
                    st.success("Actualizado.")
