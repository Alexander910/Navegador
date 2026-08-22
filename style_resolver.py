"""Fase 4: cascada de estilos computados, separada de Layout y Paint."""

from cssom import CSSParser
from dom import Element


INHERITED_PROPERTIES = {"color", "font-size", "font-family", "font-weight"}
INITIAL_STYLE = {
    "display": "block", "color": "black", "background-color": "transparent",
    "font-size": "16px", "font-family": "Arial", "font-weight": "normal",
    "width": "auto", "height": "auto",
    "margin-top": "0px", "margin-right": "0px", "margin-bottom": "0px", "margin-left": "0px",
    "padding-top": "0px", "padding-right": "0px", "padding-bottom": "0px", "padding-left": "0px",
    "border-width": "0px", "border-color": "black",
}
USER_AGENT_STYLES = {"button": {"width": "120px", "height": "40px"}}
INLINE_SPECIFICITY = 1000


class StyleResolver:
    def __init__(self):
        self.computed_styles = {}

    def resolve(self, document, stylesheet):
        self.computed_styles = {}
        self._resolve_node(document, None, stylesheet)
        return self.computed_styles

    def _resolve_node(self, node, parent_style, stylesheet):
        style = dict(INITIAL_STYLE)
        if parent_style:
            for property_name in INHERITED_PROPERTIES:
                style[property_name] = parent_style[property_name]

        if isinstance(node, Element):
            style.update(USER_AGENT_STYLES.get(node.tag, {}))
            winners = {}
            for rule in stylesheet.rules:
                if rule.selector.matches(node):
                    for declaration_index, declaration in enumerate(rule.declarations):
                        for property_name, value in self._expanded_declaration(
                                declaration.property, declaration.value):
                            priority = (rule.selector.specificity(), rule.order, declaration_index)
                            if property_name not in winners or priority >= winners[property_name][0]:
                                winners[property_name] = (priority, value)
            for property_name, (_, value) in winners.items():
                style[property_name] = value
            # Inline tiene prioridad superior y conserva el orden de escritura.
            for declaration in CSSParser.parse_declarations(node.get_attribute("style", "")):
                for property_name, value in self._expanded_declaration(
                        declaration.property, declaration.value):
                    style[property_name] = value

        self.computed_styles[node] = style
        for child in node.children:
            self._resolve_node(child, style, stylesheet)

    @staticmethod
    def _expanded_declaration(property_name, value):
        """Expande shorthand justo donde aparece para conservar la cascada real."""
        if property_name not in {"margin", "padding"}:
            return ((property_name, value),)
        values = value.split()
        if len(values) == 1:
            values *= 4
        elif len(values) == 2:
            values = [values[0], values[1], values[0], values[1]]
        elif len(values) == 3:
            values = [values[0], values[1], values[2], values[1]]
        elif len(values) != 4:
            return ()
        return tuple((f"{property_name}-{side}", side_value)
                     for side, side_value in zip(("top", "right", "bottom", "left"), values))
