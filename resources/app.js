// Mutaciones iniciales, síncronas y verificables del caso integral.
const mensaje = document.getElementById("mensaje");
mensaje.innerHTML = "estilos cambiados"; // contenido
mensaje.style.color = "gray";      // Repaint
mensaje.style.fontSize = "18px";   // Reflow + Paint

// Interacción visible: el Canvas despacha el clic al botón mediante QuickJS.
const boton = document.getElementById("boton");
boton.onclick = function () {
    mensaje.innerHTML = "¡Botón ejecutado!";
    mensaje.style.color = "blue";
    mensaje.style.fontSize = "22px";
};
