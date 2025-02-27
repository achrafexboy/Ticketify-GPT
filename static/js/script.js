document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('assistantForm');
    const photosInput = document.getElementById('photos');
    const fileUploadContainer = document.getElementById('file-upload-container');
    const previewDiv = document.getElementById('preview');
    const responseContainer = document.getElementById('responseContainer');
    const editableResponseElement = document.getElementById('editableResponse');
    const submitBtn = document.getElementById('submitBtn');
    const submitSpinner = document.getElementById('submitSpinner');
    const sendToSlackBtn = document.getElementById('sendToSlackBtn');
    const slackSpinner = document.getElementById('slackSpinner');

    // Handle drag and drop file upload
    fileUploadContainer.addEventListener('click', function() {
        photosInput.click();
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        fileUploadContainer.style.borderColor = '#4f46e5';
        fileUploadContainer.style.backgroundColor = '#f0f9ff';
    }

    function unhighlight() {
        fileUploadContainer.style.borderColor = '#d1d5db';
        fileUploadContainer.style.backgroundColor = 'transparent';
    }

    fileUploadContainer.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        photosInput.files = files;
        handleFiles(files);
    }

    // Handle file selection and preview
    photosInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        previewDiv.innerHTML = '';
        
        if (files && files.length > 0) {
            Array.from(files).forEach((file, index) => {
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const container = document.createElement('div');
                        container.classList.add('preview-image-container');
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.classList.add('preview-image');
                        container.appendChild(img);
                        
                        const removeBtn = document.createElement('button');
                        removeBtn.innerHTML = '×';
                        removeBtn.classList.add('remove-image');
                        removeBtn.dataset.index = index;
                        removeBtn.addEventListener('click', removeImage);
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

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show spinner, disable button
        submitBtn.disabled = true;
        submitSpinner.classList.remove('d-none');
        
        const formData = new FormData(form);
        
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate the editable textarea with the response
                editableResponseElement.value = data.assistant_response;
                
                // Show the response container with animation
                responseContainer.classList.remove('d-none');
                
                // Scroll to response
                responseContainer.scrollIntoView({ behavior: 'smooth' });
            } else {
                showAlert('Error: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while processing your request.', 'danger');
        })
        .finally(() => {
            // Hide spinner, enable button
            submitBtn.disabled = false;
            submitSpinner.classList.add('d-none');
        });
    });

    // Handle sending to Slack
    sendToSlackBtn.addEventListener('click', function() {
        // Get the edited response text
        const editedResponse = editableResponseElement.value;
        
        if (!editedResponse.trim()) {
            showAlert('The message cannot be empty.', 'warning');
            return;
        }
        
        // Show spinner, disable button
        sendToSlackBtn.disabled = true;
        slackSpinner.classList.remove('d-none');
        
        fetch('/send-to-slack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                edited_response: editedResponse
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Message sent to Slack successfully!', 'success');
                // Hide the response container
                responseContainer.classList.add('d-none');
                // Reset the form
                form.reset();
                previewDiv.innerHTML = '';
            } else {
                showAlert('Error: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while sending to Slack.', 'danger');
        })
        .finally(() => {
            // Hide spinner, enable button
            sendToSlackBtn.disabled = false;
            slackSpinner.classList.add('d-none');
        });
    });

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const cardBody = document.querySelector('.card-body');
        cardBody.insertBefore(alertDiv, cardBody.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
});