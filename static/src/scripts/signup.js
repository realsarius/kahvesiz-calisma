document.getElementById("signup-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const csrfToken = document
        .querySelector('meta[name="csrf-token"]')
        ?.getAttribute("content");

    const messageContainer = document.getElementById("message-container");

    try {
        const response = await fetch("/api/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({name, email, password}),
        });

        const result = await response.json();
        const apiData = result.data || {};
        const apiError = result.error?.message;

        if (response.ok) {
            messageContainer.innerHTML = `<div class="text-green-400">${apiData.message || "İşlem başarılı."}</div>`;
            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);
        } else {
            messageContainer.innerHTML = `<div class="text-red-400">${apiError || "Beklenmeyen bir hata oluştu."}</div>`;
        }
    } catch (error) {
        // Handle network errors or other unexpected issues
        messageContainer.innerHTML = `<div class="text-red-400">An unexpected error occurred: ${error.message}</div>`;
    }
});
