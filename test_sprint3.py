"""Pruebas del caso integral y de las siete fases sin abrir Tkinter."""

from pathlib import Path
import tempfile
import unittest

from css_loader import CSSLoadError, CSSLoader
from cssom import CLASS_SPECIFICITY, ID_SPECIFICITY, TAG_SPECIFICITY, CSSParser
from dom import Document, Element, TextNode
from dom_bridge import DOMBridge, QuickJSAdapter, quickjs_available
from javascript_loader import JavaScriptLoadError, JavaScriptLoader
from lector_html import LectorHTML
from main import RESOURCES, load_document
from painter import Painter
from pipeline import RenderPipeline
from render_tree import RenderTreeBuilder
from style_resolver import StyleResolver


def add(parent, tag, attributes=None, text=None):
    element = parent.append_child(Element(tag, attributes))
    if text is not None:
        element.append_child(TextNode(text))
    return element


def find_by_id(node, identifier):
    if isinstance(node, Element) and node.get_attribute("id") == identifier:
        return node
    for child in node.children:
        found = find_by_id(child, identifier)
        if found:
            return found
    return None


def render_contains(node, dom_node):
    if node.dom_node is dom_node:
        return True
    return any(render_contains(child, dom_node) for child in node.children)


def render_node_for(node, dom_node):
    if node.dom_node is dom_node:
        return node
    for child in node.children:
        found = render_node_for(child, dom_node)
        if found:
            return found
    return None


class FakeCanvas:
    def __init__(self):
        self.operations = []

    def delete(self, *args):
        self.operations.append(("delete", args))

    def create_text(self, *args, **kwargs):
        self.operations.append(("text", args, kwargs))

    def create_rectangle(self, *args, **kwargs):
        self.operations.append(("rectangle", args, kwargs))


class ResourceAndPipelineTests(unittest.TestCase):
    def setUp(self):
        self.html_path = RESOURCES / "index.html"
        self.document = load_document(self.html_path)

    def test_real_html_builds_dom_and_discovers_css_and_javascript(self):
        title = find_by_id(self.document, "titulo")
        self.assertIsNotNone(title)
        self.assertEqual(title.tag, "h1")
        pipeline = RenderPipeline(self.document, FakeCanvas(), self.html_path)
        pipeline.render()
        self.assertEqual(pipeline.css_paths, ["style.css"])
        self.assertIn("#titulo", pipeline.css_sources[0].source)
        self.assertEqual(len(pipeline.cssom.rules), 7)
        self.assertEqual(pipeline.script_discovery.discover(self.document), ["app.js"])
        scripts = pipeline.javascript_loader.load_all(["app.js"])
        self.assertIn("mensaje.innerHTML", scripts[0].source)

    def test_official_computed_styles_and_hidden_render_exclusion(self):
        pipeline = RenderPipeline(self.document, FakeCanvas(), self.html_path)
        tree = pipeline.render()
        title = find_by_id(self.document, "titulo")
        description = find_by_id(self.document, "mensaje")
        hidden = find_by_id(self.document, "oculto")
        button = find_by_id(self.document, "boton")
        self.assertEqual(pipeline.computed_styles[title]["color"], "blue")
        self.assertEqual(pipeline.computed_styles[title]["font-size"], "32px")
        self.assertEqual(pipeline.computed_styles[description]["color"], "gray")
        self.assertEqual(pipeline.computed_styles[description]["font-size"], "18px")
        self.assertEqual(pipeline.computed_styles[button]["color"], "white")
        self.assertEqual(pipeline.computed_styles[button]["background-color"], "blue")
        self.assertEqual((pipeline.computed_styles[button]["width"], pipeline.computed_styles[button]["height"]),
                         ("120px", "40px"))
        self.assertIsNotNone(hidden.parent)
        self.assertFalse(render_contains(tree, hidden))

    def test_pipeline_has_seven_explicit_phases_without_tkinter(self):
        canvas = FakeCanvas()
        pipeline = RenderPipeline(self.document, canvas, self.html_path)
        pipeline.render()
        self.assertEqual(pipeline.phase_log, ["style-discovery", "css-loader", "css-parser",
                                              "style-resolver", "render-tree", "layout", "paint"])
        self.assertEqual(pipeline.events, ["render"])
        self.assertTrue(canvas.operations)

    def test_painter_uses_computed_styles_for_official_visuals(self):
        canvas = FakeCanvas()
        RenderPipeline(self.document, canvas, self.html_path).render()
        texts = [operation[2] for operation in canvas.operations if operation[0] == "text"]
        title = next(item for item in texts if item["text"] == "Quickjs Funionando")
        description = next(item for item in texts if item["text"] == "estilos cambiados")
        self.assertEqual((title["fill"], title["font"][1]), ("blue", 32))
        self.assertEqual((description["fill"], description["font"][1]), ("gray", 18))
        self.assertNotIn("No deberías verme", [item["text"] for item in texts])
        self.assertTrue(any(op[0] == "rectangle" and op[2]["fill"] == "blue"
                            for op in canvas.operations))

    def test_display_block_none_block_rebuilds_render_tree(self):
        pipeline = RenderPipeline(self.document, FakeCanvas(), self.html_path)
        pipeline.render()
        hidden = find_by_id(self.document, "oculto")
        bridge = pipeline.dom_bridge
        bridge.set_inline_style(hidden, "display", "block")
        self.assertTrue(render_contains(pipeline.render_tree, hidden))
        bridge.set_inline_style(hidden, "display", "none")
        self.assertFalse(render_contains(pipeline.render_tree, hidden))
        bridge.set_inline_style(hidden, "display", "block")
        self.assertTrue(render_contains(pipeline.render_tree, hidden))
        self.assertEqual(pipeline.events, ["render", "render", "render", "render"])

    def test_content_visual_and_geometry_invalidation_are_minimal(self):
        pipeline = RenderPipeline(self.document, FakeCanvas(), self.html_path)
        pipeline.render()
        pipeline.events.clear()
        pipeline.phase_log.clear()
        message = find_by_id(self.document, "mensaje")
        bridge = pipeline.dom_bridge
        bridge.set_text(message.children[0], "Contenido actualizado")
        bridge.set_inline_style(message, "color", "gray")
        bridge.set_inline_style(message, "fontSize", "18px")
        self.assertEqual(pipeline.events, ["render", "repaint", "reflow"])
        self.assertEqual(pipeline.phase_log.count("layout"), 2)  # contenido + geometria
        self.assertEqual(pipeline.phase_log.count("render-tree"), 1)


class CSSCascadeTests(unittest.TestCase):
    def _paragraph_style(self, css):
        document = Document()
        paragraph = add(document, "p", {"id": "item", "class": "notice"})
        return StyleResolver().resolve(document, CSSParser().parse(css))[paragraph]

    def test_specificity_values_and_last_equal_rule(self):
        parser = CSSParser()
        self.assertEqual(parser.parse_selector("p").specificity(), TAG_SPECIFICITY)
        self.assertEqual(parser.parse_selector(".notice").specificity(), CLASS_SPECIFICITY)
        self.assertEqual(parser.parse_selector("#item").specificity(), ID_SPECIFICITY)
        style = self._paragraph_style("p { color: red; } .notice { color: green; } #item { color: blue; }")
        self.assertEqual(style["color"], "blue")
        self.assertEqual(self._paragraph_style("p { color: red; } p { color: blue; }")["color"], "blue")

    def test_shorthand_longhand_order_is_preserved(self):
        first = self._paragraph_style("p { margin: 10px; margin-left: 20px; }")
        second = self._paragraph_style("p { margin-left: 20px; margin: 10px; }")
        self.assertEqual((first["margin-top"], first["margin-left"]), ("10px", "20px"))
        self.assertEqual((second["margin-top"], second["margin-left"]), ("10px", "10px"))

    def test_inheritance_and_inline_priority(self):
        document = Document()
        parent = add(document, "div", {"style": "color: purple; font-size: 21px"})
        text = parent.append_child(TextNode("Heredado"))
        style = StyleResolver().resolve(document, CSSParser().parse("div { color: red; font-size: 10px; }"))
        self.assertEqual(style[text]["color"], "purple")
        self.assertEqual(style[text]["font-size"], "21px")
        element = add(document, "p", {"id": "prioridad", "style": "color: orange"})
        style = StyleResolver().resolve(document, CSSParser().parse("#prioridad { color: blue; }"))
        self.assertEqual(style[element]["color"], "orange")


class DOMAndErrorTests(unittest.TestCase):
    def test_append_child_reparents_without_duplicates_and_preserves_parent(self):
        first, second, child = Element("div"), Element("section"), Element("p")
        first.append_child(child)
        first.append_child(child)
        self.assertEqual(first.children, [child])
        second.append_child(child)
        self.assertEqual(first.children, [])
        self.assertEqual(second.children, [child])
        self.assertIs(child.parent, second)
        with self.assertRaises(ValueError):
            child.append_child(second)

    def test_resource_load_errors_name_the_missing_resource(self):
        with tempfile.TemporaryDirectory() as folder:
            html = Path(folder) / "index.html"
            html.write_text("<html></html>", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "archivo HTML"):
                LectorHTML(Path(folder) / "missing.html").leer()
            with self.assertRaisesRegex(CSSLoadError, "missing.css"):
                CSSLoader(document_path=html).load("missing.css")
            with self.assertRaisesRegex(JavaScriptLoadError, "missing.js"):
                JavaScriptLoader(document_path=html).load("missing.js")

    def test_painter_has_no_tag_specific_visual_decisions(self):
        source = Path("painter.py").read_text(encoding="utf-8")
        self.assertNotIn("tag ==", source)
        document = Document()
        tree = RenderTreeBuilder().build(document, StyleResolver().resolve(document, CSSParser().parse("")))
        Painter(FakeCanvas()).paint(tree)


@unittest.skipUnless(quickjs_available(), "QuickJS no esta instalado")
class QuickJSIntegrationTests(unittest.TestCase):
    def test_adapter_exposes_document_and_applies_all_three_mutations(self):
        document = load_document(RESOURCES / "index.html")
        pipeline = RenderPipeline(document, FakeCanvas(), RESOURCES / "index.html")
        pipeline.render()
        pipeline.events.clear()
        pipeline.execute_scripts()
        message = find_by_id(document, "mensaje")
        self.assertEqual(message.children[0].text, "estilos cambiados")
        self.assertEqual(pipeline.events, ["render", "repaint", "reflow"])
        self.assertEqual(pipeline.computed_styles[message]["color"], "gray")
        self.assertEqual(pipeline.computed_styles[message]["font-size"], "18px")

    def test_adapter_supports_attributes_and_style_proxy(self):
        document = Document()
        element = add(document, "p", {"id": "sample"}, "Inicial")
        bridge = DOMBridge(document)
        QuickJSAdapter(bridge).execute(
            'const el = document.getElementById("sample"); el.setAttribute("title", "ok"); '
            'el.style.color = "red"; el.innerHTML = "Final";', "adapter-test.js")
        self.assertEqual(element.get_attribute("title"), "ok")
        self.assertEqual(element.get_attribute("style"), "color: red")
        self.assertEqual(element.children[0].text, "Final")

    def test_canvas_click_dispatches_onclick_to_quickjs(self):
        document = load_document(RESOURCES / "index.html")
        pipeline = RenderPipeline(document, FakeCanvas(), RESOURCES / "index.html")
        pipeline.render()
        pipeline.execute_scripts()
        pipeline.events.clear()
        button = find_by_id(document, "boton")
        box = render_node_for(pipeline.render_tree, button).box
        self.assertTrue(pipeline.dispatch_click(box.x + 1, box.y + 1))
        message = find_by_id(document, "mensaje")
        self.assertEqual(message.children[0].text, "¡Botón ejecutado!")
        self.assertEqual(pipeline.events, ["render", "repaint", "reflow"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
