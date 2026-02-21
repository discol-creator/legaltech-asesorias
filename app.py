import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS PERSONALIZADO (Minimalismo Moderno) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9; }
    h1 { color: #0f172a; font-weight: 600; letter-spacing: -1.5px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #0f172a; color: white; border: none; padding: 0.7rem; font-weight: 600; }
    .stButton>button:hover { background-color: #334155; transform: translateY(-1px); }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE PDF MINIMALISTA ---
class MinimalPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(15, 23, 42) # Azul Medianoche
        self.cell(0, 10, "FRANCISCO BARRAGÁN", ln=True, align="L")
        self.set_font("Arial", "", 9)
        self.set_text_color(100, 116, 139) # Gris Slate
        self.cell(0, 5, "Consultoría Técnica en Innovación Social & Accesibilidad", ln=True, align="L")
        self.cell(0, 5, "RUT Actividad 7490 | Medellín, Colombia", ln=True, align="L")
        self.ln(10)
        self.set_draw_color(226, 232, 240)
        self.line(10, 35, 200, 35) # Línea divisoria sutil
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "I", 8)
        self.set_text_color(148, 163, 184)
        self.multi_cell(0, 5, "Este documento es una consultoría técnica estratégica. No constituye representación jurídica ni defensa legal reservada a abogados titulados.", align="C")

def generar_pdf_premium(datos):
    pdf = MinimalPDF()
    pdf.add_page()
    
    # Título del Contrato
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, f"ORDEN DE SERVICIO Y CONTRATO No. {datos['numero']}", ln=True)
    pdf.ln(5)

    # Cuerpo del Contrato
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(51, 65, 85)
    
    contenido = [
        ("FECHA DE EMISIÓN", datos['fecha']),
        ("CLIENTE", datos['nombre']),
        ("IDENTIFICACIÓN", datos['cedula']),
        ("TRÁMITE", datos['tramite']),
        ("ENTIDAD (ACCIONADO)", datos['accionado'])
    ]

    for label, value in contenido:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(45, 8, f"{label}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, str(value), ln=1)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "ACUERDO DE SERVICIOS", ln=True)
    pdf.set_font("Arial", "", 10)
    
    clausulas = (
        f"1. OBJETO: El consultor se compromete a realizar la gestión técnica estratégica del proceso "
        f"de {datos['tramite']} buscando la garantía de derechos y ajustes razonables.\n\n"
        f"2. HONORARIOS: El valor total del servicio se pacta en ${datos['valor']:,.0f} COP. "
        f"Se cancelará un 50% (${datos['valor']/2:,.0f}) como anticipo y el saldo contra entrega.\n\n"
        f"3. ALCANCE TÉCNICO: El cliente acepta que Francisco Barragán actúa bajo la actividad 7490 "
        f"del RUT como experto técnico. Toda gestión judicial que requiera abogado titulado será "
        f"responsabilidad del cliente o tratada en acuerdo aparte."
    )
    pdf.multi_cell(0, 7, clausulas)

    # Firmas
    pdf.ln(30)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.line(120, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 10, "EL CONSULTOR", ln=0, align="C")
    pdf.cell(90, 10, "EL CLIENTE", ln=1, align="C")
    
    return pdf.output(dest='S')

# --- INICIALIZAR DB ---
conn = sqlite3.connect('consultoria.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS contratos
             (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
              tramite TEXT, accionado TEXT, valor REAL, estado TEXT, avances TEXT, fecha TEXT)''')
conn.commit()

# --- INTERFAZ ---
with st.sidebar:
    st.title("⚖️ Barragán Tech")
    menu = st.radio("Navegación", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])

if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    st.markdown("Gestión técnica para el cumplimiento de tus derechos.")
    with st.container():
        n = st.text_input("Tu Nombre")
        w = st.text_input("WhatsApp")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Detalles")
        if st.button("Enviar Pedido"):
            msg = f"Hola Francisco! Nuevo pedido de {n}. Servicio: {s}. Detalles: {d}"
            st.markdown(f'<a href="https://wa.me/573116651518?text={urllib.parse.quote(msg)}" target="_blank">🚀 Confirmar en WhatsApp</a>', unsafe_allow_html=True)

elif menu == "🔍 Consultar":
    st.title("Seguimiento")
    cc = st.text_input("Cédula", type="password")
    if st.button("Consultar"):
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        if not df.empty:
            st.success(f"Estado: {df['estado'][0]}")
            st.info(f"Avance: {df['avances'][0]}")
        else: st.error("No encontrado.")

elif menu == "🔒 Admin":
    if st.sidebar.text_input("Clave", type="password") == "1234":
        st.title("Panel de Control")
        with st.form("nuevo"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Cliente")
            ced = c1.text_input("Cédula")
            tra = c2.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
            val = c2.number_input("Valor", min_value=0)
            acc = st.text_input("Entidad")
            if st.form_submit_button("Generar Contrato"):
                fec = datetime.now().strftime("%Y-%m-%d")
                num = f"FB-{datetime.now().strftime('%y%m%d%H')}"
                c.execute("INSERT INTO contratos (numero, nombre, cedula, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?)",
                          (num, nom, ced, tra, acc, val, "Abierto", "Iniciado", fec))
                conn.commit()
                pdf = generar_pdf_premium({"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "accionado":acc, "valor":val, "fecha":fec})
                st.download_button("📥 Descargar PDF Minimalista", pdf, f"Contrato_{nom}.pdf", "application/pdf")
