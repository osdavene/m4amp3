# 🎵 Conversor de M4A a MP3 (Desktop & Web)

Aplicación para convertir archivos de audio en formato **M4A (AAC/ALAC)** a **MP3** con calidad ajustable (128 kbps, 192 kbps, 256 kbps, 320 kbps). Cuenta tanto con **interfaz de escritorio (Tkinter)** como con **interfaz web moderna (FastAPI + HTML5/CSS3)** lista para ser desplegada en servidores o contenedores Docker.

---

## ✨ Características

- ⚡ **Conversión Rápida**: Basada directamente en el motor nativo de **FFmpeg**.
- 🌐 **Versión Web Moderna**: Interfaz limpia con *Drag & Drop*, procesamiento individual y por lotes con descarga directa o empaquetado automático en `.zip`.
- 🖥️ **Versión de Escritorio**: GUI nativa en Tkinter para procesar carpetas enteras y subcarpetas en tu computadora.
- 🎚️ **Calidad Seleccionable**: 128 kbps (Estándar), 192 kbps (Recomendada), 256 kbps (Alta calidad) y 320 kbps (Máxima fidelidad).
- 🔒 **Privacidad Total**: En la versión web, los archivos temporales de entrada y salida se eliminan automáticamente del servidor una vez completada la entrega.
- 🐳 **Docker Ready**: Empaquetado listo para correr en cualquier servidor Linux o Cloud con un solo comando.

---

## 📁 Estructura del Proyecto

```text
m4amp3/
├── converter.py          # Módulo central de conversión con FFmpeg
├── app.py                # Aplicación de escritorio (Tkinter)
├── server.py             # Servidor Web y API REST (FastAPI)
├── templates/
│   └── index.html        # Interfaz Web responsiva
├── static/
│   ├── css/style.css     # Estilos modernos y animaciones
│   └── js/main.js        # Lógica de arrastrar/soltar y subida
├── Dockerfile            # Configuración para contenedor Docker
├── docker-compose.yml    # Orquestación con Docker Compose
├── requirements.txt      # Dependencias de Python
└── README.md             # Documentación del proyecto
```

---

## 🚀 Instalación y Uso Local

### 1. Clonar el repositorio y configurar el entorno

```bash
git clone https://github.com/osdavene/m4amp3.git
cd m4amp3

# Crear entorno virtual (opcional pero recomendado)
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación Web

```bash
python server.py
# O usando uvicorn directamente:
uvicorn server:app --reload --port 8000
```

Abre tu navegador en: [http://localhost:8000](http://localhost:8000)

### 3. Ejecutar la Aplicación de Escritorio

```bash
python app.py
```

---

## 🐳 Despliegue con Docker

Para correr la versión web en cualquier servidor con Docker instalado:

```bash
# Construir y levantar el contenedor en segundo plano
docker compose up -d --build
```

El servicio estará disponible inmediatamente en `http://tu-servidor-o-ip:8000`.

Para detener el servicio:
```bash
docker compose down
```

---

## ☁️ Despliegue en la Nube (Render, Railway, Fly.io, VPS)

### Opción A: Render / Railway / Fly.io
1. Sube este repositorio a tu cuenta de GitHub (`osdavene/m4amp3`).
2. En tu panel de **Render** o **Railway**, crea un nuevo *Web Service* vinculado a tu repositorio.
3. El servicio detectará automáticamente el `Dockerfile` y expondrá la aplicación web en el puerto `8000` con certificado SSL HTTPS gratuito.

### Opción B: En tu propio VPS (Ubuntu / Debian)
```bash
git clone https://github.com/osdavene/m4amp3.git
cd m4amp3
docker compose up -d
```

---

## 🔌 API REST

### `POST /api/convert`
Convierte uno o varios archivos `.m4a` a `.mp3`.

- **Parámetros (`multipart/form-data`):**
  - `files`: Archivos de audio `.m4a` (uno o varios).
  - `bitrate`: Opcional (`128k`, `192k`, `256k`, `320k` - por defecto `192k`).
- **Respuesta:**
  - Si es **1 archivo**: Retorna el archivo `.mp3` con cabecera `Content-Disposition`.
  - Si son **múltiples archivos**: Retorna un archivo `.zip` con todos los `.mp3` convertidos.

### `GET /api/health`
Verifica el estado del servicio y la disponibilidad del ejecutable FFmpeg en el sistema.

---

## 👤 Autor

- **Oscar** ([@osdavene](https://github.com/osdavene))
