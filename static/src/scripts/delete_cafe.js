document.addEventListener("DOMContentLoaded", function () {
    const deleteBtn = document.getElementById("delete-cafe-btn");
    const modal = document.getElementById("confirmation-modal");
    const confirmDeleteBtn = document.getElementById("confirm-delete");
    const cancelDeleteBtn = document.getElementById("cancel-delete");
    let cafeId = null; // To store cafe ID

    // Show modal and set cafe ID
    deleteBtn.addEventListener("click", function () {
        cafeId = this.getAttribute("data-cafe-id");
        modal.classList.remove("hidden");
    });

    // Confirm delete
    confirmDeleteBtn.addEventListener("click", function () {
        if (cafeId) {
            fetch(`/api/delete_cafe/${cafeId}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
            })
                .then((response) => response.json())
                .then((result) => {
                    modal.classList.add("hidden");
                    if (result.error) {
                        alert(result.error);
                    } else {
                        alert(result.message);
                        window.location.href = "/cafes"; // Redirect or update the page
                    }
                })
                .catch((error) => {
                    console.error("Error:", error);
                    modal.classList.add("hidden");
                });
        }
    });

    // Cancel delete
    cancelDeleteBtn.addEventListener("click", function () {
        modal.classList.add("hidden");
    });
});