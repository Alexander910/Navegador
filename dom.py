class Node:

    def _init_(self):

        self.parent = None
        self.children = []


class Document(Node):

    def _init_(self):

        super()._init_()

        self.type = "Document"


class Element(Node):

    def _init_(self, tag, attributes=None):

        super()._init_()

        self.tag = tag

        self.attributes = attributes or {}


class TextNode(Node):

    def _init_(self, text):

        super()._init_()

        self.text = text