/**
 * toast.js (loaded inline within app.js scope)
 * Small toast notification helper shared across modules via window.Toast.
 */
const Toast = (() => {
  function show(message, type = "success", duration = 3500) {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity 200ms ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 220);
    }, duration);
  }

  return {
    success: (msg) => show(msg, "success"),
    error: (msg) => show(msg, "error"),
    warning: (msg) => show(msg, "warning"),
  };
})();
