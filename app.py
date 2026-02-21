import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import qrcode
import io
import urllib.parse

# --- CONFIGURACIÓN DE SEGURIDAD Y MARCA ---
CLAVE_ADMIN = "1234"  # Cámbiala por tu clave real
APP_URL = "https://tu-app-barragan.streamlit.app" # Cambia esto al publicar

if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# --- DISEÑO MINIMALISTA (CSS) ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    .st-emotion-cache-1r6slb0 { background-color: white; border-radius: 20px; padding: 2.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.03); border: 1px solid #f0f0f0; }
    h1 { color: #1a1a1a; font-weight: 600; letter-spacing: -1.5px; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #000; color: #fff; border: none; padding: 0.8rem; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { background-color: #333; transform: translateY(-2px); }
    .status-card { padding: 15px; border-radius: 10px; border-left: 5px solid #000; background: #f9f9f9; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('barragan_data.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla principal de procesos
    c.execute('''CREATE TABLE IF NOT EXISTS procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  num_contrato TEXT, nombre TEXT, cedula TEXT, telefono TEXT,
                  tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE PDF PREMIUM ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "FRANCISCO BARRAGÁN", ln=True, align="L")
        self.set_font("Arial", "", 9)
        self.cell(0, 5, "Consultoría Técnica & Innovación Social | RUT 7490", ln=True)
        self.ln(10)

def create_pdf(datos):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"CONTRATO DE SERVICIOS No. {datos['numero']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    
    info = [
        ("CLIENTE", datos['nombre']), ("CÉDULA", datos['cedula']),
        ("TRÁMITE", datos['tramite']), ("ENTIDAD", datos['entidad']),
        ("VALOR TOTAL", f"${datos['valor']:,.0f} COP")
    ]
    
    for label, val in info:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, f"{label}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, str(val), ln=1)
    
    pdf.ln(10)
    pdf.multi_cell(0, 8, "Este documento certifica el inicio de la gestión técnica estratégica. El cliente puede consultar avances escaneando el QR adjunto.")
    
    # QR Code
    qr = qrcode.make(APP_URL)
    qr_img = io.BytesIO()
    qr.save(qr_img, format="PNG")
    qr_img.seek(0)
    pdf.image(qr_img, x=160, y=240, w=30)
    
    return pdf.output(dest='S')

# --- INTERFAZ PRINCIPAL ---
with st.sidebar:
    st.markdown("# ⚖️ Menú")
    opt = st.radio("Navegación", ["✨ Solicitar", "🔍 Mi Proceso", "🔒 Admin"])
    if st.session_state.auth and st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO 1: SOLICITAR (PÚBLICO) ---
if opt == "✨ Solicitar":
    st.title("Inicia tu Trámite")
    st.write("Completa los datos y nos pondremos en contacto contigo.")
    with st.container():
        n = st.text_input("Nombre Completo")
        c_p = st.text_input("Documento / Cédula")
        t_p = st.text_input("WhatsApp (con +57)")
        s_p = st.selectbox("Servicio Requerido", ["Ajustes Razonables", "Borrados de Reportes", "Derecho de Petición"])
        d_p = st.text_area("Cuéntanos tu caso")
        
        if st.button("Enviar Solicitud"):
            msg = f"Hola Francisco! Nuevo caso de *{n}* ({c_p}).\nServicio: {s_p}\nDetalles: {d_p}"
            wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:600;">🚀 Enviar vía WhatsApp</div></a>', unsafe_allow_html=True)

# --- MÓDULO 2: MI PROCESO (CLIENTES SEGURIDAD) ---
elif opt == "🔍 Mi Proceso":
    st.title("Consulta de Avances")
    search_cc = st.text_input("Ingresa tu Cédula", type="password")
    if st.button("Ver Mi Proceso"):
        conn = sqlite3.connect('barragan_data.db')
        res = pd.read_sql_query("SELECT * FROM procesos WHERE cedula = ?", conn, params=(search_cc,))
        conn.close()
        
        if not res.empty:
            st.balloons()
            row = res.iloc[0]
            st.markdown(f"### Hola, {row['nombre']}")
            st.markdown(f'<div class="status-card"><b>Estado Actual:</b> {row["estado"]}</div>', unsafe_allow_html=True)
            st.info(f"**Trámite:** {row['tramite']} contra {row['accionado']}")
            st.warning(f"**Último Avance:** {row['avances']}")
            if row['firmado']:
                st.success("✅ Tu contrato ya se encuentra firmado y archivado.")
        else:
            st.error("No se encontró información asociada a este documento.")

# --- MÓDULO 3: ADMIN (GESTIÓN TOTAL) ---
elif opt == "🔒 Admin":
    if not st.session_state.auth:
        pw = st.text_input("Clave de Acceso", type="password")
        if st.button("Entrar"):
            if pw == CLAVE_ADMIN:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    else:
        st.title("Panel Administrativo")
        t1, t2 = st.tabs(["📝 Registrar Caso", "📂 Gestionar / Firmados"])
        
        with t1:
            with st.form("new_case"):
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre Cliente")
                cedula = col1.text_input("Cédula")
                tel = col2.text_input("Teléfono (+57)")
                val = col2.number_input("Valor (COP)", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Petición"])
                ent = st.text_input("Entidad (Accionado)")
                
                if st.form_submit_button("Crear Registro y PDF"):
                    num = f"CONTRATO-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_data.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO procesos (num_contrato, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nombre, cedula, tel, tra, ent, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    
                    pdf = create_pdf({"numero":num, "nombre":nombre, "cedula":cedula, "tramite":tra, "entidad":ent, "valor":val})
                    st.success(f"Caso {num} registrado.")
                    st.download_button("📥 Descargar Contrato para Firma", pdf, f"Contrato_{nombre}.pdf", "application/pdf")

        with t2:
            conn = sqlite3.connect('barragan_data.db')
            df = pd.read_sql_query("SELECT id, num_contrato, nombre, estado, fecha FROM procesos", conn)
            st.dataframe(df, use_container_width=True)
            
            sel_id = st.selectbox("ID de Proceso para actualizar", df['id'])
            col_a, col_b = st.columns(2)
            nuevo_est = col_a.selectbox("Nuevo Estado", ["Apertura", "Enviado", "En Proceso", "Firmado", "Cerrado Exitoso"])
            archivo_firmado = col_b.file_uploader("Subir Contrato Firmado (PDF)", type="pdf")
            nuevo_av = st.text_area("Describa el avance técnico")
            
            if st.button("Guardar Cambios"):
                conn = sqlite3.connect('barragan_data.db')
                cur = conn.cursor()
                if archivo_firmado:
                    binary_pdf = archivo_firmado.read()
                    cur.execute("UPDATE procesos SET estado=?, avances=?, firmado=? WHERE id=?", (nuevo_est, nuevo_av, binary_pdf, sel_id))
                else:
                    cur.execute("UPDATE procesos SET estado=?, avances=? WHERE id=?", (nuevo_est, nuevo_av, sel_id))
                conn.commit()
                conn.close()
                st.success("Proceso actualizado.")
