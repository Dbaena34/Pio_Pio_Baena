"""
Módulo de Ventas
Gestiona pedidos, despachos y ventas de huevos por canastillas
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Importar la base de datos y repositorios
import sys
sys.path.append('..')
from data.database import db
from data.models import PedidosRepository, ClientesRepository, PreciosRepository, StockRepository


class VentasModule:
    """Clase principal del módulo de ventas"""
    
    def __init__(self):
        self.pedidos_repo = PedidosRepository(db)
        self.clientes_repo = ClientesRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.stock_repo = StockRepository(db)
        self.categorias = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.HUEVOS_POR_CANASTILLA = 30
    
    def render(self):
        """Renderiza la interfaz completa del módulo"""
        st.header("🚚 Gestión de Ventas")
        
        # Crear tabs
        tabs = st.tabs(["🛒 Crear Pedido", "📦 Despachar Pedidos", "📊 Historial de Ventas", "👥 Clientes"])
        
        with tabs[0]:
            self._render_crear_pedido()
        
        with tabs[1]:
            self._render_despachar_pedidos()
        
        with tabs[2]:
            self._render_historial_ventas()
        
        with tabs[3]:
            self._render_gestion_clientes()
    
    def _calcular_canastillas_disponibles(self, stock: Dict) -> Dict:
        """Calcula cuántas canastillas completas hay disponibles por categoría"""
        categorias_db = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
        canastillas = {}
        
        for cat_db, cat_nombre in zip(categorias_db, self.categorias):
            huevos = stock.get(cat_db, 0) or 0
            canastillas[cat_nombre] = huevos // self.HUEVOS_POR_CANASTILLA
            
        return canastillas
    
    def _render_crear_pedido(self):
        """Renderiza el formulario para crear un nuevo pedido"""
        st.subheader("🛒 Crear Nuevo Pedido")
        
        try:
            # Obtener stock y precios
            stock = self.stock_repo.obtener_stock_actual()
            canastillas_disponibles = self._calcular_canastillas_disponibles(stock)
            precios = self.precios_repo.obtener_precio_actual()
            
            if not precios:
                st.error("❌ No hay precios configurados. Configura los precios primero.")
                return
            
            # Mostrar disponibilidad
            st.markdown("### 📦 Disponibilidad de Canastillas")
            cols_disp = st.columns(6)
            
            for col, cat in zip(cols_disp, self.categorias):
                with col:
                    disponibles = canastillas_disponibles[cat]
                    color = "🟢" if disponibles > 5 else "🟡" if disponibles > 0 else "🔴"
                    st.metric(
                        f"{color} {cat}",
                        f"{disponibles}",
                        help=f"{disponibles * self.HUEVOS_POR_CANASTILLA} huevos disponibles"
                    )
            
            st.divider()
            
            # Sección de cliente
            st.markdown("### 👤 Información del Cliente")
            
            col_cliente, col_nuevo = st.columns([3, 1])
            
            with col_cliente:
                clientes = self.clientes_repo.obtener_clientes_activos()
                
                if clientes:
                    cliente_seleccionado = st.selectbox(
                        "Seleccionar cliente",
                        options=[c['id'] for c in clientes],
                        format_func=lambda x: next((c['nombre'] for c in clientes if c['id'] == x), ""),
                        key="select_cliente"
                    )
                else:
                    st.warning("⚠️ No hay clientes registrados")
                    cliente_seleccionado = None
            
            with col_nuevo:
                st.write("")
                st.write("")
                if st.button("➕ Nuevo Cliente", use_container_width=True, key="btn_nuevo_cliente_pedido"):
                    st.session_state['mostrar_form_nuevo_cliente'] = True
            
            # Formulario para nuevo cliente
            if st.session_state.get('mostrar_form_nuevo_cliente', False):
                with st.expander("➕ Registrar Nuevo Cliente", expanded=True):
                    col_nom, col_cont = st.columns(2)
                    
                    with col_nom:
                        nuevo_nombre = st.text_input("Nombre", key="nuevo_cliente_nombre")
                    with col_cont:
                        nuevo_contacto = st.text_input("Teléfono/Contacto", key="nuevo_cliente_contacto")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar Cliente", key="btn_guardar_nuevo_cliente"):
                            if nuevo_nombre:
                                try:
                                    nuevo_id = self.clientes_repo.crear_cliente(
                                        nombre=nuevo_nombre,
                                        contacto=nuevo_contacto if nuevo_contacto else None
                                    )
                                    st.success(f"✅ Cliente '{nuevo_nombre}' creado exitosamente")
                                    st.session_state['mostrar_form_nuevo_cliente'] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            else:
                                st.warning("⚠️ Ingresa el nombre del cliente")
                    
                    with col_btn2:
                        if st.button("❌ Cancelar", key="btn_cancelar_nuevo_cliente"):
                            st.session_state['mostrar_form_nuevo_cliente'] = False
                            st.rerun()
            
            if not cliente_seleccionado:
                st.info("👆 Selecciona o crea un cliente para continuar")
                return
            
            st.divider()
            
            # Sección de pedido
            st.markdown("### 📝 Detalles del Pedido")
            
            # Información de fecha
            col_fecha, col_hora = st.columns(2)
            with col_fecha:
                fecha_pedido = st.date_input(
                    "Fecha del pedido",
                    value=date.today(),
                    key="fecha_pedido"
                )
            with col_hora:
                hora_pedido = st.time_input(
                    "Hora del pedido",
                    value=datetime.now().time(),
                    key="hora_pedido"
                )
            
            st.markdown("**Cantidad de canastillas por categoría:**")
            
            # Inputs de canastillas
            cols_cant = st.columns(6)
            canastillas_pedido = {}
            precios_categoria = {}
            
            categorias_db_precios = ['precio_c', 'precio_b', 'precio_a', 'precio_aa', 'precio_aaa', 'precio_jumbo']
            
            for col, cat, precio_db in zip(cols_cant, self.categorias, categorias_db_precios):
                with col:
                    max_canastillas = canastillas_disponibles[cat]
                    precio_unitario = precios.get(precio_db, 0)
                    precio_canastilla = precio_unitario * self.HUEVOS_POR_CANASTILLA
                    
                    canastillas_pedido[cat] = st.number_input(
                        f"📦 {cat}",
                        min_value=0,
                        max_value=max_canastillas,
                        step=1,
                        value=0,
                        key=f"cant_{cat}",
                        help=f"Disponibles: {max_canastillas} - Precio: ${precio_canastilla:,.0f}/canastilla"
                    )
                    
                    precios_categoria[cat] = precio_canastilla
            
            # Calcular totales
            total_canastillas = sum(canastillas_pedido.values())
            subtotales = {cat: canastillas_pedido[cat] * precios_categoria[cat] for cat in self.categorias}
            total_precio = sum(subtotales.values())
            
            # Mostrar resumen
            if total_canastillas > 0:
                st.markdown("---")
                st.markdown("### 💰 Resumen del Pedido")
                
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    st.markdown("**Cantidades:**")
                    for cat in self.categorias:
                        if canastillas_pedido[cat] > 0:
                            huevos = canastillas_pedido[cat] * self.HUEVOS_POR_CANASTILLA
                            st.write(f"• {cat}: {canastillas_pedido[cat]} canastillas ({huevos} huevos)")
                    st.write(f"**Total: {total_canastillas} canastillas ({total_canastillas * self.HUEVOS_POR_CANASTILLA} huevos)**")
                
                with col_res2:
                    st.markdown("**Valores:**")
                    for cat in self.categorias:
                        if subtotales[cat] > 0:
                            st.write(f"• {cat}: ${subtotales[cat]:,.0f}")
                    st.markdown(f"### **Total: ${total_precio:,.0f}**")
                
                # Ajuste manual de precio
                st.markdown("---")
                col_ajuste1, col_ajuste2 = st.columns([2, 1])
                
                with col_ajuste1:
                    precio_ajustado = st.number_input(
                        "Ajustar precio total (opcional)",
                        min_value=0.0,
                        value=float(total_precio),
                        step=1000.0,
                        key="precio_ajustado",
                        help="Modifica el precio si hay descuentos o ajustes especiales"
                    )
                
                with col_ajuste2:
                    if precio_ajustado != total_precio:
                        diferencia = precio_ajustado - total_precio
                        color = "🟢" if diferencia < 0 else "🔴"
                        st.metric("Ajuste", f"{color} ${diferencia:+,.0f}")
            
            # Observaciones
            observaciones = st.text_area(
                "Observaciones (opcional)",
                placeholder="Ej: Cliente prefiere entrega en la tarde, pedido especial, etc.",
                key="obs_pedido"
            )
            
            # Opciones de guardado
            st.markdown("---")
            col_tipo_pedido, col_btn = st.columns([2, 1])
            
            with col_tipo_pedido:
                tipo_pedido = st.radio(
                    "¿Cómo deseas procesar este pedido?",
                    options=['pendiente', 'despachar_ahora'],
                    format_func=lambda x: '📋 Guardar como pendiente (despachar después)' if x == 'pendiente' else '✅ Despachar inmediatamente',
                    key="tipo_pedido"
                )
            
            with col_btn:
                st.write("")
                st.write("")
                if total_canastillas > 0:
                    if st.button("💾 Procesar Pedido", use_container_width=True, type="primary", key="btn_crear_pedido"):
                        try:
                            # Crear el pedido
                            pedido_id = self.pedidos_repo.crear_pedido(
                                cliente_id=cliente_seleccionado,
                                fecha=fecha_pedido,
                                hora=hora_pedido.strftime("%H:%M:%S"),
                                canastillas_c=canastillas_pedido['C'],
                                canastillas_b=canastillas_pedido['B'],
                                canastillas_a=canastillas_pedido['A'],
                                canastillas_aa=canastillas_pedido['AA'],
                                canastillas_aaa=canastillas_pedido['AAA'],
                                canastillas_jumbo=canastillas_pedido['Jumbo'],
                                precio_total=precio_ajustado if total_canastillas > 0 else total_precio,
                                observaciones=observaciones if observaciones else None
                            )
                            
                            st.success(f"✅ Pedido #{pedido_id} creado exitosamente")
                            
                            # Si se debe despachar inmediatamente
                            if tipo_pedido == 'despachar_ahora':
                                self.pedidos_repo.despachar_pedido(
                                    pedido_id=pedido_id,
                                    fecha=fecha_pedido,
                                    hora=hora_pedido.strftime("%H:%M:%S"),
                                    canastillas_c=canastillas_pedido['C'],
                                    canastillas_b=canastillas_pedido['B'],
                                    canastillas_a=canastillas_pedido['A'],
                                    canastillas_aa=canastillas_pedido['AA'],
                                    canastillas_aaa=canastillas_pedido['AAA'],
                                    canastillas_jumbo=canastillas_pedido['Jumbo'],
                                    observaciones="Despacho inmediato"
                                )
                                st.success(f"✅ Pedido #{pedido_id} despachado exitosamente")
                                st.balloons()
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al crear el pedido: {str(e)}")
                else:
                    st.warning("⚠️ Agrega al menos una canastilla para crear el pedido")
        
        except Exception as e:
            st.error(f"❌ Error al cargar el formulario: {str(e)}")
    
    def _render_despachar_pedidos(self):
        """Renderiza la gestión de despachos"""
        st.subheader("📦 Despachar Pedidos Pendientes")
        
        try:
            # Obtener pedidos pendientes
            pedidos_pendientes = self.pedidos_repo.obtener_pedidos_pendientes()
            
            if pedidos_pendientes:
                st.info(f"📋 Hay {len(pedidos_pendientes)} pedido(s) pendiente(s)")
                
                # Mostrar lista de pedidos
                st.markdown("### 📋 Pedidos Pendientes")
                
                for pedido in pedidos_pendientes:
                    with st.expander(
                        f"📦 Pedido #{pedido['id']} - {pedido['cliente_nombre']} - {pedido['total_canastillas']} canastillas - ${pedido['precio_total']:,.0f}",
                        expanded=False
                    ):
                        col_info, col_detalle = st.columns([1, 1])
                        
                        with col_info:
                            st.markdown("**Información del Cliente:**")
                            st.write(f"👤 **Nombre:** {pedido['cliente_nombre']}")
                            st.write(f"📞 **Contacto:** {pedido.get('cliente_contacto', 'N/A')}")
                            st.write(f"📅 **Fecha:** {pedido['fecha']}")
                            st.write(f"🕐 **Hora:** {pedido['hora']}")
                            if pedido.get('observaciones'):
                                st.write(f"📝 **Obs:** {pedido['observaciones']}")
                        
                        with col_detalle:
                            st.markdown("**Detalle del Pedido:**")
                            categorias_db = ['canastillas_c', 'canastillas_b', 'canastillas_a', 
                                           'canastillas_aa', 'canastillas_aaa', 'canastillas_jumbo']
                            
                            for cat, cat_db in zip(self.categorias, categorias_db):
                                cantidad = pedido.get(cat_db, 0)
                                if cantidad > 0:
                                    huevos = cantidad * self.HUEVOS_POR_CANASTILLA
                                    st.write(f"📦 {cat}: {cantidad} canastillas ({huevos} huevos)")
                            
                            st.markdown(f"### 💰 Total: ${pedido['precio_total']:,.0f}")
                        
                        st.markdown("---")
                        
                        # Botones de acción
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button(f"✅ Despachar", key=f"despachar_{pedido['id']}", use_container_width=True):
                                try:
                                    self.pedidos_repo.despachar_pedido(
                                        pedido_id=pedido['id'],
                                        fecha=date.today(),
                                        hora=datetime.now().strftime("%H:%M:%S"),
                                        canastillas_c=pedido['canastillas_c'],
                                        canastillas_b=pedido['canastillas_b'],
                                        canastillas_a=pedido['canastillas_a'],
                                        canastillas_aa=pedido['canastillas_aa'],
                                        canastillas_aaa=pedido['canastillas_aaa'],
                                        canastillas_jumbo=pedido['canastillas_jumbo'],
                                        observaciones="Despachado"
                                    )
                                    st.success(f"✅ Pedido #{pedido['id']} despachado exitosamente")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        with col_btn2:
                            if st.button(f"✏️ Editar", key=f"editar_{pedido['id']}", use_container_width=True):
                                st.session_state[f'editando_{pedido["id"]}'] = True
                                st.rerun()
                        
                        with col_btn3:
                            if st.button(f"❌ Cancelar", key=f"cancelar_{pedido['id']}", use_container_width=True):
                                try:
                                    self.pedidos_repo.cancelar_pedido(pedido['id'])
                                    st.success(f"✅ Pedido #{pedido['id']} cancelado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        # Formulario de edición
                        if st.session_state.get(f'editando_{pedido["id"]}', False):
                            st.markdown("---")
                            st.markdown("### ✏️ Editar Pedido")
                            
                            cols_edit = st.columns(6)
                            nuevas_cantidades = {}
                            
                            for col, cat, cat_db in zip(cols_edit, self.categorias, categorias_db):
                                with col:
                                    nuevas_cantidades[cat] = st.number_input(
                                        f"{cat}",
                                        min_value=0,
                                        step=1,
                                        value=pedido.get(cat_db, 0),
                                        key=f"edit_{cat}_{pedido['id']}"
                                    )
                            
                            nuevo_total = sum(nuevas_cantidades.values())
                            
                            if nuevo_total > 0:
                                # Obtener precios actuales
                                precios = self.precios_repo.obtener_precio_actual()
                                categorias_db_precios = ['precio_c', 'precio_b', 'precio_a', 
                                                        'precio_aa', 'precio_aaa', 'precio_jumbo']
                                
                                nuevo_precio = sum([
                                    nuevas_cantidades[cat] * precios.get(precio_db, 0) * self.HUEVOS_POR_CANASTILLA
                                    for cat, precio_db in zip(self.categorias, categorias_db_precios)
                                ])
                                
                                st.info(f"📦 Nuevo total: {nuevo_total} canastillas - ${nuevo_precio:,.0f}")
                                
                                col_save, col_cancel = st.columns(2)
                                
                                with col_save:
                                    if st.button("💾 Guardar Cambios", key=f"save_edit_{pedido['id']}"):
                                        try:
                                            self.pedidos_repo.actualizar_pedido(
                                                pedido_id=pedido['id'],
                                                canastillas_c=nuevas_cantidades['C'],
                                                canastillas_b=nuevas_cantidades['B'],
                                                canastillas_a=nuevas_cantidades['A'],
                                                canastillas_aa=nuevas_cantidades['AA'],
                                                canastillas_aaa=nuevas_cantidades['AAA'],
                                                canastillas_jumbo=nuevas_cantidades['Jumbo'],
                                                precio_total=nuevo_precio
                                            )
                                            st.success("✅ Pedido actualizado")
                                            del st.session_state[f'editando_{pedido["id"]}']
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                
                                with col_cancel:
                                    if st.button("❌ Cancelar Edición", key=f"cancel_edit_{pedido['id']}"):
                                        del st.session_state[f'editando_{pedido["id"]}']
                                        st.rerun()
            else:
                st.success("✅ No hay pedidos pendientes")
                st.info("💡 Crea un nuevo pedido en la pestaña 'Crear Pedido'")
        
        except Exception as e:
            st.error(f"❌ Error al cargar pedidos pendientes: {str(e)}")
    
    def _render_historial_ventas(self):
        """Renderiza el historial de ventas"""
        st.subheader("📊 Historial de Ventas")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_inicio = st.date_input(
                "Desde",
                value=date.today() - timedelta(days=30),
                key="hist_ventas_inicio"
            )
        
        with col2:
            fecha_fin = st.date_input(
                "Hasta",
                value=date.today(),
                key="hist_ventas_fin"
            )
        
        try:
            ventas = self.pedidos_repo.obtener_historial_ventas(fecha_inicio, fecha_fin)
            
            if ventas:
                df = pd.DataFrame(ventas)
                
                # Métricas generales
                st.markdown("### 📈 Resumen del Período")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("Total Ventas", len(df))
                
                with col_m2:
                    total_canastillas = df['total_canastillas'].sum()
                    st.metric("Canastillas Vendidas", f"{total_canastillas:,.0f}")
                
                with col_m3:
                    total_huevos = total_canastillas * self.HUEVOS_POR_CANASTILLA
                    st.metric("Huevos Vendidos", f"{total_huevos:,.0f}")
                
                with col_m4:
                    total_ingresos = df['precio_total'].sum()
                    st.metric("Ingresos", f"${total_ingresos:,.0f}")
                
                st.markdown("---")
                
                # Gráficos
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    # Ventas por día
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    ventas_diarias = df.groupby('fecha')['precio_total'].sum().reset_index()
                    
                    fig_ventas = px.line(
                        ventas_diarias,
                        x='fecha',
                        y='precio_total',
                        title='Ingresos por Día',
                        labels={'fecha': 'Fecha', 'precio_total': 'Ingresos ($)'},
                        markers=True
                    )
                    st.plotly_chart(fig_ventas, use_container_width=True)
                
                with col_graf2:
                    # Top clientes
                    top_clientes = df.groupby('cliente_nombre')['precio_total'].sum().sort_values(ascending=False).head(5)
                    
                    fig_clientes = px.bar(
                        x=top_clientes.values,
                        y=top_clientes.index,
                        orientation='h',
                        title='Top 5 Clientes',
                        labels={'x': 'Total Comprado ($)', 'y': 'Cliente'}
                    )
                    st.plotly_chart(fig_clientes, use_container_width=True)
                
                # Tabla detallada
                st.markdown("---")
                st.markdown("### 📋 Detalle de Ventas")
                
                df_display = df[[
                    'id', 'fecha', 'cliente_nombre', 'canastillas_c', 'canastillas_b',
                    'canastillas_a', 'canastillas_aa', 'canastillas_aaa', 'canastillas_jumbo',
                    'total_canastillas', 'precio_total'
                ]].copy()
                
                df_display.columns = [
                    'ID', 'Fecha', 'Cliente', 'C', 'B', 'A', 'AA', 'AAA', 'Jumbo',
                    'Total Can.', 'Total $'
                ]
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Total $": st.column_config.NumberColumn(format="$%,.0f")
                    }
                )
                
                # Exportar
                if st.button("📥 Exportar a CSV", key="btn_exportar_ventas"):
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"ventas_{fecha_inicio}_a_{fecha_fin}.csv",
                        mime="text/csv"
                    )
            
            else:
                st.info("ℹ️ No hay ventas en el período seleccionado")
        
        except Exception as e:
            st.error(f"❌ Error al cargar historial: {str(e)}")
    
    def _render_gestion_clientes(self):
        """Renderiza la gestión de clientes"""
        st.subheader("👥 Gestión de Clientes")
        
        try:
            clientes = self.clientes_repo.obtener_clientes_activos()
            
            if clientes:
                st.info(f"👥 Total de clientes activos: {len(clientes)}")
                
                # Tabla de clientes
                df = pd.DataFrame(clientes)
                df_display = df[['id', 'nombre', 'contacto', 'created_at']].copy()
                df_display.columns = ['ID', 'Nombre', 'Contacto', 'Fecha Registro']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                
                # Editar cliente
                st.markdown("### ✏️ Editar Cliente")
                
                cliente_editar = st.selectbox(
                    "Selecciona el cliente a editar",
                    options=[c['id'] for c in clientes],
                    format_func=lambda x: next((c['nombre'] for c in clientes if c['id'] == x), ""),
                    key="cliente_editar_select"
                )
                
                if cliente_editar:
                    cliente_data = next((c for c in clientes if c['id'] == cliente_editar), None)
                    
                    col_edit1, col_edit2 = st.columns(2)
                    
                    with col_edit1:
                        nuevo_nombre = st.text_input(
                            "Nombre",
                            value=cliente_data['nombre'],
                            key="edit_nombre"
                        )
                    
                    with col_edit2:
                        nuevo_contacto = st.text_input(
                            "Contacto",
                            value=cliente_data.get('contacto', ''),
                            key="edit_contacto"
                        )
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("💾 Guardar Cambios", key="btn_guardar_edit_cliente"):
                            if nuevo_nombre:
                                try:
                                    self.clientes_repo.actualizar_cliente(
                                        cliente_id=cliente_editar,
                                        nombre=nuevo_nombre,
                                        contacto=nuevo_contacto if nuevo_contacto else None
                                    )
                                    st.success("✅ Cliente actualizado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            else:
                                st.warning("⚠️ El nombre es obligatorio")
                    
                    with col_btn2:
                        if st.button("🗑️ Desactivar Cliente", key="btn_desactivar_cliente"):
                            try:
                                self.clientes_repo.desactivar_cliente(cliente_editar)
                                st.success("✅ Cliente desactivado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            
            else:
                st.info("ℹ️ No hay clientes registrados")
            
            # Agregar nuevo cliente
            st.markdown("---")
            st.markdown("### ➕ Agregar Nuevo Cliente")
            
            col_nuevo1, col_nuevo2 = st.columns(2)
            
            with col_nuevo1:
                nombre_nuevo = st.text_input("Nombre", key="nuevo_cliente_nombre_tab")
            
            with col_nuevo2:
                contacto_nuevo = st.text_input("Contacto", key="nuevo_cliente_contacto_tab")
            
            if st.button("💾 Crear Cliente", key="btn_crear_cliente_tab"):
                if nombre_nuevo:
                    try:
                        self.clientes_repo.crear_cliente(
                            nombre=nombre_nuevo,
                            contacto=contacto_nuevo if contacto_nuevo else None
                        )
                        st.success(f"✅ Cliente '{nombre_nuevo}' creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ El nombre es obligatorio")
        
        except Exception as e:
            st.error(f"❌ Error al cargar clientes: {str(e)}")


# Función principal para llamar desde app.py
def render_ventas():
    """Función principal que se llama desde app.py"""
    module = VentasModule()
    module.render()


# Para testing en Jupyter
if __name__ == "__main__":
    render_ventas()
