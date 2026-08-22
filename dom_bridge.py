"""Puente DOM, QuickJS opcional e invalidaciones del Render Pipeline."""

import importlib.util

from dom import Element, TextNode


STRUCTURAL_PROPERTIES = {"display"}
GEOMETRY_PROPERTIES = {
    "width", "height", "margin", "margin-top", "margin-right", "margin-bottom",
    "margin-left", "padding", "padding-top", "padding-right", "padding-bottom",
    "padding-left", "border", "border-width", "font-size", "font-family", "font-weight",
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

    def get_inner_html(self, element):
        return self.get_text(self._element(element))

    def set_inner_html(self, element, content):
        """Alcance educativo: reemplaza el contenido por texto, sin parsear HTML anidado."""
        element = self._element(element)
        for child in list(element.children):
            element.remove_child(child)
        element.append_child(TextNode(str(content)))
        self._invalidate_content()

    def get_attribute(self, element, name):
        return self._element(element).get_attribute(name)

    def set_attribute(self, element, name, value):
        self._element(element).set_attribute(name, value)
        self._invalidate_structural()

    def set_inline_style(self, element, property_name, value):
        element = self._element(element)
        property_name = self._to_kebab_case(property_name)
        previous = element.get_attribute("style", "").strip()
        declaration = f"{property_name}: {str(value).strip()}"
        element.set_attribute("style", f"{previous}; {declaration}" if previous else declaration)
        if property_name in STRUCTURAL_PROPERTIES:
            self._invalidate_structural()
        elif property_name in GEOMETRY_PROPERTIES:
            self._invalidate_geometry()
        else:
            self._invalidate_visual()

    def get_inline_style(self, element, property_name):
        property_name = self._to_kebab_case(property_name)
        value = ""
        for declaration in self._element(element).get_attribute("style", "").split(";"):
            if ":" not in declaration:
                continue
            name, candidate = declaration.split(":", 1)
            if name.strip().lower() == property_name:
                value = candidate.strip()
        return value

    def find_by_id(self, identifier):
        return self._find_by_id(self.document, identifier)

    def get_text_by_id(self, identifier):
        node = self.find_by_id(identifier)
        return self.get_text(node) if node else ""

    def set_text_by_id(self, identifier, text):
        element = self.find_by_id(identifier)
        if element is None:
            return False
        self.set_inner_html(element, text)
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
            if found is not None:
                return found
        return None

    def _invalidate_content(self):
        if self.pipeline:
            self.pipeline.render()

    def _invalidate_structural(self):
        if self.pipeline:
            self.pipeline.render()

    def _invalidate_geometry(self):
        if self.pipeline:
            self.pipeline.restyle_and_reflow()

    def _invalidate_visual(self):
        if self.pipeline:
            self.pipeline.refresh_visual_styles()

    @staticmethod
    def _to_kebab_case(property_name):
        result = []
        for character in str(property_name).strip():
            result.extend(("-", character.lower()) if character.isupper() else character)
        return "".join(result).lstrip("-").lower()


class QuickJSAdapter:
    """Expone document.getElementById y miniDOM sobre callbacks de IDs."""

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
        context.add_callable("__dom_get_style", self._get_style)
        context.add_callable("__dom_set_style", self._set_style)
        context.eval("""
            const __miniHandlers = Object.create(null);
            function __miniElement(id) {
              return {
                get innerHTML() { return __dom_get_text(id); },
                set innerHTML(value) { __dom_set_text(id, String(value)); },
                get textContent() { return __dom_get_text(id); },
                set textContent(value) { __dom_set_text(id, String(value)); },
                getAttribute: function(name) { return __dom_get_attribute(id, String(name)); },
                setAttribute: function(name, value) { return __dom_set_attribute(id, String(name), String(value)); },
                get onclick() { return (__miniHandlers[id] || {}).click || null; },
                set onclick(handler) {
                  (__miniHandlers[id] || (__miniHandlers[id] = {})).click = handler;
                },
                addEventListener: function(type, handler) {
                  (__miniHandlers[id] || (__miniHandlers[id] = {}))[String(type)] = handler;
                },
                click: function() { __miniDispatch(id, "click"); },
                style: new Proxy({}, {
                  get: function(_, property) { return __dom_get_style(id, String(property)); },
                  set: function(_, property, value) {
                    __dom_set_style(id, String(property), String(value)); return true;
                  }
                })
              };
            }
            const document = { getElementById: function(id) { return __miniElement(String(id)); } };
            function __miniDispatch(id, type) {
              const handler = (__miniHandlers[id] || {})[type];
              if (typeof handler === "function") {
                handler.call(__miniElement(id), { type: type, target: __miniElement(id) });
                return true;
              }
              return false;
            }
            const miniDOM = {
              getElementById: document.getElementById,
              getText: function(id) { return __dom_get_text(String(id)); },
              setText: function(id, text) { return __dom_set_text(String(id), String(text)); },
              getAttribute: function(id, name) { return __dom_get_attribute(String(id), String(name)); },
              setAttribute: function(id, name, value) { return __dom_set_attribute(String(id), String(name), String(value)); },
              setStyle: function(id, property, value) { return __dom_set_style(String(id), String(property), String(value)); }
            };
        """)
        return context

    @staticmethod
    def dispatch_event(context, identifier, event_type):
        """Ejecuta un handler registrado por onclick/addEventListener."""
        import json
        return bool(context.eval(
            f"__miniDispatch({json.dumps(str(identifier))}, {json.dumps(str(event_type))})"))

    def execute(self, source, filename="<script>", context=None):
        context = context or self.create_context()
        try:
            context.eval(source)
        except Exception as error:
            raise RuntimeError(f"Error al ejecutar JavaScript '{filename}': {error}") from error
        return context

    def _get_attribute(self, identifier, name):
        element = self.bridge.find_by_id(identifier)
        return self.bridge.get_attribute(element, name) if element else ""

    def _set_attribute(self, identifier, name, value):
        element = self.bridge.find_by_id(identifier)
        if element is None:
            return False
        self.bridge.set_attribute(element, name, value)
        return True

    def _get_style(self, identifier, property_name):
        element = self.bridge.find_by_id(identifier)
        return self.bridge.get_inline_style(element, property_name) if element else ""

    def _set_style(self, identifier, property_name, value):
        element = self.bridge.find_by_id(identifier)
        if element is None:
            return False
        self.bridge.set_inline_style(element, property_name, value)
        return True
