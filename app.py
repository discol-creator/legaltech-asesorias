import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- DATOS DEL CONSULTOR ---
NOMBRE_CONSULTOR = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
ID_CONSULTOR = "CE 7354548"
CLAVE_ADMIN = "1234"
# Cambia esta URL por la de tu app real en Streamlit Cloud
APP_URL = "https://legaltech-asesorias.streamlit.app"

# --- INICIALIZACIÓN DE ESTADOS ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_contrato' not in st.session_state:
    st.session_state.pdf_contrato = None

# --- ESTILO CSS (MINIMALISMO MODERNO) ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .st-emotion-cache-1r6slb0 { background-color: #fcfcfc; border-radius: 12px; padding: 2rem; border: 1px solid #eee; }
    h1, h2, h3 { color: #000; font-weight: 600; letter-spacing: -1px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #000; color: #fff; font-weight: 600; padding: 0.6rem; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #0066ff; color: #fff; font-weight: 600; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('barragan_legal.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE PDF (FIX DE ESPACIO HORIZONTAL) ---
def generar_pdf_seguro(datos):
    pdf = FPDF()
    pdf.add_page()
    w_pag = pdf.epw # Ancho efectivo de la página
    
    # Encabezado
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(w_pag, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(5)
    
    # Datos Partes
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_pag, 6, f"CONTRATANTE: {datos['nombre']}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.ln(2)
    pdf.multi_cell(w_pag, 6, f"CONSULTOR: {NOMBRE_CONSULTOR}, identificado con {ID_CONSULTOR}, profesional con Maestría en Innovación Social y experto en Accesibilidad, operando bajo la actividad económica RUT 7490.")
    pdf.ln(5)
    
    pdf.multi_cell(w_pag, 6, "Las partes acuerdan suscribir el presente contrato de consultoría técnica bajo las siguientes cláusulas:")
    pdf.ln(3)

    # Cláusulas Dinámicas
    claúsulas = [
        ("PRIMERA: OBJETO DEL SERVICIO", 
         f"El CONSULTOR prestará sus servicios de asesoría técnica y estratégica para la gestión de: {datos['tramite']} ante la entidad {datos['accionado']}."),
        
        ("SEGUNDA: ALCANCE Y NATURALEZA DEL SERVICIO", 
         "El CONTRATANTE declara entender que el servicio prestado es de naturaleza técnica y de gestión administrativa. El CONSULTOR no es abogado titulado y no ofrece representación judicial ni defensa jurídica reservada a profesionales del derecho."),
        
        ("TERCERA: VALOR Y FORMA DE PAGO", 
         f"El valor total es de ${datos['valor']:,.0f} COP.\n- Anticipo (50%): ${datos['valor']*0.5:,.0f} (Inicio).\n- Saldo (50%): ${datos['valor']*0.5:,.0f} (Entrega)."),
        
        ("CUARTA: OBLIGACIONES", 
         "Análisis técnico con rigor, entrega de documentos en plazos acordados y confidencialidad absoluta."),
        
        ("QUINTA: PROTECCIÓN DE DATOS", 
         "Tratamiento conforme a la Ley 1581 de 2012.")
    ]

    for tit, cont in claúsulas:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_pag, 8, tit, ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(w_pag, 6, cont)
        pdf.ln(2)

    # Cierre y Firmas
    pdf.ln(5)
    fecha_hoy = datetime.now().strftime("%d de %m de 2026")
    pdf.cell(w_pag, 10, f"Medellín, {fecha_hoy}.", ln=True)
    
    pdf.ln(20)
    y_firma = pdf.get_y()
    pdf.line(10, y_firma, 90, y_firma)
    pdf.line(120, y_firma, 200, y_firma)
    pdf.cell(90, 10, "EL CONTRATANTE", align='C')
    pdf.cell(110, 10, "EL CONSULTOR", align='C')

    # Código QR de seguimiento
    qr = qrcode.make(APP_URL)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format="PNG")
    pdf.image(qr_buffer, x=165, y=250, w=30)

    return bytes(pdf.output())

# --- NAVEGACIÓN ---
with st.sidebar:
    st.markdown("### ⚖️ Barragán Tech")
    seccion = st.radio("Ir a:", ["✨ Solicitar", "🔍 Mi Proceso", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO SOLICITUD (CLIENTES) ---
if seccion == "✨ Solicitar":
    st.title("Inicia tu Trámite")
    with st.container():
        nom_c = st.text_input("Nombre Completo")
        wa_c = st.text_input("WhatsApp")
        tra_c = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        if st.button("Enviar solicitud"):
            msg = f"Hola Francisco! Quiero iniciar un proceso de {tra_c}. Mi nombre es {nom_c}."
            st.markdown(f'<a href="https://wa.me/573116651518?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;">🚀 Contactar por WhatsApp</div></a>', unsafe_allow_html=True)

# --- MÓDULO CONSULTA (CLIENTES) ---
elif seccion == "🔍 Mi Proceso":
    st.title("Consulta de Proceso")
    cc_search = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Consultar Estado"):
        conn = sqlite3.connect('barragan_legal.db')
        res = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc_search,))
        conn.close()
        if not res.empty:
            st.success(f"Estado: {res['estado'].iloc[0]}")
            st.info(f"Avances: {res['avances'].iloc[0]}")
        else: st.error("No se encontró información.")

# --- MÓDULO ADMIN (PROTEGIDO) ---
elif seccion == "🔒 Admin":
    if not st.session_state.auth:
        if st.text_input("Clave de Acceso", type="password") == CLAVE_ADMIN:
            st.session_state.auth = True
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["📝 Registro", "📂 Seguimiento & Firmados"])
        
        with tab1:
            with st.form("registro_proceso", clear_on_submit=False):
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre Cliente")
                cedula = col1.text_input("Cédula")
                tel = col2.text_input("WhatsApp")
                val = col2.number_input("Valor total COP", min_value=0)
                tramite = st.selectbox("Tipo de Trámite", ["Solicitud de Ajustes Razonables", "Reclamación falta de notificación", "Estructuración Derecho de Petición"])
                entidad = st.text_input("Entidad (Accionado)")
                
                if st.form_submit_button("Registrar y Crear PDF"):
                    num = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_legal.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nombre, cedula, tel, tramite, entidad, val, "Abierto", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    
                    # Generar PDF seguro
                    st.session_state.pdf_contrato = generar_pdf_seguro({"nombre":nombre, "cedula":cedula, "tramite":tramite, "accionado":entidad, "valor":val})
                    st.success(f"Caso {num} registrado exitosamente.")

            if st.session_state.pdf_contrato:
                st.download_button("📥 DESCARGAR CONTRATO LEGAL (PDF)", st.session_state.pdf_contract, f"Contrato_{datetime.now().day}.pdf", "application/pdf")

        with tab2:
            conn = sqlite3.connect('barragan_legal.db')
            df = pd.read_sql_query("SELECT id, nombre, tramite, estado FROM gestion_procesos", conn)
            st.dataframe(df, use_container_width=True)
            
            if not df.empty:
                sel_id = st.selectbox("ID de proceso para actualizar", df['id'])
                nuevo_avance = st.text_area("Nuevo avance técnico")
                nuevo_est = st.selectbox("Actualizar Estado", ["En proceso", "Pendiente Entidad", "Cerrado Exitoso"])
                pdf_firmado = st.file_uploader("Subir contrato firmado (PDF)", type="pdf")
                
                if st.button("Guardar Cambios"):
                    conn = sqlite3.connect('barragan_legal.db')
                    cur = conn.cursor()
                    if pdf_firmado:
                        blob = pdf_firmado.read()
                        cur.execute("UPDATE gestion_procesos SET estado=?, avances=?, firmado=? WHERE id=?", (nuevo_est, nuevo_avance, blob, sel_id))
                    else:
                        cur.execute("UPDATE gestion_procesos SET estado=?, avances=? WHERE id=?", (nuevo_est, nuevo_avance, sel_id))
                    conn.commit()
                    conn.close()
                    st.success("Cambios guardados.")
