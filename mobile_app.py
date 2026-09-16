"""Aplicacion Movil Offline para Android usando Kivy y motor nativo de audio."""

import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform

from converter import convert_audio, get_ffmpeg_exe, SUPPORTED_INPUT_EXTENSIONS


def request_android_permissions():
    """Solicita permisos de almacenamiento en Android."""
    if platform == "android":
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.MANAGE_EXTERNAL_STORAGE,
        ])


class MobileAudioConverterApp(App):
    def build(self):
        self.title = "Conversor Universal de Audio"
        self.selected_files = []
        self.convirtiendo = False

        request_android_permissions()

        # Layout Principal
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        # Header
        header = Label(
            text="[b]Conversor Universal de Audio[/b]\n[size=14]Modo 100% Offline[/size]",
            markup=True,
            size_hint_y=None,
            height=60,
            halign="center"
        )
        root.add_widget(header)

        # Botones para agregar archivos / carpeta
        btn_box = BoxLayout(size_hint_y=None, height=45, spacing=10)
        btn_add_files = Button(text="+ Archivo(s)", background_color=(0.38, 0.4, 0.95, 1))
        btn_add_files.bind(on_release=self.abrir_selector_archivos)
        btn_box.add_widget(btn_add_files)

        btn_add_folder = Button(text="+ Carpeta Completa", background_color=(0.02, 0.71, 0.83, 1))
        btn_add_folder.bind(on_release=self.abrir_selector_carpeta)
        btn_box.add_widget(btn_add_folder)

        root.add_widget(btn_box)

        # Opciones de Conversion (Formato y Calidad)
        options_box = BoxLayout(size_hint_y=None, height=45, spacing=10)
        options_box.add_widget(Label(text="Formato:", size_hint_x=0.3))
        self.spinner_formato = Spinner(
            text="mp3",
            values=["mp3", "m4a", "wav", "flac", "ogg", "opus", "aac", "wma"],
            size_hint_x=0.35
        )
        options_box.add_widget(self.spinner_formato)

        options_box.add_widget(Label(text="Calidad:", size_hint_x=0.25))
        self.spinner_bitrate = Spinner(
            text="192k",
            values=["128k", "192k", "256k", "320k"],
            size_hint_x=0.3
        )
        options_box.add_widget(self.spinner_bitrate)
        root.add_widget(options_box)

        # Contador y lista de archivos
        self.lbl_archivos = Label(text="Archivos seleccionados: 0", size_hint_y=None, height=30)
        root.add_widget(self.lbl_archivos)

        # Lista de archivos en ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        self.file_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_list_layout.bind(minimum_height=self.file_list_layout.setter("height"))
        scroll.add_widget(self.file_list_layout)
        root.add_widget(scroll)

        # Barra de progreso
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        root.add_widget(self.progress_bar)

        self.lbl_status = Label(text="Listo para convertir", size_hint_y=None, height=30)
        root.add_widget(self.lbl_status)

        # Boton de accion
        self.btn_convert = Button(
            text="Comenzar Conversión",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            bold=True
        )
        self.btn_convert.bind(on_release=self.iniciar_conversion)
        root.add_widget(self.btn_convert)

        return root

    def abrir_selector_archivos(self, _):
        initial_path = "/sdcard/Download" if platform == "android" else os.path.expanduser("~")
        chooser = FileChooserListView(path=initial_path, multiselect=True)
        
        popup_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        popup_layout.add_widget(chooser)
        
        btn_select = Button(text="Seleccionar", size_hint_y=None, height=45)
        popup_layout.add_widget(btn_select)
        
        popup = Popup(title="Seleccionar Archivos de Audio", content=popup_layout, size_hint=(0.95, 0.95))

        def on_select(_):
            for path in chooser.selection:
                _, ext = os.path.splitext(path)
                if ext.lower() in SUPPORTED_INPUT_EXTENSIONS and path not in self.selected_files:
                    self.selected_files.append(path)
            self.actualizar_ui_archivos()
            popup.dismiss()

        btn_select.bind(on_release=on_select)
        popup.open()

    def abrir_selector_carpeta(self, _):
        initial_path = "/sdcard/Music" if platform == "android" else os.path.expanduser("~")
        chooser = FileChooserListView(path=initial_path, dirselect=True)
        
        popup_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        popup_layout.add_widget(chooser)
        
        btn_select = Button(text="Seleccionar Esta Carpeta", size_hint_y=None, height=45)
        popup_layout.add_widget(btn_select)
        
        popup = Popup(title="Seleccionar Carpeta", content=popup_layout, size_hint=(0.95, 0.95))

        def on_select(_):
            folder_path = chooser.path
            for raiz, _dirs, nombres in os.walk(folder_path):
                for nombre in nombres:
                    _, ext = os.path.splitext(nombre)
                    if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                        full_path = os.path.join(raiz, nombre)
                        if full_path not in self.selected_files:
                            self.selected_files.append(full_path)
            self.actualizar_ui_archivos()
            popup.dismiss()

        btn_select.bind(on_release=on_select)
        popup.open()

    def actualizar_ui_archivos(self):
        self.file_list_layout.clear_widgets()
        self.lbl_archivos.text = f"Archivos seleccionados: {len(self.selected_files)}"
        for idx, fpath in enumerate(self.selected_files):
            row = BoxLayout(size_hint_y=None, height=35, spacing=5)
            row.add_widget(Label(text=os.path.basename(fpath), halign="left", text_size=(300, None)))
            btn_del = Button(text="X", size_hint_x=None, width=40, background_color=(0.9, 0.2, 0.2, 1))
            btn_del.bind(on_release=lambda _, i=idx: self.remover_archivo(i))
            row.add_widget(btn_del)
            self.file_list_layout.add_widget(row)

    def remover_archivo(self, index):
        if 0 <= index < len(self.selected_files):
            self.selected_files.pop(index)
            self.actualizar_ui_archivos()

    def iniciar_conversion(self, _):
        if self.convirtiendo or not self.selected_files:
            return

        self.convirtiendo = True
        self.btn_convert.disabled = True
        self.progress_bar.max = len(self.selected_files)
        self.progress_bar.value = 0
        self.lbl_status.text = "Iniciando conversión..."

        target_fmt = self.spinner_formato.text.lower()
        bitrate = self.spinner_bitrate.text

        # Directorio destino en Android o Escritorio
        if platform == "android":
            out_dir = "/sdcard/Music/ConvertedAudio"
        else:
            out_dir = os.path.join(os.path.expanduser("~"), "Music", "ConvertedAudio")

        os.makedirs(out_dir, exist_ok=True)

        thread = threading.Thread(
            target=self._proceso_conversion,
            args=(list(self.selected_files), out_dir, target_fmt, bitrate),
            daemon=True
        )
        thread.start()

    def _proceso_conversion(self, files, out_dir, target_fmt, bitrate):
        try:
            ffmpeg_exe = get_ffmpeg_exe()
        except Exception as e:
            Clock.schedule_once(lambda dt: self._finalizar_error(f"Error con FFmpeg: {e}"))
            return

        exitos = 0
        for i, in_path in enumerate(files, start=1):
            base_name = os.path.splitext(os.path.basename(in_path))[0]
            out_path = os.path.join(out_dir, f"{base_name}.{target_fmt}")
            
            Clock.schedule_once(lambda dt, name=base_name: self._actualizar_status(f"Convirtiendo: {name}"))
            
            code, _ = convert_audio(in_path, out_path, target_format=target_fmt, bitrate=bitrate, ffmpeg_exe=ffmpeg_exe)
            if code == 0:
                exitos += 1

            Clock.schedule_once(lambda dt, val=i: self._actualizar_progreso(val))

        Clock.schedule_once(lambda dt: self._finalizar_exito(exitos, len(files), out_dir))

    def _actualizar_status(self, texto):
        self.lbl_status.text = texto

    def _actualizar_progreso(self, val):
        self.progress_bar.value = val

    def _finalizar_exito(self, exitos, total, out_dir):
        self.convirtiendo = False
        self.btn_convert.disabled = False
        self.lbl_status.text = f"¡Completado! {exitos}/{total} guardados en {out_dir}"

    def _finalizar_error(self, err_msg):
        self.convirtiendo = False
        self.btn_convert.disabled = False
        self.lbl_status.text = err_msg


if __name__ == "__main__":
    MobileAudioConverterApp().run()
