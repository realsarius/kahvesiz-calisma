// Event listener for "Users" link
document
  .getElementById("users-link")
  .addEventListener("click", function (event) {
    event.preventDefault();
    // Hide the cafes container and show the users container
    document.getElementById("cafes-container").classList.add("hidden");
    document.getElementById("users-container").classList.remove("hidden");

    // Fetch and display users
    fetchUsers();
  });

// Event listener for "Cafes" link
document
  .getElementById("cafes-link")
  .addEventListener("click", function (event) {
    event.preventDefault();
    // Hide the users container and show the cafes container
    document.getElementById("users-container").classList.add("hidden");
    document.getElementById("cafes-container").classList.remove("hidden");

    // Fetch and display cafes
    fetchCafes();
  });

// Function to fetch and display users
function fetchUsers() {
  fetch("/api/users")
    .then((response) => response.json())
    .then((data) => {
      const usersContainer = document.getElementById("users-container");
      const usersList = document.getElementById("users-list");

      // Clear existing content
      usersList.innerHTML = "";

      if (data.users) {
        data.users.forEach((user) => {
          const row = document.createElement("tr");
          row.innerHTML = `
              <td class="px-6 py-2 whitespace-nowrap">${user.id}</td>
              <td class="px-6 py-2 whitespace-nowrap">${user.name}</td>
              <td class="px-6 py-2 whitespace-nowrap">${user.email}</td>
              <td class="px-6 py-2 whitespace-nowrap">${user.created_at}</td>
              <td class="px-6 py-2 whitespace-nowrap">
                <button class="px-4 py-2 border rounded">Edit</button>
                <button class="px-4 py-2 border rounded">Delete</button>
              </td>
            `;
          usersList.appendChild(row);
        });

        // Show the users container
        usersContainer.classList.remove("hidden");
      } else {
        console.error("No users found");
      }
    })
    .catch((error) => console.error("Error fetching users:", error));
}

// Function to fetch and display cafes
function fetchCafes() {
  fetch("/api/cafes")
    .then((response) => response.json())
    .then((data) => {
      const cafesContainer = document.getElementById("cafes-container");
      const cafesList = document.getElementById("cafes-list");

      // Clear existing content
      cafesList.innerHTML = "";

      if (data.cafes) {
        data.cafes.forEach((cafe) => {
          const row = document.createElement("tr");
          row.innerHTML = `
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.id}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.name}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.map_url}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.img_url}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.location}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.seats}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${cafe.coffee_price}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">
                <button class="px-4 py-2 border rounded">Edit</button>
                <button class="px-4 py-2 border rounded">Delete</button>
              </td>
            `;
          cafesList.appendChild(row);
        });

        // Show the cafes container
        cafesContainer.classList.remove("hidden");
      } else {
        console.error("No cafes found");
      }
    })
    .catch((error) => console.error("Error fetching cafes:", error));
}
