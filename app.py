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
APP_URL = "https://legaltech-asesorias.streamlit.app" 

# Inicializar estados de sesión
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = ""

# --- ESTILO CSS MINIMALISTA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .st-emotion-cache-1r6slb0 { background-color: white; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; }
    h1 { color: #1a1a1a; font-weight: 600; letter-spacing: -1.2px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; background-color: #000; color: white; border: none; padding: 0.6rem; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #0066ff; color: white; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('consultoria_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_bytes(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FRANCISCO BARRAGÁN - CONSULTORÍA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO No. {datos['numero']}", ln=True)
    pdf.ln(5)
    
    # Datos en tabla simple
    for k, v in [("Cliente", datos['nombre']), ("Documento", datos['cedula']), 
                  ("Trámite", datos['tramite']), ("Valor", f"${datos['valor']:,.0f} COP")]:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, f"{k}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, str(v), ln=1)
    
    # Agregar QR
    qr = qrcode.make(APP_URL)
    qr_img = io.BytesIO()
    qr.save(qr_img, format="PNG")
    pdf.image(qr_img, x=150, y=200, w=40)
    
    # Retornar como BYTES (Esto corrige el error de Streamlit)
    return bytes(pdf.output())

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Barragán")
    menu = st.radio("Sección", ["✨ Solicitar", "🔍 Mi Proceso", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Trámite")
    n = st.text_input("Nombre Completo")
    t = st.text_input("WhatsApp")
    s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
    if st.button("Enviar Pedido"):
        if n and t:
            msg = f"Hola Francisco! Nuevo pedido de {n}. WhatsApp: {t}. Servicio: {s}"
            wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Enviar por WhatsApp</div></a>', unsafe_allow_html=True)
        else: st.error("Faltan datos.")

# --- MÓDULO CONSULTAR ---
elif menu == "🔍 Mi Proceso":
    st.title("Consulta de Estado")
    cc_busqueda = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('consultoria_pro.db')
        df = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(cc_busqueda,))
        conn.close()
        if not df.empty:
            st.success(f"Estado: {df['estado'].iloc[0]}")
            st.info(f"Último Avance: {df['avances'].iloc[0]}")
        else: st.error("No se encontró el registro.")

# --- MÓDULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state.auth:
        clave = st.text_input("Clave Admin", type="password")
        if st.button("Entrar"):
            if clave == CLAVE_ADMIN:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    else:
        st.title("Panel Administrativo")
        tab1, tab2 = st.tabs(["📝 Registrar Caso", "📂 Gestión / Firmados"])
        
        with tab1:
            with st.form("registro_form"):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre Cliente")
                ced = col1.text_input("Cédula")
                pho = col2.text_input("WhatsApp")
                val = col2.number_input("Valor (COP)", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                
                if st.form_submit_button("Guardar Registro"):
                    if nom and ced:
                        num = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                        fec = datetime.now().strftime("%Y-%m-%d")
                        conn = sqlite3.connect('consultoria_pro.db')
                        cur = conn.cursor()
                        cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (num, nom, ced, pho, tra, acc, val, "Abierto", "Iniciado", fec))
                        conn.commit()
                        conn.close()
                        
                        # Guardamos los bytes en el estado de sesión para el botón
                        st.session_state.pdf_data = generar_pdf_bytes({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "valor":val})
                        st.session_state.pdf_name = f"Contrato_{nom}.pdf"
                        st.success(f"✅ Caso {num} guardado.")
                    else: st.error("Nombre y cédula obligatorios.")

            # El botón de descarga SOLO aparece si hay datos y está FUERA del form
            if st.session_state.pdf_data is not None:
                st.download_button(
                    label="📥 DESCARGAR CONTRATO AHORA",
                    data=st.session_state.pdf_data,
                    file_name=st.session_state.pdf_name,
                    mime="application/pdf"
                )

        with tab2:
            st.subheader("Subir Contrato Firmado")
            conn = sqlite3.connect('consultoria_pro.db')
            df_admin = pd.read_sql_query("SELECT id, nombre, estado FROM gestion_procesos", conn)
            conn.close()
            
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True)
                sel_id = st.selectbox("Seleccione ID para subir PDF firmado", df_admin['id'])
                archivo_firmado = st.file_uploader("Subir contrato firmado (PDF)", type="pdf")
                
                if st.button("Guardar PDF Firmado"):
                    if archivo_firmado:
                        blob = archivo_firmado.read()
                        conn = sqlite3.connect('consultoria_pro.db')
                        cur = conn.cursor()
                        cur.execute("UPDATE gestion_procesos SET firmado=?, estado='Firmado' WHERE id=?", (blob, sel_id))
                        conn.commit()
                        conn.close()
                        st.success("Archivo guardado exitosamente.")
                    else: st.warning("Cargue un archivo primero.")
