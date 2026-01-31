"""
Módulo de Producción Diaria
Gestiona el registro y visualización de la producción de huevos
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict
from modules import utils as util

# Importar la base de datos y repositorios
import sys
sys.path.append('..')
from data.database import db
from data.models import ProduccionRepository, StockRepository, GallinasRepository


class ProduccionModule:
    """Clase principal del módulo de producción"""
    
    def __init__(self):
        self.produccion_repo = ProduccionRepository(db)
        self.stock_repo = StockRepository(db)
        self.gallinas_repo = GallinasRepository(db)
        self.categorias = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
    
    def render(self):
        """Renderiza la interfaz completa del módulo"""
        #util.set_custom_style()
        st.header("📊 Gestión de Producción Diaria")
        
        # Crear sub-tabs dentro de producción
        tabs = st.tabs(["➕ Registrar Producción", "📋 Historial", "📊 Análisis"])
        
        with tabs[0]:
            self._render_registro_produccion()
        
        with tabs[1]:
            self._render_historial()
        
        with tabs[2]:
            self._render_analisis()
    
    def _render_registro_produccion(self):
        """Formulario para registrar producción diaria"""
        st.subheader("Registrar Producción del Día")
        
        # ==================== FORMULARIO 1: PRODUCCIÓN DE HUEVOS ====================
        with st.form("form_produccion", clear_on_submit=True):
            col_fecha, col_hora = st.columns([2, 1])
            
            with col_fecha:
                fecha = st.date_input(
                    "Fecha de recolección",
                    value=date.today(),
                    max_value=date.today()
                )
            
            with col_hora:
                hora = st.time_input(
                    "Hora de recolección",
                    value=datetime.now().time()
                )
            
            st.markdown("---")
            st.markdown("**Cantidad por categoría:**")
            
            # Inputs de cantidades en columnas
            col_c, col_b, col_a, col_aa, col_aaa, col_jumbo = st.columns(6)
            
            with col_c:
                tipo_c = st.number_input("🥚 Tipo C", min_value=0, step=1, value=0)
            with col_b:
                tipo_b = st.number_input("🥚 Tipo B", min_value=0, step=1, value=0)
            with col_a:
                tipo_a = st.number_input("🥚 Tipo A", min_value=0, step=1, value=0)
            with col_aa:
                tipo_aa = st.number_input("🥚 Tipo AA", min_value=0, step=1, value=0)
            with col_aaa:
                tipo_aaa = st.number_input("🥚 Tipo AAA", min_value=0, step=1, value=0)
            with col_jumbo:
                tipo_jumbo = st.number_input("🥚 Jumbo", min_value=0, step=1, value=0)
            
            # Calcular total
            total_huevos = tipo_c + tipo_b + tipo_a + tipo_aa + tipo_aaa + tipo_jumbo
            st.info(f"📦 **Total de huevos a registrar:** {total_huevos}")
            
            # Observaciones
            observaciones = st.text_area(
                "Observaciones (opcional)",
                placeholder="Ej: Temperatura alta, estrés en las aves, etc.",
                height=80
            )
            
            # Botones
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                submitted = st.form_submit_button("💾 Guardar Producción", use_container_width=True)
            with col_btn2:
                if total_huevos == 0:
                    st.warning("⚠️ Debes ingresar al menos un huevo para registrar")
        
        # Procesar el formulario de producción
        if submitted:
            if total_huevos > 0:
                try:
                    # Registrar en la base de datos
                    produccion_id = self.produccion_repo.registrar_produccion(
                        fecha=fecha,
                        hora=hora.strftime("%H:%M:%S"),  # Convertir a string
                        tipo_c=tipo_c,
                        tipo_b=tipo_b,
                        tipo_a=tipo_a,
                        tipo_aa=tipo_aa,
                        tipo_aaa=tipo_aaa,
                        tipo_jumbo=tipo_jumbo,
                        observaciones=observaciones if observaciones else None
                    )
                    
                    st.success(f"✅ Producción registrada exitosamente (ID: {produccion_id})")
                    st.success(f"📦 Total: {total_huevos} huevos agregados al stock")
                    
                    # Mostrar stock actualizado
                    stock_actual = self.stock_repo.obtener_stock_actual()
                    self._mostrar_stock_resumido(stock_actual)
                    
                except Exception as e:
                    st.error(f"❌ Error al registrar la producción: {str(e)}")
            else:
                st.error("⚠️ Debes ingresar al menos un huevo para registrar")
        
        # ==================== FORMULARIOS ADICIONALES ====================
    
        # ==================== REGISTROS ADICIONALES ====================
        st.divider()
        st.markdown("### 📋 Registros Complementarios")
        st.markdown("---")
        col_chickens, col_food = st.columns(2)
        
        # SECCIÓN 1: POBLACIÓN DE GALLINAS (sin formulario)
        with col_chickens:
            st.subheader("🐔 Población de Gallinas")
            
            # Obtener población actual
            poblacion_actual = self.gallinas_repo.obtener_poblacion_actual()
            cantidad_actual = poblacion_actual.get('cantidad_gallinas', 0)
            
            st.info(f"**Población actual:** {cantidad_actual} gallinas")
            
            cantidad_gallinas = st.number_input(
                "Cantidad total de gallinas",
                min_value=0,
                step=1,
                value=cantidad_actual,
                help="Total de gallinas ponedoras activas",
                key="input_gallinas"
            )
            
            descartes = st.number_input(
                "Descartes del día",
                min_value=0,
                step=1,
                value=0,
                help="Gallinas muertas o descartadas hoy",
                key="input_descartes"
            )
            
            obs_gallinas = st.text_input(
                "Observaciones",
                placeholder="Opcional",
                key="obs_gallinas"
            )
            
            if st.button("💾 Guardar Población", use_container_width=True, key="btn_gallinas"):
                try:
                    gallinas_id = self.gallinas_repo.registrar_poblacion(
                        fecha=date.today(),
                        hora=datetime.now().strftime("%H:%M:%S"),
                        cantidad_gallinas=cantidad_gallinas,
                        descartes=descartes,
                        observaciones=obs_gallinas if obs_gallinas else None
                    )
                    st.success(f"✅ Población registrada: {cantidad_gallinas} gallinas")
                    if descartes > 0:
                        st.info(f"📉 Descartes registrados: {descartes}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # SECCIÓN 2: CONSUMO DE ALIMENTO (sin formulario)
        with col_food:
            st.subheader("🌾 Consumo de Alimento")
            
            # Obtener población actual para el cálculo
            poblacion_actual = self.gallinas_repo.obtener_poblacion_actual()
            cantidad_gallinas_actual = poblacion_actual.get('cantidad_gallinas', 0)
            
            if cantidad_gallinas_actual > 0:
                st.info(f"**Gallinas activas:** {cantidad_gallinas_actual}")
            else:
                st.warning("⚠️ Registra primero la población de gallinas")
            
            consumo_por_gallina = st.number_input(
                "Consumo por gallina (gramos)",
                min_value=0,
                step=1,
                value=0,
                help="Gramos de alimento consumido por cada gallina hoy",
                key="input_consumo"
            )
            
            if consumo_por_gallina > 0 and cantidad_gallinas_actual > 0:
                consumo_total = consumo_por_gallina * cantidad_gallinas_actual
                st.success(f"📊 **Consumo total:** {consumo_total:.0f} gramos ({consumo_total/1000:.2f} kg)")
            
            obs_alimento = st.text_input(
                "Observaciones",
                placeholder="Opcional",
                key="obs_alimento"
            )
            
            if st.button("💾 Guardar Consumo", use_container_width=True, key="btn_alimento"):
                if consumo_por_gallina > 0 and cantidad_gallinas_actual > 0:
                    try:
                        alimento_id = self.gallinas_repo.registrar_consumo_alimento(
                            fecha=date.today(),
                            hora=datetime.now().strftime("%H:%M:%S"),
                            consumo_por_gallina=consumo_por_gallina,
                            cantidad_gallinas=cantidad_gallinas_actual,
                            observaciones=obs_alimento if obs_alimento else None
                        )
                        consumo_total = consumo_por_gallina * cantidad_gallinas_actual
                        st.success(f"✅ Consumo registrado: {consumo_total/1000:.2f} kg")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                elif cantidad_gallinas_actual == 0:
                    st.error("⚠️ Primero registra la población de gallinas")
                else:
                    st.error("⚠️ Ingresa el consumo de alimento")
        
    def _render_historial(self):
        """Muestra el historial de producción"""
        st.subheader("📋 Historial de Producción")
        
        # Filtros de fecha
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            fecha_inicio = st.date_input(
                "Fecha inicio",
                value=date.today() - timedelta(days=30)
            )
        
        with col2:
            fecha_fin = st.date_input(
                "Fecha fin",
                value=date.today()
            )
        
        with col3:
            if st.button("🔍 Buscar", use_container_width=True):
                st.rerun()
        
        # Obtener datos
        try:
            registros = self.produccion_repo.obtener_produccion_por_fecha(
                fecha_inicio, fecha_fin
            )
            
            if registros:
                # Convertir a DataFrame
                df = pd.DataFrame(registros)
                
                # Calcular total por registro
                df['total'] = (
                    df['tipo_c'] + df['tipo_b'] + df['tipo_a'] + 
                    df['tipo_aa'] + df['tipo_aaa'] + df['tipo_jumbo']
                )
                
                # Mostrar métricas
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("📅 Días registrados", len(df))
                
                with col_m2:
                    st.metric("🥚 Total producido", f"{df['total'].sum():,}")
                
                with col_m3:
                    promedio = df['total'].mean()
                    st.metric("📊 Promedio diario", f"{promedio:.0f}")
                
                with col_m4:
                    mejor_dia = df.loc[df['total'].idxmax()]
                    st.metric("🏆 Mejor día", f"{mejor_dia['total']}")
                
                st.markdown("---")
                
                # Tabla de registros
                st.markdown("**Registros detallados:**")
                
                # Preparar datos para mostrar
                df_display = df[[
                    'fecha', 'hora', 'tipo_c', 'tipo_b', 'tipo_a', 
                    'tipo_aa', 'tipo_aaa', 'tipo_jumbo', 'total', 'observaciones'
                ]].copy()
                
                # Renombrar columnas para mejor visualización
                df_display.columns = [
                    'Fecha', 'Hora', 'C', 'B', 'A', 'AA', 'AAA', 'Jumbo', 'Total', 'Observaciones'
                ]
                
                # Mostrar con opciones de formato
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                        "Hora": st.column_config.TimeColumn("Hora", format="HH:mm"),
                        "Total": st.column_config.NumberColumn("Total", format="%d 🥚")
                    }
                )
                
                # Opción de exportar
                if st.button("📥 Exportar a CSV"):
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"produccion_{fecha_inicio}_a_{fecha_fin}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("ℹ️ No hay registros en el período seleccionado")
        
        except Exception as e:
            st.error(f"❌ Error al cargar el historial: {str(e)}")
        
        
    def _render_analisis(self):
        """Renderiza gráficos y análisis de producción"""
        st.subheader("📊 Análisis de Producción")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_inicio = st.date_input(
                "Desde",
                value=date.today() - timedelta(days=30),
                key="analisis_inicio"
            )
        
        with col2:
            fecha_fin = st.date_input(
                "Hasta",
                value=date.today(),
                key="analisis_fin"
            )
        
        try:
            # Obtener datos
            registros = self.produccion_repo.obtener_produccion_por_fecha(
                fecha_inicio, fecha_fin
            )
            
            if registros:
                df = pd.DataFrame(registros)
                
                # Calcular total
                df['total'] = (
                    df['tipo_c'] + df['tipo_b'] + df['tipo_a'] + 
                    df['tipo_aa'] + df['tipo_aaa'] + df['tipo_jumbo']
                )
                
                # Convertir fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])
                
                # Gráfico 1: Producción total por día
                st.markdown("**Producción diaria total:**")
                fig_total = px.line(
                    df, 
                    x='fecha', 
                    y='total',
                    title='Producción Total por Día',
                    labels={'fecha': 'Fecha', 'total': 'Cantidad de huevos'},
                    markers=True
                )
                fig_total.update_layout(hovermode='x unified')
                st.plotly_chart(fig_total, use_container_width=True)
                
                # Gráfico 2: Producción por categoría (área apilada)
                st.markdown("**Producción por categoría:**")
                df_categorias = df[['fecha', 'tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']].copy()
                df_categorias = df_categorias.melt(
                    id_vars=['fecha'], 
                    var_name='Categoría', 
                    value_name='Cantidad'
                )
                
                # Renombrar categorías
                categoria_map = {
                    'tipo_c': 'C',
                    'tipo_b': 'B',
                    'tipo_a': 'A',
                    'tipo_aa': 'AA',
                    'tipo_aaa': 'AAA',
                    'tipo_jumbo': 'Jumbo'
                }
                df_categorias['Categoría'] = df_categorias['Categoría'].map(categoria_map)
                
                fig_categorias = px.area(
                    df_categorias,
                    x='fecha',
                    y='Cantidad',
                    color='Categoría',
                    title='Distribución de Producción por Categoría',
                    labels={'fecha': 'Fecha', 'Cantidad': 'Cantidad de huevos'}
                )
                st.plotly_chart(fig_categorias, use_container_width=True)
                
                # Gráfico 3: Distribución porcentual por categoría
                st.markdown("**Distribución total del período:**")
                total_periodo = self.produccion_repo.obtener_total_produccion_periodo(
                    fecha_inicio, fecha_fin
                )
                
                categorias_data = {
                    'C': total_periodo.get('total_c', 0) or 0,
                    'B': total_periodo.get('total_b', 0) or 0,
                    'A': total_periodo.get('total_a', 0) or 0,
                    'AA': total_periodo.get('total_aa', 0) or 0,
                    'AAA': total_periodo.get('total_aaa', 0) or 0,
                    'Jumbo': total_periodo.get('total_jumbo', 0) or 0
                }
                
                # Filtrar categorías con producción > 0
                categorias_data = {k: v for k, v in categorias_data.items() if v > 0}
                
                if categorias_data:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=list(categorias_data.keys()),
                        values=list(categorias_data.values()),
                        hole=0.3
                    )])
                    fig_pie.update_layout(title='Distribución por Categoría (%)')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Resumen estadístico
                st.markdown("---")
                st.markdown("**📈 Resumen Estadístico:**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Producción Total", f"{df['total'].sum():,} huevos")
                    st.metric("Promedio Diario", f"{df['total'].mean():.0f} huevos")
                
                with col2:
                    st.metric("Producción Máxima", f"{df['total'].max()} huevos")
                    st.metric("Producción Mínima", f"{df['total'].min()} huevos")
                
                with col3:
                    st.metric("Desviación Estándar", f"{df['total'].std():.1f}")
                    st.metric("Días Registrados", len(df))
                
            else:
                st.info("ℹ️ No hay datos suficientes para generar análisis")
        
        except Exception as e:
            st.error(f"❌ Error al generar análisis: {str(e)}")
    
    def _mostrar_stock_resumido(self, stock: Dict):
        """Muestra el stock actual de forma resumida"""
        st.markdown("---")
        st.markdown("**📦 Stock actualizado:**")
        
        cols = st.columns(6)
        categorias = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
        nombres = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        
        for col, cat, nombre in zip(cols, categorias, nombres):
            with col:
                st.metric(nombre, f"{stock.get(cat, 0):,}")


# Función principal para llamar desde app.py
def render_produccion():
    """Función principal que se llama desde app.py"""
    module = ProduccionModule()
    module.render()


# Para testing en Jupyter
if __name__ == "__main__":
    render_produccion()
