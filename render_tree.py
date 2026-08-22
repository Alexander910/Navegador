"""Representacion visual: distinta del DOM y sin modificarlo."""

from dataclasses import dataclass, field

from dom import Document, Element, TextNode


@dataclass
class Box:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    content_x: float = 0
    content_y: float = 0
    content_width: float = 0
    content_height: float = 0
    margin_top: float = 0
    margin_right: float = 0
    margin_bottom: float = 0
    margin_left: float = 0
    padding_top: float = 0
    padding_right: float = 0
    padding_bottom: float = 0
    padding_left: float = 0
    border_width: float = 0

    @property
    def outer_bottom(self):
        return self.y + self.height + self.margin_bottom


@dataclass
class RenderNode:
    dom_node: object
    styles: dict
    node_type: str
    text: str = ""
    tag: str = ""
    children: list = field(default_factory=list)
    box: Box = field(default_factory=Box)

    @property
    def is_text(self):
        return self.node_type == "text"


class RenderTreeBuilder:
    """Fase 5: recibe DOM estilizado; no conoce Canvas ni calcula geometria."""

    def build(self, document, computed_styles):
        self.computed_styles = computed_styles
        return self._build_node(document)

    def _build_node(self, node):
        style = self.computed_styles[node]
        if isinstance(node, Element) and style.get("display") == "none":
            return None
        if isinstance(node, TextNode) and not node.text.strip():
            return None
        if isinstance(node, Document):
            visual = RenderNode(node, style, "document")
        elif isinstance(node, TextNode):
            # El Painter recibe una copia de texto, no consulta el DOM.
            visual = RenderNode(node, style, "text", text=node.text)
        else:
            visual = RenderNode(node, style, "element", tag=node.tag)
        for child in node.children:
            child_visual = self._build_node(child)
            if child_visual is not None:
                visual.children.append(child_visual)
        return visual
