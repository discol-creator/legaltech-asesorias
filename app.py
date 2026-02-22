import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ==========================
# CONFIGURACIÓN
# ==========================

st.set_page_config(page_title="LegalTech - Gestión Contractual", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# ==========================
# BASE DE DATOS ROBUSTA
# ==========================

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Crear tabla básica
c.execute("""
CREATE TABLE IF NOT EXISTS casos (
    id TEXT PRIMARY KEY,
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

# Verificar si existe columna consecutivo
c.execute("PRAGMA table_info(casos)")
columns = [col[1] for col in c.fetchall()]

if "consecutivo" not in columns:
    c.execute("ALTER TABLE casos ADD COLUMN consecutivo INTEGER")
    conn.commit()

c.execute("""
CREATE TABLE IF NOT EXISTS avances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id TEXT,
    descripcion TEXT,
    fecha TEXT
)
""")

conn.commit()

# ==========================
# FUNCIONES
# ==========================

def obtener_consecutivo():
    try:
        c.execute("SELECT MAX(consecutivo) FROM casos")
        result = c.fetchone()[0]
        return 1 if result is None else result + 1
    except:
        return 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    file_path = f"contratos_generados/Contrato_{data['consecutivo']:04d}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"<b>CONTRATO No. {data['consecutivo']:04d}-2026</b>",
        styles['Title']
    ))
    elements.append(Spacer(1, 0.3 * inch))

    texto = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre:

{data['nombre']}, identificado(a) con {data['tipo_doc']} No. {data['documento']}, 
EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, identificado con {CONSULTOR_DOC}, EL CONSULTOR.

PRIMERA. OBJETO
{data['tipo_tramite']} contra {data['accionado']}.

CUARTA. VALOR
Valor total: ${data['valor']:,} COP.
Anticipo 50%: ${data['valor']//2:,} COP.
Saldo 50%: ${data['valor']//2:,} COP.

Pago vía Llave Bre-B: {LLAVE_PAGO}
Destino: {BANCO}

Firmado en Medellín el {datetime.now().strftime("%d/%m/%Y")}.
"""

    elements.append(Paragraph(texto.replace("\n", "<br/>"), styles["Normal"]))
    doc.build(elements)
    return file_path

# ==========================
# SESIÓN SIMPLE
# ==========================

if "logged" not in st.session_state:
    st.session_state.logged = False

# ==========================
# INTERFAZ PRINCIPAL
# ==========================

st.title("Gestión Contractual")

col1, col2 = st.columns([3,1])

with col2:
    if not st.session_state.logged:
        if st.button("🔐 Iniciar sesión"):
            st.session_state.show_login = True
    else:
        if st.button("Cerrar sesión"):
            st.session_state.logged = False

# LOGIN
if "show_login" in st.session_state and not st.session_state.logged:
    clave = st.text_input("Clave de acceso", type="password")
    if st.button("Ingresar"):
        if clave == CLAVE_ADMIN:
            st.session_state.logged = True
            st.success("Acceso concedido")
        else:
            st.error("Clave incorrecta")

# ==========================
# CONSULTA PÚBLICA (SIEMPRE VISIBLE)
# ==========================

st.header("Consulta de Proceso")

doc_busqueda = st.text_input("Ingrese su número de documento")

if st.button("Consultar"):
    token = generar_token(doc_busqueda)
    caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

    if caso:
        st.success("Proceso encontrado")
        st.write("Estado:", caso[7])
        st.write("Trámite:", caso[4])
        st.write("Entidad:", caso[5])
    else:
        st.error("No se encontró proceso asociado.")

# ==========================
# PANEL DE GESTIÓN (SOLO SI LOGEADO)
# ==========================

if st.session_state.logged:

    st.divider()
    st.header("Panel de Gestión")

    st.subheader("Crear Nuevo Caso")

    nombre = st.text_input("Nombre Completo")
    tipo_doc = st.selectbox("Tipo Documento", [
        "Cédula de Ciudadanía",
        "Cédula de Extranjería",
        "Pasaporte"
    ])
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
        INSERT INTO casos
        (id, nombre, tipo_doc, documento, tipo_tramite, accionado, valor, estado, token, fecha, consecutivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            caso_id,
            nombre,
            tipo_doc,
            documento,
            tipo_tramite,
            accionado,
            valor,
            "Pendiente Firma",
            token,
            datetime.now().strftime("%Y-%m-%d"),
            consecutivo
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
                file_name=f"Contrato_{consecutivo:04d}.pdf"
            )

        st.success("Contrato generado correctamente")

    # LISTADO
    st.subheader("Casos Registrados")

    casos = c.execute("SELECT consecutivo, nombre, estado FROM casos ORDER BY consecutivo DESC").fetchall()

    for caso in casos:
        st.write(f"Contrato {caso[0]:04d} - {caso[1]} - {caso[2]}")
