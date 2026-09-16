"""Punto de entrada principal para la aplicacion movil Android (Kivy)."""

import sys
import traceback

def main():
    try:
        from mobile_app import MobileAudioConverterApp
        MobileAudioConverterApp().run()
    except Exception as e:
        print("ERROR CRÍTICO AL INICIAR LA APP:", e)
        traceback.print_exc()
        try:
            from kivy.app import App
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView

            class CrashDisplayApp(App):
                def build(self):
                    err_msg = f"Error al iniciar la aplicación:\n\n{str(e)}\n\nDetalles:\n{traceback.format_exc()}"
                    sv = ScrollView()
                    lbl = Label(
                        text=err_msg,
                        size_hint_y=None,
                        color=(1, 0.3, 0.3, 1),
                        padding=(20, 20)
                    )
                    lbl.bind(texture_size=lambda *x: setattr(lbl, "height", max(lbl.texture_size[1], 400)))
                    sv.add_widget(lbl)
                    return sv

            CrashDisplayApp().run()
        except Exception:
            pass

if __name__ == "__main__":
    main()
