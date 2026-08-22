"""Descubrimiento de scripts externos declarado por el DOM."""

from dom import Element


class ScriptDiscovery:
    def discover(self, document):
        paths = []
        for node in self._walk(document):
            if isinstance(node, Element) and node.tag == "script":
                source = node.get_attribute("src")
                if source:
                    paths.append(source)
        return paths

    @staticmethod
    def _walk(node):
        yield node
        for child in node.children:
            yield from ScriptDiscovery._walk(child)
