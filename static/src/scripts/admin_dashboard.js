document.getElementById('users-link').addEventListener('click', function(event) {
    event.preventDefault();
    fetchUsers();
  });

  function fetchUsers() {
    fetch('/api/users')
      .then(response => response.json())
      .then(data => {
        const usersContainer = document.getElementById('users-container');
        const usersList = document.getElementById('users-list');

        // Clear existing content
        usersList.innerHTML = '';

        if (data.users) {
          data.users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td class="px-6 py-4 whitespace-nowrap">${user.id}</td>
              <td class="px-6 py-4 whitespace-nowrap">${user.name}</td>
              <td class="px-6 py-4 whitespace-nowrap">${user.email}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <button class="px-4 py-2 border rounded">Edit</button>
                <button class="px-4 py-2 border rounded">Delete</button>
              </td>
            `;
            usersList.appendChild(row);
          });

          // Show the users container
          usersContainer.classList.remove('hidden');
        } else {
          console.error('No users found');
        }
      })
      .catch(error => console.error('Error fetching users:', error));
  }