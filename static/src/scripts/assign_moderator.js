document.addEventListener('DOMContentLoaded', function() {
    const userSelect = document.getElementById('user_id');
    const moderatedCafesDiv = document.getElementById('moderated-cafes-list');

    userSelect.addEventListener('change', function() {
        const userId = userSelect.value;

        if (userId) {
            fetch(`/moderated_cafes/${userId}`)
                .then(response => response.json())
                .then(data => {
                    const cafes = data.cafes;
                    
                    let tableHTML = '<table class="min-w-full divide-y divide-gray-200">';
                    tableHTML += '<thead class=""><tr>';
                    tableHTML += '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cafe ID</th>';
                    tableHTML += '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cafe Name</th>';
                    tableHTML += '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>';
                    tableHTML += '</tr></thead><tbody class=" divide-y divide-gray-200">';
                    
                    cafes.forEach(cafe => {
                        tableHTML += `<tr><td class="px-6 py-4 whitespace-nowrap">${cafe.id}</td>`;
                        tableHTML += `<td class="px-6 py-4 whitespace-nowrap">${cafe.name}</td>`;
                        tableHTML += `<td class="px-6 py-4 whitespace-nowrap">
                                        <button class="remove-btn px-4 py-2 bg-red-500 text-white rounded" data-cafe-id="${cafe.id}">
                                            Remove
                                        </button>
                                      </td></tr>`;
                    });

                    tableHTML += '</tbody></table>';
                    
                    moderatedCafesDiv.innerHTML = tableHTML;

                    document.querySelectorAll('.remove-btn').forEach(button => {
                        button.addEventListener('click', function() {
                            const cafeId = this.getAttribute('data-cafe-id');
                            const confirmation = confirm('Are you sure you want to remove this cafe?');
                            if (confirmation) {
                                fetch(`/remove_moderator/${userId}/${cafeId}`, {
                                    method: 'DELETE',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-Requested-With': 'XMLHttpRequest'
                                    }
                                })
                                .then(response => response.json())
                                .then(result => {
                                    if (result.success) {
                                        alert('Cafe removed successfully.');
                                        this.closest('tr').remove();
                                    } else {
                                        alert('Failed to remove cafe.');
                                    }
                                })
                                .catch(error => {
                                    console.error('Error removing cafe:', error);
                                });
                            }
                        });
                    });
                })
                .catch(error => {
                    console.error('Error fetching cafes:', error);
                    moderatedCafesDiv.innerHTML = '<p>Error fetching cafes.</p>';
                });
        } else {
            moderatedCafesDiv.innerHTML = '<p>The user doesn\'t moderate any cafes.</p>';
        }
    });
});
