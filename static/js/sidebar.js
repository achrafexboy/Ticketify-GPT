document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const toggleButton = document.getElementById("toggleSidebar");
    const submissionList = document.getElementById("submissionList");
    const descriptionInput = document.getElementById("description");

    // Toggle Sidebar
    toggleButton.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed");
    });

    // Attach event listeners to existing items
    document.querySelectorAll(".submission-item").forEach(item => {
        const submissionText = item.querySelector(".submission-text");
        const deleteBtn = item.querySelector(".delete-btn");
        const submissionId = item.dataset.id;

        // ✅ Clicking a submission fills the description input
        submissionText.addEventListener("click", function () {
            descriptionInput.value = submissionText.textContent.replace("...", ""); // Show full text
        });

        // ✅ Delete button event
        deleteBtn.addEventListener("click", function (event) {
            event.stopPropagation(); // Prevent description from being filled
            deleteSubmission(submissionId, item);
        });
    });

    function deleteSubmission(submissionId, itemElement) {
        fetch(`/delete-submission/${submissionId}`, {
            method: "DELETE",
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // ✅ Animate deletion before removing
                itemElement.classList.add("fade-out");
                setTimeout(() => itemElement.remove(), 300);
            } else {
                alert("Error deleting submission: " + data.message);
            }
        })
        .catch(error => console.error("Error deleting submission:", error));
    }
});
