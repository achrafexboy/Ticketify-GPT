document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("registerForm");
    const loginForm = document.getElementById("loginForm");

    if (registerForm) {
        setupValidation(registerForm, [
            { id: "email", validator: validateEmail, errorId: "emailError", message: "Enter a valid email (example@mail.com)" },
            { id: "username", validator: (val) => (val.length >= 3 && val.length <= 20), errorId: "usernameError", message: "Username must be at least 3 characters & at most 20 charecters" },
            { id: "poste", validator: (val) => val !== "", errorId: "roleError", message: "Please select a role" },
            { id: "password", validator: validatePassword, errorId: "passwordError", message: "Password must be at least 8 characters, contain an uppercase letter, a number, and a symbol" },
            { id: "confirm_password", validator: (val) => val === document.getElementById("password").value, errorId: "confirmPasswordError", message: "Passwords do not match" }
        ]);
    }

    if (loginForm) {
        setupValidation(loginForm, [
            { id: "email", validator: validateEmail, errorId: "emailError", message: "Enter a valid email (example@mail.com)" },
            { id: "password", validator: (val) => val.length >= 6, errorId: "passwordError", message: "Password must be at least 6 characters" }
        ]);
    }

    function setupValidation(form, fields) {
        fields.forEach(({ id, validator, errorId, message }) => {
            const input = document.getElementById(id);
            const errorElement = document.getElementById(errorId);

            input.addEventListener("blur", function () {
                validateField(input, validator(input.value), errorElement, message);
            });

            input.addEventListener("focus", function () {
                clearError(errorElement, input);
            });
        });

        form.addEventListener("submit", function (e) {
            let hasErrors = false;
            fields.forEach(({ id, validator, errorId, message }) => {
                const input = document.getElementById(id);
                const errorElement = document.getElementById(errorId);
                if (!validateField(input, validator(input.value), errorElement, message)) {
                    hasErrors = true;
                }
            });

            if (hasErrors) {
                e.preventDefault();
            }
        });
    }

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function validatePassword(password) {
        return /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(password);
    }

    function validateField(input, isValid, errorElement, message) {
        if (!isValid) {
            input.classList.add("input-error");
            errorElement.textContent = message;
            errorElement.style.display = "block";
            return false;
        } else {
            clearError(errorElement, input);
            return true;
        }
    }

    function clearError(errorElement, input) {
        input.classList.remove("input-error");
        errorElement.style.display = "none";
    }
});
