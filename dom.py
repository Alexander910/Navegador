"""Modelo DOM pequeno y unico usado por MiniBrowser EDU."""


class Node:
    """Nodo base. Las relaciones se mantienen solamente desde este modelo."""

    def __init__(self):
        self.parent = None
        self.children = []

    def append_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None


class Document(Node):
    def __init__(self):
        super().__init__()
        self.node_type = "document"


class Element(Node):
    def __init__(self, tag, attributes=None):
        super().__init__()
        self.node_type = "element"
        self.tag = tag.lower()
        self.attributes = {
            str(name).lower(): str(value)
            for name, value in (attributes or {}).items()
        }

    def get_attribute(self, name, default=None):
        return self.attributes.get(name.lower(), default)

    def set_attribute(self, name, value):
        self.attributes[name.lower()] = str(value)


class TextNode(Node):
    def __init__(self, text):
        super().__init__()
        self.node_type = "text"
        self.text = str(text)
