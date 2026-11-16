/**
 * Shared JavaScript utilities for ReadWise
 * Lightweight and performance-optimized - O(1) operations where possible
 */

(function() {
    'use strict';

    /**
     * Remove an element from the DOM
     * Time: O(1), Space: O(1)
     */
    function removeElement(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }

    /**
     * Add event listener with error handling
     * Time: O(1), Space: O(1)
     */
    function addListener(selector, event, callback) {
        try {
            const element = document.querySelector(selector);
            if (element) {
                element.addEventListener(event, callback);
            }
        } catch (e) {
            console.warn(`Failed to add listener for ${selector}:`, e);
        }
    }

    /**
     * Add class to element
     * Time: O(1), Space: O(1)
     */
    function addClass(element, className) {
        if (element && element.classList) {
            element.classList.add(className);
        }
    }

    /**
     * Remove class from element
     * Time: O(1), Space: O(1)
     */
    function removeClass(element, className) {
        if (element && element.classList) {
            element.classList.remove(className);
        }
    }

    /**
     * Toggle class on element
     * Time: O(1), Space: O(1)
     */
    function toggleClass(element, className) {
        if (element && element.classList) {
            element.classList.toggle(className);
        }
    }

    /**
     * Add error styling to form field
     * Time: O(1), Space: O(1)
     */
    function markFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            addClass(field, 'error');
            field.setAttribute('aria-invalid', 'true');
        }
    }

    /**
     * Remove error styling from form field
     * Time: O(1), Space: O(1)
     */
    function clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            removeClass(field, 'error');
            field.setAttribute('aria-invalid', 'false');
        }
    }

    /**
     * Validate email format
     * Time: O(n) where n = email length, Space: O(1)
     */
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate password strength
     * Time: O(n) where n = password length, Space: O(1)
     */
    function isValidPassword(password) {
        return password && password.length >= 8;
    }

    /**
     * Initialize form validation
     * Time: O(n) where n = number of fields, Space: O(1)
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('form[data-validate="true"]');
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                const fields = form.querySelectorAll('[data-validate]');
                let isValid = true;

                fields.forEach(function(field) {
                    const value = field.value.trim();
                    const type = field.getAttribute('data-validate');

                    // Clear previous error
                    clearFieldError(field.id);

                    // Validate based on type - O(1) per field
                    if (type === 'email') {
                        if (!isValidEmail(value)) {
                            markFieldError(field.id);
                            isValid = false;
                        }
                    } else if (type === 'password') {
                        if (!isValidPassword(value)) {
                            markFieldError(field.id);
                            isValid = false;
                        }
                    } else if (type === 'required') {
                        if (!value) {
                            markFieldError(field.id);
                            isValid = false;
                        }
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                }
            });
        });
    }

    /**
     * Initialize DOM when ready
     */
    document.addEventListener('DOMContentLoaded', function() {
        initFormValidation();
    });

    // Export functions for global use
    window.ReadWiseUI = {
        removeElement: removeElement,
        addListener: addListener,
        addClass: addClass,
        removeClass: removeClass,
        toggleClass: toggleClass,
        markFieldError: markFieldError,
        clearFieldError: clearFieldError,
        isValidEmail: isValidEmail,
        isValidPassword: isValidPassword
    };
})();
