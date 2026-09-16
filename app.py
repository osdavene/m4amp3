"""Conversor de M4A a MP3 con interfaz grafica (tkinter)."""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from converter import convert_m4a_to_mp3, get_ffmpeg_exe


def buscar_archivos_m4a(carpeta, incluir_subcarpetas):
    archivos = []
    if incluir_subcarpetas:
        for raiz, _dirs, nombres in os.walk(carpeta):
            for nombre in nombres:
                if nombre.lower().endswith(".m4a"):
                    archivos.append(os.path.join(raiz, nombre))
    else:
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta) and nombre.lower().endswith(".m4a"):
                archivos.append(ruta)
    return sorted(archivos)


def ruta_destino_mp3(ruta_m4a, carpeta_origen, carpeta_destino):
    ruta_relativa = os.path.relpath(os.path.dirname(ruta_m4a), carpeta_origen)
    carpeta_salida = os.path.join(carpeta_destino, ruta_relativa) if ruta_relativa != "." else carpeta_destino
    nombre_mp3 = os.path.splitext(os.path.basename(ruta_m4a))[0] + ".mp3"
    return os.path.join(carpeta_salida, nombre_mp3)


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Conversor M4A a MP3")
        self.geometry("640x480")
        self.minsize(520, 400)

        self.carpeta = tk.StringVar()
        self.carpeta_destino = tk.StringVar()
        self.incluir_subcarpetas = tk.BooleanVar(value=True)
        self.sobrescribir = tk.BooleanVar(value=False)
        self.bitrate = tk.StringVar(value="192k")
        self.convirtiendo = False

        self._construir_ui()

    def _construir_ui(self):
        pad = {"padx": 10, "pady": 6}

        frame_carpeta = ttk.Frame(self)
        frame_carpeta.pack(fill="x", **pad)
        ttk.Label(frame_carpeta, text="Carpeta:").pack(side="left")
        ttk.Entry(frame_carpeta, textvariable=self.carpeta, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(frame_carpeta, text="Examinar...", command=self._elegir_carpeta).pack(side="left")

        frame_destino = ttk.Frame(self)
        frame_destino.pack(fill="x", **pad)
        ttk.Label(frame_destino, text="Destino:").pack(side="left")
        ttk.Entry(frame_destino, textvariable=self.carpeta_destino, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(frame_destino, text="Examinar...", command=self._elegir_carpeta_destino).pack(side="left")

        frame_opciones = ttk.Frame(self)
        frame_opciones.pack(fill="x", **pad)
        ttk.Checkbutton(
            frame_opciones, text="Incluir subcarpetas", variable=self.incluir_subcarpetas
        ).pack(side="left")
        ttk.Checkbutton(
            frame_opciones, text="Sobrescribir MP3 existentes", variable=self.sobrescribir
        ).pack(side="left", padx=12)

        ttk.Label(frame_opciones, text="Calidad:").pack(side="left", padx=(12, 4))
        ttk.Combobox(
            frame_opciones,
            textvariable=self.bitrate,
            values=["128k", "192k", "256k", "320k"],
            width=6,
            state="readonly",
        ).pack(side="left")

        self.boton_convertir = ttk.Button(self, text="Convertir", command=self._iniciar_conversion)
        self.boton_convertir.pack(**pad)

        self.barra = ttk.Progressbar(self, mode="determinate")
        self.barra.pack(fill="x", **pad)

        self.log = tk.Text(self, height=15, state="disabled")
        self.log.pack(fill="both", expand=True, **pad)

    def _elegir_carpeta(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta con archivos M4A")
        if ruta:
            self.carpeta.set(ruta)

    def _elegir_carpeta_destino(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta destino para los MP3")
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
            messagebox.showwarning("Aviso", "Selecciona primero una carpeta de origen valida.")
            return

        carpeta_destino = self.carpeta_destino.get()
        if not carpeta_destino:
            messagebox.showwarning("Aviso", "Selecciona una carpeta destino para los MP3.")
            return

        archivos = buscar_archivos_m4a(carpeta, self.incluir_subcarpetas.get())
        if not archivos:
            messagebox.showinfo("Sin archivos", "No se encontraron archivos .m4a en la carpeta seleccionada.")
            return

        if not self.sobrescribir.get():
            archivos = [
                a for a in archivos
                if not os.path.exists(ruta_destino_mp3(a, carpeta, carpeta_destino))
            ]
            if not archivos:
                messagebox.showinfo("Nada que hacer", "Todos los archivos ya tienen su MP3 correspondiente en el destino.")
                return

        self.convirtiendo = True
        self.boton_convertir.configure(state="disabled")
        self.barra.configure(value=0, maximum=len(archivos))
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        hilo = threading.Thread(
            target=self._convertir_en_hilo, args=(archivos, carpeta, carpeta_destino), daemon=True
        )
        hilo.start()

    def _convertir_en_hilo(self, archivos, carpeta, carpeta_destino):
        try:
            ffmpeg_exe = get_ffmpeg_exe()
        except Exception as error:
            self.after(0, lambda: messagebox.showerror("Error", f"No se pudo obtener ffmpeg:\n{error}"))
            self.after(0, self._finalizar_conversion)
            return

        exitos = 0
        errores = 0

        for indice, ruta_m4a in enumerate(archivos, start=1):
            nombre = os.path.basename(ruta_m4a)
            ruta_mp3 = ruta_destino_mp3(ruta_m4a, carpeta, carpeta_destino)
            self.after(0, self._escribir_log, f"Convirtiendo: {nombre}")
            try:
                codigo, salida = convert_m4a_to_mp3(ruta_m4a, ruta_mp3, self.bitrate.get(), ffmpeg_exe=ffmpeg_exe)
                if codigo == 0:
                    exitos += 1
                    self.after(0, self._escribir_log, f"  OK -> {ruta_mp3}")
                else:
                    errores += 1
                    self.after(0, self._escribir_log, f"  ERROR (codigo {codigo}):\n{salida.strip()[-400:]}")
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
