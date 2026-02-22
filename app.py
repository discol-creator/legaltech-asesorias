import streamlit as st
import sqlite3
import uuid
import os
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(page_title="LegalTech Gestión", layout="wide")

CONSULTOR_NOMBRE = "FRANCISCO JOSÉ BARRAGÁN BARRAGÁN"
CONSULTOR_DOC = "CE 7354548"
LLAVE_PAGO = "@francisbarragan"
BANCO = "Banco de Bogotá"
CLAVE_ADMIN = "Francis2026Secure"

os.makedirs("contratos_generados", exist_ok=True)
os.makedirs("contratos_firmados", exist_ok=True)

# =====================================
# BASE DE DATOS ROBUSTA
# =====================================

conn = sqlite3.connect("database.db", check_same_thread=False)
conn.row_factory = sqlite3.Row  # 🔥 CLAVE: acceso por nombre
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

# =====================================
# FUNCIONES
# =====================================

def obtener_consecutivo():
    c.execute("SELECT COALESCE(MAX(consecutivo),0) as maximo FROM casos")
    return c.fetchone()["maximo"] + 1

def generar_token(documento):
    return hashlib.sha256(documento.encode()).hexdigest()

def generar_pdf(data):
    anticipo = data["valor"] // 2
    saldo = data["valor"] - anticipo

    texto = f"""
CONTRATO No. {data['consecutivo']:04d}-2026

CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA TÉCNICA Y ESTRATÉGICA

Entre los suscritos:

{data['nombre']}, mayor de edad, identificado(a) con {data['tipo_doc']} No. {data['documento']}, quien actúa en nombre propio y se denomina EL CONTRATANTE,

y

{CONSULTOR_NOMBRE}, identificado con {CONSULTOR_DOC}, inscrito en RUT 7490, quien se denomina EL CONSULTOR.

PRIMERA. OBJETO
Prestación de servicios para {data['tipo_tramite']} contra {data['accionado']}.

CUARTA. VALOR
Valor total: ${data['valor']:,} COP.
Anticipo 50%: ${anticipo:,} COP.
Saldo 50%: ${saldo:,} COP.

Pago vía Llave Bre-B: {LLAVE_PAGO}
Destino: {BANCO}.

Firmado en Medellín el {datetime.now().strftime("%d/%m/%Y")}.
"""

    path = f"contratos_generados/Contrato_{data['consecutivo']:04d}.pdf"
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(texto.replace("\n", "<br/>"), styles["Normal"]))
    doc.build(elements)
    return path

# =====================================
# SESIÓN
# =====================================

if "logged" not in st.session_state:
    st.session_state.logged = False

# =====================================
# INTERFAZ
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

doc_busqueda = st.text_input("Ingrese su número de documento")

if st.button("Consultar proceso"):
    token = generar_token(doc_busqueda)
    caso = c.execute("SELECT * FROM casos WHERE token=?", (token,)).fetchone()

    if caso:
        st.success("Proceso encontrado")
        st.write("Estado:", caso["estado"])
        st.write("Trámite:", caso["tipo_tramite"])
        st.write("Entidad:", caso["accionado"])
    else:
        st.error("No se encontró proceso asociado.")

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
                st.download_button("📄 Descargar Contrato", f, file_name=os.path.basename(pdf))

            st.success("Contrato generado correctamente")

    # GESTIONAR CASOS
    with tab2:
        casos = c.execute("SELECT * FROM casos ORDER BY consecutivo DESC").fetchall()

        for caso in casos:
            consecutivo = caso["consecutivo"] or 0

            with st.expander(f"Contrato {int(consecutivo):04d} - {caso['nombre']}"):

                st.write("Estado actual:", caso["estado"])

                nuevo_estado = st.selectbox(
                    "Actualizar Estado",
                    ["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"],
                    index=["Pendiente Firma", "Firmado", "En Gestión", "Cerrado"].index(caso["estado"]),
                    key=caso["id"]
                )

                if st.button("Guardar Estado", key="estado"+caso["id"]):
                    c.execute("UPDATE casos SET estado=? WHERE id=?", (nuevo_estado, caso["id"]))
                    conn.commit()
                    st.success("Estado actualizado")

                st.subheader("Subir contrato firmado")
                archivo = st.file_uploader("Adjuntar PDF firmado", type=["pdf"], key="file"+caso["id"])

                if archivo:
                    with open(f"contratos_firmados/{caso['id']}.pdf", "wb") as f:
                        f.write(archivo.read())
                    st.success("Contrato firmado guardado")

                st.subheader("Avances")
                nuevo_avance = st.text_area("Nuevo avance", key="avance"+caso["id"])

                if st.button("Guardar Avance", key="btn"+caso["id"]):
                    c.execute("INSERT INTO avances (caso_id, descripcion, fecha) VALUES (?, ?, ?)",
                              (caso["id"], nuevo_avance, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Avance guardado")

                avances = c.execute("SELECT * FROM avances WHERE caso_id=?", (caso["id"],)).fetchall()

                for a in avances:
                    st.write(f"{a['fecha']} - {a['descripcion']}")
