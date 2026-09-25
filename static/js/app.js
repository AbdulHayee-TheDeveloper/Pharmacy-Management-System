"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // Sidebar toggle
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
        });
    }

    // Medicine filters
    const medicineFilterForm = document.getElementById("medicineFilterForm");

    if (medicineFilterForm) {
        const searchInput = document.getElementById("medicineSearch");
        const categorySelect = document.getElementById("medicineCategory");
        const statusSelect = document.getElementById("medicineStatus");

        let searchTimer;

        const submitFilters = () => {
            medicineFilterForm.requestSubmit();
        };

        // Search: apply after 200ms
        if (searchInput) {
            searchInput.addEventListener("input", () => {
                clearTimeout(searchTimer);

                searchTimer = setTimeout(() => {
                    submitFilters();
                }, 200);
            });
        }

        // Category: apply immediately
        if (categorySelect) {
            categorySelect.addEventListener("change", submitFilters);
        }

        // Status: apply immediately
        if (statusSelect) {
            statusSelect.addEventListener("change", submitFilters);
        }
    }
});

