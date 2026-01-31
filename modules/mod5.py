"""
Módulo de Reportes
Dashboard ejecutivo, análisis detallados, alertas y exportación de reportes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
import io

# Importar la base de datos y repositorios
import sys
sys.path.append('..')
from data.database import db
from data.models import (ReportesRepository, ProduccionRepository, StockRepository, 
                         PedidosRepository, InsumosRepository, PreciosRepository)


class ReportesModule:
    """Clase principal del módulo de reportes"""
    
    def __init__(self):
        self.reportes_repo = ReportesRepository(db)
        self.produccion_repo = ProduccionRepository(db)
        self.stock_repo = StockRepository(db)
        self.pedidos_repo = PedidosRepository(db)
        self.insumos_repo = InsumosRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
    
    def render(self):
        """Renderiza la interfaz completa del módulo"""
        st.header("📈 Reportes y Análisis")
        
        # Alertas en la parte superior
        self._mostrar_alertas()
        
        st.markdown("---")
        
        # Crear tabs
        tabs = st.tabs([
            "📊 Dashboard General",
            "🥚 Análisis de Producción",
            "💰 Análisis de Ventas",
            "💵 Análisis Financiero",
            "📄 Exportar Reportes"
        ])
        
        with tabs[0]:
            self._render_dashboard_general()
        
        with tabs[1]:
            self._render_analisis_produccion()
        
        with tabs[2]:
            self._render_analisis_ventas()
        
        with tabs[3]:
            self._render_analisis_financiero()
        
        with tabs[4]:
            self._render_exportar_reportes()
    
    def _mostrar_alertas(self):
        """Muestra alertas importantes en la parte superior"""
        try:
            # Alertas de stock bajo de insumos
            alertas_stock = self.stock_repo.obtener_alertas_stock()
            
            if alertas_stock:
                st.warning(f"⚠️ **ALERTAS ACTIVAS ({len(alertas_stock)})**")
                
                cols_alertas = st.columns(min(len(alertas_stock), 3))
                
                for idx, alerta in enumerate(alertas_stock[:3]):  # Mostrar máximo 3
                    with cols_alertas[idx]:
                        st.error(f"""
                        **🔴 Stock Bajo: {alerta['nombre']}**
                        - Actual: {alerta['cantidad_actual']} {alerta['unidad']}
                        - Mínimo: {alerta['stock_minimo']} {alerta['unidad']}
                        - Categoría: {alerta['categoria']}
                        """)
                
                if len(alertas_stock) > 3:
                    st.info(f"💡 Hay {len(alertas_stock) - 3} alertas más. Revisa el módulo de Stock.")
        
        except Exception as e:
            st.error(f"❌ Error al cargar alertas: {str(e)}")
    
    def _obtener_periodo_seleccionado(self, key_prefix: str = ""):
        """Componente reutilizable para selección de período"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            periodo_preset = st.selectbox(
                "Período predefinido",
                options=['Personalizado', 'Última semana', 'Último mes', 'Último semestre', 'Año actual'],
                key=f"{key_prefix}_periodo_preset"
            )
        
        # Calcular fechas según preset
        hoy = date.today()
        
        if periodo_preset == 'Última semana':
            fecha_inicio = hoy - timedelta(days=7)
            fecha_fin = hoy
        elif periodo_preset == 'Último mes':
            fecha_inicio = hoy - timedelta(days=30)
            fecha_fin = hoy
        elif periodo_preset == 'Último semestre':
            fecha_inicio = hoy - timedelta(days=180)
            fecha_fin = hoy
        elif periodo_preset == 'Año actual':
            fecha_inicio = date(hoy.year, 1, 1)
            fecha_fin = hoy
        else:  # Personalizado
            with col2:
                fecha_inicio = st.date_input(
                    "Desde",
                    value=hoy - timedelta(days=30),
                    key=f"{key_prefix}_fecha_inicio"
                )
            with col3:
                fecha_fin = st.date_input(
                    "Hasta",
                    value=hoy,
                    key=f"{key_prefix}_fecha_fin"
                )
        
        return fecha_inicio, fecha_fin, periodo_preset
    
    def _render_dashboard_general(self):
        """Dashboard ejecutivo con KPIs principales"""
        st.subheader("📊 Dashboard Ejecutivo")
        
        # Selección de período
        fecha_inicio, fecha_fin, periodo = self._obtener_periodo_seleccionado("dashboard")
        
        # Comparar con período anterior
        col_comp1, col_comp2 = st.columns([3, 1])
        
        with col_comp2:
            comparar = st.checkbox("Comparar con período anterior", value=True, key="comparar_dashboard")
        
        if comparar:
            dias_periodo = (fecha_fin - fecha_inicio).days
            fecha_inicio_anterior = fecha_inicio - timedelta(days=dias_periodo + 1)
            fecha_fin_anterior = fecha_inicio - timedelta(days=1)
        
        try:
            # Obtener datos del período actual
            balance = self.reportes_repo.obtener_balance_periodo(fecha_inicio, fecha_fin)
            resumen_prod_ventas = self.reportes_repo.obtener_resumen_produccion_ventas(fecha_inicio, fecha_fin)
            
            # Datos del período anterior si se compara
            if comparar:
                balance_anterior = self.reportes_repo.obtener_balance_periodo(fecha_inicio_anterior, fecha_fin_anterior)
                resumen_anterior = self.reportes_repo.obtener_resumen_produccion_ventas(fecha_inicio_anterior, fecha_fin_anterior)
            
            # KPIs principales
            st.markdown("### 📈 Indicadores Clave")
            
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            
            with col_k1:
                total_ingresos = balance.get('total_ingresos', 0) or 0
                if comparar:
                    ingresos_anterior = balance_anterior.get('total_ingresos', 0) or 0
                    delta_ingresos = total_ingresos - ingresos_anterior
                    delta_pct = (delta_ingresos / ingresos_anterior * 100) if ingresos_anterior > 0 else 0
                    st.metric(
                        "💰 Ingresos",
                        f"${total_ingresos:,.0f}",
                        delta=f"{delta_pct:+.1f}%"
                    )
                else:
                    st.metric("💰 Ingresos", f"${total_ingresos:,.0f}")
            
            with col_k2:
                total_egresos = balance.get('total_egresos', 0) or 0
                if comparar:
                    egresos_anterior = balance_anterior.get('total_egresos', 0) or 0
                    delta_egresos = total_egresos - egresos_anterior
                    delta_pct = (delta_egresos / egresos_anterior * 100) if egresos_anterior > 0 else 0
                    st.metric(
                        "💸 Egresos",
                        f"${total_egresos:,.0f}",
                        delta=f"{delta_pct:+.1f}%",
                        delta_color="inverse"
                    )
                else:
                    st.metric("💸 Egresos", f"${total_egresos:,.0f}")
            
            with col_k3:
                balance_neto = balance.get('balance', 0) or 0
                if comparar:
                    balance_anterior_neto = balance_anterior.get('balance', 0) or 0
                    delta_balance = balance_neto - balance_anterior_neto
                    st.metric(
                        "📊 Balance Neto",
                        f"${balance_neto:,.0f}",
                        delta=f"${delta_balance:+,.0f}"
                    )
                else:
                    st.metric("📊 Balance Neto", f"${balance_neto:,.0f}")
            
            with col_k4:
                if total_ingresos > 0:
                    margen = (balance_neto / total_ingresos) * 100
                    if comparar and ingresos_anterior > 0:
                        margen_anterior = (balance_anterior_neto / ingresos_anterior) * 100
                        delta_margen = margen - margen_anterior
                        st.metric(
                            "💹 Margen",
                            f"{margen:.1f}%",
                            delta=f"{delta_margen:+.1f}pp"
                        )
                    else:
                        st.metric("💹 Margen", f"{margen:.1f}%")
                else:
                    st.metric("💹 Margen", "N/A")
            
            st.markdown("---")
            
            # Producción y Ventas
            col_pv1, col_pv2, col_pv3 = st.columns(3)
            
            with col_pv1:
                total_producido = resumen_prod_ventas.get('total_producido', 0) or 0
                if comparar:
                    prod_anterior = resumen_anterior.get('total_producido', 0) or 0
                    delta_prod = total_producido - prod_anterior
                    delta_pct = (delta_prod / prod_anterior * 100) if prod_anterior > 0 else 0
                    st.metric(
                        "🥚 Huevos Producidos",
                        f"{total_producido:,}",
                        delta=f"{delta_pct:+.1f}%"
                    )
                else:
                    st.metric("🥚 Huevos Producidos", f"{total_producido:,}")
            
            with col_pv2:
                total_vendido = resumen_prod_ventas.get('total_vendido', 0) or 0
                if comparar:
                    vend_anterior = resumen_anterior.get('total_vendido', 0) or 0
                    delta_vend = total_vendido - vend_anterior
                    delta_pct = (delta_vend / vend_anterior * 100) if vend_anterior > 0 else 0
                    st.metric(
                        "📦 Huevos Vendidos",
                        f"{total_vendido:,}",
                        delta=f"{delta_pct:+.1f}%"
                    )
                else:
                    st.metric("📦 Huevos Vendidos", f"{total_vendido:,}")
            
            with col_pv3:
                if total_producido > 0:
                    tasa_venta = (total_vendido / total_producido) * 100
                    if comparar and prod_anterior > 0:
                        tasa_anterior = (vend_anterior / prod_anterior) * 100
                        delta_tasa = tasa_venta - tasa_anterior
                        st.metric(
                            "📊 Tasa de Venta",
                            f"{tasa_venta:.1f}%",
                            delta=f"{delta_tasa:+.1f}pp"
                        )
                    else:
                        st.metric("📊 Tasa de Venta", f"{tasa_venta:.1f}%")
                else:
                    st.metric("📊 Tasa de Venta", "N/A")
            
            st.markdown("---")
            
            # Costos y Eficiencia
            st.markdown("### 💵 Costos y Eficiencia")
            
            col_c1, col_c2, col_c3 = st.columns(3)
            
            with col_c1:
                costo_por_huevo = self.reportes_repo.calcular_costo_produccion_por_huevo(fecha_inicio, fecha_fin)
                if comparar:
                    costo_anterior = self.reportes_repo.calcular_costo_produccion_por_huevo(fecha_inicio_anterior, fecha_fin_anterior)
                    delta_costo = costo_por_huevo - costo_anterior
                    st.metric(
                        "💰 Costo/Huevo",
                        f"${costo_por_huevo:.2f}",
                        delta=f"${delta_costo:+.2f}",
                        delta_color="inverse"
                    )
                else:
                    st.metric("💰 Costo/Huevo", f"${costo_por_huevo:.2f}")
            
            with col_c2:
                # Precio promedio de venta
                if total_vendido > 0:
                    precio_promedio = total_ingresos / total_vendido
                    if comparar and vend_anterior > 0:
                        precio_anterior = ingresos_anterior / vend_anterior
                        delta_precio = precio_promedio - precio_anterior
                        st.metric(
                            "💲 Precio Promedio/Huevo",
                            f"${precio_promedio:.2f}",
                            delta=f"${delta_precio:+.2f}"
                        )
                    else:
                        st.metric("💲 Precio Promedio/Huevo", f"${precio_promedio:.2f}")
                else:
                    st.metric("💲 Precio Promedio/Huevo", "N/A")
            
            with col_c3:
                # Ganancia por huevo
                if total_vendido > 0:
                    ganancia_huevo = precio_promedio - costo_por_huevo
                    margen_huevo = (ganancia_huevo / precio_promedio * 100) if precio_promedio > 0 else 0
                    st.metric(
                        "💹 Ganancia/Huevo",
                        f"${ganancia_huevo:.2f}",
                        delta=f"{margen_huevo:.1f}% margen"
                    )
                else:
                    st.metric("💹 Ganancia/Huevo", "N/A")
            
            st.markdown("---")
            
            # Gráficos de tendencias
            st.markdown("### 📈 Tendencias")
            
            # Producción y ventas diarias
            prod_diaria = self.reportes_repo.obtener_produccion_diaria_periodo(fecha_inicio, fecha_fin)
            ventas_diarias = self.reportes_repo.obtener_ventas_diarias_periodo(fecha_inicio, fecha_fin)
            
            if prod_diaria or ventas_diarias:
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    if prod_diaria:
                        df_prod = pd.DataFrame(prod_diaria)
                        df_prod['fecha'] = pd.to_datetime(df_prod['fecha'])
                        
                        fig_prod = px.line(
                            df_prod,
                            x='fecha',
                            y='total',
                            title='Producción Diaria',
                            labels={'fecha': 'Fecha', 'total': 'Huevos'},
                            markers=True
                        )
                        st.plotly_chart(fig_prod, use_container_width=True)
                
                with col_graf2:
                    if ventas_diarias:
                        df_ventas = pd.DataFrame(ventas_diarias)
                        df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])
                        
                        fig_ventas = px.line(
                            df_ventas,
                            x='fecha',
                            y='total_ingresos',
                            title='Ingresos Diarios',
                            labels={'fecha': 'Fecha', 'total_ingresos': 'Ingresos ($)'},
                            markers=True
                        )
                        st.plotly_chart(fig_ventas, use_container_width=True)
            
            # Stock actual
            st.markdown("---")
            st.markdown("### 📦 Estado del Stock")
            
            stock_stats = self.reportes_repo.obtener_estadisticas_stock()
            
            if stock_stats:
                total_stock = stock_stats.get('total_huevos', 0) or 0
                
                col_stock1, col_stock2 = st.columns([1, 2])
                
                with col_stock1:
                    st.metric("🥚 Total en Stock", f"{total_stock:,} huevos")
                    
                    if total_producido > 0:
                        dias_stock = total_stock / (total_producido / ((fecha_fin - fecha_inicio).days + 1))
                        st.metric("📅 Días de Stock", f"{dias_stock:.1f} días")
                
                with col_stock2:
                    # Gráfico de distribución
                    categorias_db = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
                    stock_por_cat = {
                        cat: stock_stats.get(cat_db, 0) or 0
                        for cat, cat_db in zip(self.categorias_huevos, categorias_db)
                    }
                    
                    # Filtrar solo categorías con stock
                    stock_por_cat = {k: v for k, v in stock_por_cat.items() if v > 0}
                    
                    if stock_por_cat:
                        fig_stock = go.Figure(data=[go.Pie(
                            labels=list(stock_por_cat.keys()),
                            values=list(stock_por_cat.values()),
                            hole=0.3
                        )])
                        fig_stock.update_layout(title='Distribución del Stock')
                        st.plotly_chart(fig_stock, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error al cargar el dashboard: {str(e)}")
    
    def _render_analisis_produccion(self):
        """Análisis detallado de producción"""
        st.subheader("🥚 Análisis de Producción")
        
        # Selección de período
        fecha_inicio, fecha_fin, periodo = self._obtener_periodo_seleccionado("prod")
        
        try:
            # Obtener datos
            produccion_diaria = self.reportes_repo.obtener_produccion_diaria_periodo(fecha_inicio, fecha_fin)
            total_produccion = self.produccion_repo.obtener_total_produccion_periodo(fecha_inicio, fecha_fin)
            
            if produccion_diaria:
                df = pd.DataFrame(produccion_diaria)
                df['fecha'] = pd.to_datetime(df['fecha'])
                
                # Métricas
                st.markdown("### 📊 Resumen de Producción")
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    total = df['total'].sum()
                    st.metric("🥚 Total Producido", f"{total:,}")
                
                with col_m2:
                    promedio = df['total'].mean()
                    st.metric("📊 Promedio Diario", f"{promedio:.0f}")
                
                with col_m3:
                    maximo = df['total'].max()
                    st.metric("🏆 Mejor Día", f"{maximo:,}")
                
                with col_m4:
                    minimo = df['total'].min()
                    st.metric("📉 Peor Día", f"{minimo:,}")
                
                st.markdown("---")
                
                # Gráficos
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    # Producción total por día
                    fig_total = px.area(
                        df,
                        x='fecha',
                        y='total',
                        title='Producción Total por Día',
                        labels={'fecha': 'Fecha', 'total': 'Huevos'}
                    )
                    st.plotly_chart(fig_total, use_container_width=True)
                
                with col_g2:
                    # Producción por categoría (área apilada)
                    df_categorias = df[['fecha', 'tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']].copy()
                    df_categorias = df_categorias.melt(
                        id_vars=['fecha'],
                        var_name='Categoría',
                        value_name='Cantidad'
                    )
                    
                    categoria_map = {
                        'tipo_c': 'C', 'tipo_b': 'B', 'tipo_a': 'A',
                        'tipo_aa': 'AA', 'tipo_aaa': 'AAA', 'tipo_jumbo': 'Jumbo'
                    }
                    df_categorias['Categoría'] = df_categorias['Categoría'].map(categoria_map)
                    
                    fig_cat = px.area(
                        df_categorias,
                        x='fecha',
                        y='Cantidad',
                        color='Categoría',
                        title='Producción por Categoría'
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)
                
                # Distribución total del período
                st.markdown("---")
                st.markdown("### 📈 Distribución por Categoría")
                
                col_dist1, col_dist2 = st.columns(2)
                
                with col_dist1:
                    categorias_data = {
                        'C': total_produccion.get('total_c', 0) or 0,
                        'B': total_produccion.get('total_b', 0) or 0,
                        'A': total_produccion.get('total_a', 0) or 0,
                        'AA': total_produccion.get('total_aa', 0) or 0,
                        'AAA': total_produccion.get('total_aaa', 0) or 0,
                        'Jumbo': total_produccion.get('total_jumbo', 0) or 0
                    }
                    
                    # Filtrar categorías con producción
                    categorias_data = {k: v for k, v in categorias_data.items() if v > 0}
                    
                    if categorias_data:
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=list(categorias_data.keys()),
                            values=list(categorias_data.values()),
                            hole=0.3
                        )])
                        fig_pie.update_layout(title='Distribución Porcentual')
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_dist2:
                    # Tabla de producción por categoría
                    df_tabla = pd.DataFrame({
                        'Categoría': list(categorias_data.keys()),
                        'Cantidad': list(categorias_data.values())
                    })
                    df_tabla['Porcentaje'] = (df_tabla['Cantidad'] / df_tabla['Cantidad'].sum() * 100).round(1)
                    
                    st.dataframe(
                        df_tabla,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Cantidad": st.column_config.NumberColumn(format="%,d"),
                            "Porcentaje": st.column_config.NumberColumn(format="%.1f%%")
                        }
                    )
                
                # Estadísticas avanzadas
                st.markdown("---")
                st.markdown("### 📉 Estadísticas Avanzadas")
                
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    st.metric("Desviación Estándar", f"{df['total'].std():.1f}")
                    st.metric("Coeficiente de Variación", f"{(df['total'].std() / df['total'].mean() * 100):.1f}%")
                
                with col_stats2:
                    st.metric("Mediana", f"{df['total'].median():.0f}")
                    st.metric("Rango", f"{df['total'].max() - df['total'].min():,}")
                
                with col_stats3:
                    st.metric("Días Registrados", len(df))
                    st.metric("Tendencia", "📈 Creciente" if df['total'].iloc[-1] > df['total'].iloc[0] else "📉 Decreciente")
            
            else:
                st.info("ℹ️ No hay datos de producción en el período seleccionado")
        
        except Exception as e:
            st.error(f"❌ Error al cargar análisis de producción: {str(e)}")
    
    def _render_analisis_ventas(self):
        """Análisis detallado de ventas"""
        st.subheader("💰 Análisis de Ventas")
        
        # Selección de período
        fecha_inicio, fecha_fin, periodo = self._obtener_periodo_seleccionado("ventas")
        
        try:
            # Obtener datos
            ventas_diarias = self.reportes_repo.obtener_ventas_diarias_periodo(fecha_inicio, fecha_fin)
            top_clientes = self.reportes_repo.obtener_top_clientes(fecha_inicio, fecha_fin, limit=10)
            ventas_categoria = self.reportes_repo.obtener_ventas_por_categoria(fecha_inicio, fecha_fin)
            historial_ventas = self.pedidos_repo.obtener_historial_ventas(fecha_inicio, fecha_fin)
            
            if historial_ventas:
                df_ventas = pd.DataFrame(historial_ventas)
                
                # Métricas
                st.markdown("### 📊 Resumen de Ventas")
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    total_ventas = len(df_ventas)
                    st.metric("🛒 Total Ventas", f"{total_ventas:,}")
                
                with col_m2:
                    total_ingresos = df_ventas['precio_total'].sum()
                    st.metric("💰 Ingresos Totales", f"${total_ingresos:,.0f}")
                
                with col_m3:
                    ticket_promedio = df_ventas['precio_total'].mean()
                    st.metric("🎫 Ticket Promedio", f"${ticket_promedio:,.0f}")
                
                with col_m4:
                    total_canastillas = df_ventas['total_canastillas'].sum()
                    st.metric("📦 Canastillas Vendidas", f"{total_canastillas:,.0f}")
                
                st.markdown("---")
                
                # Gráficos
                if ventas_diarias:
                    col_g1, col_g2 = st.columns(2)
                    
                    with col_g1:
                        df_vd = pd.DataFrame(ventas_diarias)
                        df_vd['fecha'] = pd.to_datetime(df_vd['fecha'])
                        
                        fig_ingresos = px.bar(
                            df_vd,
                            x='fecha',
                            y='total_ingresos',
                            title='Ingresos Diarios',
                            labels={'fecha': 'Fecha', 'total_ingresos': 'Ingresos ($)'}
                        )
                        st.plotly_chart(fig_ingresos, use_container_width=True)
                    
                    with col_g2:
                        fig_cantidad = px.line(
                            df_vd,
                            x='fecha',
                            y='cantidad_ventas',
                            title='Cantidad de Ventas por Día',
                            labels={'fecha': 'Fecha', 'cantidad_ventas': 'Ventas'},
                            markers=True
                        )
                        st.plotly_chart(fig_cantidad, use_container_width=True)
                
                # Top clientes
                st.markdown("---")
                st.markdown("### 🏆 Top Clientes")
                
                if top_clientes:
                    col_top1, col_top2 = st.columns(2)
                    
                    with col_top1:
                        df_top = pd.DataFrame(top_clientes)
                        
                        fig_top = px.bar(
                            df_top,
                            x='total_comprado',
                            y='nombre',
                            orientation='h',
                            title='Top 10 Clientes por Compras',
                            labels={'total_comprado': 'Total Comprado ($)', 'nombre': 'Cliente'}
                        )
                        st.plotly_chart(fig_top, use_container_width=True)
                    
                    with col_top2:
                        df_display_top = df_top[['nombre', 'cantidad_compras', 'total_canastillas', 'total_comprado']].copy()
                        df_display_top.columns = ['Cliente', 'Compras', 'Canastillas', 'Total ($)']
                        
                        st.dataframe(
                            df_display_top,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Total ($)": st.column_config.NumberColumn(format="$%,.0f")
                            }
                        )
                
                # Ventas por categoría
                st.markdown("---")
                st.markdown("### 📦 Ventas por Categoría de Huevo")
                
                col_cat1, col_cat2 = st.columns(2)
                
                with col_cat1:
                    categorias_ventas = {
                        'C': ventas_categoria.get('total_c', 0) or 0,
                        'B': ventas_categoria.get('total_b', 0) or 0,
                        'A': ventas_categoria.get('total_a', 0) or 0,
                        'AA': ventas_categoria.get('total_aa', 0) or 0,
                        'AAA': ventas_categoria.get('total_aaa', 0) or 0,
                        'Jumbo': ventas_categoria.get('total_jumbo', 0) or 0
                    }
                    
                    # Filtrar categorías vendidas
                    categorias_ventas = {k: v for k, v in categorias_ventas.items() if v > 0}
                    
                    if categorias_ventas:
                        fig_cat_pie = go.Figure(data=[go.Pie(
                            labels=list(categorias_ventas.keys()),
                            values=list(categorias_ventas.values()),
                            hole=0.3
                        )])
                        fig_cat_pie.update_layout(title='Distribución de Ventas por Categoría (Canastillas)')
                        st.plotly_chart(fig_cat_pie, use_container_width=True)
                
                with col_cat2:
                    df_cat_tabla = pd.DataFrame({
                        'Categoría': list(categorias_ventas.keys()),
                        'Canastillas': list(categorias_ventas.values())
                    })
                    df_cat_tabla['Huevos'] = df_cat_tabla['Canastillas'] * 30
                    df_cat_tabla['Porcentaje'] = (df_cat_tabla['Canastillas'] / df_cat_tabla['Canastillas'].sum() * 100).round(1)
                    
                    st.dataframe(
                        df_cat_tabla,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Canastillas": st.column_config.NumberColumn(format="%,d"),
                            "Huevos": st.column_config.NumberColumn(format="%,d"),
                            "Porcentaje": st.column_config.NumberColumn(format="%.1f%%")
                        }
                    )
            
            else:
                st.info("ℹ️ No hay ventas en el período seleccionado")
        
        except Exception as e:
            st.error(f"❌ Error al cargar análisis de ventas: {str(e)}")
    
    def _render_analisis_financiero(self):
        """Análisis financiero detallado"""
        st.subheader("💵 Análisis Financiero")
        
        # Selección de período
        fecha_inicio, fecha_fin, periodo = self._obtener_periodo_seleccionado("financiero")
        
        try:
            # Obtener datos
            balance = self.reportes_repo.obtener_balance_periodo(fecha_inicio, fecha_fin)
            movimientos_categoria = self.reportes_repo.obtener_movimientos_por_categoria(fecha_inicio, fecha_fin)
            
            # Estado de resultados simplificado
            st.markdown("### 📋 Estado de Resultados")
            
            total_ingresos = balance.get('total_ingresos', 0) or 0
            total_egresos = balance.get('total_egresos', 0) or 0
            balance_neto = balance.get('balance', 0) or 0
            
            col_er1, col_er2, col_er3 = st.columns(3)
            
            with col_er1:
                st.metric("💰 Ingresos", f"${total_ingresos:,.0f}")
            
            with col_er2:
                st.metric("💸 Egresos", f"${total_egresos:,.0f}")
            
            with col_er3:
                color = "normal" if balance_neto >= 0 else "inverse"
                st.metric(
                    "📊 Resultado",
                    f"${balance_neto:,.0f}",
                    delta="Ganancia" if balance_neto >= 0 else "Pérdida",
                    delta_color=color
                )
            
            # Gráfico de cascada (waterfall)
            st.markdown("---")
            
            fig_waterfall = go.Figure(go.Waterfall(
                name="Flujo de Caja",
                orientation="v",
                measure=["relative", "relative", "total"],
                x=["Ingresos", "Egresos", "Balance Neto"],
                y=[total_ingresos, -total_egresos, balance_neto],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))
            
            fig_waterfall.update_layout(
                title="Flujo de Caja del Período",
                showlegend=False
            )
            
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            # Desglose de egresos
            st.markdown("---")
            st.markdown("### 💸 Desglose de Egresos")
            
            if movimientos_categoria:
                df_mov = pd.DataFrame(movimientos_categoria)
                df_egresos = df_mov[df_mov['tipo'] == 'egreso']
                
                if not df_egresos.empty:
                    col_eg1, col_eg2 = st.columns(2)
                    
                    with col_eg1:
                        fig_egresos_pie = go.Figure(data=[go.Pie(
                            labels=df_egresos['categoria'],
                            values=df_egresos['total'],
                            hole=0.3
                        )])
                        fig_egresos_pie.update_layout(title='Distribución de Egresos')
                        st.plotly_chart(fig_egresos_pie, use_container_width=True)
                    
                    with col_eg2:
                        df_display_eg = df_egresos[['categoria', 'cantidad_movimientos', 'total']].copy()
                        df_display_eg.columns = ['Categoría', 'Movimientos', 'Total']
                        df_display_eg['%'] = (df_display_eg['Total'] / df_display_eg['Total'].sum() * 100).round(1)
                        
                        st.dataframe(
                            df_display_eg,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Total": st.column_config.NumberColumn(format="$%,.0f"),
                                "%": st.column_config.NumberColumn(format="%.1f%%")
                            }
                        )
            
            # Ratios financieros
            st.markdown("---")
            st.markdown("### 📊 Ratios Financieros")
            
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            with col_r1:
                if total_ingresos > 0:
                    margen_bruto = (balance_neto / total_ingresos) * 100
                    st.metric("💹 Margen Bruto", f"{margen_bruto:.1f}%")
                else:
                    st.metric("💹 Margen Bruto", "N/A")
            
            with col_r2:
                if total_ingresos > 0:
                    ratio_gastos = (total_egresos / total_ingresos) * 100
                    st.metric("📉 Ratio de Gastos", f"{ratio_gastos:.1f}%")
                else:
                    st.metric("📉 Ratio de Gastos", "N/A")
            
            with col_r3:
                # ROI simplificado
                if total_egresos > 0:
                    roi = (balance_neto / total_egresos) * 100
                    st.metric("📈 ROI", f"{roi:.1f}%")
                else:
                    st.metric("📈 ROI", "N/A")
            
            with col_r4:
                dias_periodo = (fecha_fin - fecha_inicio).days + 1
                ingreso_diario = total_ingresos / dias_periodo if dias_periodo > 0 else 0
                st.metric("💰 Ingreso Diario Prom.", f"${ingreso_diario:,.0f}")
            
            # Proyección simple
            st.markdown("---")
            st.markdown("### 🔮 Proyección Mensual")
            
            if dias_periodo > 0:
                factor_mensual = 30 / dias_periodo
                
                col_proy1, col_proy2, col_proy3 = st.columns(3)
                
                with col_proy1:
                    ingresos_proyectados = total_ingresos * factor_mensual
                    st.metric("💰 Ingresos Proyectados (30 días)", f"${ingresos_proyectados:,.0f}")
                
                with col_proy2:
                    egresos_proyectados = total_egresos * factor_mensual
                    st.metric("💸 Egresos Proyectados (30 días)", f"${egresos_proyectados:,.0f}")
                
                with col_proy3:
                    balance_proyectado = balance_neto * factor_mensual
                    st.metric("📊 Balance Proyectado (30 días)", f"${balance_proyectado:,.0f}")
                
                st.info(f"💡 Proyección basada en {dias_periodo} días de datos reales")
        
        except Exception as e:
            st.error(f"❌ Error al cargar análisis financiero: {str(e)}")
    
    def _render_exportar_reportes(self):
        """Exportación de reportes en PDF y Excel"""
        st.subheader("📄 Exportar Reportes")
        
        st.info("💡 Genera reportes completos en PDF o Excel para archivo o presentación")
        
        # Selección de período
        fecha_inicio, fecha_fin, periodo = self._obtener_periodo_seleccionado("export")
        
        # Selección de contenido
        st.markdown("### 📋 Selecciona el contenido del reporte")
        
        col_check1, col_check2 = st.columns(2)
        
        with col_check1:
            incluir_kpis = st.checkbox("KPIs Principales", value=True)
            incluir_produccion = st.checkbox("Análisis de Producción", value=True)
            incluir_ventas = st.checkbox("Análisis de Ventas", value=True)
        
        with col_check2:
            incluir_financiero = st.checkbox("Análisis Financiero", value=True)
            incluir_graficos = st.checkbox("Incluir Gráficos", value=True)
            incluir_tablas = st.checkbox("Incluir Tablas Detalladas", value=True)
        
        st.markdown("---")
        
        # Botones de exportación
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("📥 Exportar a Excel", use_container_width=True, type="primary"):
                try:
                    excel_data = self._generar_excel(
                        fecha_inicio, fecha_fin,
                        incluir_kpis, incluir_produccion, incluir_ventas,
                        incluir_financiero, incluir_tablas
                    )
                    
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=excel_data,
                        file_name=f"reporte_granja_{fecha_inicio}_a_{fecha_fin}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Reporte Excel generado exitosamente")
                
                except Exception as e:
                    st.error(f"❌ Error al generar Excel: {str(e)}")
        
        with col_btn2:
            if st.button("📄 Generar Vista Previa PDF", use_container_width=True):
                st.info("📄 Funcionalidad de PDF en desarrollo")
                st.markdown("""
                **El reporte PDF incluirá:**
                - Carátula con logo y período
                - Resumen ejecutivo
                - Gráficos y tablas seleccionados
                - Conclusiones y recomendaciones
                """)
    
    def _generar_excel(self, fecha_inicio, fecha_fin, 
                      incluir_kpis, incluir_produccion, incluir_ventas,
                      incluir_financiero, incluir_tablas):
        """Genera un archivo Excel con el reporte completo"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Resumen
            if incluir_kpis:
                balance = self.reportes_repo.obtener_balance_periodo(fecha_inicio, fecha_fin)
                resumen_prod_ventas = self.reportes_repo.obtener_resumen_produccion_ventas(fecha_inicio, fecha_fin)
                
                df_resumen = pd.DataFrame({
                    'Indicador': [
                        'Período',
                        'Total Ingresos',
                        'Total Egresos',
                        'Balance Neto',
                        'Margen (%)',
                        'Huevos Producidos',
                        'Huevos Vendidos',
                        'Tasa de Venta (%)'
                    ],
                    'Valor': [
                        f"{fecha_inicio} a {fecha_fin}",
                        f"${balance.get('total_ingresos', 0):,.0f}",
                        f"${balance.get('total_egresos', 0):,.0f}",
                        f"${balance.get('balance', 0):,.0f}",
                        f"{(balance.get('balance', 0) / balance.get('total_ingresos', 1) * 100):.1f}%",
                        f"{resumen_prod_ventas.get('total_producido', 0):,}",
                        f"{resumen_prod_ventas.get('total_vendido', 0):,}",
                        f"{(resumen_prod_ventas.get('total_vendido', 0) / resumen_prod_ventas.get('total_producido', 1) * 100):.1f}%"
                    ]
                })
                
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja 2: Producción
            if incluir_produccion and incluir_tablas:
                produccion = self.reportes_repo.obtener_produccion_diaria_periodo(fecha_inicio, fecha_fin)
                if produccion:
                    df_prod = pd.DataFrame(produccion)
                    df_prod.to_excel(writer, sheet_name='Producción', index=False)
            
            # Hoja 3: Ventas
            if incluir_ventas and incluir_tablas:
                ventas = self.pedidos_repo.obtener_historial_ventas(fecha_inicio, fecha_fin)
                if ventas:
                    df_ventas = pd.DataFrame(ventas)
                    df_ventas.to_excel(writer, sheet_name='Ventas', index=False)
            
            # Hoja 4: Financiero
            if incluir_financiero and incluir_tablas:
                movimientos = self.reportes_repo.obtener_todos_movimientos(fecha_inicio, fecha_fin)
                if movimientos:
                    df_mov = pd.DataFrame(movimientos)
                    df_mov.to_excel(writer, sheet_name='Movimientos', index=False)
        
        output.seek(0)
        return output.getvalue()


# Función principal para llamar desde app.py
def render_reportes():
    """Función principal que se llama desde app.py"""
    module = ReportesModule()
    module.render()


# Para testing en Jupyter
if __name__ == "__main__":
    render_reportes()
