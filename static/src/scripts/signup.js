document
  .getElementById("signup-form")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/api/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password }),
    });

    const result = await response.json();
    const messageContainer = document.getElementById("message-container");

    if (response.ok) {
      messageContainer.innerHTML = `<div class="text-green-400">${result.message}</div>`;
      setTimeout(() => (window.location.href = "/login"), 2000);
    } else {
      messageContainer.innerHTML = `<div class="text-red-400">${result.error}</div>`;
    }
  });
