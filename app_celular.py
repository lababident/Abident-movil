import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de la pantalla del celular
st.set_page_config(page_title="ABIDENT Celular", page_icon="🦷", layout="centered")

# 👇 Pega tus llaves secretas aquí 👇
SUPABASE_URL = "https://ougxdvnzjcuenmsedqsl.supabase.co"
SUPABASE_KEY = "sb_publishable_9TFE3xrzyZeQ5qktNdrKSA_Uv-lyFo3"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Diseño de la cabecera
st.title("🦷 ABIDENT")
st.subheader("Estado de Cuenta")
st.markdown("---")

# Función para conectarnos a tu nube
@st.cache_data(ttl=5) # Refresca los datos cada 5 segundos
def obtener_doctores():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/doctores?select=id,nombre", headers=HEADERS)
        return {d['nombre']: d['id'] for d in res.json()}
    except:
        return {}

dict_doctores = obtener_doctores()

# Selector de doctores (como en una app real)
if dict_doctores:
    doc_nom = st.selectbox("Selecciona un Doctor:", ["-- Elige un Doctor --"] + list(dict_doctores.keys()))
    
    if doc_nom != "-- Elige un Doctor --":
        doc_id = dict_doctores[doc_nom]
        
        # Traer órdenes y pagos de la nube
        ord_res = requests.get(f"{SUPABASE_URL}/rest/v1/ordenes?doctor_id=eq.{doc_id}&estado=neq.ELIMINADA&select=id,fecha_ingreso,paciente,monto_total", headers=HEADERS).json()
        pag_res = requests.get(f"{SUPABASE_URL}/rest/v1/pagos?doctor_id=eq.{doc_id}&select=id,fecha,monto", headers=HEADERS).json()
        
        movimientos = []
        for o in ord_res:
            movimientos.append({"Fecha": o.get('fecha_ingreso'), "Concepto": f"Orden #{o.get('id'):04d} - {o.get('paciente')}", "Cargo": o.get('monto_total', 0), "Abono": 0})
        for p in pag_res:
            movimientos.append({"Fecha": p.get('fecha'), "Concepto": f"Abono #{p.get('id'):04d}", "Cargo": 0, "Abono": p.get('monto', 0)})
            
        def fecha_orden(f_str):
            try: return datetime.strptime(f_str, "%d/%m/%Y")
            except: return datetime.min
            
        movimientos.sort(key=lambda x: fecha_orden(x["Fecha"]))
        
        saldo = 0.0
        datos_tabla = []
        for mov in movimientos:
            saldo += mov["Cargo"] - mov["Abono"]
            datos_tabla.append({
                "Fecha": mov["Fecha"],
                "Concepto": mov["Concepto"],
                "Cargo": f"${mov['Cargo']:.2f}" if mov['Cargo'] > 0 else "",
                "Abono": f"${mov['Abono']:.2f}" if mov['Abono'] > 0 else "",
                "Saldo": f"${saldo:.2f}"
            })
        
        # Mostrar Deuda Total con colores llamativos
        st.markdown("<br>", unsafe_allow_html=True)
        if saldo > 0:
            st.error(f"**DEUDA TOTAL: ${saldo:.2f}**")
        else:
            st.success(f"**DEUDA TOTAL: ${saldo:.2f} (Al día)**")
            
        # Mostrar la tabla estilo estado de cuenta
        st.markdown("### Movimientos")
        if datos_tabla:
            df = pd.DataFrame(datos_tabla)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay órdenes ni abonos para este doctor.")
else:
    st.warning("Cargando base de datos o aún no hay doctores registrados...")