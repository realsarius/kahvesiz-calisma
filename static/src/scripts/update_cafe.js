document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("update-cafe-form");
    const cafeId = document.getElementById("cafe-id").value;

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission

        // Ensure TinyMCE content is synced to textarea
        tinymce.get("details").save();

        const formData = new FormData(form);
        const data = {
            name: formData.get("name"),
            map_url: formData.get("map_url"),
            img_url: formData.get("img_url"),
            location: formData.get("location"),
            has_sockets: formData.get("has_sockets") === "on",
            has_toilet: formData.get("has_toilet") === "on",
            has_wifi: formData.get("has_wifi") === "on",
            can_take_calls: formData.get("can_take_calls") === "on",
            seats: formData.get("seats"),
            coffee_price: formData.get("coffee_price"),
            details: formData.get("details"),
        };

        fetch(`/api/update_cafe/${cafeId}`, {
            method: "PUT", // Use PUT method as defined in your route
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": formData.get("csrf_token"), // Include CSRF token if needed
            },
        })
            .then((response) => response.json())
            .then((result) => {
                if (result.error) {
                    // Display errors
                    alert(result.error);
                } else {
                    // Success message
                    alert(result.message);
                    window.location.href = `/cafes/${cafeId}`; // Redirect or update the page
                }
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const cafeId = document.getElementById("cafe-id").value;

    // Initialize TinyMCE
    tinymce.init({
        selector: "#details",
        plugins:
            "anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount checklist mediaembed casechange export formatpainter pageembed linkchecker a11ychecker tinymcespellchecker permanentpen powerpaste advtable advcode editimage advtemplate ai mentions tinycomments tableofcontents footnotes mergetags autocorrect typography inlinecss markdown",
        skin: window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "oxide-dark"
            : "oxide",
        content_css: window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "default",
        toolbar:
            "undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table mergetags | addcomment showcomments | spellcheckdialog a11ycheck typography | align lineheight | checklist numlist bullist indent outdent | emoticons charmap | removeformat",
        tinycomments_mode: "embedded",
        tinycomments_author: "Author name",
        mergetags_list: [
            {value: "First.Name", title: "First Name"},
            {value: "Email", title: "Email"},
        ],
        ai_request: (request, respondWith) =>
            respondWith.string(() =>
                Promise.reject("See docs to implement AI Assistant")
            ),
        setup: (editor) => {
            editor.on("init", () => {
                // Fetch cafe details
                fetch(`/api/cafes/${cafeId}`)
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.details) {
                            editor.setContent(data.details);
                        } else {
                            console.error("No details found");
                        }
                    })
                    .catch((error) =>
                        console.error("Error fetching cafe details:", error)
                    );
            });
        },
    });
});
