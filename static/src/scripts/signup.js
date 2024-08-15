document.getElementById("signup-form").addEventListener("submit", async function (event) {
  event.preventDefault();

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const messageContainer = document.getElementById("message-container");

  try {
      const response = await fetch("/api/signup", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ name, email, password }),
      });

      const result = await response.json();

      if (response.ok) {
          messageContainer.innerHTML = `<div class="text-green-400">${result.message}</div>`;
          setTimeout(() => {
              window.location.href = "/login";
          }, 2000);
      } else {
          messageContainer.innerHTML = `<div class="text-red-400">${result.error || 'An unexpected error occurred.'}</div>`;
      }
  } catch (error) {
      // Handle network errors or other unexpected issues
      messageContainer.innerHTML = `<div class="text-red-400">An unexpected error occurred: ${error.message}</div>`;
  }
});
