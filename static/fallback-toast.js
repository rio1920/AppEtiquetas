// Fallback script for toast notifications
document.addEventListener("DOMContentLoaded", function () {
  console.log("Fallback toast script loaded");

  // Check if we have variables to show
  const fallbackElement = document.getElementById("variables-fallback-data");
  if (!fallbackElement) {
    console.log("No fallback element found");
    return;
  }

  try {
    if (fallbackElement.dataset.mostrar === "true") {
      const variables = JSON.parse(fallbackElement.dataset.variables);
      const idioma = fallbackElement.dataset.idioma;

      console.log("Fallback script - Variables:", variables);
      console.log("Fallback script - Idioma:", idioma);

      if (variables && variables.length > 0) {
        setTimeout(function () {
          // Create a simple toast-like notification
          const toast = document.createElement("div");
          toast.className = "fallback-alert";
          toast.innerHTML = `
                        <strong>ADVERTENCIA:</strong>
                        <p>Las siguientes variables no tienen traducción en el idioma '${idioma}' y se están mostrando en español:</p>
                        <p>${variables.join(", ")}</p>
                        <button style="position: absolute; top: 5px; right: 5px; background: none; border: none; cursor: pointer;"
                            onclick="this.parentNode.remove();">×</button>
                    `;
          document.body.appendChild(toast);

          // Remove after 8 seconds
          setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.5s";
            setTimeout(() => toast.remove(), 500);
          }, 8000);
        }, 2000);
      }
    }
  } catch (e) {
    console.error("Error in fallback script:", e);
  }
});
