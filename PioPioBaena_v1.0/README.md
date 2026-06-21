# 📊 Sistema de Gestión de Producción y Ventas

Interfaz desarrollada en **Streamlit** para la gestión integral de:

- Producción
- Insumos
- Ventas
- Pedidos
- Despachos
- Informes

El sistema fue diseñado como una herramienta operativa real para uso familiar, con enfoque en control de datos, trazabilidad y automatización de procesos administrativos.

---

## 🧠 Arquitectura del proyecto

El sistema utiliza:

- **Frontend**: Streamlit
- **Base de datos**: SQLite
- **Lenguaje principal**: Python
- **Persistencia de datos**: Base relacional local

La lógica del sistema separa:

- capa de interfaz
- capa de acceso a datos
- estructura de base SQL

Esto permite migrar fácilmente a bases de datos remotas en el futuro.

---

## 📁 Estructura del repositorio

```
project/
│
├── app.py
├── config.py          # rutas, DB config
├── requirements.txt
│
├── data/
│   └── schema.sql     # estructura DB
│
├── modules/           #Paginas
├── utils/
├── images/
├── fonts/
│
└── README.md

```

---

## 🔒 Protección de datos

Los archivos de base de datos reales (`.db`) **no se incluyen** en el repositorio por contener información operativa y privada.

Se incluyen únicamente:

- estructura SQL
- scripts de creación de tablas
- datos de ejemplo ficticios

---

## 💾 Backups

La base activa se mantiene en entorno local.

Los respaldos se generan como copias cerradas de la base y pueden almacenarse en:

- almacenamiento externo
- nube privada
- unidades seguras

El repositorio no se utiliza como sistema de backup de producción.

---

## 🚀 Ejecución local

Instalar dependencias:

```
pip install -r requirements.txt
```

Ejecutar la aplicación:

```
streamlit run app/main.py
```

---

## 🔮 Futuro del proyecto

El sistema está preparado para:

- migración a base de datos remota
- despliegue en la nube
- uso multiusuario
- integración con reportes avanzados

---

## 📌 Nota

Proyecto en evolución continua.  
Enfocado en aprendizaje, automatización y mejora de procesos reales.
