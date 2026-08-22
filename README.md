# MiniBrowser EDU - Práctica 3 CSSOM

MiniBrowser EDU es un navegador didáctico mínimo construido con Python y Tkinter. El caso completo se encuentra en `resources/index.html`, con sus recursos relativos `style.css` y `app.js`.

## Estructura

```text
main.py                 Punto de entrada y carga de HTML
browser.py              Ventana Tkinter y Canvas
dom.py                  Modelo DOM consistente
style_discovery.py      1. Descubre <link rel="stylesheet">
css_loader.py           2. Carga CSS relativo al HTML
cssom.py                3. Parser CSS y CSSOM
style_resolver.py       4. Cascada y estilos computados
render_tree.py          5. Árbol visual (omite display: none)
layout.py               6. Cajas de flujo vertical
painter.py              7. Pintura exclusiva del Render Tree
pipeline.py             Coordinación e invalidaciones
script_discovery.py     Descubre <script src>
javascript_loader.py    Carga JavaScript relativo al HTML
dom_bridge.py           Bridge DOM y adaptador opcional QuickJS
resources/              index.html, style.css y app.js
test_sprint3.py         Pruebas unittest sin ventana real
```

## Arquitectura

La ruta completa es:

```text
DOM -> Style Discovery -> CSS Loader -> CSS Parser/CSSOM -> Style Resolver
    -> Render Tree Builder -> Layout Engine -> Painter (Canvas)
```

El Painter solo recibe `RenderNode`, estilos computados y cajas de layout; no consulta el DOM ni toma decisiones por etiqueta. Los nodos `display: none` siguen en el DOM, pero no se copian al Render Tree.

## Requisitos y ejecución

Se requiere Python 3.10+ con Tkinter. Desde la raíz del proyecto:

```powershell
python main.py
python -m unittest -v
```

QuickJS es opcional para poder abrir y probar las fases que no usan JavaScript. Para ejecutar `resources/app.js` mediante el bridge real:

```powershell
python -m pip install quickjs
python main.py
```

Al estar disponible, QuickJS carga los scripts declarados con `src`, expone `document.getElementById`, `innerHTML`, `textContent`, atributos y `element.style.propiedad`; también conserva `miniDOM` como alias compatible. El Canvas entrega los clics al elemento visual correspondiente, por lo que `element.onclick` y `addEventListener("click", ...)` funcionan. El script de ejemplo hace una mutación de contenido, una visual y una geométrica de forma síncrona, y el botón cambia el mensaje al hacer clic.

## Invalidaciones

- Contenido: actualiza el DOM y reconstruye Render Tree, Layout y Paint.
- Visual (`color`, `background-color`): recalcula estilos y hace Repaint, sin Layout.
- Geométrica (`font-size`, dimensiones, margen, padding o borde): recalcula estilos, hace Reflow y Paint.
- Estructural (`display`): reconstruye el Render Tree, luego Layout y Paint.

## Limitaciones deliberadas

El parser HTML es educativo: reconoce etiquetas simples, atributos y texto; no implementa el estándar HTML completo. El parser CSS acepta selectores simples de etiqueta, clase e ID, sin combinadores, pseudo-clases ni media queries. `innerHTML` del bridge reemplaza el contenido por texto y no interpreta HTML anidado. El layout es flujo vertical de bloques y no implementa inline layout, flexbox ni el algoritmo de cajas completo de CSS.
