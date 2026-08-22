"""CSSOM reducido al alcance de la Practica No. 3."""

from dataclasses import dataclass, field
import re

from dom import Element


TAG_SPECIFICITY = 1
CLASS_SPECIFICITY = 10
ID_SPECIFICITY = 100


@dataclass(frozen=True)
class Declaration:
    property: str
    value: str


@dataclass(frozen=True)
class Selector:
    """Un selector simple: etiqueta, .clase o #identificador."""
    text: str

    def specificity(self):
        if self.text.startswith("#"):
            return ID_SPECIFICITY
        if self.text.startswith("."):
            return CLASS_SPECIFICITY
        return TAG_SPECIFICITY

    def matches(self, element):
        if not isinstance(element, Element):
            return False
        if self.text.startswith("#"):
            return element.get_attribute("id") == self.text[1:]
        if self.text.startswith("."):
            return self.text[1:] in element.get_attribute("class", "").split()
        return element.tag == self.text


@dataclass(frozen=True)
class CSSRule:
    selector: Selector
    declarations: dict
    order: int


@dataclass
class CSSStyleSheet:
    rules: list[CSSRule] = field(default_factory=list)


# Nombre conservado para ejemplos previos del proyecto.
Stylesheet = CSSStyleSheet


class CSSParser:
    """Convierte CSSSource(s) a un CSSStyleSheet, sin cargar archivos."""

    def parse(self, sources):
        if isinstance(sources, str):
            css_text = sources
        elif hasattr(sources, "source"):
            css_text = sources.source
        else:
            css_text = "\n".join(source.source for source in (sources or []))

        css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
        rules = []
        for order, match in enumerate(re.finditer(r"([^{}]+)\{([^{}]*)\}", css_text)):
            selector = self.parse_selector(match.group(1).strip())
            declarations = self.parse_declarations(match.group(2))
            if selector is not None and declarations:
                rules.append(CSSRule(selector, declarations, order))
        return CSSStyleSheet(rules)

    @staticmethod
    def parse_selector(text):
        # Fuera de alcance: combinadores, pseudoclases y selectores compuestos.
        if re.fullmatch(r"#[\w-]+|\.[\w-]+|[A-Za-z][\w-]*", text or ""):
            return Selector(text.lower() if not text.startswith(("#", ".")) else text)
        return None

    @staticmethod
    def parse_declarations(text):
        declarations = {}
        for fragment in text.split(";"):
            if ":" not in fragment:
                continue
            property_name, value = fragment.split(":", 1)
            property_name = property_name.strip().lower()
            value = value.strip()
            if property_name and value:
                declarations[property_name] = value
        return declarations


def parse_css(sources):
    return CSSParser().parse(sources)
