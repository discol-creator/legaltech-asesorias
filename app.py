import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

# ========================
# CONFIGURACIÓN GENERAL
# ========================

st.set_page_config(page_title="LegalTech Gestión Contractual", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# ========================
# BASE DE DATOS SEGURA
# ========================

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS casos (
    id TEXT PRIMARY KEY,
    consecutivo INTEGER,
    nombre TEXT,
    tipo_doc TEXT,
    documento TEXT,
    tipo_tramite TEXT,
    accionado TEXT,
    valor INTEGER,
    estado TEXT,
    token TEXT,
    fecha TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS avances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id TEXT,
    descripcion TEXT,
    fecha TEXT
)
""")

conn.commit()

# ========================
# FUNCIONES
# ========================

def obtener_consecutivo():
    c.execute("SELECT COALESCE(MAX(consecutivo),0) FROM casos")
    return c.fetchone()[0] + 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    file_path = f"contratos_generados/Contrato_{data['consecutivo']}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>CONTRATO No. {data['consecutivo']:04d}-2026</b>", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    texto = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre los suscritos:

{data['nombre']}, identificado(a) con {data['tipo_doc']} No. {data['documento']}, 
quien se denominará EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, identificado con {CONSULTOR_DOC}, 
inscrito en RUT 7490, quien se denominará EL CONSULTOR,

PRIMERA. OBJETO
{data['tipo_tramite']} contra {data['accionado']}.

CUARTA. VALOR
Valor total: ${data['valor']:,} COP.
Anticipo 50%: ${data['valor']//2:,} COP.
Saldo 50%: ${data['valor']//2:,} COP.

Pago vía Llave Bre-B: {LLAVE_PAGO}
Destino: {BANCO}

El consultor no ejerce representación judicial.

Firmado en Medellín el {datetime.now().strftime("%d/%m/%Y")}.
"""

    elements.append(Paragraph(texto.replace("\n", "<br/>"), styles["Normal"]))
    doc.build(elements)

    return file_path

# ========================
# AUTENTICACIÓN
# ========================

if "auth" not in st.session_state:
    st.session_state.auth = False

menu = st.sidebar.radio("Menú", ["Consulta Pública", "Panel Gestión"])

if menu == "Panel Gestión":
    if not st.session_state.auth:
        clave = st.sidebar.text_input("Clave de acceso", type="password")
        if st.sidebar.button("Ingresar"):
            if clave == CLAVE_ADMIN:
                st.session_state.auth = True
                st.success("Acceso concedido")
            else:
                st.error("Clave incorrecta")
        st.stop()

# ========================
# CREAR CASO (PROTEGIDO)
# ========================

if menu == "Panel Gestión" and st.session_state.auth:

    st.header("Crear Nuevo Caso")

    nombre = st.text_input("Nombre Completo")
    tipo_doc = st.selectbox("Tipo Documento", ["Cédula de Ciudadanía", "Cédula de Extranjería", "Pasaporte"])
    documento = st.text_input("Número Documento")
    tipo_tramite = st.selectbox("Tipo de Trámite", [
        "Solicitud de Ajustes Razonables",
        "Reclamación reporte negativo",
        "Derecho de Petición",
        "Otro"
    ])
    accionado = st.text_input("Entidad Accionada")
    valor = st.number_input("Valor (COP)", min_value=0, step=50000)

    if st.button("Generar Contrato"):
        consecutivo = obtener_consecutivo()
        caso_id = str(uuid.uuid4())
        token = generar_token(documento)

        c.execute("""
        INSERT INTO casos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            caso_id,
            consecutivo,
            nombre,
            tipo_doc,
            documento,
            tipo_tramite,
            accionado,
            valor,
            "Pendiente Firma",
            token,
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()

        pdf_path = generar_pdf({
            "consecutivo": consecutivo,
            "nombre": nombre,
            "tipo_doc": tipo_doc,
            "documento": documento,
            "tipo_tramite": tipo_tramite,
            "accionado": accionado,
            "valor": valor
        })

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Descargar Contrato",
                f,
                file_name=f"Contrato_{consecutivo}.pdf"
            )

        st.success("Contrato generado correctamente")

    # GESTIÓN DE CASOS
    st.header("Gestión de Casos")

    casos = c.execute("SELECT * FROM casos ORDER BY consecutivo DESC").fetchall()

    for caso in casos:
        with st.expander(f"Contrato {caso[1]:04d} - {caso[2]} - {caso[8]}"):
            st.write(f"Documento: {caso[4]}")
            st.write(f"Trámite: {caso[5]}")
            st.write(f"Accionado: {caso[6]}")
            st.write(f"Valor: ${caso[7]:,} COP")

            nuevo_estado = st.selectbox(
                "Estado",
                ["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"],
                index=["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"].index(caso[8]),
                key=caso[0]
            )

            if st.button("Actualizar", key=caso[0]):
                c.execute("UPDATE casos SET estado=? WHERE id=?", (nuevo_estado, caso[0]))
                conn.commit()
                st.success("Estado actualizado")

# ========================
# CONSULTA PÚBLICA
# ========================

if menu == "Consulta Pública":

    st.header("Consulta de Proceso")

    doc = st.text_input("Ingrese su número de documento")

    if st.button("Consultar"):
        token = generar_token(doc)
        caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

        if caso:
            st.write(f"Estado: {caso[8]}")
            st.write(f"Trámite: {caso[5]}")
            st.write(f"Entidad: {caso[6]}")
        else:
            st.error("No se encontró proceso asociado.")
