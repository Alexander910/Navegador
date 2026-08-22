# MiniBrowser EDU — Práctica No. 3

El renderizado se divide en siete fases independientes:

```text
DOM -> Style Discovery -> CSS Loader -> CSS Parser/CSSOM -> Style Resolver
    -> Render Tree Builder -> Layout Engine -> Painter (Tkinter Canvas)
```

`RenderPipeline.render()` sigue explícitamente esta secuencia:

```python
css_paths = style_discovery.discover(dom)
css_sources = css_loader.load_all(css_paths)
cssom = css_parser.parse(css_sources)
computed_styles = style_resolver.resolve(dom, cssom)
render_tree = render_tree_builder.build(dom, computed_styles)
layout_engine.layout(render_tree)
painter.paint(render_tree)
```

El DOM no se pinta directamente. `LayoutEngine` no conoce Tkinter y `Painter`
consume texto, estilos y cajas ya presentes en el Render Tree.

Ejecuta el navegador con `python main.py` y las pruebas con
`python -m unittest discover -v`.

QuickJS sigue siendo opcional: `dom_bridge.py` funciona sin el motor y ofrece
`QuickJSAdapter` para activarlo tras instalar `quickjs`. Las mutaciones de
contenido reconstruyen el pipeline; las visuales repintan; y las geométricas
recalculan estilos, Layout y Paint.
