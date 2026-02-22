import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- DATOS DEL CONSULTOR ---
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
    conn = sqlite3.connect('barragan_legal_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE PDF A4 PULCRO ---
def generar_contrato_final(datos):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=25, top=25, right=25)
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    w_util = pdf.epw 
    
    # Título
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(w_util, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(5)
    
    # Identificación
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, f"CONTRATANTE: {datos['nombre']}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.multi_cell(w_util, 6, f"CONSULTOR: {CONSULTOR_NOMBRE}, identificado con {ID_CONSULTOR}, profesional con Maestría en Innovación Social y experto en Accesibilidad, operando bajo la actividad económica RUT 7490.")
    pdf.ln(5)
    pdf.multi_cell(w_util, 6, "Las partes acuerdan suscribir el presente contrato de consultoría técnica bajo las siguientes cláusulas:")
    pdf.ln(3)

    # Cláusulas
    secciones = [
        ("PRIMERA: OBJETO DEL SERVICIO", 
         f"El CONSULTOR prestará sus servicios de asesoría técnica y estratégica para la gestión de: {datos['tramite']} ante la entidad {datos['accionado']}."),
        
        ("SEGUNDA: ALCANCE Y NATURALEZA DEL SERVICIO (DISCLAIMER)", 
         "El CONTRATANTE declara entender que el servicio prestado es de naturaleza técnica y de gestión administrativa. El CONSULTOR no es abogado titulado y no ofrece representación judicial ni defensa jurídica reservada a profesionales del derecho."),
        
        ("TERCERA: VALOR Y FORMA DE PAGO", 
         f"El valor total de la consultoría es de ${datos['valor']:,.0f} COP, los cuales se cancelarán así:\n"
         f"- Anticipo (50%): ${datos['valor']*0.5:,.0f} a la firma del contrato.\n"
         f"- Saldo (50%): ${datos['valor']*0.5:,.0f} pagaderos al momento de la entrega de los documentos."),
        
        ("CUARTA: OBLIGACIONES DEL CONSULTOR", 
         "1. Analizar la información suministrada con rigor técnico.\n2. Entregar los documentos oportunamente.\n3. Mantener absoluta confidencialidad."),
        
        ("QUINTA: OBLIGACIONES DEL CONTRATANTE", 
         "1. Suministrar información veraz.\n2. Radicar documentos bajo su propia responsabilidad.\n3. Cumplir con los pagos pactados."),
        
        ("SEXTA: PROTECCIÓN DE DATOS", 
         "Ambas partes autorizan el tratamiento de datos personales conforme a la Ley 1581 de 2012.")
    ]

    for tit, cont in secciones:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_util, 8, tit, ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(w_util, 6, cont)
        pdf.ln(2)

    # Cierre
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    f = datetime.now()
    pdf.ln(5)
    pdf.cell(w_util, 10, f"En la ciudad de Medellín, a los {f.day} días del mes de {meses[f.month-1]} de 2026.", ln=True)
    
    # --- BLOQUE DE FIRMAS CORREGIDO ---
    pdf.ln(20)
    y_f = pdf.get_y()
    # Líneas de firma simétricas (70mm cada una)
    pdf.line(25, y_f + 10, 95, y_f + 10) # Izquierda
    pdf.line(115, y_f + 10, 185, y_f + 10) # Derecha
    pdf.ln(12)
    # Celdas de texto simétricas (80mm cada una, total 160mm)
    pdf.cell(80, 10, "EL CONTRATANTE", align='C')
    pdf.cell(80, 10, "EL CONSULTOR", align='C')

    # QR
    qr = qrcode.make(APP_URL)
    qr_io = io.BytesIO()
    qr.save(qr_io, format="PNG")
    pdf.image(qr_io, x=170, y=250, w=25)

    return bytes(pdf.output())

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Panel")
    opcion = st.radio("Secciones", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULOS ---
if opcion == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    n_cl = st.text_input("Nombre")
    w_cl = st.text_input("WhatsApp")
    s_cl = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
    if st.button("Enviar Pedido"):
        wa = f"https://wa.me/573116651518?text=Hola Francisco! Soy {n_cl}. Requiero: {s_cl}"
        st.markdown(f'<a href="{wa}" target="_blank">🚀 Enviar</a>', unsafe_allow_html=True)

elif opcion == "🔍 Consultar":
    st.title("Estado de Trámite")
    cc_s = st.text_input("Cédula", type="password")
    if st.button("Ver Mi Estado"):
        conn = sqlite3.connect('barragan_legal_final.db')
        res = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc_s,))
        conn.close()
        if not res.empty:
            st.success(f"Estado: {res['estado'].iloc[0]}")
            st.info(f"Avance: {res['avances'].iloc[0]}")
        else: st.error("No registrado.")

elif opcion == "🔒 Admin":
    if not st.session_state.auth:
        clave_i = st.text_input("Clave de Seguridad", type="password")
        if st.button("Entrar"):
            if clave_i == CLAVE_ADMIN:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    else:
        st.title("Panel de Administración")
        tab1, tab2 = st.tabs(["📝 Registrar Caso", "📂 Gestionar"])
        with tab1:
            with st.form("nuevo_registro"):
                c1, c2 = st.columns(2)
                nom_i = c1.text_input("Nombre Cliente")
                ced_i = c1.text_input("Cédula")
                pho_i = c2.text_input("Teléfono")
                val_i = c2.number_input("Valor total COP", min_value=0)
                tra_i = st.selectbox("Trámite", ["Solicitud de Ajustes Razonables", "Reclamación falta de notificación", "Estructuración Derechos de Petición"])
                ent_i = st.text_input("Entidad")
                if st.form_submit_button("Guardar y Generar PDF"):
                    num_c = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec_c = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_legal_final.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num_c, nom_i, ced_i, pho_i, tra_i, ent_i, val_i, "Abierto", "Iniciado", fec_c))
                    conn.commit()
                    conn.close()
                    st.session_state.pdf_contrato = generar_contrato_final({"nombre":nom_i, "cedula":ced_i, "tramite":tra_i, "accionado":ent_i, "valor":val_i})
                    st.session_state.nombre_pdf = f"Contrato_{nom_i}.pdf"
                    st.success("✅ Caso registrado.")

            if st.session_state.pdf_contrato is not None:
                st.download_button("📥 DESCARGAR CONTRATO A4", st.session_state.pdf_contrato, st.session_state.nombre_pdf, "application/pdf")

        with tab2:
            conn = sqlite3.connect('barragan_legal_final.db')
            df_g = pd.read_sql_query("SELECT id, nombre, tramite, estado FROM gestion_procesos", conn)
            conn.close()
            st.dataframe(df_g, use_container_width=True)
