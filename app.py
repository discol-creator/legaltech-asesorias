import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# CONFIG
st.set_page_config(page_title="Gestión Contractual", layout="wide")

CONSULTOR_NOMBRE = "Francisco Jose Barragan Barragan"
CONSULTOR_DOC = "CE 7354548"
PAGO_LLAVE = "@francisbarragan"

if not os.path.exists("contratos_generados"):
    os.makedirs("contratos_generados")

if not os.path.exists("contratos_firmados"):
    os.makedirs("contratos_firmados")

# DB INIT
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS casos (
    id TEXT PRIMARY KEY,
    nombre TEXT,
    documento TEXT,
    tipo_tramite TEXT,
    accionado TEXT,
    valor INTEGER,
    estado TEXT,
    token TEXT,
    fecha TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS avances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id TEXT,
    descripcion TEXT,
    fecha TEXT
)
''')

conn.commit()

# FUNCIONES

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    file_path = f"contratos_generados/{data['id']}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>CONTRATO DE PRESTACIÓN DE SERVICIOS</b>", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    contenido = f"""
    Entre {data['nombre']} identificado con C.C {data['documento']} y 
    {CONSULTOR_NOMBRE}, identificado con {CONSULTOR_DOC}, se celebra contrato 
    de prestación de servicios para {data['tipo_tramite']} contra {data['accionado']}.

    Valor del contrato: ${data['valor']:,} COP.

    Forma de pago:
    50% anticipo y 50% contra entrega.
    Pagos vía Llave Bre-B: {PAGO_LLAVE}.

    El consultor no actúa como abogado ni representante judicial.
    """

    elements.append(Paragraph(contenido, styles['Normal']))
    doc.build(elements)

# SIDEBAR

menu = st.sidebar.selectbox(
    "Menú",
    ["Crear Caso", "Gestión Interna", "Consulta Cliente"]
)

# CREAR CASO

if menu == "Crear Caso":
    st.title("Crear Nuevo Caso")

    nombre = st.text_input("Nombre Completo")
    documento = st.text_input("Número de Documento")
    tipo = st.selectbox("Tipo de trámite", [
        "Ajustes Razonables",
        "Eliminación Reporte Negativo",
        "Derecho de Petición"
    ])
    accionado = st.text_input("Entidad accionada")
    valor = st.number_input("Valor del contrato (COP)", min_value=0)

    if st.button("Crear Caso"):
        caso_id = str(uuid.uuid4())
        token = generar_token(documento)
        fecha = datetime.now().strftime("%Y-%m-%d")

        c.execute('''
            INSERT INTO casos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            caso_id, nombre, documento, tipo,
            accionado, valor, "Abierto", token, fecha
        ))
        conn.commit()

        generar_pdf({
            "id": caso_id,
            "nombre": nombre,
            "documento": documento,
            "tipo_tramite": tipo,
            "accionado": accionado,
            "valor": valor
        })

        st.success("Caso creado y contrato generado.")

# GESTIÓN INTERNA

elif menu == "Gestión Interna":
    st.title("Panel de Gestión")

    casos = c.execute("SELECT * FROM casos").fetchall()

    for caso in casos:
        with st.expander(f"{caso[1]} - {caso[3]} - Estado: {caso[6]}"):
            st.write(f"Documento: {caso[2]}")
            st.write(f"Accionado: {caso[4]}")
            st.write(f"Valor: ${caso[5]:,} COP")

            nuevo_estado = st.selectbox(
                "Cambiar Estado",
                ["Abierto", "En Gestión", "Pendiente Firma", "Firmado", "Cerrado"],
                index=["Abierto", "En Gestión", "Pendiente Firma", "Firmado", "Cerrado"].index(caso[6]),
                key=caso[0]
            )

            if st.button("Actualizar Estado", key=caso[0]+"estado"):
                c.execute("UPDATE casos SET estado=? WHERE id=?", (nuevo_estado, caso[0]))
                conn.commit()
                st.success("Estado actualizado")

            avance = st.text_area("Agregar Avance", key=caso[0]+"avance")
            if st.button("Guardar Avance", key=caso[0]+"btnavance"):
                c.execute("INSERT INTO avances (caso_id, descripcion, fecha) VALUES (?, ?, ?)",
                          (caso[0], avance, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Avance guardado")

            firmado = st.file_uploader("Subir contrato firmado", type=["pdf"], key=caso[0]+"file")
            if firmado:
                with open(f"contratos_firmados/{caso[0]}.pdf", "wb") as f:
                    f.write(firmado.read())
                st.success("Contrato firmado almacenado")

# CONSULTA CLIENTE

elif menu == "Consulta Cliente":
    st.title("Consulta de Proceso")

    doc_consulta = st.text_input("Ingrese su número de documento")

    if st.button("Consultar"):
        token = generar_token(doc_consulta)
        caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

        if caso:
            st.write(f"Estado actual: {caso[6]}")
            st.write(f"Tipo de trámite: {caso[3]}")
            st.write(f"Entidad accionada: {caso[4]}")

            avances = c.execute("SELECT descripcion, fecha FROM avances WHERE caso_id=?", (caso[0],)).fetchall()
            for a in avances:
                st.write(f"{a[1]} - {a[0]}")
        else:
            st.error("No se encontró proceso asociado.")
