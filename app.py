import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import urllib.parse
import io

# --- CONFIGURACIÓN DE SEGURIDAD ---
CLAVE_ADMIN_REAL = "1234" 
APP_URL = "https://tu-app-barragan.streamlit.app"

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Barragán Consultoría", layout="centered", page_icon="⚖️")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 600; padding: 0.7rem; }
    .stLinkButton>a { width: 100% !important; border-radius: 10px !important; text-align: center !important; font-weight: 600 !important; background-color: #25d366 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (REPARACIÓN AUTOMÁTICA) ---
def init_db():
    conn = sqlite3.connect('consultoria.db', check_same_thread=False)
    c = conn.cursor()
    
    # 1. Crear tabla con la estructura completa si no existe
    c.execute('''CREATE TABLE IF NOT EXISTS contratos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nombre TEXT, cedula TEXT, 
                  telefono TEXT, tramite TEXT, accionado TEXT, valor REAL, 
                  estado TEXT, avances TEXT, fecha TEXT)''')
    
    # 2. MIGRACIÓN FORZOSA: Verificar si la columna 'telefono' existe
    c.execute("PRAGMA table_info(contratos)")
    columnas = [col[1] for col in c.fetchall()]
    
    if 'telefono' not in columnas:
        # Si no existe, la añadimos para que no de error
        try:
            c.execute("ALTER TABLE contratos ADD COLUMN telefono TEXT DEFAULT ''")
            conn.commit()
        except:
            pass # Si ya existía por algún motivo, ignorar
            
    conn.close()

init_db()

# --- MÓDULO PDF ---
def generar_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FRANCISCO BARRAGÁN - ORDEN DE SERVICIO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for k, v in datos.items():
        pdf.cell(50, 10, f"{k.capitalize()}:", ln=0)
        pdf.cell(0, 10, str(v), ln=1)
    return pdf.output(dest='S')

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("⚖️ Barragán Admin")
    menu = st.radio("Menú", ["✨ Solicitar", "🔍 Consultar", "🔒 Admin"])
    if st.session_state['autenticado']:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# --- MÓDULO SOLICITAR ---
if menu == "✨ Solicitar":
    st.title("Inicia tu Proceso")
    with st.container():
        n = st.text_input("Nombre Completo")
        tel_cliente = st.text_input("Tu WhatsApp (Ej: +57311...)")
        s = st.selectbox("Servicio", ["Ajustes Razonables", "Borrados", "Peticiones"])
        d = st.text_area("Detalles")
        
        if st.button("Generar Resumen de Pedido"):
            if n and tel_cliente:
                # El mensaje se envía a TU número como administrador
                msg = f"¡Hola Francisco! 👋\nNuevo pedido de servicio:\n\n👤 *{n}*\n📱 WhatsApp: {tel_cliente}\n🛠 Servicio: {s}\n📝 Detalles: {d}"
                wa_link = f"https://wa.me/573116651518?text={urllib.parse.quote(msg)}"
                st.success("✅ Pedido listo para enviar.")
                st.link_button("🚀 ENVIAR AHORA POR WHATSAPP", wa_link)
            else:
                st.error("Por favor completa nombre y teléfono.")

# --- MÓDULO CONSULTAR ---
elif menu == "🔍 Consultar":
    st.title("Estado de tu Proceso")
    cc = st.text_input("Cédula", type="password")
    if st.button("Consultar"):
        conn = sqlite3.connect('consultoria.db')
        df = pd.read_sql_query("SELECT * FROM contratos WHERE cedula=?", conn, params=(cc,))
        conn.close()
        if not df.empty:
            st.success(f"Hola {df['nombre'].iloc[0]}")
            st.info(f"**Estado:** {df['estado'].iloc[0]}")
            st.write(f"**Avance:** {df['avances'].iloc[0]}")
        else: st.error("No se encontró registro.")

# --- MÓDULO ADMIN ---
elif menu == "🔒 Admin":
    if not st.session_state['autenticado']:
        with st.form("login"):
            pw = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar"):
                if pw == CLAVE_ADMIN_REAL:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Clave Incorrecta")
    else:
        st.title("Panel de Control")
        t1, t2 = st.tabs(["📝 Nuevo Proceso", "📊 Seguimiento"])
        
        with t1:
            with st.form("crear_caso", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre")
                ced = c1.text_input("Cédula")
                pho = c2.text_input("Teléfono (con +57)")
                val = c2.number_input("Valor", min_value=0)
                tra = st.selectbox("Trámite", ["Ajustes Razonables", "Borrados", "Peticiones"])
                acc = st.text_input("Entidad")
                
                if st.form_submit_button("Registrar y Generar PDF"):
                    num = f"FB-{datetime.now().strftime('%y%m%d%H%M')}"
                    fec = datetime.now().strftime("%Y-%m-%d")
                    
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    # Aquí insertamos los 10 campos exactamente como están en la tabla
                    cur.execute("INSERT INTO contratos (numero, nombre, cedula, telefono, tramite, accionado, valor, estado, avances, fecha) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (num, nom, ced, pho, tra, acc, val, "Apertura", "Iniciado", fec))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Caso guardado en la base de datos.")
                    pdf_data = {"numero":num, "nombre":nom, "cedula":ced, "tramite":tra, "valor":val, "fecha":fec}
                    pdf = generar_pdf(pdf_data)
                    st.download_button("📥 Descargar PDF", pdf, f"Contrato_{nom}.pdf", "application/pdf")

        with t2:
            conn = sqlite3.connect('consultoria.db')
            df_admin = pd.read_sql_query("SELECT * FROM contratos", conn)
            conn.close()
            if not df_admin.empty:
                st.dataframe(df_admin)
                idx = st.selectbox("Seleccione ID del proceso", df_admin['id'])
                n_est = st.selectbox("Nuevo Estado", ["En Proceso", "Pendiente Entidad", "Finalizado"])
                n_av = st.text_area("Describa el avance")
                
                if st.button("Actualizar Cliente"):
                    conn = sqlite3.connect('consultoria.db')
                    cur = conn.cursor()
                    cur.execute("UPDATE contratos SET estado=?, avances=? WHERE id=?", (n_est, n_av, idx))
                    conn.commit()
                    conn.close()
                    
                    # Notificar por WA
                    sel = df_admin[df_admin['id'] == idx].iloc[0]
                    notif = f"Hola {sel['nombre']}, tu proceso de {sel['tramite']} tiene un avance:\n\n*Estado:* {n_est}\n*Detalle:* {n_av}"
                    wa_notif = f"https://wa.me/{sel['telefono']}?text={urllib.parse.quote(notif)}"
                    st.link_button("📲 NOTIFICAR POR WHATSAPP", wa_notif)
