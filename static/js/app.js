"use strict";

document.addEventListener("DOMContentLoaded", () => {

    /* ================================================================
       SIDEBAR TOGGLE
    ================================================================ */

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");

    if (sidebar && sidebarToggle) {

        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
        });

    }


    /* ================================================================
       MEDICINE LIST FILTERS
    ================================================================ */

    const medicineFilterForm = document.getElementById(
        "medicineFilterForm"
    );

    if (medicineFilterForm) {

        const searchInput = document.getElementById(
            "medicineSearch"
        );

        const categorySelect = document.getElementById(
            "medicineCategory"
        );

        const statusSelect = document.getElementById(
            "medicineStatus"
        );

        let searchTimer;


        const submitFilters = () => {
            medicineFilterForm.requestSubmit();
        };


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                () => {

                    clearTimeout(searchTimer);

                    searchTimer = setTimeout(
                        submitFilters,
                        200
                    );

                }
            );

        }


        if (categorySelect) {

            categorySelect.addEventListener(
                "change",
                submitFilters
            );

        }


        if (statusSelect) {

            statusSelect.addEventListener(
                "change",
                submitFilters
            );

        }

    }


    /* ================================================================
       INVENTORY LIST FILTERS
    ================================================================ */

    const inventoryFilterForm = document.getElementById(
        "inventoryFilterForm"
    );

    if (inventoryFilterForm) {

        const searchInput = document.getElementById(
            "inventorySearch"
        );

        const statusSelect = document.getElementById(
            "inventoryStatus"
        );

        let searchTimer;


        const submitFilters = () => {
            inventoryFilterForm.requestSubmit();
        };


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                () => {

                    clearTimeout(searchTimer);

                    searchTimer = setTimeout(
                        submitFilters,
                        200
                    );

                }
            );

        }


        if (statusSelect) {

            statusSelect.addEventListener(
                "change",
                submitFilters
            );

        }

    }


    /* ================================================================
       INVENTORY — EXISTING MEDICINE SEARCH
       Used on inventory/form.html
    ================================================================ */

    const medicineSearchInput = document.getElementById(
        "medicineSearchInput"
    );

    const medicineSearchResults = document.getElementById(
        "medicineSearchResults"
    );

    const medicineIdInput = document.getElementById(
        "id_medicine"
    );

    const selectedMedicine = document.getElementById(
        "selectedMedicine"
    );

    const selectedMedicineName = document.getElementById(
        "selectedMedicineName"
    );

    const selectedMedicineMeta = document.getElementById(
        "selectedMedicineMeta"
    );

    const selectedMedicineIdentifiers = document.getElementById(
        "selectedMedicineIdentifiers"
    );

    const removeSelectedMedicine = document.getElementById(
        "removeSelectedMedicine"
    );

    const clearMedicineSearch = document.getElementById(
        "clearMedicineSearch"
    );


    if (
        medicineSearchInput
        && medicineSearchResults
        && medicineIdInput
    ) {

        let searchTimer = null;
        let currentController = null;


        /* ============================================================
           HELPERS
        ============================================================ */

        const escapeHtml = (value) => {

            const div = document.createElement("div");

            div.textContent = value ?? "";

            return div.innerHTML;
        };


        const hideSearchResults = () => {

            medicineSearchResults.innerHTML = "";

            medicineSearchResults.style.display = "none";
        };


        const showSearchMessage = (message) => {

            medicineSearchResults.innerHTML = "";

            const messageElement = document.createElement("div");

            messageElement.className =
                "p-3 text-muted small";

            messageElement.textContent = message;

            medicineSearchResults.appendChild(
                messageElement
            );

            medicineSearchResults.style.display = "block";
        };


        const clearMedicineSelection = () => {

            medicineIdInput.value = "";

            if (selectedMedicine) {
                selectedMedicine.style.display = "none";
            }

            if (selectedMedicineName) {
                selectedMedicineName.textContent = "";
            }

            if (selectedMedicineMeta) {
                selectedMedicineMeta.textContent = "";
            }

            if (selectedMedicineIdentifiers) {
                selectedMedicineIdentifiers.textContent = "";
            }

            medicineSearchInput.value = "";

            medicineSearchInput.disabled = false;

            if (clearMedicineSearch) {
                clearMedicineSearch.style.display = "none";
            }

            hideSearchResults();
        };


        /* ============================================================
           SELECT MEDICINE
        ============================================================ */

        const selectMedicine = (medicine) => {

            medicineIdInput.value = medicine.id;


            if (selectedMedicineName) {

                selectedMedicineName.textContent =
                    `${medicine.name}${medicine.strength
                        ? ` ${medicine.strength}`
                        : ""
                    }`;

            }


            if (selectedMedicineMeta) {

                const meta = [];

                if (medicine.generic_name) {
                    meta.push(medicine.generic_name);
                }

                if (medicine.dosage_form) {
                    meta.push(medicine.dosage_form);
                }

                if (medicine.category) {
                    meta.push(medicine.category);
                }

                selectedMedicineMeta.textContent =
                    meta.join(" • ");

            }


            if (selectedMedicineIdentifiers) {

                const identifiers = [];

                if (medicine.sku) {
                    identifiers.push(
                        `SKU: ${medicine.sku}`
                    );
                }

                if (medicine.barcode) {
                    identifiers.push(
                        `Barcode: ${medicine.barcode}`
                    );
                }

                selectedMedicineIdentifiers.textContent =
                    identifiers.join(" • ");

            }


            if (selectedMedicine) {
                selectedMedicine.style.display = "block";
            }


            medicineSearchInput.value =
                `${medicine.name}${medicine.strength
                    ? ` ${medicine.strength}`
                    : ""
                }`;


            medicineSearchInput.disabled = true;


            if (clearMedicineSearch) {
                clearMedicineSearch.style.display = "block";
            }


            hideSearchResults();
        };


        /* ============================================================
           RENDER SEARCH RESULTS
        ============================================================ */

        const renderMedicineResults = (results) => {

            medicineSearchResults.innerHTML = "";


            if (!results.length) {

                showSearchMessage(
                    "No matching medicines found."
                );

                return;
            }


            results.forEach((medicine) => {

                const resultButton =
                    document.createElement("button");


                resultButton.type = "button";

                resultButton.className =
                    "w-100 border-0 bg-white text-start p-3";


                resultButton.style.borderBottom =
                    "1px solid #e7eaee";


                const medicineTitle =
                    document.createElement("div");

                medicineTitle.className =
                    "fw-semibold";


                medicineTitle.textContent =
                    `${medicine.name}${medicine.strength
                        ? ` ${medicine.strength}`
                        : ""
                    }`;


                const medicineMeta =
                    document.createElement("div");

                medicineMeta.className =
                    "small text-muted mt-1";


                const meta = [];

                if (medicine.generic_name) {
                    meta.push(medicine.generic_name);
                } else {
                    meta.push("Generic name not specified");
                }

                if (medicine.dosage_form) {
                    meta.push(medicine.dosage_form);
                }

                if (medicine.category) {
                    meta.push(medicine.category);
                }

                medicineMeta.textContent =
                    meta.join(" • ");


                const identifiers = [];


                if (medicine.sku) {
                    identifiers.push(
                        `SKU: ${medicine.sku}`
                    );
                }

                if (medicine.barcode) {
                    identifiers.push(
                        `Barcode: ${medicine.barcode}`
                    );
                }


                resultButton.appendChild(
                    medicineTitle
                );

                resultButton.appendChild(
                    medicineMeta
                );


                if (identifiers.length) {

                    const identifierElement =
                        document.createElement("div");

                    identifierElement.className =
                        "small text-muted mt-1";

                    identifierElement.textContent =
                        identifiers.join(" • ");

                    resultButton.appendChild(
                        identifierElement
                    );

                }


                resultButton.addEventListener(
                    "mouseenter",
                    () => {
                        resultButton.style.backgroundColor =
                            "#f8fafc";
                    }
                );


                resultButton.addEventListener(
                    "mouseleave",
                    () => {
                        resultButton.style.backgroundColor =
                            "#ffffff";
                    }
                );


                resultButton.addEventListener(
                    "click",
                    () => {
                        selectMedicine(medicine);
                    }
                );


                medicineSearchResults.appendChild(
                    resultButton
                );

            });


            medicineSearchResults.style.display =
                "block";
        };


        /* ============================================================
           AJAX SEARCH
        ============================================================ */

        const searchMedicines = async (query) => {

            if (currentController) {
                currentController.abort();
            }


            if (!query) {

                hideSearchResults();

                return;
            }


            currentController =
                new AbortController();


            showSearchMessage(
                "Searching medicines..."
            );


            try {

                const searchUrl =
                    `/inventory/search-medicines/?q=${encodeURIComponent(query)}`;


                const response = await fetch(
                    searchUrl,
                    {
                        method: "GET",
                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest",
                        },
                        credentials: "same-origin",
                        signal: currentController.signal,
                    }
                );


                if (!response.ok) {
                    throw new Error(
                        "Medicine search failed."
                    );
                }


                const data =
                    await response.json();


                renderMedicineResults(
                    data.results || []
                );

            } catch (error) {

                if (error.name === "AbortError") {
                    return;
                }


                showSearchMessage(
                    "Unable to search medicines. Please try again."
                );
            }
        };


        /* ============================================================
           SEARCH INPUT
        ============================================================ */

        medicineSearchInput.addEventListener(
            "input",
            () => {

                const query =
                    medicineSearchInput.value.trim();


                clearTimeout(searchTimer);


                if (clearMedicineSearch) {

                    clearMedicineSearch.style.display =
                        query ? "block" : "none";

                }


                searchTimer = setTimeout(
                    () => {
                        searchMedicines(query);
                    },
                    200
                );

            }
        );


        /* ============================================================
           CLEAR / CHANGE MEDICINE
        ============================================================ */

        if (removeSelectedMedicine) {

            removeSelectedMedicine.addEventListener(
                "click",
                () => {

                    clearMedicineSelection();

                    medicineSearchInput.focus();

                }
            );

        }


        if (clearMedicineSearch) {

            clearMedicineSearch.addEventListener(
                "click",
                () => {

                    clearMedicineSelection();

                    medicineSearchInput.focus();

                }
            );

        }


        /* ============================================================
           CLOSE SEARCH RESULTS ON OUTSIDE CLICK
        ============================================================ */

        document.addEventListener(
            "click",
            (event) => {

                if (
                    !medicineSearchResults.contains(
                        event.target
                    )
                    && !medicineSearchInput.contains(
                        event.target
                    )
                    && !(
                        clearMedicineSearch
                        && clearMedicineSearch.contains(
                            event.target
                        )
                    )
                ) {

                    hideSearchResults();

                }

            }
        );

    }

});