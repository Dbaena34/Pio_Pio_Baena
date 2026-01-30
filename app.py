import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from modules import utils as util

from modules.mod1 import render_produccion
from modules.mod2 import render_stock




# Cargar el logo (ruta relativa al directorio desde donde ejecutas streamlit)
st.set_page_config(page_title="Pio Pio Baena", page_icon="images/Logo.png", layout="wide")
col_title, col_logo = st.columns([6,2])
with col_title:
    st.title("Pio Pio Baena - Gestión Avícola")
with col_logo:
    util.show_logo(width=90)
#util.set_custom_style()
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
    st.header("🚚 Gestión de Ventas y Pedidos")
    st.write("Registra y gestiona las ventas y pedidos de insumos y productos.")
    subtabs = st.tabs(["🛒 Pedidos", "🚚 Ventas"]) 
    with subtabs[0]: 
        st.header("🛒 Gestión de Pedidos")
        st.write("Registra y gestiona los pedidos de insumos y productos.")
        # Contenido específico para la pestaña de Pedidos
        order_item = st.text_input("Nombre del insumo/producto a pedir")
        order_quantity = st.number_input("Cantidad a pedir", min_value=0, step=1)
        if st.button("Registrar Pedido"):
            st.success(f"Pedido registrado: {order_item} - {order_quantity} unidades.")
    with subtabs[1]:        
        st.header("🚚 Gestión de Ventas")
        st.write("Registra las ventas diarias y analiza el rendimiento.")
        # Contenido específico para la pestaña de Ventas
        sale_item = st.text_input("Nombre del producto vendido")
        sale_quantity = st.number_input("Cantidad vendida", min_value=0, step=1)
        sale_price = st.number_input("Precio por unidad", min_value=0.0, step=0.01)
        if st.button("Registrar Venta"):
            total_sale = sale_quantity * sale_price
            st.success(f"Venta registrada: {sale_item} - {sale_quantity} unidades a ${sale_price:.2f} cada una. Total: ${total_sale:.2f}")
                
with tabs[3]:
    st.header("💰 Gestión de Insumos y Pagos")
    st.write("Controla los insumos adquiridos y los pagos realizados.")
    # Contenido específico para la pestaña de Insumos & Pagos
    expense_item = st.text_input("Nombre del insumo/gasto")
    expense_amount = st.number_input("Monto del gasto", min_value=0.0, step=0.01)
    if st.button("Registrar Gasto"):
        st.success(f"Gasto registrado: {expense_item} - ${expense_amount:.2f}")

with tabs[4]:
    st.header("📈 Reportes")
    st.write("Genera reportes detallados sobre producción, ventas y stock.")
    # Contenido específico para la pestaña de Reportes
    if st.button("Generar Reporte de Producción"):
        st.info("Reporte de Producción generado. (Funcionalidad en desarrollo)")
    if st.button("Generar Reporte de Ventas"):
        st.info("Reporte de Ventas generado. (Funcionalidad en desarrollo)")
    if st.button("Generar Reporte de Stock"):
        st.info("Reporte de Stock generado. (Funcionalidad en desarrollo)")