"""Modulo central para la conversion universal de archivos de audio usando FFmpeg."""

import os
import shutil
import subprocess
from typing import Tuple, Optional, List, Set

SUPPORTED_INPUT_EXTENSIONS: Set[str] = {
    ".m4a", ".mp3", ".wav", ".flac", ".ogg", ".opus", ".aac",
    ".wma", ".aiff", ".aif", ".m4r", ".mp4", ".webm", ".mkv",
    ".mov", ".avi", ".amr", ".3gp"
}

CODEC_CONFIG = {
    "mp3": ["-c:a", "libmp3lame", "-b:a"],
    "m4a": ["-c:a", "aac", "-b:a"],
    "aac": ["-c:a", "aac", "-b:a"],
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac"],
    "ogg": ["-c:a", "libvorbis", "-b:a"],
    "opus": ["-c:a", "libopus", "-b:a"],
    "wma": ["-c:a", "wmav2", "-b:a"],
    "aiff": ["-c:a", "pcm_s16be"],
    "m4r": ["-c:a", "aac", "-b:a"],
}


def get_ffmpeg_exe() -> str:
    """Obtiene la ruta del ejecutable FFmpeg del sistema o de imageio-ffmpeg."""
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        return ffmpeg_system
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        # En Android o entornos sin imageio-ffmpeg
        return "ffmpeg"


def find_audio_files(carpeta: str, incluir_subcarpetas: bool = True) -> List[str]:
    """Busca recursivamente todos los archivos de audio y video soportados en una carpeta."""
    archivos = []
    if incluir_subcarpetas:
        for raiz, _dirs, nombres in os.walk(carpeta):
            for nombre in nombres:
                _, ext = os.path.splitext(nombre)
                if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                    archivos.append(os.path.join(raiz, nombre))
    else:
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta):
                _, ext = os.path.splitext(nombre)
                if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                    archivos.append(ruta)
    return sorted(archivos)


def convert_audio(
    input_path: str,
    output_path: str,
    target_format: str = "mp3",
    bitrate: str = "192k",
    ffmpeg_exe: Optional[str] = None
) -> Tuple[int, str]:
    """
    Convierte cualquier archivo de audio/video a un formato de audio destino usando FFmpeg.
    """
    if ffmpeg_exe is None:
        ffmpeg_exe = get_ffmpeg_exe()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    target_format = target_format.lower().lstrip(".")

    comando = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        "-vn",  # Descartar video
    ]

    codec_args = CODEC_CONFIG.get(target_format, ["-c:a", "libmp3lame", "-b:a"])
    
    # Formatos sin compresion o con bitrate especifico
    if target_format in ["wav", "flac", "aiff"]:
        comando.extend(codec_args)
    else:
        comando.extend(codec_args)
        comando.append(bitrate)

    comando.append(output_path)

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    return resultado.returncode, resultado.stdout.decode(errors="ignore")


# Funcion de compatibilidad con versiones anteriores
def convert_m4a_to_mp3(
    input_path: str,
    output_path: str,
    bitrate: str = "192k",
    ffmpeg_exe: Optional[str] = None
) -> Tuple[int, str]:
    return convert_audio(
        input_path=input_path,
        output_path=output_path,
        target_format="mp3",
        bitrate=bitrate,
        ffmpeg_exe=ffmpeg_exe
    )
