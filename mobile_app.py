"""Aplicacion Movil para Android con Interfaz Moderna, Adaptativa (DPI) y Selector Tactil."""

import os
import threading
from kivy.app import App
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.utils import platform

from converter import convert_audio, get_ffmpeg_exe, SUPPORTED_INPUT_EXTENSIONS


def get_base_storage_dir(subfolder=""):
    """Obtiene una ruta valida de almacenamiento en Android o Escritorio."""
    if platform == "android":
        candidates = [
            "/storage/emulated/0",
            "/sdcard",
            os.environ.get("EXTERNAL_STORAGE", "")
        ]
        base_dir = "/storage/emulated/0"
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                base_dir = candidate
                break
        
        if subfolder:
            target = os.path.join(base_dir, subfolder)
            if os.path.exists(target):
                return target
        return base_dir
    else:
        user_home = os.path.expanduser("~")
        if subfolder:
            target = os.path.join(user_home, subfolder)
            if os.path.exists(target):
                return target
        return user_home


class CardLayout(BoxLayout):
    """Contenedor con fondo redondeado estilo tarjeta moderna."""
    def __init__(self, bg_color=(0.12, 0.16, 0.23, 1), radius=12, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            self.color_instruction = Color(*self.bg_color)
            self.rect_instruction = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(self.radius)]
            )
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect_instruction.pos = self.pos
        self.rect_instruction.size = self.size


class PillButton(Button):
    """Boton tipo chip/pildora para seleccion rapida de opciones."""
    def __init__(self, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.is_selected = is_selected
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_size = sp(14)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(42)
        
        with self.canvas.before:
            self.bg_color = Color(*self.get_color())
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def get_color(self):
        if self.is_selected:
            return (0.39, 0.4, 0.95, 1)  # Indigo vibrante
        return (0.18, 0.22, 0.31, 1)     # Gris azulado oscuro

    def set_selected(self, selected):
        self.is_selected = selected
        self.bg_color.rgba = self.get_color()
        self.color = (1, 1, 1, 1) if selected else (0.75, 0.8, 0.88, 1)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class ModernFilePickerModal(ModalView):
    """Explorador de archivos tactil a pantalla completa adaptado para Android."""
    def __init__(self, app_ref, initial_dir=None, only_dirs=False, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.only_dirs = only_dirs
        self.current_dir = initial_dir or get_base_storage_dir()
        self.selected_items = set()

        self.size_hint = (0.96, 0.94)
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.7)

        # Layout Principal del Modal
        card = CardLayout(orientation="vertical", bg_color=(0.09, 0.12, 0.18, 1), padding=dp(12), spacing=dp(10))
        
        # Header con titulo y boton cerrar
        head_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        title_text = "📁 Seleccionar Carpeta" if only_dirs else "🎵 Seleccionar Archivos de Audio"
        lbl_title = Label(
            text=f"[b]{title_text}[/b]",
            markup=True,
            font_size=sp(16),
            halign="left",
            valign="middle"
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        head_box.add_widget(lbl_title)

        btn_close = Button(
            text="✕",
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            background_normal="",
            background_color=(0.85, 0.25, 0.25, 1),
            font_size=sp(18),
            bold=True
        )
        btn_close.bind(on_release=self.dismiss)
        head_box.add_widget(btn_close)
        card.add_widget(head_box)

        # Barra de atajos rapidos
        shortcuts = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_up = Button(text="⬆ Subir", background_normal="", background_color=(0.22, 0.28, 0.38, 1), font_size=sp(13))
        btn_up.bind(on_release=self.subir_nivel)
        shortcuts.add_widget(btn_up)

        btn_downloads = Button(text="📥 Descargas", background_normal="", background_color=(0.22, 0.28, 0.38, 1), font_size=sp(13))
        btn_downloads.bind(on_release=lambda _: self.navegar_a(get_base_storage_dir("Download")))
        shortcuts.add_widget(btn_downloads)

        btn_music = Button(text="🎵 Música", background_normal="", background_color=(0.22, 0.28, 0.38, 1), font_size=sp(13))
        btn_music.bind(on_release=lambda _: self.navegar_a(get_base_storage_dir("Music")))
        shortcuts.add_widget(btn_music)
        card.add_widget(shortcuts)

        # Ruta actual
        self.lbl_path = Label(
            text=self.current_dir,
            font_size=sp(12),
            color=(0.6, 0.7, 0.85, 1),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle"
        )
        self.lbl_path.bind(size=self.lbl_path.setter("text_size"))
        card.add_widget(self.lbl_path)

        # Lista deslizable de archivos/carpetas
        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(6))
        self.items_layout = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter("height"))
        scroll.add_widget(self.items_layout)
        card.add_widget(scroll)

        # Barra inferior con boton de confirmacion
        foot_box = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        
        if not only_dirs:
            btn_all = Button(
                text="Seleccionar Todo",
                size_hint_x=0.45,
                background_normal="",
                background_color=(0.22, 0.28, 0.38, 1),
                font_size=sp(14)
            )
            btn_all.bind(on_release=self.seleccionar_todo_en_carpeta)
            foot_box.add_widget(btn_all)

        btn_confirm = Button(
            text="✔ Confirmar Selección",
            background_normal="",
            background_color=(0.13, 0.65, 0.38, 1),
            font_size=sp(15),
            bold=True
        )
        btn_confirm.bind(on_release=self.confirmar_seleccion)
        foot_box.add_widget(btn_confirm)
        card.add_widget(foot_box)

        self.add_widget(card)
        self.cargar_directorio()

    def navegar_a(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            self.current_dir = path
            self.cargar_directorio()

    def subir_nivel(self, _):
        padre = os.path.dirname(self.current_dir)
        if padre and os.path.exists(padre):
            self.current_dir = padre
            self.cargar_directorio()

    def cargar_directorio(self):
        self.items_layout.clear_widgets()
        self.lbl_path.text = f"📍 {self.current_dir}"
        
        try:
            entradas = os.listdir(self.current_dir)
        except Exception as e:
            err_lbl = Label(text=f"No se pudo acceder a esta carpeta:\n{e}", size_hint_y=None, height=dp(80), color=(1, 0.4, 0.4, 1))
            self.items_layout.add_widget(err_lbl)
            return

        carpetas = []
        archivos = []

        for nombre in entradas:
            if nombre.startswith("."):
                continue
            ruta_completa = os.path.join(self.current_dir, nombre)
            if os.path.isdir(ruta_completa):
                carpetas.append(nombre)
            elif not self.only_dirs:
                _, ext = os.path.splitext(nombre)
                if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                    archivos.append(nombre)

        carpetas.sort(key=lambda s: s.lower())
        archivos.sort(key=lambda s: s.lower())

        # Renderizar Carpetas
        for carpeta in carpetas:
            ruta = os.path.join(self.current_dir, carpeta)
            btn = Button(
                text=f"📁  {carpeta}/",
                size_hint_y=None,
                height=dp(48),
                background_normal="",
                background_color=(0.14, 0.18, 0.26, 1),
                color=(0.9, 0.9, 0.9, 1),
                font_size=sp(14),
                halign="left",
                valign="middle",
                padding=(dp(12), 0)
            )
            btn.bind(size=btn.setter("text_size"))
            btn.bind(on_release=lambda _, r=ruta: self.navegar_a(r))
            self.items_layout.add_widget(btn)

        # Renderizar Archivos de Audio
        if not self.only_dirs:
            for archivo in archivos:
                ruta = os.path.join(self.current_dir, archivo)
                is_selected = ruta in self.selected_items or ruta in self.app_ref.selected_files
                
                btn = Button(
                    text=f"{'✔ ' if is_selected else '🎵  '}{archivo}",
                    size_hint_y=None,
                    height=dp(50),
                    background_normal="",
                    background_color=(0.28, 0.35, 0.65, 1) if is_selected else (0.12, 0.15, 0.22, 1),
                    color=(1, 1, 1, 1) if is_selected else (0.8, 0.85, 0.95, 1),
                    font_size=sp(14),
                    halign="left",
                    valign="middle",
                    padding=(dp(12), 0)
                )
                btn.bind(size=btn.setter("text_size"))
                btn.bind(on_release=lambda _, r=ruta, b=btn, a=archivo: self.toggle_archivo(r, b, a))
                self.items_layout.add_widget(btn)

        if not carpetas and not archivos:
            vacio = Label(
                text="No hay archivos de audio compatibles aquí",
                size_hint_y=None,
                height=dp(60),
                color=(0.5, 0.55, 0.65, 1),
                font_size=sp(14)
            )
            self.items_layout.add_widget(vacio)

    def toggle_archivo(self, ruta, btn, nombre):
        if ruta in self.selected_items:
            self.selected_items.remove(ruta)
            btn.background_color = (0.12, 0.15, 0.22, 1)
            btn.text = f"🎵  {nombre}"
            btn.color = (0.8, 0.85, 0.95, 1)
        else:
            self.selected_items.add(ruta)
            btn.background_color = (0.28, 0.35, 0.65, 1)
            btn.text = f"✔  {nombre}"
            btn.color = (1, 1, 1, 1)

    def seleccionar_todo_en_carpeta(self, _):
        for nombre in os.listdir(self.current_dir):
            _, ext = os.path.splitext(nombre)
            if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                self.selected_items.add(os.path.join(self.current_dir, nombre))
        self.cargar_directorio()

    def confirmar_seleccion(self, _):
        if self.only_dirs:
            # Agregar todos los audios de la carpeta
            for raiz, _, nombres in os.walk(self.current_dir):
                for nombre in nombres:
                    _, ext = os.path.splitext(nombre)
                    if ext.lower() in SUPPORTED_INPUT_EXTENSIONS:
                        full_path = os.path.join(raiz, nombre)
                        if full_path not in self.app_ref.selected_files:
                            self.app_ref.selected_files.append(full_path)
        else:
            for item in self.selected_items:
                if item not in self.app_ref.selected_files:
                    self.app_ref.selected_files.append(item)
                    
        self.app_ref.actualizar_ui_archivos()
        self.dismiss()


class MobileAudioConverterApp(App):
    def build(self):
        self.title = "Conversor de Audio"
        self.selected_files = []
        self.convirtiendo = False
        self.formato_actual = "mp3"
        self.bitrate_actual = "192k"

        # Contenedor Raiz con fondo oscuro elegante
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(0.06, 0.08, 0.12, 1)
            self.bg_root = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self.bg_root, "pos", root.pos),
                  size=lambda *_: setattr(self.bg_root, "size", root.size))

        # Espaciado superior para notch / barra de estado en Android
        top_safe_padding = dp(36) if platform == "android" else dp(14)
        main_content = BoxLayout(
            orientation="vertical",
            padding=[dp(14), top_safe_padding, dp(14), dp(14)],
            spacing=dp(12)
        )

        # 1. Cabecera Moderna
        header_card = CardLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(14), dp(8)],
            bg_color=(0.11, 0.14, 0.22, 1)
        )
        lbl_app_title = Label(
            text="[b]Conversor Universal de Audio[/b]\n[size=12][color=#38bdf8]⚡ Modo Rápido Offline[/color][/size]",
            markup=True,
            font_size=sp(16),
            halign="left",
            valign="middle"
        )
        lbl_app_title.bind(size=lbl_app_title.setter("text_size"))
        header_card.add_widget(lbl_app_title)
        main_content.add_widget(header_card)

        # 2. Botones de Accion Grandes y Claros
        btn_bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        
        btn_add_files = Button(
            text="➕ Agregar Archivos",
            background_normal="",
            background_color=(0.38, 0.4, 0.95, 1),
            font_size=sp(14),
            bold=True
        )
        btn_add_files.bind(on_release=self.abrir_selector_archivos)
        btn_bar.add_widget(btn_add_files)

        btn_add_folder = Button(
            text="📁 Carpeta Entera",
            background_normal="",
            background_color=(0.06, 0.72, 0.82, 1),
            font_size=sp(14),
            bold=True
        )
        btn_add_folder.bind(on_release=self.abrir_selector_carpeta)
        btn_bar.add_widget(btn_add_folder)
        main_content.add_widget(btn_bar)

        # 3. Selector de Formato Destino (Pills visuales)
        fmt_card = CardLayout(orientation="vertical", size_hint_y=None, height=dp(86), padding=dp(10), spacing=dp(6))
        lbl_fmt = Label(
            text="[b]Formato de Salida:[/b]",
            markup=True,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            color=(0.8, 0.85, 0.95, 1)
        )
        lbl_fmt.bind(size=lbl_fmt.setter("text_size"))
        fmt_card.add_widget(lbl_fmt)

        fmt_scroll = ScrollView(size_hint=(1, None), height=dp(44), do_scroll_y=False)
        self.fmt_box = BoxLayout(size_hint_x=None, spacing=dp(8), height=dp(42))
        self.fmt_box.bind(minimum_width=self.fmt_box.setter("width"))
        
        self.fmt_buttons = {}
        for fmt in ["mp3", "m4a", "wav", "flac", "ogg", "opus", "aac", "wma"]:
            btn = PillButton(
                text=fmt.upper(),
                is_selected=(fmt == self.formato_actual),
                size_hint=(None, None),
                size=(dp(72), dp(40))
            )
            btn.bind(on_release=lambda _, f=fmt: self.seleccionar_formato(f))
            self.fmt_buttons[fmt] = btn
            self.fmt_box.add_widget(btn)
        fmt_scroll.add_widget(self.fmt_box)
        fmt_card.add_widget(fmt_scroll)
        main_content.add_widget(fmt_card)

        # 4. Selector de Calidad / Bitrate
        bitrate_card = CardLayout(orientation="vertical", size_hint_y=None, height=dp(86), padding=dp(10), spacing=dp(6))
        lbl_bitrate = Label(
            text="[b]Calidad de Audio (Bitrate):[/b]",
            markup=True,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            color=(0.8, 0.85, 0.95, 1)
        )
        lbl_bitrate.bind(size=lbl_bitrate.setter("text_size"))
        bitrate_card.add_widget(lbl_bitrate)

        self.bitrate_box = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.bitrate_buttons = {}
        for b_rate in ["128k", "192k", "256k", "320k"]:
            btn = PillButton(
                text=b_rate,
                is_selected=(b_rate == self.bitrate_actual),
                size_hint_x=1
            )
            btn.bind(on_release=lambda _, b=b_rate: self.seleccionar_bitrate(b))
            self.bitrate_buttons[b_rate] = btn
            self.bitrate_box.add_widget(btn)
        bitrate_card.add_widget(self.bitrate_box)
        main_content.add_widget(bitrate_card)

        # 5. Lista de Archivos Seleccionados con Contador
        list_header = BoxLayout(size_hint_y=None, height=dp(32))
        self.lbl_archivos = Label(
            text="Archivos seleccionados: [b]0[/b]",
            markup=True,
            font_size=sp(14),
            halign="left",
            valign="middle",
            color=(0.8, 0.85, 0.95, 1)
        )
        self.lbl_archivos.bind(size=self.lbl_archivos.setter("text_size"))
        list_header.add_widget(self.lbl_archivos)

        self.btn_limpiar = Button(
            text="Limpiar Todo",
            size_hint=(None, None),
            size=(dp(100), dp(30)),
            background_normal="",
            background_color=(0.6, 0.2, 0.2, 1),
            font_size=sp(12)
        )
        self.btn_limpiar.bind(on_release=self.limpiar_archivos)
        list_header.add_widget(self.btn_limpiar)
        main_content.add_widget(list_header)

        # Contenedor desplazable de archivos
        scroll_archivos = ScrollView(size_hint=(1, 1), bar_width=dp(6))
        self.file_list_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.file_list_layout.bind(minimum_height=self.file_list_layout.setter("height"))
        scroll_archivos.add_widget(self.file_list_layout)
        main_content.add_widget(scroll_archivos)

        # 6. Barra de Progreso y Estado
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(16))
        main_content.add_widget(self.progress_bar)

        self.lbl_status = Label(
            text="Listo para convertir",
            font_size=sp(13),
            size_hint_y=None,
            height=dp(26),
            color=(0.7, 0.8, 0.9, 1),
            halign="center"
        )
        main_content.add_widget(self.lbl_status)

        # 7. Boton Principal Grande de Conversion
        self.btn_convert = Button(
            text="⚡ COMENZAR CONVERSIÓN",
            size_hint_y=None,
            height=dp(56),
            background_normal="",
            background_color=(0.15, 0.68, 0.38, 1),
            font_size=sp(16),
            bold=True
        )
        self.btn_convert.bind(on_release=self.iniciar_conversion)
        main_content.add_widget(self.btn_convert)

        root.add_widget(main_content)
        return root

    def on_start(self):
        """Solicita permisos una vez que la UI esta activa."""
        if platform == "android":
            Clock.schedule_once(lambda dt: self.solicitar_permisos_android(), 0.5)

    def solicitar_permisos_android(self):
        try:
            from android.permissions import request_permissions, Permission
            perms = []
            if hasattr(Permission, "READ_EXTERNAL_STORAGE"):
                perms.append(Permission.READ_EXTERNAL_STORAGE)
            else:
                perms.append("android.permission.READ_EXTERNAL_STORAGE")
            if hasattr(Permission, "WRITE_EXTERNAL_STORAGE"):
                perms.append(Permission.WRITE_EXTERNAL_STORAGE)
            else:
                perms.append("android.permission.WRITE_EXTERNAL_STORAGE")
            if hasattr(Permission, "READ_MEDIA_AUDIO"):
                perms.append(Permission.READ_MEDIA_AUDIO)
            else:
                perms.append("android.permission.READ_MEDIA_AUDIO")
            request_permissions(perms)
        except Exception as e:
            print(f"Permisos Android: {e}")

    def seleccionar_formato(self, fmt):
        self.formato_actual = fmt
        for f, btn in self.fmt_buttons.items():
            btn.set_selected(f == fmt)

    def seleccionar_bitrate(self, b_rate):
        self.bitrate_actual = b_rate
        for b, btn in self.bitrate_buttons.items():
            btn.set_selected(b == b_rate)

    def abrir_selector_archivos(self, _):
        picker = ModernFilePickerModal(
            app_ref=self,
            initial_dir=get_base_storage_dir("Download"),
            only_dirs=False
        )
        picker.open()

    def abrir_selector_carpeta(self, _):
        picker = ModernFilePickerModal(
            app_ref=self,
            initial_dir=get_base_storage_dir("Music"),
            only_dirs=True
        )
        picker.open()

    def limpiar_archivos(self, _):
        self.selected_files.clear()
        self.actualizar_ui_archivos()

    def actualizar_ui_archivos(self):
        self.file_list_layout.clear_widgets()
        self.lbl_archivos.text = f"Archivos seleccionados: [b]{len(self.selected_files)}[/b]"
        
        if not self.selected_files:
            empty_lbl = Label(
                text="Toca '+ Agregar Archivos' para elegir audios",
                size_hint_y=None,
                height=dp(50),
                color=(0.45, 0.5, 0.6, 1),
                font_size=sp(14)
            )
            self.file_list_layout.add_widget(empty_lbl)
            return

        for idx, fpath in enumerate(self.selected_files):
            row = CardLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=[dp(12), dp(4)],
                spacing=dp(8),
                bg_color=(0.13, 0.17, 0.25, 1)
            )
            
            lbl_name = Label(
                text=f"🎵 {os.path.basename(fpath)}",
                halign="left",
                valign="middle",
                font_size=sp(13),
                color=(0.9, 0.92, 0.98, 1),
                shorten=True,
                shorten_from="center"
            )
            lbl_name.bind(size=lbl_name.setter("text_size"))
            row.add_widget(lbl_name)

            btn_del = Button(
                text="✕",
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                background_normal="",
                background_color=(0.8, 0.25, 0.25, 1),
                font_size=sp(16),
                bold=True
            )
            btn_del.bind(on_release=lambda _, i=idx: self.remover_archivo(i))
            row.add_widget(btn_del)
            self.file_list_layout.add_widget(row)

    def remover_archivo(self, index):
        if 0 <= index < len(self.selected_files):
            self.selected_files.pop(index)
            self.actualizar_ui_archivos()

    def iniciar_conversion(self, _):
        if self.convirtiendo:
            return
        if not self.selected_files:
            self.lbl_status.text = "⚠️ Por favor selecciona al menos un archivo de audio"
            return

        self.convirtiendo = True
        self.btn_convert.disabled = True
        self.progress_bar.max = len(self.selected_files)
        self.progress_bar.value = 0
        self.lbl_status.text = "Iniciando conversión..."

        target_fmt = self.formato_actual
        bitrate = self.bitrate_actual

        if platform == "android":
            out_dir = os.path.join(get_base_storage_dir(), "Music", "ConvertedAudio")
        else:
            out_dir = os.path.join(os.path.expanduser("~"), "Music", "ConvertedAudio")

        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass

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
            Clock.schedule_once(lambda dt: self._finalizar_error(f"Error: {e}"))
            return

        exitos = 0
        for i, in_path in enumerate(files, start=1):
            base_name = os.path.splitext(os.path.basename(in_path))[0]
            out_path = os.path.join(out_dir, f"{base_name}.{target_fmt}")
            
            Clock.schedule_once(lambda dt, name=base_name: self._actualizar_status(f"Convirtiendo ({i}/{len(files)}): {name}"))
            
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
        self.lbl_status.text = f"✅ ¡Completado! {exitos}/{total} guardados en Música/ConvertedAudio"

    def _finalizar_error(self, err_msg):
        self.convirtiendo = False
        self.btn_convert.disabled = False
        self.lbl_status.text = f"❌ {err_msg}"


if __name__ == "__main__":
    MobileAudioConverterApp().run()
