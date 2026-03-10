document.addEventListener("DOMContentLoaded", function () {
    const usersLink = document.getElementById("users-link");
    const cafesLink = document.getElementById("cafes-link");
    const assignModeratorLink = document.getElementById("assign-moderator-link");

    const usersContainer = document.getElementById("users-container");
    const cafesContainer = document.getElementById("cafes-container");
    const assignModeratorContainer = document.getElementById(
        "assign-moderator-container"
    );

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // Function to show the appropriate container based on the clicked link
    function showContainer(container) {
        usersContainer.classList.add("hidden");
        cafesContainer.classList.add("hidden");
        assignModeratorContainer.classList.add("hidden");
        container.classList.remove("hidden");
    }

    usersLink.addEventListener("click", function () {
        showContainer(usersContainer);
        fetchUsers(); // Fetch and display users when showing the users container
    });

    cafesLink.addEventListener("click", function () {
        showContainer(cafesContainer);
        fetchCafes(); // Fetch and display cafes when showing the cafes container
    });

    assignModeratorLink.addEventListener("click", function () {
        showContainer(assignModeratorContainer);
        populateSelectOptions();
        populateModeratedCafes(); // Populate moderated cafes when showing the assign moderator container
    });

    // Function to fetch and display users
    function fetchUsers() {
        fetch("/api/users")
            .then((response) => response.json())
            .then((data) => {
                const usersList = document.getElementById("users-list");

                // Clear existing content
                usersList.innerHTML = "";

                if (data.users) {
                    data.users.forEach((user) => {
                        const row = document.createElement("tr");
                        row.innerHTML = `
              <td class="px-6 py-2 whitespace-nowrap">${escapeHtml(user.id)}</td>
              <td class="px-6 py-2 whitespace-nowrap">${escapeHtml(user.name)}</td>
              <td class="px-6 py-2 whitespace-nowrap">${escapeHtml(user.email)}</td>
              <td class="px-6 py-2 whitespace-nowrap">${escapeHtml(user.created_at)}</td>
              <td class="px-6 py-2 whitespace-nowrap">
                <span class="text-xs text-zinc-500">N/A</span>
              </td>
            `;
                        usersList.appendChild(row);
                    });
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
                const cafesList = document.getElementById("cafes-list");

                // Clear existing content
                cafesList.innerHTML = "";

                if (data.cafes) {
                    data.cafes.forEach((cafe) => {
                        const row = document.createElement("tr");
                        row.innerHTML = `
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.id)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.name)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.map_url)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.img_url)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.location)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.seats)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">${escapeHtml(cafe.coffee_price)}</td>
              <td class="px-6 py-2 whitespace-nowrap max-w-xs truncate">
                <span class="text-xs text-zinc-500">N/A</span>
              </td>
            `;
                        cafesList.appendChild(row);
                    });
                } else {
                    console.error("No cafes found");
                }
            })
            .catch((error) => console.error("Error fetching cafes:", error));
    }

    function populateSelectOptions() {
        const userSelect = document.getElementById("user_id");
        const cafeSelect = document.getElementById("cafe_id");

        // Fetch users
        fetch("api/users")
            .then((response) => response.json())
            .then((data) => {
                const users = data.users;
                userSelect.innerHTML = "";
                const defaultOption = document.createElement("option");
                defaultOption.value = "";
                defaultOption.textContent = "Select User";
                userSelect.appendChild(defaultOption);
                users.forEach((user) => {
                    const option = document.createElement("option");
                    option.value = String(user.id);
                    option.textContent = user.name;
                    userSelect.appendChild(option);
                });
            })
            .catch((error) => {
                console.error("Error fetching users:", error);
            });

        // Fetch cafes
        fetch("api/cafes")
            .then((response) => response.json())
            .then((data) => {
                const cafes = data.cafes;
                cafeSelect.innerHTML = "";
                const defaultOption = document.createElement("option");
                defaultOption.value = "";
                defaultOption.textContent = "Select Cafe";
                cafeSelect.appendChild(defaultOption);
                cafes.forEach((cafe) => {
                    const option = document.createElement("option");
                    option.value = String(cafe.id);
                    option.textContent = cafe.name;
                    cafeSelect.appendChild(option);
                });
            })
            .catch((error) => {
                console.error("Error fetching cafes:", error);
            });
    }

    // Function to populate moderated cafes for the selected user
    function populateModeratedCafes() {
        const userSelect = document.getElementById("user_id");
        const moderatedCafesDiv = document.getElementById("moderated-cafes-list");

        userSelect.addEventListener("change", function () {
            const userId = userSelect.value;

            if (userId) {
                fetch(`/moderated_cafes/${userId}`)
                    .then((response) => response.json())
                    .then((data) => {
                        const cafes = data.cafes;

                        // Create the table structure
                        let tableHTML =
                            '<table class="min-w-full divide-y divide-gray-200">';
                        tableHTML += "<thead><tr>";
                        tableHTML +=
                            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cafe ID</th>';
                        tableHTML +=
                            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cafe Name</th>';
                        tableHTML +=
                            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>';
                        tableHTML += "</tr></thead><tbody>";

                        cafes.forEach((cafe) => {
                            tableHTML += `<tr><td class="px-6 py-4 whitespace-nowrap">${escapeHtml(cafe.id)}</td>`;
                            tableHTML += `<td class="px-6 py-4 whitespace-nowrap">${escapeHtml(cafe.name)}</td>`;
                            tableHTML += `<td class="px-6 py-4 whitespace-nowrap"><button class="px-4 py-2 border rounded remove-moderator-btn" data-user-id="${escapeHtml(userId)}" data-cafe-id="${escapeHtml(cafe.id)}">Remove</button></td></tr>`;
                        });

                        tableHTML += "</tbody></table>";

                        moderatedCafesDiv.innerHTML = tableHTML;
                        moderatedCafesDiv
                            .querySelectorAll(".remove-moderator-btn")
                            .forEach((button) => {
                                button.addEventListener("click", () => {
                                    const selectedUserId =
                                        button.getAttribute("data-user-id");
                                    const selectedCafeId =
                                        button.getAttribute("data-cafe-id");
                                    window.removeModerator(
                                        selectedUserId,
                                        selectedCafeId
                                    );
                                });
                            });
                    })
                    .catch((error) => {
                        console.error("Error fetching cafes:", error);
                    });
            } else {
                moderatedCafesDiv.innerHTML =
                    "<p>The user doesn't moderate any cafes.</p>";
            }
        });
    }

    // Function to remove a moderator
    window.removeModerator = function (userId, cafeId) {
        fetch(`/remove_moderator/${userId}/${cafeId}`, {
            method: "DELETE",
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    alert("Moderator removed successfully.");
                    // Refresh the moderated cafes list
                    document.getElementById("user_id").dispatchEvent(new Event("change"));
                } else {
                    alert("Failed to remove moderator: " + data.message);
                }
            })
            .catch((error) => {
                console.error("Error removing moderator:", error);
            });
    };
});
