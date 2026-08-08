from dom import TextNode


class DOMBridge:
    """Expone operaciones puntuales sobre el DOM Python a QuickJS."""

    def __init__(self, dom):
        # Referencia al DOM real construido por TreeBuilder.
        self.dom = dom
        self.elementos = {}
        self.siguiente_handle = 1

    def get_element_by_id(self, id_elemento):
        """Devuelve un handle positivo si encuentra el id, o 0 si no existe."""
        nodo = self._buscar_por_id(self.dom, id_elemento)

        if nodo is None:
            return 0

        # QuickJS recibe únicamente un handle, nunca el nodo Python.
        handle = self.siguiente_handle
        self.siguiente_handle += 1
        self.elementos[handle] = nodo
        return handle

    def _buscar_por_id(self, nodo, id_elemento):
        if hasattr(nodo, "attributes"):
            if nodo.attributes.get("id") == id_elemento:
                return nodo

        if hasattr(nodo, "children"):
            for hijo in nodo.children:
                resultado = self._buscar_por_id(hijo, id_elemento)
                if resultado is not None:
                    return resultado

        return None

    def obtener_elemento(self, handle):
        """Obtiene el nodo Python real asociado a un handle."""
        return self.elementos.get(handle)

    def get_text_content(self, handle):
        """Obtiene recursivamente el texto del nodo real asociado al handle."""
        nodo = self.obtener_elemento(handle)
        if nodo is None:
            return ""

        return self._obtener_texto(nodo)

    def _obtener_texto(self, nodo):
        # Los TextNode del proyecto contienen el valor en el atributo ``text``.
        if hasattr(nodo, "text"):
            return nodo.text or ""

        texto = ""
        for hijo in getattr(nodo, "children", []):
            texto += self._obtener_texto(hijo)

        return texto

    def set_text_content(self, handle, nuevo_texto):
        """Reemplaza el contenido del nodo real asociado al handle."""
        nodo = self.obtener_elemento(handle)
        if nodo is None or not hasattr(nodo, "children"):
            return False

        # Se modifica el mismo nodo construido por TreeBuilder.
        nodo.children.clear()
        nodo.add_child(TextNode(str(nuevo_texto)))
        return True
