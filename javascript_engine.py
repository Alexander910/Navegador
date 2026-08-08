import quickjs

from console_js import ConsoleJS
from dom_bridge import DOMBridge


class JavaScriptEngine:
    def __init__(self, dom):
        # Crear contexto QuickJS
        self.contexto = quickjs.Context()

        # Exponer función Python a JavaScript
        self.contexto.add_callable(
            "__console_log",
            ConsoleJS.log,
        )

        # El bridge conserva las referencias al DOM real de Python.
        self.dom_bridge = DOMBridge(dom)
        self.contexto.add_callable(
            "__dom_get_element_by_id",
            self.dom_bridge.get_element_by_id,
        )
        self.contexto.add_callable(
            "__dom_get_text_content",
            self.dom_bridge.get_text_content,
        )
        self.contexto.add_callable(
            "__dom_set_text_content",
            self.dom_bridge.set_text_content,
        )

        # Crear las APIs disponibles dentro de JavaScript.
        self.contexto.eval("""
            const console = {
                log: function(mensaje) {
                    __console_log(mensaje);
                }
            };

            const document = {
                getElementById: function(id) {
                    const handle = __dom_get_element_by_id(id);

                    if (handle === 0) {
                        return null;
                    }

                    return {
                        __handle: handle,

                        get textContent() {
                            return __dom_get_text_content(this.__handle);
                        },

                        set textContent(valor) {
                            __dom_set_text_content(this.__handle, valor);
                        }
                    };
                }
            };
        """)

    def ejecutar(self, codigo):
        try:
            return self.contexto.eval(codigo)
        except quickjs.JSException as error:
            print(f"Error de JavaScript: {error}")
            return None
