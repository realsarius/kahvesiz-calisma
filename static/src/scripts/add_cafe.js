document.addEventListener("DOMContentLoaded", function () {
  console.log("Add Cafe");
  
  const form = document.getElementById("cafe-form");
  const nameInput = document.getElementById("name");
  const mapUrlInput = document.getElementById("map_url");
  const imgUrlInput = document.getElementById("img_url");

  async function isUnique(field, value) {
    try {
      const response = await fetch("/api/cafes");
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Error fetching cafes.");
      }

      const cafes = data.cafes;
      return !cafes.some((cafe) => cafe[field] === value);
    } catch (error) {
      console.error("API error:", error);
      return false; // Treat as not unique in case of an API error
    }
  }

  form.addEventListener("submit", async function (event) {
    let hasErrors = false;

    // Clear previous errors
    document.getElementById("name-error").textContent = "";
    document.getElementById("map-url-error").textContent = "";
    document.getElementById("img-url-error").textContent = "";

    // Validate required fields
    if (!nameInput.value.trim()) {
      document.getElementById("name-error").textContent = "Name is required.";
      hasErrors = true;
    }
    if (!mapUrlInput.value.trim()) {
      document.getElementById("map-url-error").textContent =
        "Map URL is required.";
      hasErrors = true;
    }
    if (!imgUrlInput.value.trim()) {
      document.getElementById("img-url-error").textContent =
        "Image URL is required.";
      hasErrors = true;
    }

    // Check for uniqueness only if no errors yet
    if (!hasErrors) {
      const nameUnique = await isUnique("name", nameInput.value.trim());
      const mapUrlUnique = await isUnique("map_url", mapUrlInput.value.trim());
      const imgUrlUnique = await isUnique("img_url", imgUrlInput.value.trim());

      if (!nameUnique) {
        document.getElementById("name-error").textContent =
          "A cafe with this name already exists.";
        hasErrors = true;
      }
      if (!mapUrlUnique) {
        document.getElementById("map-url-error").textContent =
          "A cafe with this Map URL already exists.";
        hasErrors = true;
      }
      if (!imgUrlUnique) {
        document.getElementById("img-url-error").textContent =
          "A cafe with this Image URL already exists.";
        hasErrors = true;
      }
    }

    // If there are errors, prevent form submission
    if (hasErrors) {
      event.preventDefault();
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  
  tinymce.init({
    selector: "#details",
    skin: (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'oxide-dark' : 'oxide'),
    content_css: (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'),
    plugins:
      "anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount checklist mediaembed casechange export formatpainter pageembed linkchecker a11ychecker tinymcespellchecker permanentpen powerpaste advtable advcode editimage advtemplate ai mentions tinycomments tableofcontents footnotes mergetags autocorrect typography inlinecss markdown",
    toolbar:
      "undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table mergetags | addcomment showcomments | spellcheckdialog a11ycheck typography | align lineheight | checklist numlist bullist indent outdent | emoticons charmap | removeformat",
    tinycomments_mode: "embedded",
    tinycomments_author: "Author name",
    mergetags_list: [
      { value: "First.Name", title: "First Name" },
      { value: "Email", title: "Email" },
    ],
    ai_request: (request, respondWith) =>
      respondWith.string(() =>
        Promise.reject("See docs to implement AI Assistant")
      ),
      
  });
});