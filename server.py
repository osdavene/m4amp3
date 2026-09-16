"""Servidor Web FastAPI para conversion de archivos M4A a MP3."""

import os
import shutil
import tempfile
import zipfile
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from converter import convert_m4a_to_mp3, get_ffmpeg_exe

app = FastAPI(
    title="M4A to MP3 Converter Web",
    description="Servicio web para convertir archivos de audio M4A a MP3 individualmente o por lotes.",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


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
async def convert_audio(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    bitrate: str = Form("192k")
):
    """
    Recibe uno o varios archivos .m4a, los convierte a .mp3 y retorna el archivo individual o un ZIP.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos para convertir.")

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

    # Directorio temporal unico para la sesion de conversion
    temp_dir = tempfile.mkdtemp(prefix="m4amp3_web_")
    background_tasks.add_task(cleanup_directory, temp_dir)

    converted_files = []
    errors = []

    for file_item in files:
        original_name = file_item.filename or "audio.m4a"
        base_name, ext = os.path.splitext(original_name)

        if ext.lower() not in [".m4a", ".mp4", ".aac", ".alac"]:
            errors.append(f"{original_name}: Formato no soportado (debe ser .m4a)")
            continue

        input_path = os.path.join(temp_dir, f"input_{original_name}")
        output_name = f"{base_name}.mp3"
        output_path = os.path.join(temp_dir, f"output_{output_name}")

        try:
            # Guardar archivo subido en disco
            with open(input_path, "wb") as f_out:
                shutil.copyfileobj(file_item.file, f_out)

            # Ejecutar conversion
            code, output_msg = convert_m4a_to_mp3(
                input_path, output_path, bitrate=bitrate, ffmpeg_exe=ffmpeg_exe
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

    # Si es solo 1 archivo convertido con exito y no hubo mas solicitudes
    if len(converted_files) == 1 and len(files) == 1:
        single_path, single_name = converted_files[0]
        return FileResponse(
            path=single_path,
            filename=single_name,
            media_type="audio/mpeg",
            headers={"Content-Disposition": f'attachment; filename="{single_name}"'}
        )

    # Si son multiples archivos, empaquetar en un .zip
    zip_filename = "audios_convertidos.zip"
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
