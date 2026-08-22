"""Coordinador de las siete fases del Render Pipeline educativo."""

from css_loader import CSSLoader
from cssom import CSSParser, CSSStyleSheet
from layout import LayoutEngine
from painter import Painter
from render_tree import RenderTreeBuilder
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
        self.css_paths = []
        self.css_sources = []
        self.cssom = CSSStyleSheet()
        self.computed_styles = {}
        self.render_tree = None

    def render(self):
        # 1. Style Discovery -> rutas declaradas con <link rel="stylesheet">.
        self.css_paths = self.style_discovery.discover(self.document)
        # 2. CSS Loader -> CSSSource; archivos faltantes producen fuente vacia.
        self.css_sources = self.css_loader.load_all(self.css_paths)
        # 3. CSS Parser -> CSSOM.
        self.cssom = self.css_parser.parse(self.css_sources)
        # 4. Style Resolver -> estilos computados.
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        # 5. Render Tree Builder -> contenido visual independiente del DOM.
        self.render_tree = self.render_tree_builder.build(self.document, self.computed_styles)
        # 6. Layout Engine -> solo cajas geometricas del Render Tree.
        self.layout_engine.layout(self.render_tree)
        # 7. Painter -> solo Render Tree con layout.
        self.painter.paint(self.render_tree)
        return self.render_tree

    def reflow(self):
        """Reutiliza el Render Tree y recalcula solamente layout + paint."""
        if self.render_tree is None:
            return self.render()
        self.layout_engine.layout(self.render_tree)
        self.painter.paint(self.render_tree)
        return self.render_tree

    def repaint(self):
        """Reutiliza estilos y geometria existentes; ejecuta solo Paint."""
        self.painter.paint(self.render_tree)

    def refresh_visual_styles(self):
        """Para color/fondo: recalcula estilos y pinta sin ejecutar Layout."""
        if self.render_tree is None:
            return self.render()
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        self._replace_styles(self.render_tree)
        self.repaint()

    def restyle_and_reflow(self):
        """Para font-size y otras propiedades geometricas: estilo + layout + paint."""
        if self.render_tree is None:
            return self.render()
        self.computed_styles = self.style_resolver.resolve(self.document, self.cssom)
        self._replace_styles(self.render_tree)
        self.reflow()

    def _replace_styles(self, visual_node):
        visual_node.styles = self.computed_styles[visual_node.dom_node]
        for child in visual_node.children:
            self._replace_styles(child)
