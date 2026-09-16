"""Servidor Web FastAPI para conversion universal de archivos de audio."""

import os
import shutil
import tempfile
import zipfile
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from converter import convert_audio, get_ffmpeg_exe, SUPPORTED_INPUT_EXTENSIONS

app = FastAPI(
    title="Conversor Universal de Audio Web",
    description="Servicio web para convertir archivos y carpetas completas de audio entre múltiples formatos.",
    version="2.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

MIME_MAP = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
    "wma": "audio/x-ms-wma",
    "aiff": "audio/aiff",
    "m4r": "audio/x-m4r",
}


def cleanup_directory(path: str):
    """Elimina de forma segura un directorio temporal y su contenido."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza la pagina principal."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
async def health():
    """Chequeo de salud del servicio y disponibilidad de FFmpeg."""
    try:
        ffmpeg_exe = get_ffmpeg_exe()
        ffmpeg_ok = bool(ffmpeg_exe and os.path.exists(ffmpeg_exe))
    except Exception:
        ffmpeg_ok = False

    return {
        "status": "healthy" if ffmpeg_ok else "degraded",
        "ffmpeg_available": ffmpeg_ok,
    }


@app.post("/api/convert")
async def convert_audio_endpoint(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    target_format: str = Form("mp3"),
    bitrate: str = Form("192k")
):
    """
    Recibe uno o varios archivos/carpetas de audio, los convierte al formato deseado y retorna el resultado.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos para convertir.")

    target_format = target_format.lower().lstrip(".")
    if target_format not in MIME_MAP:
        target_format = "mp3"

    valid_bitrates = {"128k", "192k", "256k", "320k"}
    if bitrate not in valid_bitrates:
        bitrate = "192k"

    try:
        ffmpeg_exe = get_ffmpeg_exe()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo inicializar FFmpeg en el servidor: {exc}"
        )

    temp_dir = tempfile.mkdtemp(prefix="audio_conv_web_")
    background_tasks.add_task(cleanup_directory, temp_dir)

    converted_files = []
    errors = []

    for file_item in files:
        original_name = file_item.filename or "audio"
        clean_filename = os.path.basename(original_name)
        base_name, ext = os.path.splitext(clean_filename)

        if ext.lower() not in SUPPORTED_INPUT_EXTENSIONS:
            errors.append(f"{original_name}: Formato de entrada no soportado")
            continue

        input_path = os.path.join(temp_dir, f"in_{clean_filename}")
        output_name = f"{base_name}.{target_format}"
        output_path = os.path.join(temp_dir, f"out_{output_name}")

        try:
            with open(input_path, "wb") as f_out:
                shutil.copyfileobj(file_item.file, f_out)

            code, output_msg = convert_audio(
                input_path,
                output_path,
                target_format=target_format,
                bitrate=bitrate,
                ffmpeg_exe=ffmpeg_exe
            )

            if code == 0 and os.path.exists(output_path):
                converted_files.append((output_path, output_name))
            else:
                errors.append(f"{original_name}: Error al convertir ({output_msg.strip()[-200:]})")
        except Exception as err:
            errors.append(f"{original_name}: {str(err)}")
        finally:
            await file_item.close()

    if not converted_files:
        raise HTTPException(
            status_code=400,
            detail={"message": "No se pudo convertir ningun archivo.", "errors": errors}
        )

    # Si es solo 1 archivo
    if len(converted_files) == 1 and len(files) == 1:
        single_path, single_name = converted_files[0]
        media_type = MIME_MAP.get(target_format, "application/octet-stream")
        return FileResponse(
            path=single_path,
            filename=single_name,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{single_name}"'}
        )

    # Si son multiples archivos, empaquetar en ZIP
    zip_filename = f"audios_{target_format}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f_path, f_name in converted_files:
            zipf.write(f_path, arcname=f_name)

    return FileResponse(
        path=zip_path,
        filename=zip_filename,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
