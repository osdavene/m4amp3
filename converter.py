"""Modulo central para la conversion de archivos M4A a MP3."""

import os
import shutil
import subprocess
from typing import Tuple, Optional
import imageio_ffmpeg


def get_ffmpeg_exe() -> str:
    """Obtiene la ruta del ejecutable FFmpeg del sistema o de imageio-ffmpeg."""
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        return ffmpeg_system
    return imageio_ffmpeg.get_ffmpeg_exe()


def convert_m4a_to_mp3(
    input_path: str,
    output_path: str,
    bitrate: str = "192k",
    ffmpeg_exe: Optional[str] = None
) -> Tuple[int, str]:
    """
    Convierte un archivo .m4a a formato .mp3 utilizando FFmpeg.

    Args:
        input_path: Ruta del archivo M4A de entrada.
        output_path: Ruta de destino del archivo MP3.
        bitrate: Tasa de bits del MP3 (ej. '128k', '192k', '256k', '320k').
        ffmpeg_exe: Ruta opcional al ejecutable de FFmpeg.

    Returns:
        Tuple[int, str]: Código de salida (0 si tuvo éxito) y mensaje/salida de FFmpeg.
    """
    if ffmpeg_exe is None:
        ffmpeg_exe = get_ffmpeg_exe()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    comando = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        "-vn",
        "-b:a", bitrate,
        output_path,
    ]

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    return resultado.returncode, resultado.stdout.decode(errors="ignore")
