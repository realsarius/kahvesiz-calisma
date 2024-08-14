document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');
    const resultsDiv = document.getElementById('search-results');
    const normalResultsDiv = document.getElementById('cafes-search-results');
    const paginationDiv = document.getElementById('cafes-pagination');
    let timeoutId;

    searchInput.addEventListener('input', function() {
        const query = searchInput.value.trim();

        // Clear previous timeout if input changes before 500ms
        clearTimeout(timeoutId);

        // Hide normal results when there is a search query
        if (query.length > 2) {
            normalResultsDiv.style.display = 'none';
            paginationDiv.style.display = 'none';

            timeoutId = setTimeout(() => {
                fetch(`/api/cafes?search=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.cafes) {
                            renderResults(data.cafes);
                        } else {
                            resultsDiv.innerHTML = '<p>Hiçbir kafe bulunamadı.</p>';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching cafes:', error);
                        resultsDiv.innerHTML = '<p>An error occurred. Please try again later.</p>';
                    });
            }, 500);
        } else {
            // Show normal results when search input is empty
            normalResultsDiv.style.display = 'grid';
            paginationDiv.style.display = 'flex';
            resultsDiv.innerHTML = ''; // Clear search results
        }
    });

    function renderResults(cafes) {
        resultsDiv.innerHTML = cafes.map(cafe => `
            <div class="bg-white/20 border border-gray-200 rounded-lg shadow dark:bg-zinc-900/20 dark:border-zinc-800 overflow-hidden backdrop-blur-sm">
                <a href="/cafes/${cafe.id}">
                    <img
                        class="rounded-t-lg w-full h-44 object-cover hover:scale-105 transition-transform duration-200"
                        src="${cafe.img_url}"
                        alt="${cafe.name}"
                    />
                </a>
                <div class="p-5">
                    <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white drop-shadow">${cafe.name}</h5>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Nerede:</strong> ${cafe.location}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Priz:</strong> ${cafe.has_sockets ? 'Evet' : 'Hayır'}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Tuvalet:</strong> ${cafe.has_toilet ? 'Evet' : 'Hayır'}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Wifi:</strong> ${cafe.has_wifi ? 'Evet' : 'Hayır'}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Çağrı alıyor mu:</strong> ${cafe.can_take_calls ? 'Evet' : 'Hayır'}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Koltuklar:</strong> ${cafe.seats}</p>
                    <p class="mb-3 font-normal dark:text-zinc-200 text-zinc-700"><strong>Kahve fiyatı:</strong> ${cafe.coffee_price}</p>
                    <div class="flex align-middle gap-4">
                        <a href="/cafes/${cafe.id}" class="inline-flex items-center px-3 py-2 rounded transition-colors duration-200 bg-lavender dark:text-zinc-950 dark:hover:bg-violet-200">Daha Fazla</a>
                        <a href="${cafe.map_url}" class="inline-flex items-center py-2 text-center transition-colors duration-200 drop-shadow-md hover:text-dark-purple dark:hover:text-lavender" target="_blank">Haritada Gör
                            <svg class="rtl:rotate-180 w-3.5 h-3.5 ms-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 10">
                                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 5h12m0 0L9 1m4 4L9 9"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
        `).join('');
    }
});
