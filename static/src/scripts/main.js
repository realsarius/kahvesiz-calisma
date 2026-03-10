document.addEventListener("DOMContentLoaded", function () {
    const dropdownButton = document.getElementById("dropdownAvatarNameButton");
    const dropdownMenu = document.getElementById("dropdownAvatarName");

    if (dropdownButton && dropdownMenu) {
        dropdownButton.addEventListener("click", function () {
            dropdownMenu.classList.toggle("hidden");
        });

        // Optional: Close the dropdown if clicked outside
        document.addEventListener("click", function (event) {
            if (
                !dropdownButton.contains(event.target) &&
                !dropdownMenu.contains(event.target)
            ) {
                dropdownMenu.classList.add("hidden");
            }
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const toggles = document.querySelectorAll("[data-dial-toggle]");
    const plusSvg = document.getElementById("plus-svg");

    toggles.forEach((toggle) => {
        toggle.addEventListener("click", function () {
            const targetId = this.getAttribute("data-dial-toggle");
            const target = document.getElementById(targetId);
            if (target) {
                target.classList.toggle("flex");
                if (plusSvg) {
                    plusSvg.classList.toggle("rotate-45");
                }
                target.classList.toggle("hidden");
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const toast = document.getElementById("toast-message-cta");
    const toastLink = document.getElementById("show-add-cafe-toast");
    if (!toast || !toastLink) {
        return;
    }

    const closeButton = toast.querySelector('[data-dismiss-target="#toast-message-cta"]');

    toastLink.addEventListener("click", function (event) {
        event.preventDefault();
        toast.classList.remove("hidden");

        setTimeout(function () {
            toast.classList.add("hidden");
        }, 10000);
    });

    if (closeButton) {
        closeButton.addEventListener("click", function () {
            toast.classList.add("hidden");
        });
    }
});
