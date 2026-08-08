class Node:
    """Nodo base del DOM."""

    def __init__(self):
        self.parent = None
        self.children = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)


class Document(Node):
    def __init__(self):
        super().__init__()
        self.type = "Document"


class Element(Node):
    def __init__(self, tag, attributes=None):
        super().__init__()
        self.tag = tag
        self.attributes = attributes or {}


class TextNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text
