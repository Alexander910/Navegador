from dom import Document
from javascript_engine import JavaScriptEngine


motor_js = JavaScriptEngine(Document())

codigo = """
let x = 10;
let y = 20;
x + y;
"""

resultado = motor_js.ejecutar(codigo)

print("Resultado:", resultado)
