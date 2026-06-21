# 🐣 Pío Pío Baena — Sistema de Gestión Avícola

Sistema de gestión operativa para una granja familiar de gallinas ponedoras, desarrollado en **Python + Streamlit + SQLite**.

Cubre el control integral de producción de huevos, inventario de insumos, ventas, pedidos, despachos e informes. Diseñado como herramienta real de uso diario, con énfasis en trazabilidad, automatización y simplicidad de operación.

---

## 📁 Versiones en este repositorio

Este repositorio conserva el historial de desarrollo del sistema en sus dos versiones Streamlit:

### [`PioPioBaena_v1.0/`](./PioPioBaena_v1.0)
Primera versión funcional del sistema. Cubre todos los módulos principales y establece la arquitectura base (separación de capas, esquema SQL, triggers automáticos). Versión operativa pero con algunas inconsistencias menores en la interfaz y lógica de negocio.

**Stack:** Python · Streamlit · SQLite

### [`PioPioBaena_v1.1/`](./PioPioBaena_v1.1)
Versión pulida y estable del sistema. Corrige los problemas identificados en v1.0, refina la experiencia de usuario, consolida la lógica de módulos y deja el sistema listo para uso familiar continuo.

**Stack:** Python · Streamlit · SQLite

---

## 🧠 Arquitectura general

Ambas versiones comparten la misma arquitectura en tres capas:

- **Interfaz** — Streamlit (páginas por módulo)
- **Lógica de negocio** — módulos Python independientes
- **Persistencia** — SQLite con esquema relacional y triggers automáticos

Esta separación facilita el mantenimiento y una eventual migración a base de datos remota o interfaz alternativa.

---

## 🔒 Datos y privacidad

Los archivos `.db` con datos reales **no se incluyen** en el repositorio. Se publican únicamente:

- Esquema SQL (`schema.sql`)
- Scripts de creación de tablas
- Datos de ejemplo ficticios donde aplique

---

## 📌 Nota

Proyecto de uso familiar real, desarrollado de forma incremental como herramienta operativa y ejercicio de ingeniería de software aplicada.
