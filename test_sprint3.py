"""Pruebas sin Tkinter de las siete fases de la Practica No. 3."""

from pathlib import Path
import tempfile
import unittest

from css_loader import CSSLoader, CSSSource
from cssom import CLASS_SPECIFICITY, ID_SPECIFICITY, TAG_SPECIFICITY, CSSParser
from cssom_inspector import CSSOMInspector
from dom import Document, Element, TextNode
from dom_bridge import DOMBridge
from layout import LayoutEngine
from painter import Painter
from render_tree import RenderTreeBuilder
from style_discovery import StyleDiscovery
from style_resolver import StyleResolver


CASE_CSS = """body { background-color: white; }
h1 { color: red; font-size: 32px; }
.principal { color: green; }
#titulo { color: blue; }
.descripcion { color: gray; font-size: 18px; }
#oculto { display: none; }
button { color: white; background-color: blue; font-size: 16px; }"""


def add(parent, tag, attributes=None, text=None):
    element = parent.append_child(Element(tag, attributes))
    if text is not None:
        element.append_child(TextNode(text))
    return element


def case_document():
    document = Document()
    html = add(document, "html")
    head = add(html, "head")
    add(head, "link", {"rel": "stylesheet", "href": "style.css"})
    body = add(html, "body")
    title = add(body, "h1", {"id": "titulo", "class": "principal"}, "MiniBrowser EDU")
    message = add(body, "p", {"id": "mensaje", "class": "descripcion"}, "Render Pipeline funcionando")
    hidden = add(body, "p", {"id": "oculto"}, "No deberías verme")
    button = add(body, "button", {"id": "boton"}, "Ejecutar")
    return document, title, message, hidden, button


class DiscoveryAndCSSOMTests(unittest.TestCase):
    def test_style_discovery_finds_link_stylesheet(self):
        document, *_ = case_document()
        self.assertEqual(StyleDiscovery().discover(document), ["style.css"])

    def test_loader_reads_css_source_and_missing_file_is_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            html = Path(folder) / "index.html"
            html.write_text("<html></html>", encoding="utf-8")
            (Path(folder) / "style.css").write_text("h1 { color: red; }", encoding="utf-8")
            source = CSSLoader(document_path=html).load("style.css")
            self.assertEqual(source.filename, "style.css")
            self.assertIn("color: red", source.source)
            self.assertEqual(CSSLoader(document_path=html).load("missing.css").source, "")

    def test_parser_builds_the_seven_official_rules(self):
        sheet = CSSParser().parse([CSSSource("style.css", CASE_CSS)])
        self.assertEqual(len(sheet.rules), 7)
        self.assertEqual(CSSOMInspector().inspect(sheet)[0]["selector"], "body")

    def test_selector_matching_and_official_specificities(self):
        document, title, *_ = case_document()
        parser = CSSParser()
        self.assertTrue(parser.parse_selector("h1").matches(title))
        self.assertTrue(parser.parse_selector(".principal").matches(title))
        self.assertTrue(parser.parse_selector("#titulo").matches(title))
        self.assertEqual(parser.parse_selector("h1").specificity(), TAG_SPECIFICITY)
        self.assertEqual(parser.parse_selector(".principal").specificity(), CLASS_SPECIFICITY)
        self.assertEqual(parser.parse_selector("#titulo").specificity(), ID_SPECIFICITY)
        self.assertIsNone(parser.parse_selector("div p"))
        self.assertIsNone(parser.parse_selector("h1.principal"))


class StyleAndRenderTreeTests(unittest.TestCase):
    def test_title_is_blue_and_keeps_font_size_from_tag_rule(self):
        document, title, *_ = case_document()
        styles = StyleResolver().resolve(document, CSSParser().parse(CASE_CSS))
        self.assertEqual(styles[title]["color"], "blue")
        self.assertEqual(styles[title]["font-size"], "32px")

    def test_later_equal_specificity_wins(self):
        document = Document()
        paragraph = add(document, "p", {"class": "descripcion"})
        sheet = CSSParser().parse(".descripcion { color: red; } .descripcion { color: blue; }")
        self.assertEqual(StyleResolver().resolve(document, sheet)[paragraph]["color"], "blue")

    def test_hidden_node_stays_in_dom_but_not_render_tree(self):
        document, _, _, hidden, _ = case_document()
        styles = StyleResolver().resolve(document, CSSParser().parse(CASE_CSS))
        tree = RenderTreeBuilder().build(document, styles)
        self.assertIsNotNone(hidden.parent)
        visual_nodes = []
        def collect(node):
            visual_nodes.append(node.dom_node)
            for child in node.children:
                collect(child)
        collect(tree)
        self.assertNotIn(hidden, visual_nodes)


class LayoutAndPainterTests(unittest.TestCase):
    def _tree(self):
        document, *_ = case_document()
        styles = StyleResolver().resolve(document, CSSParser().parse(CASE_CSS))
        return RenderTreeBuilder().build(document, styles)

    def test_layout_calculates_boxes_without_canvas_or_paint(self):
        tree = self._tree()
        LayoutEngine(800, 600).layout(tree)
        body = tree.children[0].children[1]
        title, message, button = body.children[0], body.children[1], body.children[2]
        self.assertEqual(body.box.width, 800)
        self.assertGreater(title.box.height, 0)
        self.assertGreater(message.box.y, title.box.y)
        self.assertEqual(button.box.width, 120)
        self.assertEqual(button.box.height, 40)

    def test_painter_only_operates_when_explicitly_called(self):
        class FakeCanvas:
            def __init__(self): self.operations = []
            def delete(self, *args): self.operations.append("delete")
            def create_text(self, *args, **kwargs): self.operations.append("text")
            def create_rectangle(self, *args, **kwargs): self.operations.append("rectangle")

        tree = self._tree()
        canvas = FakeCanvas()
        LayoutEngine(800, 600).layout(tree)
        self.assertEqual(canvas.operations, [])
        Painter(canvas).paint(tree)
        self.assertIn("delete", canvas.operations)
        self.assertIn("text", canvas.operations)


class BridgeTests(unittest.TestCase):
    def test_content_visual_and_geometry_invalidations(self):
        class FakePipeline:
            def __init__(self): self.calls = []
            def render(self): self.calls.append("render")
            def refresh_visual_styles(self): self.calls.append("repaint")
            def restyle_and_reflow(self): self.calls.append("reflow")

        document, title, *_ = case_document()
        bridge = DOMBridge(document, FakePipeline())
        bridge.set_text(title.children[0], "Nuevo título")
        bridge.set_inline_style(title, "color", "red")
        bridge.set_inline_style(title, "fontSize", "80px")
        self.assertEqual(bridge.pipeline.calls, ["render", "repaint", "reflow"])


if __name__ == "__main__":
    unittest.main()
