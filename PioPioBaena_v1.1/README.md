# 📊 Pío Pío Baena v1.1 — Sistema de Gestión Avícola

Versión **estable y pulida** del sistema de gestión para granja familiar de gallinas ponedoras. Desarrollada en **Streamlit + SQLite**, esta versión corrige las inconsistencias de v1.0 y consolida todos los módulos en un sistema completamente operativo.

---

## ✅ Mejoras respecto a v1.0

- Lógica de negocio revisada y corregida en todos los módulos
- Interfaz más consistente y sin comportamientos inesperados
- Triggers SQL y validaciones de datos estabilizados
- Flujos de usuario probados en uso real continuo

---

## 🧠 Arquitectura del proyecto

- **Frontend**: Streamlit
- **Base de datos**: SQLite
- **Lenguaje**: Python
- **Persistencia**: Base relacional local

La lógica está organizada en tres capas separadas:

- Capa de interfaz (`modules/`)
- Capa de acceso a datos (`utils/`)
- Estructura SQL (`data/schema.sql`)

---

## 📦 Módulos del sistema

| Módulo | Descripción |
|---|---|
| Producción | Registro diario de huevos por categoría |
| Insumos | Control de stock de alimento y suministros |
| Ventas | Registro de ventas por cliente y categoría |
| Pedidos | Gestión de pedidos pendientes |
| Despachos | Confirmación y trazabilidad de entregas |
| Informes | Reportes de producción, ventas e inventario |

---

## 📁 Estructura del repositorio

```
PioPioBaena_v1.1/
│
├── app.py
├── config.py
├── requirements.txt
│
├── data/
│   └── schema.sql
│
├── modules/        # Páginas Streamlit por módulo
├── utils/          # Acceso a datos y lógica compartida
├── images/
├── fonts/
│
└── README.md
```

---

## 🔒 Protección de datos

Los archivos `.db` con datos reales **no se incluyen** en el repositorio. Se publica únicamente:

- Esquema SQL de todas las tablas
- Scripts de creación y triggers
- Datos de ejemplo ficticios donde aplique

---

## 💾 Backups

La base activa se mantiene en entorno local. Los respaldos se generan como copias cerradas y se almacenan en unidades externas o nube privada. Este repositorio no se usa como sistema de backup de producción.

---

## 🚀 Ejecución local

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:

```bash
streamlit run app.py
```

---

## 📌 Nota

Versión final del sistema en Streamlit. El desarrollo posterior del proyecto continúa en una nueva arquitectura de escritorio (CustomTkinter), optimizada para el hardware disponible en el entorno familiar.
