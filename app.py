import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(page_title="LegalTech Gestión Contractual", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# =====================================
# BASE DE DATOS ESTABLE
# =====================================

conn = sqlite3.connect("database.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS casos (
    consecutivo INTEGER PRIMARY KEY AUTOINCREMENT,
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
    consecutivo INTEGER,
    descripcion TEXT,
    fecha TEXT
)
""")

conn.commit()

# =====================================
# FUNCIONES
# =====================================

ESTADOS = ["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"]

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):

    anticipo = data["valor"] // 2
    saldo = data["valor"] - anticipo

    path = f"contratos_generados/Contrato_{data['consecutivo']}.pdf"
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    style_bold = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold'
    )

    elements = []

    # Título
    elements.append(Paragraph(
        f"<b>CONTRATO No. {data['consecutivo']}-2026</b>",
        style_bold
    ))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(
        "<b>CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA</b>",
        style_bold
    ))
    elements.append(Spacer(1, 0.3 * inch))

    cuerpo = [
        "Entre los suscritos a saber:",
        "",
        f"{data['nombre']}, mayor de edad, identificado(a) con {data['tipo_doc']} No. {data['documento']}, quien actúa en nombre propio y para efectos del presente contrato se denominará EL CONTRATANTE,",
        "",
        f"y {CONSULTOR_NOMBRE}, mayor de edad, identificado con {CONSULTOR_DOC}, profesional con Maestría en Innovación Social, consultor en accesibilidad y gestión estratégica, inscrito en el RUT bajo la actividad económica 7490, quien para efectos del presente contrato se denominará EL CONSULTOR,",
        "",
        "se celebra el presente Contrato de Prestación de Servicios de Consultoría Técnica y Estratégica, el cual se regirá por las siguientes cláusulas:",
        "",
        "<b>PRIMERA. OBJETO</b>",
        f"EL CONSULTOR se obliga a prestar a favor de EL CONTRATANTE servicios de asesoría técnica y estratégica para {data['tipo_tramite']} contra {data['accionado']}.",
        "",
        "<b>SEGUNDA. NATURALEZA DEL SERVICIO</b>",
        "Las partes dejan expresa constancia de que el presente contrato es de naturaleza civil y de prestación de servicios independientes.",
        "EL CONSULTOR no es abogado titulado, no ejercerá representación judicial ni asumirá defensa jurídica.",
        "",
        "<b>CUARTA. VALOR Y FORMA DE PAGO</b>",
        f"El valor total de la consultoría es de ${data['valor']:,} COP.",
        f"Anticipo equivalente al 50%: ${anticipo:,} COP.",
        f"Saldo equivalente al 50%: ${saldo:,} COP.",
        f"Pago vía Llave Bre-B: {LLAVE_PAGO}. Destino: {BANCO}.",
        "",
        "<b>DÉCIMA PRIMERA. DOMICILIO Y LEY APLICABLE</b>",
        "El presente contrato se rige por las leyes de la República de Colombia y fija como domicilio contractual la ciudad de Medellín.",
        "",
        f"Para constancia, se firma en Medellín el {datetime.now().strftime('%d/%m/%Y')}.",
        "",
        "______________________________",
        "EL CONTRATANTE",
        "",
        "______________________________",
        CONSULTOR_NOMBRE,
        "EL CONSULTOR"
    ]

    for linea in cuerpo:
        elements.append(Paragraph(linea, styles["Normal"]))
        elements.append(Spacer(1, 0.15 * inch))

    doc.build(elements)
    return path

# =====================================
# SESIÓN
# =====================================

if "logged" not in st.session_state:
    st.session_state.logged = False

# =====================================
# INTERFAZ PRINCIPAL
# =====================================

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

# =====================================
# CONSULTA PÚBLICA
# =====================================

st.subheader("🔎 Consulta de Proceso")

doc_busqueda = st.text_input("Número de documento")

if st.button("Consultar"):
    token = generar_token(doc_busqueda)
    caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

    if caso:
        st.success("Proceso encontrado")
        st.write("Estado:", caso["estado"])
        st.write("Trámite:", caso["tipo_tramite"])
        st.write("Entidad:", caso["accionado"])
    else:
        st.error("No se encontró proceso")

# =====================================
# PANEL DE GESTIÓN
# =====================================

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
        tipo_tramite = st.selectbox("Tipo de Trámite", [
            "Solicitud de Ajustes Razonables",
            "Reclamación por reporte negativo",
            "Derecho de Petición",
            "Otro"
        ])
        accionado = st.text_input("Entidad Accionada")
        valor = st.number_input("Valor (COP)", min_value=0, step=50000)

        if st.button("Generar Contrato"):
            token = generar_token(documento)

            c.execute("""
            INSERT INTO casos
            (nombre, tipo_doc, documento, tipo_tramite,
             accionado, valor, estado, token, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
            consecutivo = c.lastrowid

            pdf = generar_pdf({
                "consecutivo": consecutivo,
                "nombre": nombre,
                "tipo_doc": tipo_doc,
                "documento": documento,
                "tipo_tramite": tipo_tramite,
                "accionado": accionado,
                "valor": valor
            })

            with open(pdf, "rb") as f:
                st.download_button("📄 Descargar Contrato", f)

            st.success("Contrato generado correctamente")

    # GESTIONAR CASOS
    with tab2:
        casos = c.execute("SELECT * FROM casos ORDER BY consecutivo DESC").fetchall()

        for caso in casos:

            with st.expander(f"Contrato {caso['consecutivo']} - {caso['nombre']}"):

                st.write("Estado:", caso["estado"])

                nuevo_estado = st.selectbox(
                    "Actualizar Estado",
                    ESTADOS,
                    key=f"estado_{caso['consecutivo']}"
                )

                if st.button("Guardar Estado", key=f"btnestado_{caso['consecutivo']}"):
                    c.execute(
                        "UPDATE casos SET estado=? WHERE consecutivo=?",
                        (nuevo_estado, caso["consecutivo"])
                    )
                    conn.commit()
                    st.success("Estado actualizado")

                st.subheader("Subir contrato firmado")

                archivo = st.file_uploader(
                    "PDF firmado",
                    type=["pdf"],
                    key=f"file_{caso['consecutivo']}"
                )

                if archivo:
                    with open(f"contratos_firmados/{caso['consecutivo']}.pdf", "wb") as f:
                        f.write(archivo.read())
                    st.success("Contrato firmado guardado")

                st.subheader("Avances")

                nuevo_avance = st.text_area(
                    "Nuevo avance",
                    key=f"avance_{caso['consecutivo']}"
                )

                if st.button("Guardar Avance", key=f"btnavance_{caso['consecutivo']}"):
                    c.execute(
                        "INSERT INTO avances (consecutivo, descripcion, fecha) VALUES (?, ?, ?)",
                        (caso["consecutivo"], nuevo_avance, datetime.now().strftime("%Y-%m-%d"))
                    )
                    conn.commit()
                    st.success("Avance guardado")

                avances = c.execute(
                    "SELECT * FROM avances WHERE consecutivo=?",
                    (caso["consecutivo"],)
                ).fetchall()

                for a in avances:
                    st.write(f"{a['fecha']} - {a['descripcion']}")
