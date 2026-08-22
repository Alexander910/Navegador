import tkinter as tk

from pipeline import RenderPipeline


class Browser:

    def __init__(self):

        self.window = tk.Tk()

        self.window.title("MiniBrowser")

        self.canvas = tk.Canvas(

            self.window,

            width=800,

            height=600,

            bg="white"

        )

        self.canvas.pack(fill="both", expand=True)

    def display(self, dom, document_path=None):

        self.pipeline = RenderPipeline(dom, self.canvas, document_path, 800, 600)

        self.pipeline.render()

        self.window.mainloop()
