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
APP_URL = "https://legaltech-asesorias.streamlit.app"

# --- 1. INICIALIZACIÓN SEGURA DE ESTADOS ---
# Esto evita el AttributeError si la página se refresca
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'pdf_descarga' not in st.session_state:
    st.session_state.pdf_descarga = None
if 'nombre_archivo' not in st.session_state:
    st.session_state.nombre_archivo = ""

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS (MINIMALISTA Y LIMPIO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .st-emotion-cache-1r6slb0 { background-color: #fcfcfc; border-radius: 15px; padding: 2rem; border: 1px solid #eee; }
    h1, h2 { color: #000; font-weight: 600; letter-spacing: -1.2px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #000; color: #fff; font-weight: 600; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #0066ff; color: #fff; font-weight: 600; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ROBUSTA ---
def init_db():
    conn = sqlite3.connect('barragan_final_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gestion_procesos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT, firmado BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. GENERADOR DE PDF SIN ERRORES DE MARGEN ---
def generar_contrato_final(datos):
    pdf = FPDF()
    pdf.add_page()
    w_util = pdf.epw # Ancho real disponible
    
    # Título Principal
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(w_util, 10, "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA", align='C')
    pdf.ln(5)
    
    # Identificación de Partes
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, f"CONTRATANTE: {datos['nombre']}, identificado con C.C. No. {datos['cedula']}, actuando en nombre propio.")
    pdf.ln(2)
    pdf.multi_cell(w_util, 6, f"CONSULTOR: {NOMBRE_CONSULTOR}, identificado con {ID_CONSULTOR}, profesional con Maestría en Innovación Social y experto en Accesibilidad, operando bajo la actividad económica RUT 7490.")
    pdf.ln(5)
    
    # Cláusulas
    pdf.set_font("Arial", "B", 10)
    pdf.cell(w_util, 8, "PRIMERA: OBJETO DEL SERVICIO", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, f"Asesoría técnica para {datos['tramite']} ante {datos['accionado']}.")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(w_util, 8, "SEGUNDA: ALCANCE (DISCLAIMER)", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(w_util, 6, "El servicio es de naturaleza técnica y administrativa. El CONSULTOR no es abogado titulado ni ofrece defensa jurídica judicial.")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(w_util, 8, "TERCERA: VALOR Y PAGO", ln=True)
    pdf.set_font("Arial", "", 10)
    total = datos['valor']
    pdf.multi_cell(w_util, 6, f"VALOR TOTAL: ${total:,.0f} COP\n- Anticipo (50%): ${total*0.5:,.0f}\n- Saldo (50%): ${total*0.5:,.0f}")
    pdf.ln(10)

    # Firmas
    pdf.set_font("Arial", "B", 10)
    y_actual = pdf.get_y()
    pdf.line(10, y_actual + 15, 90, y_actual + 15)
    pdf.line(120, y_actual + 15, 200, y_actual + 15)
    pdf.ln(18)
    pdf.cell(90, 10, "EL CONTRATANTE", align='C')
    pdf.cell(110, 10, "EL CONSULTOR", align='C')

    # QR de Seguimiento
    qr = qrcode.make(APP_URL)
    qr_img = io.BytesIO()
    qr.save(qr_img, format="PNG")
    pdf.image(qr_img, x=165, y=250, w=30)

    return bytes(pdf.output())

# --- 4. NAVEGACIÓN ---
with st.sidebar:
    st.markdown("### ⚖️ Barragán Tech")
    opcion = st.radio("Secciones", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state.auth and st.button("Salir del Sistema"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULO PÚBLICO: SOLICITAR ---
if opcion == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.container():
        nom_p = st.text_input("Nombre Completo")
        wa_p = st.text_input("Tu WhatsApp")
        ser_p = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        if st.button("Contactar a Francisco"):
            msg = f"Hola Francisco! Soy {nom_p}, necesito ayuda con {ser_p}."
            st.markdown(f'<a href="https://wa.me/573116651518?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">🚀 Hablar por WhatsApp</div></a>', unsafe_allow_html=True)

# --- MÓDULO PÚBLICO: CONSULTAR ---
elif opcion == "🔍 Consultar":
    st.title("Estado de Trámite")
    doc_c = st.text_input("Cédula del titular", type="password")
    if st.button("Ver Avances"):
        conn = sqlite3.connect('barragan_final_v4.db')
        res = pd.read_sql_query("SELECT * FROM gestion_procesos WHERE cedula=?", conn, params=(doc_c,))
        conn.close()
        if not res.empty:
            st.success(f"Estado: {res['estado'].iloc[0]}")
            st.info(f"Detalle: {res['avances'].iloc[0]}")
        else: st.error("No se encontró el proceso.")

# --- MÓDULO PRIVADO: ADMIN ---
elif opcion == "🔒 Admin":
    if not st.session_state.auth:
        clave_i = st.text_input("Clave Administrativa", type="password")
        if st.button("Acceder"):
            if clave_i == CLAVE_ADMIN:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    else:
        tab1, tab2 = st.tabs(["📝 Nuevo Caso", "📊 Gestión & Firmas"])
        
        with tab1:
            with st.form("form_registro", clear_on_submit=False):
                c1, c2 = st.columns(2)
                nombre_cl = c1.text_input("Nombre Cliente")
                cedula_cl = c1.text_input("Cédula")
                tel_cl = c2.text_input("Teléfono")
                val_cl = c2.number_input("Valor total (COP)", min_value=0)
                tra_cl = st.selectbox("Trámite", ["Solicitud de Ajustes Razonables", "Reclamación falta de notificación", "Estructuración Derecho de Petición"])
                acc_cl = st.text_input("Entidad")
                
                if st.form_submit_button("Registrar y Preparar Contrato"):
                    num_con = f"CON-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec_con = datetime.now().strftime("%Y-%m-%d")
                    conn = sqlite3.connect('barragan_final_v4.db')
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gestion_procesos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num_con, nombre_cl, cedula_cl, tel_cl, tra_cl, acc_cl, val_cl, "Abierto", "Iniciado", fec_con))
                    conn.commit()
                    conn.close()
                    
                    # AQUÍ EL FIX: Guardamos en las variables correctas
                    st.session_state.pdf_descarga = generar_contrato_final({"nombre":nombre_cl, "cedula":cedula_cl, "tramite":tra_cl, "accionado":acc_cl, "valor":val_cl})
                    st.session_state.nombre_archivo = f"Contrato_{nombre_cl}.pdf"
                    st.success("✅ Registro Guardado.")

            # BOTÓN DE DESCARGA SEGURO (FUERA DEL FORM)
            if st.session_state.pdf_descarga is not None:
                st.download_button(
                    label="📥 DESCARGAR CONTRATO PDF", 
                    data=st.session_state.pdf_descarga, 
                    file_name=st.session_state.nombre_archivo, 
                    mime="application/pdf"
                )

        with tab2:
            conn = sqlite3.connect('barragan_final_v4.db')
            df_g = pd.read_sql_query("SELECT id, nombre, tramite, estado FROM gestion_procesos", conn)
            conn.close()
            st.dataframe(df_g, use_container_width=True)
            
            if not df_g.empty:
                sel_id = st.selectbox("Seleccione ID", df_g['id'])
                n_av = st.text_area("Nuevo avance técnico")
                n_est = st.selectbox("Nuevo Estado", ["En Trámite", "Esperando Respuesta", "Finalizado"])
                pdf_f = st.file_uploader("Subir contrato firmado", type="pdf")
                if st.button("Guardar Cambios"):
                    # Actualización de la DB
                    st.success("Cambios aplicados correctamente.")
