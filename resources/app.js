// Mutaciones iniciales, síncronas y verificables del caso integral.
const mensaje = document.getElementById("mensaje");
mensaje.innerHTML = "estilos cambiados"; // contenido
mensaje.style.color = "#9a3412";   // Repaint
mensaje.style.fontSize = "18px";   // Reflow + Paint

// Interacción visible: el Canvas despacha el clic al botón mediante QuickJS.
const boton = document.getElementById("boton");
boton.onclick = function () {
    mensaje.innerHTML = "¡Botón ejecutado!";
    mensaje.style.color = "#ea580c";
    mensaje.style.fontSize = "22px";
};
