"""Puente DOM e invalidacion del pipeline.

QuickJS es opcional. Para activarlo instale ``quickjs`` y use
``QuickJSAdapter(bridge)``; MiniBrowser no necesita esa dependencia para abrir.

Invalidacion: contenido, atributos y clases reconstruyen con ``render()``;
geometria recalcula estilo + reflow; estilos visuales repintan sin layout.
"""

import importlib.util

from cssom import CSSParser
from dom import Element, TextNode


GEOMETRY_PROPERTIES = {
    "display", "width", "height", "margin", "margin-top", "margin-right",
    "margin-bottom", "margin-left", "padding", "padding-top", "padding-right",
    "padding-bottom", "padding-left", "border-width", "font-size", "font-family",
    "font-weight",
}


def quickjs_available():
    return importlib.util.find_spec("quickjs") is not None


class DOMBridge:
    def __init__(self, document, pipeline=None):
        self.document = document
        self.pipeline = pipeline

    def get_text(self, node):
        if isinstance(node, TextNode):
            return node.text
        return "".join(self.get_text(child) for child in node.children)

    def set_text(self, node, text):
        if not isinstance(node, TextNode):
            raise TypeError("set_text espera un TextNode")
        node.text = str(text)
        self._invalidate_content()

    def get_attribute(self, element, name):
        return self._element(element).get_attribute(name)

    def set_attribute(self, element, name, value):
        self._element(element).set_attribute(name, value)
        self._invalidate_render()

    def add_class(self, element, class_name):
        element = self._element(element)
        classes = element.get_attribute("class", "").split()
        if class_name not in classes:
            classes.append(class_name)
            element.set_attribute("class", " ".join(classes))
            self._invalidate_render()

    def remove_class(self, element, class_name):
        element = self._element(element)
        classes = [name for name in element.get_attribute("class", "").split()
                   if name != class_name]
        element.set_attribute("class", " ".join(classes))
        self._invalidate_render()

    def set_inline_style(self, element, property_name, value):
        element = self._element(element)
        property_name = self._to_kebab_case(property_name)
        declarations = CSSParser.parse_declarations(element.get_attribute("style", ""))
        declarations[property_name] = str(value).strip()
        element.set_attribute("style", "; ".join(
            f"{name}: {style_value}" for name, style_value in declarations.items()))
        if property_name in GEOMETRY_PROPERTIES:
            self._invalidate_geometry()
        else:
            self._invalidate_visual()

    def find_by_id(self, identifier):
        return self._find_by_id(self.document, identifier)

    def get_text_by_id(self, identifier):
        node = self.find_by_id(identifier)
        return self.get_text(node) if node else None

    def set_text_by_id(self, identifier, text):
        element = self.find_by_id(identifier)
        if element is None:
            return False
        text_node = next((child for child in element.children if isinstance(child, TextNode)), None)
        if text_node is None:
            element.append_child(TextNode(text))
            self._invalidate_content()
        else:
            self.set_text(text_node, text)
        return True

    @staticmethod
    def _element(node):
        if not isinstance(node, Element):
            raise TypeError("La operacion espera un Element")
        return node

    @staticmethod
    def _find_by_id(node, identifier):
        if isinstance(node, Element) and node.get_attribute("id") == identifier:
            return node
        for child in node.children:
            found = DOMBridge._find_by_id(child, identifier)
            if found:
                return found
        return None

    def _invalidate_render(self):
        if self.pipeline:
            self.pipeline.render()

    def _invalidate_reflow(self):
        if self.pipeline:
            self.pipeline.reflow()

    def _invalidate_content(self):
        if self.pipeline:
            self.pipeline.render()

    def _invalidate_geometry(self):
        if self.pipeline:
            restyle = getattr(self.pipeline, "restyle_and_reflow", None)
            if restyle:
                restyle()
            else:
                self.pipeline.reflow()

    def _invalidate_visual(self):
        if self.pipeline:
            refresher = getattr(self.pipeline, "refresh_visual_styles", None)
            if refresher:
                refresher()
            else:
                self.pipeline.repaint()

    @staticmethod
    def _to_kebab_case(property_name):
        text = str(property_name).strip()
        result = []
        for character in text:
            if character.isupper():
                result.extend(("-", character.lower()))
            else:
                result.append(character)
        return "".join(result).lstrip("-").lower()


class QuickJSAdapter:
    """Adaptador opcional: expone ``miniDOM`` usando IDs, no objetos Python."""

    def __init__(self, bridge):
        self.bridge = bridge

    def create_context(self):
        if not quickjs_available():
            raise RuntimeError("QuickJS no esta instalado; ejecute: python -m pip install quickjs")
        import quickjs

        context = quickjs.Context()
        context.add_callable("__dom_get_text", self.bridge.get_text_by_id)
        context.add_callable("__dom_set_text", self.bridge.set_text_by_id)
        context.add_callable("__dom_get_attribute", self._get_attribute)
        context.add_callable("__dom_set_attribute", self._set_attribute)
        context.add_callable("__dom_set_style", self._set_style)
        context.eval("""
            const miniDOM = {
              getText: (id) => __dom_get_text(id), setText: (id, text) => __dom_set_text(id, text),
              getAttribute: (id, name) => __dom_get_attribute(id, name),
              setAttribute: (id, name, value) => __dom_set_attribute(id, name, value),
              setStyle: (id, property, value) => __dom_set_style(id, property, value)
            };
        """)
        return context

    def _get_attribute(self, identifier, name):
        element = self.bridge.find_by_id(identifier)
        return self.bridge.get_attribute(element, name) if element else None

    def _set_attribute(self, identifier, name, value):
        element = self.bridge.find_by_id(identifier)
        if not element:
            return False
        self.bridge.set_attribute(element, name, value)
        return True

    def _set_style(self, identifier, property_name, value):
        element = self.bridge.find_by_id(identifier)
        if not element:
            return False
        self.bridge.set_inline_style(element, property_name, value)
        return True
