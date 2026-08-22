"""Painter Tkinter: consume exclusivamente RenderNode ya calculados."""


class Painter:
    def __init__(self, canvas=None):
        self.canvas = canvas

    def paint(self, render_tree):
        if self.canvas is None or render_tree is None:
            return
        self.canvas.delete("all")
        self._paint_node(render_tree)

    def _paint_node(self, node):
        if node.node_type == "element":
            self._paint_box(node)
        if node.is_text:
            self._paint_text(node)
        for child in node.children:
            self._paint_node(child)

    def _paint_box(self, node):
        box, style = node.box, node.styles
        background = style.get("background-color", "transparent")
        border_width = int(round(box.border_width))
        if background not in ("transparent", "none", ""):
            self.canvas.create_rectangle(box.x, box.y, box.x + box.width, box.y + box.height,
                fill=background, outline=style.get("border-color", "black") if border_width else "",
                width=border_width)
        elif border_width:
            self.canvas.create_rectangle(box.x, box.y, box.x + box.width, box.y + box.height,
                fill="", outline=style.get("border-color", "black"), width=border_width)

    def _paint_text(self, node):
        style = node.styles
        size = int(float(str(style.get("font-size", "16px")).replace("px", "") or 16))
        weight = str(style.get("font-weight", "normal")).lower()
        font = (style.get("font-family", "Arial"), size,
                "bold" if weight == "bold" or weight.isdigit() and int(weight) >= 600 else "normal")
        self.canvas.create_text(node.box.x, node.box.y, text=node.text, anchor="nw",
            fill=style.get("color", "black"), font=font)
