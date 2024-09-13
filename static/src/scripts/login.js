document
    .getElementById("login-form")
    .addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({email, password}),
        });

        const result = await response.json();
        const messageContainer = document.getElementById("message-container");

        if (response.ok) {
            messageContainer.innerHTML = `<div class="  text-green-300">${result.message}</div>`;
            setTimeout(() => (window.location.href = "/"), 2000);
        } else {
            messageContainer.innerHTML = `<div class=" text-red-300">${result.error}</div>`;
        }
    });
