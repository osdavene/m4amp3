"""Conversor Universal de Audio con interfaz grafica de escritorio (Tkinter)."""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from converter import convert_audio, get_ffmpeg_exe, find_audio_files


def ruta_destino_audio(ruta_origen, carpeta_origen, carpeta_destino, formato_destino):
    ruta_relativa = os.path.relpath(os.path.dirname(ruta_origen), carpeta_origen)
    carpeta_salida = os.path.join(carpeta_destino, ruta_relativa) if ruta_relativa != "." else carpeta_destino
    nombre_base = os.path.splitext(os.path.basename(ruta_origen))[0]
    nombre_final = f"{nombre_base}.{formato_destino.lower()}"
    return os.path.join(carpeta_salida, nombre_final)


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Conversor Universal de Audio")
        self.geometry("680x520")
        self.minsize(580, 440)

        self.carpeta = tk.StringVar()
        self.carpeta_destino = tk.StringVar()
        self.incluir_subcarpetas = tk.BooleanVar(value=True)
        self.sobrescribir = tk.BooleanVar(value=False)
        self.formato_destino = tk.StringVar(value="mp3")
        self.bitrate = tk.StringVar(value="192k")
        self.convirtiendo = False

        self._construir_ui()

    def _construir_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Origen
        frame_carpeta = ttk.Frame(self)
        frame_carpeta.pack(fill="x", **pad)
        ttk.Label(frame_carpeta, text="Carpeta Origen:").pack(side="left")
        ttk.Entry(frame_carpeta, textvariable=self.carpeta, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(frame_carpeta, text="Examinar...", command=self._elegir_carpeta).pack(side="left")

        # Destino
        frame_destino = ttk.Frame(self)
        frame_destino.pack(fill="x", **pad)
        ttk.Label(frame_destino, text="Carpeta Destino:").pack(side="left")
        ttk.Entry(frame_destino, textvariable=self.carpeta_destino, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(frame_destino, text="Examinar...", command=self._elegir_carpeta_destino).pack(side="left")

        # Opciones
        frame_opciones = ttk.Frame(self)
        frame_opciones.pack(fill="x", **pad)
        ttk.Checkbutton(
            frame_opciones, text="Incluir subcarpetas", variable=self.incluir_subcarpetas
        ).pack(side="left")
        ttk.Checkbutton(
            frame_opciones, text="Sobrescribir existentes", variable=self.sobrescribir
        ).pack(side="left", padx=10)

        # Formato Destino
        ttk.Label(frame_opciones, text="Convertir a:").pack(side="left", padx=(10, 4))
        combo_formato = ttk.Combobox(
            frame_opciones,
            textvariable=self.formato_destino,
            values=["mp3", "m4a", "wav", "flac", "ogg", "opus", "wma", "aac"],
            width=7,
            state="readonly",
        )
        combo_formato.pack(side="left")
        combo_formato.bind("<<ComboboxSelected>>", self._on_format_change)

        # Bitrate
        self.label_calidad = ttk.Label(frame_opciones, text="Calidad:")
        self.label_calidad.pack(side="left", padx=(10, 4))
        self.combo_bitrate = ttk.Combobox(
            frame_opciones,
            textvariable=self.bitrate,
            values=["128k", "192k", "256k", "320k"],
            width=6,
            state="readonly",
        )
        self.combo_bitrate.pack(side="left")

        # Boton Convertir
        self.boton_convertir = ttk.Button(self, text="Comenzar Conversión", command=self._iniciar_conversion)
        self.boton_convertir.pack(**pad)

        # Barra de progreso
        self.barra = ttk.Progressbar(self, mode="determinate")
        self.barra.pack(fill="x", **pad)

        # Log
        self.log = tk.Text(self, height=14, state="disabled")
        self.log.pack(fill="both", expand=True, **pad)

    def _on_format_change(self, event=None):
        formato = self.formato_destino.get().lower()
        if formato in ["wav", "flac", "aiff"]:
            self.combo_bitrate.configure(state="disabled")
        else:
            self.combo_bitrate.configure(state="readonly")

    def _elegir_carpeta(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta con archivos de audio")
        if ruta:
            self.carpeta.set(ruta)

    def _elegir_carpeta_destino(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta destino")
        if ruta:
            self.carpeta_destino.set(ruta)

    def _escribir_log(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _iniciar_conversion(self):
        if self.convirtiendo:
            return

        carpeta = self.carpeta.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning("Aviso", "Selecciona una carpeta de origen válida.")
            return

        carpeta_destino = self.carpeta_destino.get()
        if not carpeta_destino:
            messagebox.showwarning("Aviso", "Selecciona una carpeta destino.")
            return

        archivos = find_audio_files(carpeta, self.incluir_subcarpetas.get())
        if not archivos:
            messagebox.showinfo("Sin archivos", "No se encontraron archivos de audio soportados en la carpeta.")
            return

        formato_dest = self.formato_destino.get().lower()

        if not self.sobrescribir.get():
            archivos = [
                a for a in archivos
                if not os.path.exists(ruta_destino_audio(a, carpeta, carpeta_destino, formato_dest))
            ]
            if not archivos:
                messagebox.showinfo("Nada que hacer", "Todos los archivos ya tienen su correspondiente audio en el destino.")
                return

        self.convirtiendo = True
        self.boton_convertir.configure(state="disabled")
        self.barra.configure(value=0, maximum=len(archivos))
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        hilo = threading.Thread(
            target=self._convertir_en_hilo, args=(archivos, carpeta, carpeta_destino, formato_dest), daemon=True
        )
        hilo.start()

    def _convertir_en_hilo(self, archivos, carpeta, carpeta_destino, formato_dest):
        try:
            ffmpeg_exe = get_ffmpeg_exe()
        except Exception as error:
            self.after(0, lambda: messagebox.showerror("Error", f"No se pudo obtener FFmpeg:\n{error}"))
            self.after(0, self._finalizar_conversion)
            return

        exitos = 0
        errores = 0

        for indice, ruta_in in enumerate(archivos, start=1):
            nombre = os.path.basename(ruta_in)
            ruta_out = ruta_destino_audio(ruta_in, carpeta, carpeta_destino, formato_dest)
            self.after(0, self._escribir_log, f"Convirtiendo [{formato_dest.upper()}]: {nombre}")
            try:
                codigo, salida = convert_audio(
                    ruta_in, ruta_out, target_format=formato_dest, bitrate=self.bitrate.get(), ffmpeg_exe=ffmpeg_exe
                )
                if codigo == 0:
                    exitos += 1
                    self.after(0, self._escribir_log, f"  OK -> {os.path.basename(ruta_out)}")
                else:
                    errores += 1
                    self.after(0, self._escribir_log, f"  ERROR (codigo {codigo}):\n{salida.strip()[-300:]}")
            except Exception as error:
                errores += 1
                self.after(0, self._escribir_log, f"  ERROR: {error}")

            self.after(0, lambda i=indice: self.barra.configure(value=i))

        self.after(0, self._escribir_log, f"\nCompletado: {exitos} correctos, {errores} con error.")
        self.after(0, self._finalizar_conversion)

    def _finalizar_conversion(self):
        self.convirtiendo = False
        self.boton_convertir.configure(state="normal")


if __name__ == "__main__":
    Aplicacion().mainloop()
