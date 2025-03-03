document.addEventListener("DOMContentLoaded", function () {
    // Check for section parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const sectionParam = urlParams.get('section');
    
    // Tab switching functionality
    const sidebarItems = document.querySelectorAll(".sidebar-item");
    const sections = document.querySelectorAll(".account-section");
    
    // If section parameter exists, activate that section
    if (sectionParam) {
        activateSection(sectionParam);
    }

    // Function to activate a specific section
    function activateSection(sectionId) {
        // Update active state for sidebar items
        sidebarItems.forEach((el) => {
            el.classList.remove("active");
            if (el.getAttribute("data-section") === sectionId) {
                el.classList.add("active");
            }
        });

        // Show the corresponding section
        sections.forEach((section) => {
            section.classList.remove("active");
            if (section.id === sectionId) {
                section.classList.add("active");
            }
        });
        
        // Update URL without reloading the page
        const url = new URL(window.location);
        url.searchParams.set('section', sectionId);
        window.history.pushState({}, '', url);
    }

    // Add click event listeners to sidebar items
    sidebarItems.forEach((item) => {
        item.addEventListener("click", function () {
            const sectionId = this.getAttribute("data-section");
            activateSection(sectionId);
        });
    });

    // Handle back/forward browser navigation
    window.addEventListener('popstate', function() {
        const currentParams = new URLSearchParams(window.location.search);
        const currentSection = currentParams.get('section') || 'profile';
        activateSection(currentSection);
    });

    // Rest of your existing JavaScript code...
    // Form validation
    const profileForm = document.querySelector("#profile form");
    if (profileForm) {
        profileForm.addEventListener("submit", function(e) {
            const username = document.getElementById("username").value.trim();
            if (username.length < 3) {
                e.preventDefault();
                showError(document.getElementById("username"), "Username must be at least 3 characters");
            }
            else if(username.length > 21) {
                e.preventDefault();
                showError(document.getElementById("username"), "Username must be at most 20 characters");
            }
        });
    }

    // Password strength meter
    const newPasswordInput = document.getElementById("new_password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const passwordStrengthMeter = document.getElementById("password-strength");
    
    if (newPasswordInput && passwordStrengthMeter) {
        newPasswordInput.addEventListener("input", function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            updatePasswordStrengthMeter(strength);
        });
    }
    
    // Password confirmation validation
    const passwordForm = document.querySelector("#password form");
    if (passwordForm) {
        passwordForm.addEventListener("submit", function(e) {
            const newPassword = newPasswordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            if (newPassword !== confirmPassword) {
                e.preventDefault();
                showError(confirmPasswordInput, "Passwords do not match");
            }
            
            if (checkPasswordStrength(newPassword).score < 2) {
                e.preventDefault();
                showError(newPasswordInput, "Password is too weak");
            }
        });
    }

    // Helper functions
    function showError(inputElement, message) {
        // Remove any existing error messages
        const existingError = inputElement.parentElement.querySelector(".error-message");
        if (existingError) {
            existingError.remove();
        }
        
        // Create and add error message
        const errorMessage = document.createElement("div");
        errorMessage.className = "error-message";
        errorMessage.textContent = message;
        inputElement.parentElement.appendChild(errorMessage);
        
        // Highlight the input
        inputElement.classList.add("error");
        
        // Remove error styling after user starts typing again
        inputElement.addEventListener("input", function() {
            inputElement.classList.remove("error");
            const errorMsg = inputElement.parentElement.querySelector(".error-message");
            if (errorMsg) {
                errorMsg.remove();
            }
        }, { once: true });
    }
    
    function checkPasswordStrength(password) {
        // Basic password strength check
        let score = 0;
        let feedback = "";
        
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[a-z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^A-Za-z0-9]/.test(password)) score++;
        
        if (score < 2) {
            feedback = "Weak";
        } else if (score < 4) {
            feedback = "Medium";
        } else {
            feedback = "Strong";
        }
        
        return { score, feedback };
    }
    
    function updatePasswordStrengthMeter(strength) {
        if (!passwordStrengthMeter) return;
        
        // Remove previous classes
        passwordStrengthMeter.className = "password-strength-meter";
        
        // Add appropriate class based on strength
        switch(strength.feedback) {
            case "Weak":
                passwordStrengthMeter.classList.add("weak");
                break;
            case "Medium":
                passwordStrengthMeter.classList.add("medium");
                break;
            case "Strong":
                passwordStrengthMeter.classList.add("strong");
                break;
        }
        
        // Update text content
        // passwordStrengthMeter.textContent = strength.feedback;
        passwordStrengthMeter.style.display = "block";
    }

    // Notification :
    const notificationCheckbox = document.querySelector("input[name='email_notifications']");
    
    if (notificationCheckbox) {
        notificationCheckbox.addEventListener("change", function () {
            fetch("/edit-notification", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email_notifications: this.checked }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert("Notification preferences updated!", "success");
                } else {
                    showAlert("Error updating preferences", "danger");
                }
            })
            .catch(error => console.error("Error updating notifications:", error));
        });
    }
});