"""Coordinador de las siete fases del Render Pipeline educativo."""

from css_loader import CSSLoader
from cssom import CSSParser, CSSStyleSheet
from dom_bridge import DOMBridge, QuickJSAdapter, quickjs_available
from javascript_loader import JavaScriptLoader
from layout import LayoutEngine
from painter import Painter
from render_tree import RenderTreeBuilder
from script_discovery import ScriptDiscovery
from style_discovery import StyleDiscovery
from style_resolver import StyleResolver


class RenderPipeline:
    def __init__(self, document, canvas=None, document_path=None, viewport_width=800, viewport_height=600):
        self.document = document
        self.style_discovery = StyleDiscovery()
        self.css_loader = CSSLoader(document_path=document_path)
        self.css_parser = CSSParser()
        self.style_resolver = StyleResolver()
        self.render_tree_builder = RenderTreeBuilder()
        self.layout_engine = LayoutEngine(viewport_width, viewport_height)
        self.painter = Painter(canvas)
        self.script_discovery = ScriptDiscovery()
        self.javascript_loader = JavaScriptLoader(document_path=document_path)
        self.dom_bridge = DOMBridge(document, self)
        self.css_paths, self.css_sources = [], []
        self.cssom, self.computed_styles, self.render_tree = CSSStyleSheet(), {}, None
        self.script_paths, self.script_sources = [], []
        self.script_adapter, self.javascript_context = None, None
        self.phase_log, self.events = [], []

    def render(self):
        """Ejecuta las siete fases; es la ruta para contenido o estructura."""
        self.events.append("render")
        self.phase_log.extend(("style-discovery", "css-loader", "css-parser", "style-resolver",
                               "render-tree", "layout", "paint"))
        self.css_paths = self.style_discovery.discover(self.document)
        self.css_sources = self.css_loader.load_all(self.css_paths)
        self.cssom = self.css_parser.parse(self.css_sources)
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        self.render_tree = self.render_tree_builder.build(self.document, self.computed_styles)
        self.layout_engine.layout(self.render_tree)
        self.painter.paint(self.render_tree)
        return self.render_tree

    def reflow(self):
        if self.render_tree is None:
            return self.render()
        self.events.append("reflow")
        self.phase_log.extend(("layout", "paint"))
        self.layout_engine.layout(self.render_tree)
        self.painter.paint(self.render_tree)
        return self.render_tree

    def repaint(self):
        if self.render_tree is None:
            return self.render()
        self.events.append("repaint")
        self.phase_log.append("paint")
        self.painter.paint(self.render_tree)

    def refresh_visual_styles(self):
        if self.render_tree is None:
            return self.render()
        self.phase_log.append("style-resolver")
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        self._replace_styles(self.render_tree)
        self.repaint()

    def restyle_and_reflow(self):
        if self.render_tree is None:
            return self.render()
        self.phase_log.append("style-resolver")
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        self._replace_styles(self.render_tree)
        return self.reflow()

    def execute_scripts(self):
        """Descubre, carga y ejecuta scripts externos cuando QuickJS esta instalado."""
        self.script_paths = self.script_discovery.discover(self.document)
        if not self.script_paths:
            return []
        self.script_sources = self.javascript_loader.load_all(self.script_paths)
        if not quickjs_available():
            print("QuickJS no esta instalado; se omite JavaScript (python -m pip install quickjs).")
            return []
        adapter = QuickJSAdapter(self.dom_bridge)
        context = adapter.create_context()
        for source in self.script_sources:
            adapter.execute(source.source, source.filename, context)
        self.script_adapter, self.javascript_context = adapter, context
        return self.script_sources

    def dispatch_click(self, x, y):
        """Encuentra el elemento visual clicado y despacha ``click`` a QuickJS."""
        if self.render_tree is None or self.javascript_context is None:
            return False
        target = self._hit_test(self.render_tree, float(x), float(y))
        identifier = target.dom_node.get_attribute("id") if target else None
        if not identifier:
            return False
        return self.script_adapter.dispatch_event(self.javascript_context, identifier, "click")

    def _hit_test(self, node, x, y):
        box = node.box
        contains = box.x <= x <= box.x + box.width and box.y <= y <= box.y + box.height
        if not contains:
            return None
        for child in reversed(node.children):
            hit = self._hit_test(child, x, y)
            if hit is not None:
                return hit
        return node if node.node_type == "element" else None

    def _replace_styles(self, visual_node):
        visual_node.styles = self.computed_styles[visual_node.dom_node]
        for child in visual_node.children:
            self._replace_styles(child)
