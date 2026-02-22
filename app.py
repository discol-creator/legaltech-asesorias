import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ==============================
# CONFIG
# ==============================

st.set_page_config(page_title="LegalTech Gestión", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# ==============================
# BASE DE DATOS
# ==============================

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

# ==============================
# FUNCIONES
# ==============================

def obtener_consecutivo():
    c.execute("SELECT COALESCE(MAX(consecutivo),0) FROM casos")
    return c.fetchone()[0] + 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_contrato_texto(data):
    anticipo = data["valor"] // 2
    saldo = data["valor"] - anticipo

    return f"""
CONTRATO No. {data['consecutivo']:04d}-2026

CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre los suscritos a saber:

{data['nombre']}, mayor de edad, identificado(a) con {data['tipo_doc']} No. {data['documento']}, quien actúa en nombre propio y para efectos del presente contrato se denominará EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, mayor de edad, identificado con {CONSULTOR_DOC}, profesional con Maestría en Innovación Social, consultor en accesibilidad y gestión estratégica, inscrito en el RUT bajo la actividad económica 7490, quien para efectos del presente contrato se denominará EL CONSULTOR,

se celebra el presente Contrato de Prestación de Servicios de Consultoría Técnica y Estratégica, el cual se regirá por las siguientes cláusulas:

PRIMERA. OBJETO
EL CONSULTOR se obliga a prestar servicios de asesoría técnica para {data['tipo_tramite']} contra {data['accionado']}.

SEGUNDA. NATURALEZA DEL SERVICIO
Servicio civil independiente. El consultor no es abogado titulado ni ejerce representación judicial.

CUARTA. VALOR Y FORMA DE PAGO
El valor total del contrato asciende a ${data['valor']:,} COP.

Anticipo 50%: ${anticipo:,} COP.
Saldo 50%: ${saldo:,} COP.

Pago vía Llave Bre-B: {LLAVE_PAGO}
Destino: {BANCO}.

DÉCIMA PRIMERA. DOMICILIO Y LEY APLICABLE
Se firma en Medellín el {datetime.now().strftime("%d/%m/%Y")}.

EL CONTRATANTE

_____________________________

{CONSULTOR_NOMBRE}
EL CONSULTOR
"""

def generar_pdf(data):
    file_path = f"contratos_generados/Contrato_{data['consecutivo']:04d}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    texto = generar_contrato_texto(data)
    elements.append(Paragraph(texto.replace("\n", "<br/>"), styles["Normal"]))
    doc.build(elements)
    return file_path

# ==============================
# SESIÓN
# ==============================

if "logged" not in st.session_state:
    st.session_state.logged = False

# ==============================
# INTERFAZ
# ==============================

st.title("📁 Sistema de Gestión Contractual")

col1, col2 = st.columns([4,1])

with col2:
    if not st.session_state.logged:
        if st.button("🔐 Iniciar sesión"):
            st.session_state.show_login = True
    else:
        if st.button("Cerrar sesión"):
            st.session_state.logged = False

if "show_login" in st.session_state and not st.session_state.logged:
    clave = st.text_input("Clave de acceso", type="password")
    if st.button("Ingresar"):
        if clave == CLAVE_ADMIN:
            st.session_state.logged = True
            st.success("Acceso concedido")
        else:
            st.error("Clave incorrecta")

# ==============================
# CONSULTA PÚBLICA
# ==============================

st.subheader("🔎 Consulta de Proceso")

doc_busqueda = st.text_input("Ingrese su número de documento")

if st.button("Consultar proceso"):
    token = generar_token(doc_busqueda)
    caso = c.execute("SELECT estado, tipo_tramite, accionado FROM casos WHERE token=?", (token,)).fetchone()

    if caso:
        st.success("Proceso encontrado")
        st.write("Estado:", caso[0])
        st.write("Trámite:", caso[1])
        st.write("Entidad:", caso[2])
    else:
        st.error("No se encontró proceso asociado.")

# ==============================
# PANEL DE GESTIÓN
# ==============================

if st.session_state.logged:

    st.divider()
    st.header("⚙️ Panel de Gestión")

    tab1, tab2 = st.tabs(["➕ Crear Caso", "📂 Gestionar Casos"])

    # CREAR CASO
    with tab1:
        nombre = st.text_input("Nombre Completo")
        tipo_doc = st.selectbox("Tipo Documento", [
            "Cédula de Ciudadanía",
            "Cédula de Extranjería",
            "Pasaporte"
        ])
        documento = st.text_input("Número Documento")
        tipo_tramite = st.text_input("Tipo de Trámite")
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
                    "📄 Descargar Contrato",
                    f,
                    file_name=f"Contrato_{consecutivo:04d}.pdf"
                )

            st.success("Contrato generado correctamente")

    # GESTIONAR CASOS
    with tab2:
        casos = c.execute("SELECT * FROM casos ORDER BY consecutivo DESC").fetchall()

        for caso in casos:
            with st.expander(f"Contrato {caso[1]:04d} - {caso[2]}"):
                st.write("Estado actual:", caso[8])
                nuevo_estado = st.selectbox(
                    "Actualizar Estado",
                    ["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"],
                    index=["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"].index(caso[8]),
                    key=caso[0]
                )
                if st.button("Guardar Estado", key=caso[0]+"estado"):
                    c.execute("UPDATE casos SET estado=? WHERE id=?", (nuevo_estado, caso[0]))
                    conn.commit()
                    st.success("Estado actualizado")

                st.subheader("Subir contrato firmado")
                archivo = st.file_uploader("Adjuntar PDF firmado", type=["pdf"], key=caso[0])
                if archivo:
                    with open(f"contratos_firmados/{caso[0]}.pdf", "wb") as f:
                        f.write(archivo.read())
                    st.success("Contrato firmado guardado")

                st.subheader("Avances")
                avance = st.text_area("Nuevo avance", key=caso[0]+"avance")
                if st.button("Guardar Avance", key=caso[0]+"btn"):
                    c.execute("INSERT INTO avances (caso_id, descripcion, fecha) VALUES (?, ?, ?)",
                              (caso[0], avance, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Avance guardado")

                avances = c.execute("SELECT descripcion, fecha FROM avances WHERE caso_id=?", (caso[0],)).fetchall()
                for a in avances:
                    st.write(f"{a[1]} - {a[0]}")
