import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="Gestión Contractual", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"

# REGISTRAR FUENTE UNICODE
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

# CREAR CARPETAS
os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# BASE DE DATOS
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
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

def obtener_consecutivo():
    c.execute("SELECT MAX(consecutivo) FROM casos")
    result = c.fetchone()[0]
    return 1 if result is None else result + 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    file_path = f"contratos_generados/Contrato_{data['consecutivo']}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>CONTRATO No. {data['consecutivo']:04d}-2026</b>", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    contrato = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre los suscritos a saber:

{data['nombre']}, mayor de edad, identificado(a) con {data['tipo_doc']} No. {data['documento']}, 
quien actúa en nombre propio y para efectos del presente contrato se denominará EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, mayor de edad, identificado con {CONSULTOR_DOC}, profesional con Maestría 
en Innovación Social, inscrito en el RUT 7490, quien se denominará EL CONSULTOR,

se celebra el presente contrato bajo las siguientes cláusulas:

PRIMERA. OBJETO
Prestación de servicios para {data['tipo_tramite']} contra {data['accionado']}.

SEGUNDA. NATURALEZA
Servicio civil independiente. El consultor no es abogado ni actúa como apoderado.

TERCERA. VALOR
Valor total: ${data['valor']:,} COP.

Anticipo 50%: ${data['valor']//2:,} COP.
Saldo 50%: ${data['valor']//2:,} COP.

Pagos vía Llave Bre-B: {LLAVE_PAGO}
Destino: {BANCO}

DÉCIMA PRIMERA. DOMICILIO
Medellín, Colombia.

Para constancia, se firma el {datetime.now().strftime("%d/%m/%Y")}.

EL CONTRATANTE

____________________________

{CONSULTOR_NOMBRE}
"""

    elements.append(Paragraph(contrato.replace("\n", "<br/>"), styles['Normal']))
    doc.build(elements)

    return file_path

# MENÚ

menu = st.sidebar.selectbox("Menú", ["Crear Caso", "Gestión Interna", "Consulta Cliente"])

# CREAR CASO

if menu == "Crear Caso":
    st.title("Crear Nuevo Caso")

    nombre = st.text_input("Nombre Completo del Cliente")
    tipo_doc = st.selectbox("Tipo de Documento", ["Cédula de Ciudadanía", "Cédula de Extranjería", "Pasaporte"])
    documento = st.text_input("Número de Documento")
    tipo_tramite = st.selectbox("Tipo de Trámite", [
        "Solicitud de Ajustes Razonables",
        "Reclamación por reporte negativo",
        "Derecho de Petición",
        "Otro"
    ])
    accionado = st.text_input("Entidad Accionada")
    valor = st.number_input("Valor del Contrato (COP)", min_value=0, step=50000)

    if st.button("Crear y Generar Contrato"):
        consecutivo = obtener_consecutivo()
        caso_id = str(uuid.uuid4())
        token = generar_token(documento)
        fecha = datetime.now().strftime("%Y-%m-%d")

        c.execute('''
            INSERT INTO casos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            caso_id, consecutivo, nombre, tipo_doc,
            documento, tipo_tramite, accionado,
            valor, "Pendiente Firma", token, fecha
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

        with open(pdf_path, "rb") as file:
            st.download_button(
                label="Descargar Contrato para Firma",
                data=file,
                file_name=f"Contrato_{consecutivo}.pdf",
                mime="application/pdf"
            )

        st.success("Contrato generado correctamente.")

# GESTIÓN INTERNA

elif menu == "Gestión Interna":
    st.title("Panel de Gestión")

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

            if st.button("Actualizar Estado", key=caso[0]+"estado"):
                c.execute("UPDATE casos SET estado=? WHERE id=?", (nuevo_estado, caso[0]))
                conn.commit()
                st.success("Estado actualizado")

            avance = st.text_area("Agregar Avance", key=caso[0]+"avance")
            if st.button("Guardar Avance", key=caso[0]+"btn"):
                c.execute("INSERT INTO avances (caso_id, descripcion, fecha) VALUES (?, ?, ?)",
                          (caso[0], avance, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Avance guardado")

# CONSULTA CLIENTE

elif menu == "Consulta Cliente":
    st.title("Consulta de Proceso")

    doc = st.text_input("Ingrese su número de documento")

    if st.button("Consultar"):
        token = generar_token(doc)
        caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

        if caso:
            st.write(f"Estado actual: {caso[8]}")
            st.write(f"Trámite: {caso[5]}")
            st.write(f"Entidad accionada: {caso[6]}")

            avances = c.execute("SELECT descripcion, fecha FROM avances WHERE caso_id=?", (caso[0],)).fetchall()
            for a in avances:
                st.write(f"{a[1]} - {a[0]}")
        else:
            st.error("No se encontró proceso asociado.")
