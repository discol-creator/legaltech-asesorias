import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- CONFIGURACIÓN DE IDENTIDAD ---
NOMBRE_CONSULTOR = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
ID_CONSULTOR = "CE 7354548"
CLAVE_ADMIN = "1234"
APP_URL = "https://legaltech-asesorias.streamlit.app"

if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_contract' not in st.session_state:
    st.session_state.pdf_contract = None

# --- ESTILO CSS ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .st-emotion-cache-1r6slb0 { background-color: white; border-radius: 20px; padding: 2rem; border: 1px solid #eee; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #000; color: white; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #0066ff; color: white; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('barragan_final_v3.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE CONTRATO LEGAL ---
def generar_contrato_legal(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Encabezado
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, f"CONTRATANTE: {datos['nombre']}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.multi_cell(0, 6, f"CONSULTOR: {NOMBRE_CONSULTOR}, identificado con {ID_CONSULTOR}, profesional con Maestría en Innovación Social y experto en Accesibilidad, operando bajo la actividad económica RUT 7490.")
    pdf.ln(5)
    
    pdf.multi_cell(0, 6, "Las partes acuerdan suscribir el presente contrato de consultoría técnica bajo las siguientes cláusulas:")
    pdf.ln(3)

    # Cláusulas
    secciones = [
        ("PRIMERA: OBJETO DEL SERVICIO", 
         f"El CONSULTOR prestará sus servicios de asesoría técnica y estratégica para la gestión de: {datos['tramite']} ante la entidad {datos['accionado']}."),
        
        ("SEGUNDA: ALCANCE Y NATURALEZA DEL SERVICIO (DISCLAIMER)", 
         "El CONTRATANTE declara entender que el servicio prestado es de naturaleza técnica y de gestión administrativa. El CONSULTOR no es abogado titulado y no ofrece representación judicial ni defensa jurídica reservada a profesionales del derecho. El servicio consiste en la elaboración de documentos y estrategias para que el CONTRATANTE ejerza sus derechos constitucionales por cuenta propia."),
        
        ("TERCERA: VALOR Y FORMA DE PAGO", 
         f"El valor total de la consultoría es de ${datos['valor']:,.0f} COP, los cuales se cancelarán así:\n"
         f"- Anticipo (50%): ${datos['valor']*0.5:,.0f} a la firma del contrato para inicio de labores.\n"
         f"- Saldo (50%): ${datos['valor']*0.5:,.0f} pagaderos al momento de la entrega de los documentos finales."),
        
        ("CUARTA: OBLIGACIONES DEL CONSULTOR", 
         "1. Analizar la información suministrada por el cliente con rigor técnico.\n"
         "2. Entregar los documentos (peticiones, formatos, guías) de forma oportuna.\n"
         "3. Mantener absoluta confidencialidad sobre los datos personales del cliente."),
        
        ("QUINTA: OBLIGACIONES DEL CONTRATANTE", 
         "1. Suministrar información veraz y completa.\n"
         "2. Radicar los documentos ante las entidades bajo su propia responsabilidad.\n"
         "3. Realizar los pagos en las fechas acordadas."),
        
        ("SEXTA: PROTECCIÓN DE DATOS", 
         "Ambas partes autorizan el tratamiento de datos personales conforme a la Ley 1581 de 2012.")
    ]

    for titulo, contenido in secciones:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, titulo, ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, contenido)
        pdf.ln(2)

    # Cierre
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora = datetime.now()
    fecha_texto = f"En la ciudad de Medellín, a los {ahora.day} días del mes de {meses[ahora.month-1]} de 2026."
    pdf.ln(5)
    pdf.cell(0, 10, fecha_texto, ln=True)
    
    # Firmas
    pdf.ln(20)
    pdf.cell(90, 10, "__________________________", ln=0, align='C')
    pdf.cell(90, 10, "__________________________", ln=1, align='C')
    pdf.cell(90, 10, "EL CONTRATANTE", ln=0, align='C')
    pdf.cell(90, 10, "EL CONSULTOR", ln=1, align='C')

    # QR de seguimiento
    qr = qrcode.make(APP_URL)
    qr_io = io.BytesIO()
    qr.save(qr_io, format="PNG")
    pdf.image(qr_io, x=160, y=250, w=30)

    return bytes(pdf.output())

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Barragán Tech")
    menu = st.radio("Sección", ["✨ Solicitar", "🔍 Mi Proceso", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULOS ---
if menu == "✨ Solicitar":
    st.title("Solicita tu Asesoría")
    with st.container():
        n = st.text_input("Nombre")
        t = st.text_input("WhatsApp")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados DataCrédito", "Peticiones"])
        if st.button("Enviar Pedido"):
            wa = f"https://wa.me/573116651518?text=Hola Francisco! Quiero iniciar: {s}"
            st.markdown(f'<a href="{wa}" target="_blank">🚀 Enviar WhatsApp</a>', unsafe_allow_html=True)

elif menu == "🔍 Mi Proceso":
    st.title("Consulta")
    cc = st.text_input("Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('barragan_final_v3.db')
        df = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Estado: {df['estado'].iloc[0]}")
            st.info(f"Avance: {df['avances'].iloc[0]}")
        else: st.error("No registrado.")

elif menu == "🔒 Admin":
    if not st.session_state.auth:
        if st.text_input("Clave", type="password") == CLAVE_ADMIN:
            st.session_state.auth = True
            st.rerun()
    else:
        st.title("Administración")
        t1, t2 = st.tabs(["📝 Nuevo Registro", "📊 Gestión"])
        
        with t1:
            with st.form("registro_legal"):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre Cliente")
                ced = col1.text_input("Cédula")
                pho = col2.text_input("WhatsApp")
                val = col2.number_input("Valor total (COP)", min_value=0)
                tra = st.selectbox("Trámite", ["Solicitud de Ajustes Razonables", "Reclamación falta de notificación", "Estructuración Derechos de Petición"])
                acc = st.text_input("Entidad")
                if st.form_submit_button("Guardar y Generar Contrato"):
                    num = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_final_v3.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Abierto", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    st.session_state.pdf_contract = generar_contrato_legal({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val})
                    st.success("✅ Caso registrado.")

            if st.session_state.pdf_contract:
                st.download_button("📥 DESCARGAR CONTRATO LEGAL PDF", st.session_state.pdf_contract, "Contrato.pdf", "application/pdf")

        with t2:
            conn = sqlite3.connect('barragan_final_v3.db')
            df_admin = pd.read_sql_query("SELECT id, nombre, estado FROM gestion_procesos", conn)
            conn.close()
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True)
                sel_id = st.selectbox("ID para actualizar", df_admin['id'])
                archivo = st.file_uploader("Subir firmado", type="pdf")
                if st.button("Guardar Cambios"):
                    # Lógica para subir el binario si existe el archivo
                    st.success("Actualizado.")
