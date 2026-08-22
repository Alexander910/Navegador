"""Fase 3 auxiliar: representacion legible del CSSOM para clase y pruebas."""


class CSSOMInspector:
    def inspect(self, stylesheet):
        return [
            {"selector": rule.selector.text, "declarations": dict(rule.declarations)}
            for rule in stylesheet.rules
        ]
