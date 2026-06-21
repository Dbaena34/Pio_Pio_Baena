"""
Módulo de Insumos y Pagos
Gestiona compras de insumos, pagos a trabajadores, configuración de precios y resumen financiero
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
from data.models import InsumosRepository, TrabajadoresRepository, PreciosRepository, ReportesRepository


class InsumosPagosModule:
    """Clase principal del módulo de insumos y pagos"""
    
    def __init__(self):
        self.insumos_repo = InsumosRepository(db)
        self.trabajadores_repo = TrabajadoresRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.reportes_repo = ReportesRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
    
    def render(self):
        """Renderiza la interfaz completa del módulo"""
        st.header("💰 Gestión de Insumos y Pagos")
        
        # Crear tabs
        tabs = st.tabs(["🛒 Comprar Insumos", "💵 Pagar Trabajadores", "💲 Configurar Precios", "📊 Resumen Financiero"])
        
        with tabs[0]:
            self._render_comprar_insumos()
        
        with tabs[1]:
            self._render_pagar_trabajadores()
        
        with tabs[2]:
            self._render_configurar_precios()
        
        with tabs[3]:
            self._render_resumen_financiero()
    
    def _render_comprar_insumos(self):
        """Renderiza el formulario de compra de insumos"""
        st.subheader("🛒 Registrar Compra de Insumos")
        
        st.markdown("### 📝 Nueva Compra")
        
        col_fecha, col_proveedor = st.columns([1, 2])
        
        with col_fecha:
            fecha_compra = st.date_input(
                "Fecha de compra",
                value=date.today(),
                key="fecha_compra_insumo"
            )
        
        with col_proveedor:
            proveedor = st.text_input(
                "Proveedor (opcional)",
                placeholder="Nombre del proveedor",
                key="proveedor_insumo"
            )
        
        st.markdown("---")
        
        col_nombre, col_categoria = st.columns(2)
        
        with col_nombre:
            nombre_insumo = st.text_input(
                "Nombre del insumo *",
                placeholder="Ej: Alimento concentrado, Vitaminas, etc.",
                key="nombre_insumo"
            )
        
        with col_categoria:
            categoria = st.selectbox(
                "Categoría *",
                options=['Alimento', 'Medicamento', 'Mantenimiento', 'Canastillas', 'Otros'],
                key="categoria_insumo"
            )
        
        col_cantidad, col_unidad = st.columns(2)
        
        with col_cantidad:
            cantidad = st.number_input(
                "Cantidad *",
                min_value=0.0,
                step=1.0,
                value=0.0,
                key="cantidad_insumo"
            )
        
        with col_unidad:
            unidad = st.selectbox(
                "Unidad *",
                options=['kg', 'bultos', 'litros', 'unidades'],
                key="unidad_insumo"
            )
        
        col_unitario, col_total = st.columns(2)
        
        with col_unitario:
            costo_unitario = st.number_input(
                "Costo unitario *",
                min_value=0.0,
                step=100.0,
                value=0.0,
                format="%.2f",
                key="costo_unitario"
            )
        
        with col_total:
            # Calcular costo total automáticamente
            costo_total_calculado = cantidad * costo_unitario
            costo_total = st.number_input(
                "Costo total *",
                min_value=0.0,
                step=100.0,
                value=costo_total_calculado,
                format="%.2f",
                key="costo_total",
                help="Se calcula automáticamente pero puedes ajustarlo"
            )
        
        if costo_total > 0 and cantidad > 0:
            st.info(f"💰 Costo por {unidad}: ${costo_total / cantidad:,.2f}")
        
        st.markdown("---")
        
        col_btn, col_resumen = st.columns([1, 2])
        
        with col_btn:
            if st.button("💾 Registrar Compra", use_container_width=True, type="primary", key="btn_comprar_insumo"):
                if nombre_insumo and cantidad > 0 and costo_total > 0:
                    try:
                        insumo_id = self.insumos_repo.registrar_compra_insumo(
                            nombre=nombre_insumo,
                            categoria=categoria,
                            cantidad=cantidad,
                            unidad=unidad,
                            costo_unitario=costo_unitario,
                            costo_total=costo_total,
                            fecha_compra=fecha_compra,
                            proveedor=proveedor if proveedor else None
                        )
                        
                        st.success(f"✅ Compra registrada exitosamente (ID: {insumo_id})")
                        st.success(f"💰 Egreso de ${costo_total:,.2f} registrado")
                        st.success(f"📦 Stock actualizado: +{cantidad} {unidad}")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al registrar compra: {str(e)}")
                else:
                    st.warning("⚠️ Completa todos los campos obligatorios (*)")
        
        with col_resumen:
            if costo_total > 0:
                st.markdown(f"""
                **Resumen de la compra:**
                - 📦 {cantidad} {unidad} de {nombre_insumo or '[nombre]'}
                - 💰 Total: ${costo_total:,.2f}
                - 📊 Categoría: {categoria}
                """)
        
        # Historial reciente
        st.markdown("---")
        st.markdown("### 📋 Historial de Compras Recientes")
        
        col_hist1, col_hist2 = st.columns(2)
        
        with col_hist1:
            fecha_inicio_hist = st.date_input(
                "Desde",
                value=date.today() - timedelta(days=30),
                key="hist_compras_inicio"
            )
        
        with col_hist2:
            fecha_fin_hist = st.date_input(
                "Hasta",
                value=date.today(),
                key="hist_compras_fin"
            )
        
        try:
            historial = self.insumos_repo.obtener_historial_compras(fecha_inicio_hist, fecha_fin_hist)
            
            if historial:
                df = pd.DataFrame(historial)
                
                # Métricas
                col_m1, col_m2, col_m3 = st.columns(3)
                
                with col_m1:
                    st.metric("Total Compras", len(df))
                
                with col_m2:
                    total_gastado = df['costo_total'].sum()
                    st.metric("Total Gastado", f"${total_gastado:,.0f}")
                
                with col_m3:
                    # Categoría más comprada
                    cat_top = df.groupby('categoria')['costo_total'].sum().idxmax()
                    st.metric("Categoría Top", cat_top)
                
                st.markdown("---")
                
                # Tabla
                df_display = df[['fecha_compra', 'nombre', 'categoria', 'cantidad', 'unidad', 
                                'costo_unitario', 'costo_total', 'proveedor']].copy()
                df_display.columns = ['Fecha', 'Insumo', 'Categoría', 'Cantidad', 'Unidad', 
                                     'Costo Unit.', 'Costo Total', 'Proveedor']
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Costo Unit.": st.column_config.NumberColumn(format="$%.2f"),
                        "Costo Total": st.column_config.NumberColumn(format="$%,.0f")
                    }
                )
                
                # Exportar
                if st.button("📥 Exportar a CSV", key="exportar_compras"):
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"compras_{fecha_inicio_hist}_a_{fecha_fin_hist}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("ℹ️ No hay compras registradas en este período")
        
        except Exception as e:
            st.error(f"❌ Error al cargar historial: {str(e)}")
    
    def _render_pagar_trabajadores(self):
        """Renderiza el formulario de pago a trabajadores"""
        st.subheader("💵 Registrar Pago a Trabajadores")
        
        try:
            trabajadores = self.trabajadores_repo.obtener_trabajadores_activos()
            
            if not trabajadores:
                st.warning("⚠️ No hay trabajadores registrados")
                
                # Formulario rápido para agregar trabajador
                st.markdown("### ➕ Agregar Trabajador")
                
                col_nuevo1, col_nuevo2 = st.columns(2)
                
                with col_nuevo1:
                    nombre_nuevo = st.text_input("Nombre del trabajador", key="nuevo_trabajador_nombre")
                
                with col_nuevo2:
                    cargo_nuevo = st.text_input("Cargo (opcional)", key="nuevo_trabajador_cargo")
                
                if st.button("💾 Crear Trabajador", key="btn_crear_trabajador"):
                    if nombre_nuevo:
                        try:
                            self.trabajadores_repo.crear_trabajador(
                                nombre=nombre_nuevo,
                                cargo=cargo_nuevo if cargo_nuevo else None
                            )
                            st.success(f"✅ Trabajador '{nombre_nuevo}' creado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    else:
                        st.warning("⚠️ Ingresa el nombre del trabajador")
                
                return
            
            st.markdown("### 💰 Nuevo Pago")
            
            # Seleccionar trabajador
            trabajador_seleccionado = st.selectbox(
                "Seleccionar trabajador",
                options=[t['id'] for t in trabajadores],
                format_func=lambda x: f"{next((t['nombre'] for t in trabajadores if t['id'] == x), '')} - {next((t.get('cargo', 'Sin cargo') for t in trabajadores if t['id'] == x), '')}",
                key="select_trabajador_pago"
            )
            
            if trabajador_seleccionado:
                trabajador_data = next((t for t in trabajadores if t['id'] == trabajador_seleccionado), None)
                
                st.info(f"👤 **{trabajador_data['nombre']}** - {trabajador_data.get('cargo', 'Sin cargo')}")
                
                col_fecha, col_hora = st.columns(2)
                
                with col_fecha:
                    fecha_pago = st.date_input(
                        "Fecha del pago",
                        value=date.today(),
                        key="fecha_pago"
                    )
                
                with col_hora:
                    hora_pago = st.time_input(
                        "Hora del pago",
                        value=datetime.now().time(),
                        key="hora_pago"
                    )
                
                col_monto, col_concepto = st.columns([1, 2])
                
                with col_monto:
                    monto_pago = st.number_input(
                        "Monto a pagar *",
                        min_value=0.0,
                        step=1000.0,
                        value=0.0,
                        format="%.2f",
                        key="monto_pago"
                    )
                
                with col_concepto:
                    concepto_pago = st.text_input(
                        "Concepto",
                        placeholder="Ej: Pago días 1-15 enero, Pago semanal, etc.",
                        key="concepto_pago"
                    )
                
                st.markdown("---")
                
                if st.button("💾 Registrar Pago", use_container_width=True, type="primary", key="btn_pagar_trabajador"):
                    if monto_pago > 0:
                        try:
                            pago_id = self.insumos_repo.registrar_pago_trabajador(
                                trabajador_id=trabajador_seleccionado,
                                fecha=fecha_pago,
                                hora=hora_pago.strftime("%H:%M:%S"),
                                monto=monto_pago,
                                concepto=concepto_pago if concepto_pago else None
                            )
                            
                            st.success(f"✅ Pago registrado exitosamente (ID: {pago_id})")
                            st.success(f"💰 Egreso de ${monto_pago:,.2f} registrado")
                            st.balloons()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al registrar pago: {str(e)}")
                    else:
                        st.warning("⚠️ Ingresa un monto mayor a 0")
                
                # Historial del trabajador
                st.markdown("---")
                st.markdown(f"### 📋 Historial de Pagos - {trabajador_data['nombre']}")
                
                col_hist1, col_hist2 = st.columns(2)
                
                with col_hist1:
                    fecha_inicio_trab = st.date_input(
                        "Desde",
                        value=date.today() - timedelta(days=30),
                        key="hist_trab_inicio"
                    )
                
                with col_hist2:
                    fecha_fin_trab = st.date_input(
                        "Hasta",
                        value=date.today(),
                        key="hist_trab_fin"
                    )
                
                pagos_trabajador = self.insumos_repo.obtener_pagos_por_trabajador(
                    trabajador_seleccionado, fecha_inicio_trab, fecha_fin_trab
                )
                
                if pagos_trabajador:
                    df_pagos = pd.DataFrame(pagos_trabajador)
                    
                    # Métricas
                    col_m1, col_m2, col_m3 = st.columns(3)
                    
                    with col_m1:
                        st.metric("Total Pagos", len(df_pagos))
                    
                    with col_m2:
                        total_pagado = df_pagos['monto'].sum()
                        st.metric("Total Pagado", f"${total_pagado:,.0f}")
                    
                    with col_m3:
                        promedio = df_pagos['monto'].mean()
                        st.metric("Promedio por Pago", f"${promedio:,.0f}")
                    
                    st.markdown("---")
                    
                    # Tabla
                    df_display = df_pagos[['fecha', 'hora', 'monto', 'concepto']].copy()
                    df_display.columns = ['Fecha', 'Hora', 'Monto', 'Concepto']
                    
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Monto": st.column_config.NumberColumn(format="$%,.0f")
                        }
                    )
                else:
                    st.info(f"ℹ️ No hay pagos registrados para {trabajador_data['nombre']} en este período")
            
            # Historial general de pagos
            st.markdown("---")
            st.markdown("### 📊 Historial General de Pagos")
            
            col_hist_gen1, col_hist_gen2 = st.columns(2)
            
            with col_hist_gen1:
                fecha_inicio_gen = st.date_input(
                    "Desde",
                    value=date.today() - timedelta(days=30),
                    key="hist_pagos_gen_inicio"
                )
            
            with col_hist_gen2:
                fecha_fin_gen = st.date_input(
                    "Hasta",
                    value=date.today(),
                    key="hist_pagos_gen_fin"
                )
            
            historial_general = self.insumos_repo.obtener_historial_pagos(fecha_inicio_gen, fecha_fin_gen)
            
            if historial_general:
                df_general = pd.DataFrame(historial_general)
                
                # Métricas generales
                col_mg1, col_mg2, col_mg3 = st.columns(3)
                
                with col_mg1:
                    st.metric("Total Pagos", len(df_general))
                
                with col_mg2:
                    total_general = df_general['monto'].sum()
                    st.metric("Total Pagado", f"${total_general:,.0f}")
                
                with col_mg3:
                    # Trabajador con más pagos
                    top_trabajador = df_general.groupby('trabajador_nombre')['monto'].sum().idxmax()
                    st.metric("Top Trabajador", top_trabajador)
                
                st.markdown("---")
                
                # Gráfico por trabajador
                pagos_por_trabajador = df_general.groupby('trabajador_nombre')['monto'].sum().sort_values(ascending=True)
                
                fig = px.bar(
                    x=pagos_por_trabajador.values,
                    y=pagos_por_trabajador.index,
                    orientation='h',
                    title='Total Pagado por Trabajador',
                    labels={'x': 'Total Pagado ($)', 'y': 'Trabajador'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla general
                df_display_gen = df_general[['fecha', 'trabajador_nombre', 'monto', 'concepto']].copy()
                df_display_gen.columns = ['Fecha', 'Trabajador', 'Monto', 'Concepto']
                
                st.dataframe(
                    df_display_gen,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Monto": st.column_config.NumberColumn(format="$%,.0f")
                    }
                )
                
                # Exportar
                if st.button("📥 Exportar a CSV", key="exportar_pagos"):
                    csv = df_display_gen.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"pagos_{fecha_inicio_gen}_a_{fecha_fin_gen}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("ℹ️ No hay pagos registrados en este período")
        
        except Exception as e:
            st.error(f"❌ Error al cargar trabajadores: {str(e)}")
    
    def _render_configurar_precios(self):
        """Renderiza la configuración de precios de huevos"""
        st.subheader("💲 Configuración de Precios de Huevos")
        
        try:
            # Obtener precio actual
            precios_actuales = self.precios_repo.obtener_precio_actual()
            
            st.markdown("### 💰 Precios Actuales")
            
            if precios_actuales:
                st.info(f"📅 Vigente desde: {precios_actuales['fecha_vigencia']}")
                
                cols_precios = st.columns(6)
                categorias_db = ['precio_c', 'precio_b', 'precio_a', 'precio_aa', 'precio_aaa', 'precio_jumbo']
                
                for col, cat, precio_db in zip(cols_precios, self.categorias_huevos, categorias_db):
                    with col:
                        precio = precios_actuales.get(precio_db, 0)
                        precio_canastilla = precio * 30
                        st.metric(
                            f"Tipo {cat}",
                            f"${precio:,.0f}",
                            delta=f"${precio_canastilla:,.0f}/can.",
                            help=f"Precio por huevo / Precio por canastilla (30 huevos)"
                        )
            else:
                st.warning("⚠️ No hay precios configurados")
            
            st.markdown("---")
            st.markdown("### ✏️ Actualizar Precios")
            
            st.info("💡 Al actualizar los precios, se creará un nuevo registro y se desactivará el anterior automáticamente")
            
            fecha_vigencia = st.date_input(
                "Fecha de vigencia",
                value=date.today(),
                key="fecha_vigencia_precios"
            )
            
            st.markdown("**Ingresa los nuevos precios por huevo:**")
            
            cols_nuevos = st.columns(6)
            nuevos_precios = {}
            
            for col, cat, precio_db in zip(cols_nuevos, self.categorias_huevos, categorias_db):
                with col:
                    precio_actual = precios_actuales.get(precio_db, 0) if precios_actuales else 0
                    nuevos_precios[cat] = st.number_input(
                        f"💰 {cat}",
                        min_value=0.0,
                        step=10.0,
                        value=float(precio_actual),
                        format="%.0f",
                        key=f"nuevo_precio_{cat}",
                        help="Precio por huevo individual"
                    )
            
            # Mostrar precios por canastilla
            st.markdown("**Precios por canastilla (30 huevos):**")
            cols_canastilla = st.columns(6)
            
            for col, cat in zip(cols_canastilla, self.categorias_huevos):
                with col:
                    precio_can = nuevos_precios[cat] * 30
                    st.success(f"{cat}: ${precio_can:,.0f}")
            
            st.markdown("---")
            
            if st.button("💾 Guardar Nuevos Precios", use_container_width=True, type="primary", key="btn_guardar_precios"):
                if all(nuevos_precios[cat] > 0 for cat in self.categorias_huevos):
                    try:
                        precio_id = self.precios_repo.crear_nuevo_precio(
                            fecha_vigencia=fecha_vigencia,
                            precio_c=nuevos_precios['C'],
                            precio_b=nuevos_precios['B'],
                            precio_a=nuevos_precios['A'],
                            precio_aa=nuevos_precios['AA'],
                            precio_aaa=nuevos_precios['AAA'],
                            precio_jumbo=nuevos_precios['Jumbo']
                        )
                        
                        st.success(f"✅ Precios actualizados exitosamente (ID: {precio_id})")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al actualizar precios: {str(e)}")
                else:
                    st.warning("⚠️ Todos los precios deben ser mayores a 0")
            
            # Historial de precios
            st.markdown("---")
            st.markdown("### 📜 Historial de Precios")
            
            historial_precios = self.precios_repo.obtener_historial_precios(limit=10)
            
            if historial_precios:
                df_precios = pd.DataFrame(historial_precios)
                
                df_display = df_precios[['fecha_vigencia', 'precio_c', 'precio_b', 'precio_a', 
                                        'precio_aa', 'precio_aaa', 'precio_jumbo', 'activo']].copy()
                df_display.columns = ['Fecha Vigencia', 'C', 'B', 'A', 'AA', 'AAA', 'Jumbo', 'Activo']
                
                # Reemplazar activo por emoji
                df_display['Activo'] = df_display['Activo'].apply(lambda x: '✅' if x == 1 else '❌')
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "C": st.column_config.NumberColumn(format="$%.0f"),
                        "B": st.column_config.NumberColumn(format="$%.0f"),
                        "A": st.column_config.NumberColumn(format="$%.0f"),
                        "AA": st.column_config.NumberColumn(format="$%.0f"),
                        "AAA": st.column_config.NumberColumn(format="$%.0f"),
                        "Jumbo": st.column_config.NumberColumn(format="$%.0f")
                    }
                )
            else:
                st.info("ℹ️ No hay historial de precios")
        
        except Exception as e:
            st.error(f"❌ Error al cargar precios: {str(e)}")
    
    def _render_resumen_financiero(self):
        """Renderiza el resumen financiero de egresos"""
        st.subheader("📊 Resumen Financiero de Egresos")
        
        # Filtros de fecha
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_inicio = st.date_input(
                "Desde",
                value=date.today() - timedelta(days=30),
                key="resumen_fecha_inicio"
            )
        
        with col2:
            fecha_fin = st.date_input(
                "Hasta",
                value=date.today(),
                key="resumen_fecha_fin"
            )
        
        try:
            # Obtener datos
            balance = self.reportes_repo.obtener_balance_periodo(fecha_inicio, fecha_fin)
            movimientos_categoria = self.reportes_repo.obtener_movimientos_por_categoria(fecha_inicio, fecha_fin)
            compras_categoria = self.insumos_repo.obtener_compras_por_categoria(fecha_inicio, fecha_fin)
            historial_pagos = self.insumos_repo.obtener_historial_pagos(fecha_inicio, fecha_fin)
            
            # Métricas principales
            st.markdown("### 💰 Resumen del Período")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                total_egresos = balance.get('total_egresos', 0) or 0
                st.metric("Total Egresos", f"${total_egresos:,.0f}", delta=None)
            
            with col_m2:
                total_ingresos = balance.get('total_ingresos', 0) or 0
                st.metric("Total Ingresos", f"${total_ingresos:,.0f}", delta=None)
            
            with col_m3:
                balance_neto = balance.get('balance', 0) or 0
                color_delta = "normal" if balance_neto >= 0 else "inverse"
                st.metric(
                    "Balance Neto", 
                    f"${balance_neto:,.0f}",
                    delta=f"{'Positivo' if balance_neto >= 0 else 'Negativo'}",
                    delta_color=color_delta
                )
            
            with col_m4:
                if total_ingresos > 0:
                    margen = (balance_neto / total_ingresos) * 100
                    st.metric("Margen", f"{margen:.1f}%")
                else:
                    st.metric("Margen", "N/A")
            
            st.markdown("---")
            
            # Egresos por categoría
            st.markdown("### 📊 Egresos por Categoría")
            
            if movimientos_categoria:
                df_mov = pd.DataFrame(movimientos_categoria)
                df_egresos = df_mov[df_mov['tipo'] == 'egreso']
                
                if not df_egresos.empty:
                    col_graf1, col_graf2 = st.columns(2)
                    
                    with col_graf1:
                        # Gráfico de barras
                        fig_bar = px.bar(
                            df_egresos,
                            x='categoria',
                            y='total',
                            title='Egresos por Categoría',
                            labels={'categoria': 'Categoría', 'total': 'Total ($)'},
                            color='categoria'
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    with col_graf2:
                        # Gráfico de torta
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=df_egresos['categoria'],
                            values=df_egresos['total'],
                            hole=0.3
                        )])
                        fig_pie.update_layout(title='Distribución de Egresos (%)')
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Tabla de egresos
                    df_display = df_egresos[['categoria', 'cantidad_movimientos', 'total']].copy()
                    df_display.columns = ['Categoría', 'Cantidad', 'Total']
                    
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total": st.column_config.NumberColumn(format="$%,.0f")
                        }
                    )
            
            # Detalle de compras por categoría de insumo
            st.markdown("---")
            st.markdown("### 🛒 Compras de Insumos por Categoría")
            
            if compras_categoria:
                df_compras = pd.DataFrame(compras_categoria)
                
                col_tabla, col_graf = st.columns([1, 1])
                
                with col_tabla:
                    df_display_compras = df_compras[['categoria', 'cantidad_compras', 'total_gastado']].copy()
                    df_display_compras.columns = ['Categoría', 'Compras', 'Total Gastado']
                    
                    st.dataframe(
                        df_display_compras,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Gastado": st.column_config.NumberColumn(format="$%,.0f")
                        }
                    )
                
                with col_graf:
                    fig_compras = px.pie(
                        df_compras,
                        names='categoria',
                        values='total_gastado',
                        title='Distribución de Gastos en Insumos'
                    )
                    st.plotly_chart(fig_compras, use_container_width=True)
            else:
                st.info("ℹ️ No hay compras de insumos en este período")
            
            # Detalle de pagos a trabajadores
            st.markdown("---")
            st.markdown("### 💵 Pagos a Trabajadores")
            
            if historial_pagos:
                df_pagos = pd.DataFrame(historial_pagos)
                
                # Resumen por trabajador
                pagos_por_trabajador = df_pagos.groupby('trabajador_nombre')['monto'].agg(['sum', 'count']).reset_index()
                pagos_por_trabajador.columns = ['Trabajador', 'Total Pagado', 'Cantidad Pagos']
                
                col_tabla_pag, col_graf_pag = st.columns([1, 1])
                
                with col_tabla_pag:
                    st.dataframe(
                        pagos_por_trabajador,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Pagado": st.column_config.NumberColumn(format="$%,.0f")
                        }
                    )
                
                with col_graf_pag:
                    fig_pagos = px.bar(
                        pagos_por_trabajador,
                        x='Trabajador',
                        y='Total Pagado',
                        title='Total Pagado por Trabajador',
                        color='Trabajador'
                    )
                    st.plotly_chart(fig_pagos, use_container_width=True)
            else:
                st.info("ℹ️ No hay pagos a trabajadores en este período")
        
        except Exception as e:
            st.error(f"❌ Error al cargar resumen financiero: {str(e)}")


# Función principal para llamar desde app.py
def render_insumos_pagos():
    """Función principal que se llama desde app.py"""
    module = InsumosPagosModule()
    module.render()


# Para testing en Jupyter
if __name__ == "__main__":
    render_insumos_pagos()
