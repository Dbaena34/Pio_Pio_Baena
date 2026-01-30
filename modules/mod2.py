"""
Módulo de Stock
Gestiona el stock de huevos e insumos, ajustes y movimientos
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
from data.models import StockRepository, InsumosRepository


class StockModule:
    """Clase principal del módulo de stock"""
    
    def __init__(self):
        self.stock_repo = StockRepository(db)
        self.insumos_repo = InsumosRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
    
    def render(self):
        """Renderiza la interfaz completa del módulo"""
        st.header("📦 Gestión de Stock")
        
        # Crear tabs
        tabs = st.tabs(["🥚 Stock de Huevos", "🌾 Stock de Insumos", "📋 Movimientos"])
        
        with tabs[0]:
            self._render_stock_huevos()
        
        with tabs[1]:
            self._render_stock_insumos()
        
        with tabs[2]:
            self._render_movimientos()
    
    def _render_stock_huevos(self):
        """Renderiza la gestión de stock de huevos"""
        st.subheader("🥚 Stock Actual de Huevos")
        
        try:
            # Obtener stock actual
            stock = self.stock_repo.obtener_stock_actual()
            
            if stock:
                # Mostrar stock actual en cards
                st.markdown("### 📊 Inventario Actual")
                
                cols = st.columns(6)
                categorias_db = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
                
                total_stock = 0
                for col, cat_db, cat_nombre in zip(cols, categorias_db, self.categorias_huevos):
                    cantidad = stock.get(cat_db, 0) or 0
                    total_stock += cantidad
                    with col:
                        st.metric(
                            label=f"Tipo {cat_nombre}",
                            value=f"{cantidad:,}",
                            delta=None
                        )
                
                st.markdown("---")
                col_total, col_fecha = st.columns([1, 2])
                with col_total:
                    st.metric("📦 TOTAL EN STOCK", f"{total_stock:,} huevos")
                with col_fecha:
                    ultima_actualizacion = stock.get('updated_at', 'N/A')
                    st.info(f"🕐 Última actualización: {ultima_actualizacion}")
                
                # Gráfico de distribución
                st.markdown("---")
                st.markdown("### 📈 Distribución de Stock")
                
                # Preparar datos para el gráfico
                datos_grafico = {
                    'Categoría': self.categorias_huevos,
                    'Cantidad': [stock.get(cat, 0) or 0 for cat in categorias_db]
                }
                df_grafico = pd.DataFrame(datos_grafico)
                df_grafico = df_grafico[df_grafico['Cantidad'] > 0]  # Solo categorías con stock
                
                if not df_grafico.empty:
                    col_bar, col_pie = st.columns(2)
                    
                    with col_bar:
                        fig_bar = px.bar(
                            df_grafico,
                            x='Categoría',
                            y='Cantidad',
                            title='Stock por Categoría',
                            color='Categoría',
                            text='Cantidad'
                        )
                        fig_bar.update_traces(textposition='outside')
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    with col_pie:
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=df_grafico['Categoría'],
                            values=df_grafico['Cantidad'],
                            hole=0.3
                        )])
                        fig_pie.update_layout(title='Distribución Porcentual')
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                # Sección de ajustes
                st.markdown("---")
                st.markdown("### ⚙️ Ajustar Stock")
                
                col_tipo, col_form = st.columns([1, 3])
                
                with col_tipo:
                    tipo_ajuste = st.radio(
                        "Tipo de ajuste",
                        options=['merma', 'correccion'],
                        format_func=lambda x: '🔻 Merma (rotos/pérdidas)' if x == 'merma' else '✏️ Corrección de inventario'
                    )
                
                with col_form:
                    st.markdown(f"**{'Registrar Merma' if tipo_ajuste == 'merma' else 'Corrección de Inventario'}**")
                    
                    cols_ajuste = st.columns(6)
                    ajustes = {}
                    
                    for col, cat in zip(cols_ajuste, self.categorias_huevos):
                        with col:
                            if tipo_ajuste == 'merma':
                                ajustes[cat] = st.number_input(
                                    f"{cat}",
                                    min_value=0,
                                    step=1,
                                    value=0,
                                    key=f"merma_{cat}",
                                    help="Cantidad a descontar"
                                )
                            else:
                                ajustes[cat] = st.number_input(
                                    f"{cat}",
                                    step=1,
                                    value=0,
                                    key=f"corr_{cat}",
                                    help="Positivo: sumar, Negativo: restar"
                                )
                    
                    motivo = st.text_input(
                        "Motivo del ajuste",
                        placeholder="Ej: Huevos rotos en transporte, Error de conteo, etc.",
                        key="motivo_ajuste"
                    )
                    
                    col_btn1, col_btn2 = st.columns([1, 3])
                    with col_btn1:
                        if st.button("💾 Aplicar Ajuste", use_container_width=True, key="btn_ajuste_huevos"):
                            total_ajuste = sum(ajustes.values())
                            
                            if total_ajuste != 0 or tipo_ajuste == 'correccion':
                                try:
                                    # Para mermas, convertir a negativo
                                    if tipo_ajuste == 'merma':
                                        ajustes_aplicar = {k: -v for k, v in ajustes.items()}
                                    else:
                                        ajustes_aplicar = ajustes
                                    
                                    # Aplicar ajuste
                                    self.stock_repo.registrar_ajuste_huevos(
                                        tipo_ajuste=tipo_ajuste,
                                        tipo_c=ajustes_aplicar['C'],
                                        tipo_b=ajustes_aplicar['B'],
                                        tipo_a=ajustes_aplicar['A'],
                                        tipo_aa=ajustes_aplicar['AA'],
                                        tipo_aaa=ajustes_aplicar['AAA'],
                                        tipo_jumbo=ajustes_aplicar['Jumbo'],
                                        motivo=motivo if motivo else None
                                    )
                                    
                                    st.success(f"✅ Ajuste aplicado exitosamente")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al aplicar ajuste: {str(e)}")
                            else:
                                st.warning("⚠️ Ingresa al menos un valor para ajustar")
                
                # Historial de ajustes
                st.markdown("---")
                st.markdown("### 📜 Historial de Ajustes")
                
                col_hist1, col_hist2 = st.columns(2)
                with col_hist1:
                    fecha_inicio_hist = st.date_input(
                        "Desde",
                        value=date.today() - timedelta(days=30),
                        key="hist_ajustes_inicio"
                    )
                with col_hist2:
                    fecha_fin_hist = st.date_input(
                        "Hasta",
                        value=date.today(),
                        key="hist_ajustes_fin"
                    )
                
                historial = self.stock_repo.obtener_historial_ajustes_huevos(
                    fecha_inicio_hist, fecha_fin_hist
                )
                
                if historial:
                    df_hist = pd.DataFrame(historial)
                    df_hist['total_ajuste'] = (
                        df_hist['tipo_c'] + df_hist['tipo_b'] + df_hist['tipo_a'] +
                        df_hist['tipo_aa'] + df_hist['tipo_aaa'] + df_hist['tipo_jumbo']
                    )
                    
                    # Renombrar para mostrar
                    df_display = df_hist[['fecha', 'hora', 'tipo_ajuste', 'tipo_c', 'tipo_b', 
                                          'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo', 
                                          'total_ajuste', 'motivo']].copy()
                    df_display.columns = ['Fecha', 'Hora', 'Tipo', 'C', 'B', 'A', 'AA', 
                                         'AAA', 'Jumbo', 'Total', 'Motivo']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ No hay ajustes registrados en este período")
            
            else:
                st.warning("⚠️ No se pudo obtener el stock actual")
        
        except Exception as e:
            st.error(f"❌ Error al cargar el stock de huevos: {str(e)}")
    
    def _render_stock_insumos(self):
        """Renderiza la gestión de stock de insumos"""
        st.subheader("🌾 Stock de Insumos")
        
        try:
            # Obtener stock de insumos
            stock_insumos = self.stock_repo.obtener_stock_insumos()
            
            if stock_insumos:
                # Alertas de stock bajo
                alertas = [item for item in stock_insumos if item.get('alerta_stock', 0) == 1]
                
                if alertas:
                    st.warning(f"⚠️ **{len(alertas)} insumo(s) con stock bajo:**")
                    for alerta in alertas:
                        st.error(f"🔴 {alerta['nombre']} ({alerta['categoria']}): {alerta['cantidad_actual']} {alerta['unidad']} - Mínimo: {alerta['stock_minimo']}")
                    st.markdown("---")
                
                # Mostrar stock por categoría
                st.markdown("### 📊 Inventario de Insumos")
                
                # Convertir a DataFrame
                df = pd.DataFrame(stock_insumos)
                
                # Filtro por categoría
                categorias_disponibles = df['categoria'].unique().tolist()
                categoria_filtro = st.multiselect(
                    "Filtrar por categoría",
                    options=categorias_disponibles,
                    default=categorias_disponibles,
                    key="filtro_categoria_insumos"
                )
                
                df_filtrado = df[df['categoria'].isin(categoria_filtro)]
                
                # Mostrar tabla
                df_display = df_filtrado[['nombre', 'categoria', 'cantidad_actual', 'stock_minimo', 'unidad']].copy()
                df_display.columns = ['Insumo', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Unidad']
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Stock Actual": st.column_config.NumberColumn(format="%.2f"),
                        "Stock Mínimo": st.column_config.NumberColumn(format="%.2f")
                    }
                )
                
                # Gráfico de stock por categoría
                st.markdown("---")
                st.markdown("### 📈 Stock por Categoría")
                
                stock_por_categoria = df_filtrado.groupby('categoria')['cantidad_actual'].sum().reset_index()
                stock_por_categoria.columns = ['Categoría', 'Cantidad Total']
                
                if not stock_por_categoria.empty:
                    fig = px.bar(
                        stock_por_categoria,
                        x='Categoría',
                        y='Cantidad Total',
                        title='Stock Total por Categoría',
                        color='Categoría'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Sección de gestión
                st.markdown("---")
                st.markdown("### ⚙️ Gestión de Insumos")
                
                tab_consumo, tab_ajuste, tab_minimos = st.tabs([
                    "📤 Registrar Consumo/Salida",
                    "✏️ Ajustar Stock",
                    "⚠️ Actualizar Mínimos"
                ])
                
                # Tab 1: Registrar consumo
                with tab_consumo:
                    st.markdown("**Registrar consumo o salida de insumo**")
                    
                    insumo_seleccionado = st.selectbox(
                        "Selecciona el insumo",
                        options=df['insumo_id'].tolist(),
                        format_func=lambda x: f"{df[df['insumo_id']==x]['nombre'].iloc[0]} - Stock: {df[df['insumo_id']==x]['cantidad_actual'].iloc[0]} {df[df['insumo_id']==x]['unidad'].iloc[0]}",
                        key="consumo_insumo_select"
                    )
                    
                    if insumo_seleccionado:
                        insumo_data = df[df['insumo_id'] == insumo_seleccionado].iloc[0]
                        
                        col_cant, col_mot = st.columns([1, 2])
                        
                        with col_cant:
                            cantidad_consumo = st.number_input(
                                f"Cantidad ({insumo_data['unidad']})",
                                min_value=0.0,
                                step=1.0,
                                max_value=float(insumo_data['cantidad_actual']),
                                value=0.0,
                                key="cantidad_consumo"
                            )
                        
                        with col_mot:
                            motivo_consumo = st.text_input(
                                "Motivo",
                                placeholder="Ej: Consumo diario, Uso en mantenimiento, etc.",
                                key="motivo_consumo"
                            )
                        
                        if cantidad_consumo > 0:
                            nuevo_stock = insumo_data['cantidad_actual'] - cantidad_consumo
                            st.info(f"📊 Nuevo stock: {nuevo_stock:.2f} {insumo_data['unidad']}")
                        
                        if st.button("💾 Registrar Consumo", key="btn_consumo"):
                            if cantidad_consumo > 0:
                                try:
                                    self.stock_repo.registrar_consumo_insumo(
                                        insumo_id=insumo_seleccionado,
                                        cantidad=cantidad_consumo,
                                        motivo=motivo_consumo if motivo_consumo else None
                                    )
                                    st.success(f"✅ Consumo registrado: {cantidad_consumo} {insumo_data['unidad']}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            else:
                                st.warning("⚠️ Ingresa una cantidad mayor a 0")
                
                # Tab 2: Ajustar stock
                with tab_ajuste:
                    st.markdown("**Ajustar stock manualmente**")
                    
                    insumo_ajuste = st.selectbox(
                        "Selecciona el insumo",
                        options=df['insumo_id'].tolist(),
                        format_func=lambda x: f"{df[df['insumo_id']==x]['nombre'].iloc[0]} - Stock actual: {df[df['insumo_id']==x]['cantidad_actual'].iloc[0]} {df[df['insumo_id']==x]['unidad'].iloc[0]}",
                        key="ajuste_insumo_select"
                    )
                    
                    if insumo_ajuste:
                        insumo_data_ajuste = df[df['insumo_id'] == insumo_ajuste].iloc[0]
                        
                        st.info(f"📦 Stock actual: {insumo_data_ajuste['cantidad_actual']} {insumo_data_ajuste['unidad']}")
                        
                        nueva_cantidad = st.number_input(
                            f"Nueva cantidad ({insumo_data_ajuste['unidad']})",
                            min_value=0.0,
                            step=1.0,
                            value=float(insumo_data_ajuste['cantidad_actual']),
                            key="nueva_cantidad_ajuste"
                        )
                        
                        motivo_ajuste = st.text_input(
                            "Motivo del ajuste",
                            placeholder="Ej: Corrección de inventario, Error de registro, etc.",
                            key="motivo_ajuste_insumo"
                        )
                        
                        diferencia = nueva_cantidad - insumo_data_ajuste['cantidad_actual']
                        if diferencia != 0:
                            color = "🔼" if diferencia > 0 else "🔽"
                            st.warning(f"{color} Diferencia: {diferencia:+.2f} {insumo_data_ajuste['unidad']}")
                        
                        if st.button("💾 Aplicar Ajuste", key="btn_ajuste_stock"):
                            try:
                                self.stock_repo.ajustar_stock_insumo(
                                    insumo_id=insumo_ajuste,
                                    nueva_cantidad=nueva_cantidad,
                                    motivo=motivo_ajuste if motivo_ajuste else "Ajuste manual"
                                )
                                st.success(f"✅ Stock ajustado a {nueva_cantidad} {insumo_data_ajuste['unidad']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                # Tab 3: Actualizar mínimos
                with tab_minimos:
                    st.markdown("**Actualizar stocks mínimos**")
                    
                    insumo_minimo = st.selectbox(
                        "Selecciona el insumo",
                        options=df['insumo_id'].tolist(),
                        format_func=lambda x: f"{df[df['insumo_id']==x]['nombre'].iloc[0]} - Mínimo actual: {df[df['insumo_id']==x]['stock_minimo'].iloc[0]} {df[df['insumo_id']==x]['unidad'].iloc[0]}",
                        key="minimo_insumo_select"
                    )
                    
                    if insumo_minimo:
                        insumo_data_minimo = df[df['insumo_id'] == insumo_minimo].iloc[0]
                        
                        st.info(f"⚠️ Stock mínimo actual: {insumo_data_minimo['stock_minimo']} {insumo_data_minimo['unidad']}")
                        
                        nuevo_minimo = st.number_input(
                            f"Nuevo stock mínimo ({insumo_data_minimo['unidad']})",
                            min_value=0.0,
                            step=1.0,
                            value=float(insumo_data_minimo['stock_minimo']),
                            key="nuevo_minimo"
                        )
                        
                        if st.button("💾 Actualizar Mínimo", key="btn_actualizar_minimo"):
                            try:
                                self.stock_repo.actualizar_stock_minimo(
                                    insumo_id=insumo_minimo,
                                    stock_minimo=nuevo_minimo
                                )
                                st.success(f"✅ Stock mínimo actualizado a {nuevo_minimo} {insumo_data_minimo['unidad']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            
            else:
                st.info("ℹ️ No hay insumos registrados en el sistema")
                st.markdown("💡 **Tip:** Registra insumos en la pestaña 'Insumos y Pagos'")
        
        except Exception as e:
            st.error(f"❌ Error al cargar stock de insumos: {str(e)}")
    
    def _render_movimientos(self):
        """Renderiza el historial de movimientos"""
        st.subheader("📋 Historial de Movimientos")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_inicio = st.date_input(
                "Fecha inicio",
                value=date.today() - timedelta(days=30),
                key="mov_fecha_inicio"
            )
        
        with col2:
            fecha_fin = st.date_input(
                "Fecha fin",
                value=date.today(),
                key="mov_fecha_fin"
            )
        
        # Tabs para diferentes tipos de movimientos
        tab_ajustes, tab_insumos = st.tabs(["🥚 Ajustes de Huevos", "🌾 Movimientos de Insumos"])
        
        with tab_ajustes:
            try:
                historial_ajustes = self.stock_repo.obtener_historial_ajustes_huevos(
                    fecha_inicio, fecha_fin
                )
                
                if historial_ajustes:
                    df = pd.DataFrame(historial_ajustes)
                    df['total'] = (
                        df['tipo_c'] + df['tipo_b'] + df['tipo_a'] +
                        df['tipo_aa'] + df['tipo_aaa'] + df['tipo_jumbo']
                    )
                    
                    # Métricas
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Ajustes", len(df))
                    with col_m2:
                        total_mermas = df[df['tipo_ajuste'] == 'merma']['total'].sum()
                        st.metric("Total Mermas", f"{abs(total_mermas):,}")
                    with col_m3:
                        total_correcciones = df[df['tipo_ajuste'] == 'correccion']['total'].sum()
                        st.metric("Total Correcciones", f"{total_correcciones:+,}")
                    
                    st.markdown("---")
                    
                    # Tabla
                    df_display = df[['fecha', 'hora', 'tipo_ajuste', 'tipo_c', 'tipo_b', 
                                    'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo', 
                                    'total', 'motivo']].copy()
                    df_display.columns = ['Fecha', 'Hora', 'Tipo', 'C', 'B', 'A', 'AA', 
                                         'AAA', 'Jumbo', 'Total', 'Motivo']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ No hay ajustes en este período")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        with tab_insumos:
            try:
                historial_insumos = self.stock_repo.obtener_historial_movimientos_insumos(
                    fecha_inicio, fecha_fin
                )
                
                if historial_insumos:
                    df = pd.DataFrame(historial_insumos)
                    
                    # Métricas
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Movimientos", len(df))
                    with col_m2:
                        total_salidas = df[df['tipo_movimiento'] == 'salida']['cantidad'].sum()
                        st.metric("Total Salidas", f"{total_salidas:.2f}")
                    
                    st.markdown("---")
                    
                    # Tabla
                    df_display = df[['fecha', 'hora', 'insumo_nombre', 'categoria', 
                                    'tipo_movimiento', 'cantidad', 'unidad', 'motivo']].copy()
                    df_display.columns = ['Fecha', 'Hora', 'Insumo', 'Categoría', 
                                         'Tipo', 'Cantidad', 'Unidad', 'Motivo']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ No hay movimientos en este período")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# Función principal para llamar desde app.py
def render_stock():
    """Función principal que se llama desde app.py"""
    module = StockModule()
    module.render()


# Para testing en Jupyter
if __name__ == "__main__":
    render_stock()
