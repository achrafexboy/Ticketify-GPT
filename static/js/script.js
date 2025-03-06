document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("assistantForm");
    const photosInput = document.getElementById("photos");
    const fileUploadContainer = document.getElementById("file-upload-container");
    const previewDiv = document.getElementById("preview");
    const submitBtn = document.getElementById("submitBtn");
    const submitSpinner = document.getElementById("submitSpinner");
    const successMessage = document.getElementById("successMessage");

    // 🔹 File Upload Handling
    fileUploadContainer.addEventListener("click", function () {
        photosInput.click();
    });

    photosInput.addEventListener("change", function () {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        previewDiv.innerHTML = ""; // Clear previous previews

        if (files && files.length > 0) {
            Array.from(files).forEach((file, index) => {
                if (file.type.match("image.*")) {
                    const reader = new FileReader();

                    reader.onload = function (e) {
                        const container = document.createElement("div");
                        container.classList.add("preview-image-container");

                        const img = document.createElement("img");
                        img.src = e.target.result;
                        img.classList.add("preview-image");
                        container.appendChild(img);

                        // Remove Button
                        const removeBtn = document.createElement("button");
                        removeBtn.innerHTML = "×";
                        removeBtn.classList.add("remove-image");
                        removeBtn.dataset.index = index;
                        removeBtn.addEventListener("click", removeImage);
                        container.appendChild(removeBtn);

                        previewDiv.appendChild(container);
                    };

                    reader.readAsDataURL(file);
                }
            });
        }
    }

    function removeImage(e) {
        e.stopPropagation();
        const index = parseInt(e.target.dataset.index);
        const dt = new DataTransfer();
        const files = photosInput.files;

        for (let i = 0; i < files.length; i++) {
            if (i !== index) {
                dt.items.add(files[i]);
            }
        }

        photosInput.files = dt.files;
        handleFiles(photosInput.files);
    }

    // 🔹 Form Submission Handling
    form.addEventListener("submit", function (e) {
        e.preventDefault();

        // Validate fields
        const projectName = document.getElementById("project_name").value.trim();
        const description = document.getElementById("description").value.trim();
        const priority = document.getElementById("priority").value;

        if (!projectName || !description || !priority) {
            alert("Please fill in all required fields.");
            return;
        }

        // Show loading spinner
        submitBtn.disabled = true;
        submitSpinner.classList.remove("d-none");

        const formData = new FormData(form);

        fetch("/", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                successMessage.classList.remove("d-none"); // Show success message
                form.reset(); // Reset the form
                previewDiv.innerHTML = ""; // Clear image previews

                // Auto-dismiss the success message after 5 seconds
                setTimeout(() => {
                    successMessage.classList.add("d-none");
                }, 5000);
            } else {
                alert("Error processing request. Please try again.");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitSpinner.classList.add("d-none");
        });
    });
});
