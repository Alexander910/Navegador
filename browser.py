import tkinter as tk

from renderer import Renderer


class Browser:

    def _init_(self):

        self.window = tk.Tk()

        self.window.title("MiniBrowser")

        self.canvas = tk.Canvas(

            self.window,

            width=800,

            height=600,

            bg="white"

        )

        self.canvas.pack(fill="both", expand=True)

    def display(self, dom):

        renderer = Renderer(self.canvas)

        renderer.render(dom)

        self.window.mainloop()