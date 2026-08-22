"""Layout de flujo vertical de bloques; no conoce Tkinter ni el Painter."""

import re


def pixels(value, default=None):
    """Convierte un valor ``Npx`` (o ``N``) a flotante; auto devuelve default."""
    if value is None:
        return default
    match = re.fullmatch(r"\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:px)?\s*", str(value))
    return float(match.group(1)) if match else default


class LayoutEngine:
    def __init__(self, viewport_width=800, viewport_height=600):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    def layout(self, root):
        root.box.x = root.box.y = root.box.content_x = root.box.content_y = 0
        root.box.width = root.box.content_width = float(self.viewport_width)
        cursor = 0.0
        for child in root.children:
            self._layout_node(child, 0.0, cursor, float(self.viewport_width))
            cursor = child.box.outer_bottom
        root.box.content_height = cursor
        root.box.height = max(float(self.viewport_height), cursor)
        return root

    def _layout_node(self, node, containing_x, cursor_y, available_width):
        if node.is_text:
            self._layout_text(node, containing_x, cursor_y, available_width)
            return

        style, box = node.styles, node.box
        for side in ("top", "right", "bottom", "left"):
            setattr(box, f"margin_{side}", pixels(style.get(f"margin-{side}"), 0) or 0)
            setattr(box, f"padding_{side}", pixels(style.get(f"padding-{side}"), 0) or 0)
        box.border_width = max(0, pixels(style.get("border-width"), 0) or 0)

        explicit_width = pixels(style.get("width"))
        chrome_width = box.padding_left + box.padding_right + 2 * box.border_width
        automatic_width = max(0, available_width - box.margin_left - box.margin_right - chrome_width)
        box.content_width = explicit_width if explicit_width is not None else automatic_width
        box.width = box.content_width + chrome_width
        box.x = containing_x + box.margin_left
        box.y = cursor_y + box.margin_top
        box.content_x = box.x + box.border_width + box.padding_left
        box.content_y = box.y + box.border_width + box.padding_top

        child_cursor = box.content_y
        for child in node.children:
            self._layout_node(child, box.content_x, child_cursor, box.content_width)
            child_cursor = child.box.outer_bottom
        child_content_height = max(0, child_cursor - box.content_y)
        explicit_height = pixels(style.get("height"))
        box.content_height = explicit_height if explicit_height is not None else child_content_height
        box.height = box.content_height + box.padding_top + box.padding_bottom + 2 * box.border_width

    @staticmethod
    def _layout_text(node, containing_x, cursor_y, available_width):
        box = node.box
        font_size = pixels(node.styles.get("font-size"), 16) or 16
        box.x = box.content_x = containing_x
        box.y = box.content_y = cursor_y
        box.content_width = min(available_width, len(node.text) * font_size * 0.6)
        box.width = box.content_width
        box.content_height = font_size * 1.2
        box.height = box.content_height
