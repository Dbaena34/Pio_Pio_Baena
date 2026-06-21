import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from modules import utils as util

from modules.mod1 import render_produccion
from modules.mod2 import render_stock
from modules.mod3 import render_ventas
from modules.mod4 import render_insumos_pagos
from modules.mod5 import render_reportes



# Cargar el logo (ruta relativa al directorio desde donde ejecutas streamlit)
st.set_page_config(page_title="Pio Pio Baena", page_icon="images/Logo.png", layout="wide")
col_title, col_logo = st.columns([6,2])
with col_title:
    st.title("Pio Pio Baena - Gestión Avícola")
with col_logo:
    util.show_logo(width=90)
#util.set_custom_style_2()
estilo = st.sidebar.radio("Seleccionar Estilo Visual", ["Original (Verde)", "Cosecha (Cálido)", "Tecno (Limpio)"])

if estilo == "Original (Verde)":
    util.set_custom_style_2()
elif estilo == "Cosecha (Cálido)":
    util.set_harvest_style()
else:
    util.set_techno_agro_style()
#st.divider()

# app.py
tabs = st.tabs([
    "📊 Producción",
    "📦 Stock",
    "🚚 Ventas",
    "💰 Insumos y Pagos",
    "📈 Reportes"
])

with tabs[0]:
    render_produccion()
with tabs[1]:
    render_stock()
with tabs[2]:
    render_ventas()
with tabs[3]:
    render_insumos_pagos()
# En tabs[4] (Reportes)
with tabs[4]:
    render_reportes()