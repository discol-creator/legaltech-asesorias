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
# CONFIGURACIÓN GENERAL
# ==========================

st.set_page_config(
    page_title="LegalTech - Gestión Contractual",
    layout="wide",
)

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)

# ==========================
# BASE DE DATOS ROBUSTA
# ==========================

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

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
    fecha TEXT,
    consecutivo INTEGER
)
""")

conn.commit()

# Reparar consecutivos NULL si existen
c.execute("SELECT id FROM casos WHERE consecutivo IS NULL")
null_cases = c.fetchall()

if null_cases:
    contador = 1
    for caso in null_cases:
        c.execute("UPDATE casos SET consecutivo=? WHERE id=?", (contador, caso[0]))
        contador += 1
    conn.commit()

# ==========================
# FUNCIONES
# ==========================

def obtener_consecutivo():
    c.execute("SELECT COALESCE(MAX(consecutivo),0) FROM casos")
    return c.fetchone()[0] + 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    file_path = f"contratos_generados/Contrato_{data['consecutivo']:04d}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            f"<b>CONTRATO No. {data['consecutivo']:04d}-2026</b>",
            styles["Title"],
        )
    )
    elements.append(Spacer(1, 0.3 * inch))

    texto = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre:

{data['nombre']}, identificado(a) con {data['tipo_doc']} No. {data['documento']}, 
quien se denominará EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, identificado con {CONSULTOR_DOC}, 
quien se denominará EL CONSULTOR.

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
# SESIÓN
# ==========================

if "logged" not in st.session_state:
    st.session_state.logged = False

# ==========================
# CABECERA PRINCIPAL
# ==========================

st.title("📁 Sistema de Gestión Contractual")

col1, col2 = st.columns([4,1])

with col2:
    if not st.session_state.logged:
        if st.button("🔐 Iniciar sesión"):
            st.session_state.show_login = True
    else:
        if st.button("Cerrar sesión"):
            st.session_state.logged = False

# LOGIN SIMPLE
if "show_login" in st.session_state and not st.session_state.logged:
    clave = st.text_input("Clave de acceso", type="password")
    if st.button("Ingresar"):
        if clave == CLAVE_ADMIN:
            st.session_state.logged = True
            st.success("Acceso concedido")
        else:
            st.error("Clave incorrecta")

# ==========================
# CONSULTA PÚBLICA
# ==========================

st.subheader("🔎 Consulta de Proceso")

doc_busqueda = st.text_input("Ingrese su número de documento")

if st.button("Consultar proceso"):
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
# PANEL DE GESTIÓN
# ==========================

if st.session_state.logged:

    st.divider()
    st.header("⚙️ Panel de Gestión")

    tab1, tab2 = st.tabs(["➕ Crear Caso", "📂 Casos Registrados"])

    # ========= CREAR CASO =========
    with tab1:
        st.subheader("Nuevo Caso")

        colA, colB = st.columns(2)

        with colA:
            nombre = st.text_input("Nombre Completo")
            tipo_doc = st.selectbox("Tipo Documento", [
                "Cédula de Ciudadanía",
                "Cédula de Extranjería",
                "Pasaporte"
            ])
            documento = st.text_input("Número Documento")

        with colB:
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
            (id, nombre, tipo_doc, documento, tipo_tramite, accionado,
             valor, estado, token, fecha, consecutivo)
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
                    "📄 Descargar Contrato",
                    f,
                    file_name=f"Contrato_{consecutivo:04d}.pdf"
                )

            st.success("Contrato generado correctamente")

    # ========= LISTADO =========
    with tab2:
        st.subheader("Listado de Casos")

        casos = c.execute("""
        SELECT consecutivo, nombre, estado, valor
        FROM casos
        ORDER BY COALESCE(consecutivo,0) DESC
        """).fetchall()

        if casos:
            for caso in casos:
                consecutivo = caso[0] if caso[0] else 0
                with st.container():
                    col1, col2, col3, col4 = st.columns([1,3,2,2])
                    col1.write(f"{int(consecutivo):04d}")
                    col2.write(caso[1])
                    col3.write(caso[2])
                    col4.write(f"${caso[3]:,} COP")
        else:
            st.info("No hay casos registrados.")
