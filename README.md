# 🎵 Conversor Universal de Audio (Desktop, Web & Android APK)

Aplicación integral para convertir archivos y carpetas completas de audio entre múltiples formatos (**MP3, M4A/AAC, WAV, FLAC, OGG, OPUS, WMA, AIFF, M4R**) y extraer audio de pistas de video (**MP4, WEBM, MKV, AVI**).

Disponible en **3 plataformas**:
1. 🌐 **Aplicación Web**: Interfaz moderna con *Drag & Drop*, subida de carpetas completas y empaquetado en ZIP.
2. 🖥️ **Aplicación de Escritorio**: GUI nativa en Tkinter para procesamiento en lotes en tu computadora.
3. 📱 **Aplicación Móvil Android**: App nativa offline con Kivy y compilación automatizada en GitHub Actions.

---

## ✨ Características

- 🎧 **Formatos Soportados**:
  - **Entrada:** `.m4a`, `.mp3`, `.wav`, `.flac`, `.ogg`, `.opus`, `.aac`, `.wma`, `.aiff`, `.m4r`, `.mp4`, `.webm`, `.mkv`, `.mov`, `.avi`, `.amr`, `.3gp`.
  - **Salida:** `.mp3`, `.m4a`, `.wav`, `.flac`, `.ogg`, `.opus`, `.wma`, `.aac`.
- 📁 **Soporte para Carpetas Completas**: Sube o selecciona carpetas y álbumes enteros con un solo clic.
- ⚡ **Motor Nativo FFmpeg**: Máxima velocidad de procesamiento y fidelidad acústica.
- 🎚️ **Calidad Adaptativa**: Selección de bitrate (`128k`, `192k`, `256k`, `320k`) o formatos de estudio sin compresión (`WAV`, `FLAC`).
- 🔒 **Privacidad Total**: Eliminación automática de archivos temporales en el servidor.
- 📱 **Compilación de APK Automatizada**: Genera el instalador `.apk` para Android en la nube con GitHub Actions.

---

## 📁 Estructura del Proyecto

```text
m4amp3/
├── converter.py              # Motor central universal de audio (FFmpeg)
├── server.py                 # Servidor Web y API REST (FastAPI)
├── app.py                    # Aplicación de escritorio (Tkinter)
├── mobile_app.py             # Aplicación móvil para Android (Kivy)
├── buildozer.spec            # Configuración de empaquetado para Android
├── templates/
│   └── index.html            # Interfaz Web moderna
├── static/
│   ├── css/style.css         # Estilos y animaciones
│   └── js/main.js            # Lógica interactiva y subida de carpetas
├── .github/workflows/
│   ├── deploy.yml            # Despliegue automático en servidor AWS
│   └── build-apk.yml         # Compilación automática del APK de Android
├── Dockerfile                # Configuración de contenedor Docker
├── docker-compose.yml        # Orquestación con Docker Compose
└── requirements.txt          # Dependencias de Python
```

---

## 🚀 Uso Rápido

### 1. Iniciar la Aplicación Web
```bash
python server.py
```
Abre en tu navegador: [http://localhost:8000](http://localhost:8000) o en tu dominio [http://m4amp3.duckdns.org](http://m4amp3.duckdns.org).

### 2. Iniciar la Aplicación de Escritorio
```bash
python app.py
```

### 3. Compilar el APK para Android en GitHub
1. Ve a la pestaña **Actions** en tu repositorio: [https://github.com/osdavene/m4amp3/actions](https://github.com/osdavene/m4amp3/actions)
2. Selecciona el workflow **"📱 Compilar APK de Android (Buildozer)"**.
3. Haz clic en **Run workflow**.
4. En unos minutos, descarga el archivo `.apk` directamente desde los artefactos del workflow a tu teléfono.

---

## 👤 Autor

- **Oscar** ([@osdavene](https://github.com/osdavene))
