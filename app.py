import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="wide", page_icon="⚖️")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('consultoria.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  numero_contrato TEXT, nombre_cliente TEXT, cedula TEXT, 
                  tipo_tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha_creacion TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES AUXILIARES ---
def generar_pdf_contrato(datos_pdf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "CONSULTORÍA FRANCISCO BARRAGÁN", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 10, "Innovación Social & Ajustes Razonables - RUT 7490", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"CONTRATO No. {datos_pdf['numero']}", ln=True)
    pdf.set_font("Arial", "", 11)
    texto = f"""
    Entre FRANCISCO JOSÉ BARRAGÁN BARRAGÁN (Consultor) y {datos_pdf['nombre']} (Cliente), C.C. {datos_pdf['cedula']}.
    
    1. OBJETO: Gestión técnica de {datos_pdf['tramite']} ante {datos_pdf['accionado']}.
    2. AVISO LEGAL: El consultor no es abogado. Servicio técnico/estratégico (RUT 7490).
    3. VALOR TOTAL: ${datos_pdf['valor']:,.2f} COP.
    """
    pdf.multi_cell(0, 10, texto)
    return pdf.output(dest='S')

# --- INTERFAZ ---
st.sidebar.title("🚀 Barragán Legal-Tech")
menu = st.sidebar.radio("Menú", ["Solicitar Servicio", "Portal Clientes", "Nuevo Contrato (Admin)", "Seguimiento (Admin)"])

# --- MÓDULO NUEVO: HACER PEDIDO (PARA CLIENTES) ---
if menu == "Solicitar Servicio":
    st.header("📲 Solicita tu Asesoría")
    st.write("Completa los datos y te contactaremos por WhatsApp de inmediato.")
    
    with st.form("form_pedido"):
        nombre_p = st.text_input("Tu Nombre Completo")
        contacto_p = st.text_input("Tu WhatsApp o Correo")
        servicio_p = st.selectbox("Servicio que necesitas", 
                                ["Ajustes Razonables (Ley 1618)", 
                                 "Borrados de DataCrédito", 
                                 "Derecho de Petición Especializado",
                                 "Consultoría General"])
        detalles_p = st.text_area("Cuéntanos brevemente tu caso")
        
        enviar_p = st.form_submit_button("Enviar Pedido a WhatsApp")
        
        if enviar_p:
            if nombre_p and contacto_p:
                # Crear mensaje para WhatsApp
                mensaje = f"¡Hola Francisco! Nuevo pedido de servicio:\n\n" \
                          f"👤 *Cliente:* {nombre_p}\n" \
                          f"📧 *Contacto:* {contacto_p}\n" \
                          f"🛠 *Servicio:* {servicio_p}\n" \
                          f"📝 *Detalles:* {detalles_p}"
                
                # Codificar para URL
                mensaje_url = urllib.parse.quote(mensaje)
                wa_link = f"https://wa.me/573116651518?text={mensaje_url}"
                
                st.success("✅ ¡Resumen generado! Haz clic abajo para enviarlo.")
                st.link_button("🚀 Enviar por WhatsApp", wa_link)
            else:
                st.error("Por favor llena los campos obligatorios.")

# --- MÓDULO: CONSULTA CLIENTES ---
elif menu == "Portal Clientes":
    st.header("🔍 Consulta tu Proceso")
    id_c = st.text_input("Cédula del titular", type="password")
    if st.button("Buscar"):
        conn = sqlite3.connect('consultoria.db')
        res = pd.read_sql_query("SELECT estado, avances, tipo_tramite FROM contratos WHERE cedula = ?", conn, params=(id_c,))
        conn.close()
        if not res.empty:
            st.info(f"Trámite: {res['tipo_tramite'][0]}")
            st.success(f"Estado: {res['estado'][0]}")
            st.warning(f"Avance: {res['avances'][0]}")
        else:
            st.error("No se encontró información.")

# --- MÓDULO: ADMIN NUEVO CONTRATO ---
elif menu == "Nuevo Contrato (Admin)":
    st.header("✍️ Registrar Nuevo Contrato")
    with st.form("admin_contrato"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Nombre Cliente")
            ced = st.text_input("Cédula")
            tr = st.text_input("Trámite")
        with c2:
            acc = st.text_input("Accionado")
            val = st.number_input("Valor", min_value=0)
        
        if st.form_submit_button("Guardar y Generar PDF"):
            n_con = f"FB-{datetime.now().strftime('%M%S')}"
            fec = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect('consultoria.db')
            c = conn.cursor()
            c.execute("INSERT INTO contratos (numero_contrato, nombre_cliente, cedula, tipo_tramite, accionado, valor, estado, avances, fecha_creacion) VALUES (?,?,?,?,?,?,?,?,?)",
                      (n_con, n, ced, tr, acc, val, "Apertura", "Iniciado", fec))
            conn.commit()
            conn.close()
            
            pdf_b = generar_pdf_contrato({"numero": n_con, "nombre": n, "cedula": ced, "tramite": tr, "accionado": acc, "valor": val})
            st.download_button("📥 Descargar PDF", pdf_b, f"Contrato_{n}.pdf", "application/pdf")

# --- MÓDULO: ADMIN SEGUIMIENTO ---
elif menu == "Seguimiento (Admin)":
    st.header("📋 Panel Administrativo")
    conn = sqlite3.connect('consultoria.db')
    df = pd.read_sql_query("SELECT * FROM contratos", conn)
    conn.close()
    st.dataframe(df)