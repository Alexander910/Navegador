"""Fase 1: encuentra hojas CSS declaradas en el DOM."""

from dom import Element


class StyleDiscovery:
    def discover(self, document):
        paths = []
        for node in self._walk(document):
            if not isinstance(node, Element) or node.tag != "link":
                continue
            rel = node.get_attribute("rel", "").lower().split()
            href = node.get_attribute("href")
            if "stylesheet" in rel and href:
                paths.append(href)
        return paths

    @staticmethod
    def _walk(node):
        yield node
        for child in node.children:
            yield from StyleDiscovery._walk(child)
