#renderer.py from dom import Element
from dom import TextNode


class Renderer:

    def _init_(self, canvas):

        self.canvas = canvas

        self.x = 20
        self.y = 30

    def render(self, node):

        if isinstance(node, Element):

            if node.tag == "h1":

                self.draw_text(node, 24)

            elif node.tag == "p":

                self.draw_text(node, 14)

            elif node.tag == "button":

                self.draw_button(node)

        for child in node.children:

            self.render(child)

    def draw_text(self, element, size):

        for child in element.children:

            if isinstance(child, TextNode):

                self.canvas.create_text(

                    self.x,

                    self.y,

                    text=child.text,

                    anchor="nw",

                    font=("Arial", size)

                )

                self.y += size + 20

    def draw_button(self, element):

        text = ""

        for child in element.children:

            if isinstance(child, TextNode):

                text = child.text

        width = 120
        height = 35

        self.canvas.create_rectangle(

            self.x,

            self.y,

            self.x + width,

            self.y + height

        )

        self.canvas.create_text(

            self.x + width / 2,

            self.y + height / 2,

            text=text

        )

        self.y += height + 20