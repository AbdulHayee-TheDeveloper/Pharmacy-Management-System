"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // ============================================================
    // GLOBAL HELPERS
    // ============================================================

    const escapeHtml = (value) => {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    };

    const getCookie = (name) => {
        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (const cookie of cookies) {
            const trimmedCookie = cookie.trim();

            if (trimmedCookie.startsWith(`${name}=`)) {
                return decodeURIComponent(
                    trimmedCookie.substring(name.length + 1)
                );
            }
        }

        return null;
    };

    const toMoney = (value) => {
        const number = Number(value || 0);

        if (!Number.isFinite(number)) {
            return 0;
        }

        return Math.round(
            (number + Number.EPSILON) * 100
        ) / 100;
    };

    const formatMoney = (value) => {
        return toMoney(value).toFixed(2);
    };

    // ============================================================
    // SIDEBAR
    // ============================================================

    const sidebar = document.getElementById("sidebar");

    const sidebarToggle = document.getElementById(
        "sidebarToggle"
    );

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
        });
    }

    // ============================================================
    // MEDICINE LIST FILTERS
    // ============================================================

    const medicineFilterForm =
        document.getElementById(
            "medicineFilterForm"
        );

    if (medicineFilterForm) {
        const medicineSearch =
            document.getElementById(
                "medicineSearch"
            );

        const medicineCategory =
            document.getElementById(
                "medicineCategory"
            );

        const medicineStatus =
            document.getElementById(
                "medicineStatus"
            );

        let searchTimer = null;

        const submitFilters = () => {
            medicineFilterForm.requestSubmit();
        };

        if (medicineSearch) {
            medicineSearch.addEventListener(
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

        if (medicineCategory) {
            medicineCategory.addEventListener(
                "change",
                submitFilters
            );
        }

        if (medicineStatus) {
            medicineStatus.addEventListener(
                "change",
                submitFilters
            );
        }
    }

    // ============================================================
    // INVENTORY LIST FILTERS
    // ============================================================

    const inventoryFilterForm =
        document.getElementById(
            "inventoryFilterForm"
        );

    if (inventoryFilterForm) {
        const inventorySearch =
            document.getElementById(
                "inventorySearch"
            );

        const inventoryStatus =
            document.getElementById(
                "inventoryStatus"
            );

        let searchTimer = null;

        const submitInventoryFilters = () => {
            inventoryFilterForm.requestSubmit();
        };

        if (inventorySearch) {
            inventorySearch.addEventListener(
                "input",
                () => {
                    clearTimeout(searchTimer);

                    searchTimer = setTimeout(
                        submitInventoryFilters,
                        200
                    );
                }
            );
        }

        if (inventoryStatus) {
            inventoryStatus.addEventListener(
                "change",
                submitInventoryFilters
            );
        }
    }

    // ============================================================
    // INVENTORY FORM — SEARCH FIRST WORKFLOW
    // ============================================================

    const inventoryEntryTypeInput =
        document.getElementById("id_entry_type");

    const newMedicineSection =
        document.getElementById("newMedicineSection");

    const medicineSearchInput =
        document.getElementById("medicineSearchInput");

    const medicineSearchResults =
        document.getElementById("medicineSearchResults");

    const medicineIdInput =
        document.getElementById("id_medicine");

    const selectedMedicine =
        document.getElementById("selectedMedicine");

    const selectedMedicineName =
        document.getElementById("selectedMedicineName");

    const selectedMedicineMeta =
        document.getElementById("selectedMedicineMeta");

    const selectedMedicineIdentifiers =
        document.getElementById(
            "selectedMedicineIdentifiers"
        );

    const selectedMedicinePackInfo =
        document.getElementById(
            "selectedMedicinePackInfo"
        );

    const removeSelectedMedicine =
        document.getElementById(
            "removeSelectedMedicine"
        );

    const clearMedicineSearch =
        document.getElementById(
            "clearMedicineSearch"
        );

    const medicineNotFound =
        document.getElementById(
            "medicineNotFound"
        );

    const createNewMedicineButton =
        document.getElementById(
            "createNewMedicineButton"
        );

    const cancelNewMedicineButton =
        document.getElementById(
            "cancelNewMedicineButton"
        );

    const inventoryPackSizeInput =
        document.getElementById(
            "id_pack_size"
        );

    const inventoryUnitInput =
        document.getElementById(
            "id_unit"
        );

    const inventoryLooseSaleInput =
        document.getElementById(
            "id_allow_loose_sale"
        );

    const inventoryQuantityInput =
        document.getElementById(
            "id_quantity"
        );

    const inventorySellingPriceInput =
        document.getElementById(
            "id_selling_price"
        );

    const stockConversionPreview =
        document.getElementById(
            "stockConversionPreview"
        );

    const loosePricePreview =
        document.getElementById(
            "loosePricePreview"
        );

    let selectedInventoryMedicine = null;


    // ============================================================
    // INVENTORY HELPERS
    // ============================================================

    const setInventoryMode = (mode) => {

        if (inventoryEntryTypeInput) {
            inventoryEntryTypeInput.value =
                mode || "";
        }

    };


    const hideNewMedicineSection = () => {

        if (newMedicineSection) {
            newMedicineSection.style.display =
                "none";
        }

    };


    const showNewMedicineSection = () => {

        setInventoryMode("new");

        if (medicineIdInput) {
            medicineIdInput.value = "";
        }

        selectedInventoryMedicine = null;

        if (selectedMedicine) {
            selectedMedicine.style.display =
                "none";
        }

        if (medicineNotFound) {
            medicineNotFound.style.display =
                "none";
        }

        if (medicineSearchResults) {
            medicineSearchResults.style.display =
                "none";
        }

        if (newMedicineSection) {
            newMedicineSection.style.display =
                "block";

            newMedicineSection.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }

        updateInventoryPreview();

    };


    const getInventoryPackInfo = () => {

        if (selectedInventoryMedicine) {

            return {
                packSize: Math.max(
                    Number(
                        selectedInventoryMedicine
                            .pack_size || 1
                    ),
                    1
                ),

                unitLabel:
                    selectedInventoryMedicine
                        .unit_label ||
                    "Unit",

                allowLooseSale:
                    Boolean(
                        selectedInventoryMedicine
                            .allow_loose_sale
                    ),
            };

        }


        const packSize = Math.max(
            Number(
                inventoryPackSizeInput?.value ||
                1
            ),
            1
        );


        let unitLabel = "Unit";

        if (inventoryUnitInput) {

            const selectedOption =
                inventoryUnitInput.options[
                inventoryUnitInput.selectedIndex
                ];

            if (selectedOption?.text) {
                unitLabel =
                    selectedOption.text;
            }

        }


        return {
            packSize,

            unitLabel,

            allowLooseSale:
                Boolean(
                    inventoryLooseSaleInput
                        ?.checked
                ),
        };

    };


    function updateInventoryPreview() {

        const {
            packSize,
            unitLabel,
            allowLooseSale,
        } = getInventoryPackInfo();


        const packsReceived = Math.max(
            Number(
                inventoryQuantityInput
                    ?.value || 0
            ),
            0
        );


        const sellingPrice = Math.max(
            Number(
                inventorySellingPriceInput
                    ?.value || 0
            ),
            0
        );


        if (stockConversionPreview) {

            if (
                packsReceived > 0 &&
                packSize > 0
            ) {

                const totalUnits =
                    packsReceived *
                    packSize;

                const normalizedUnit =
                    String(unitLabel)
                        .toLowerCase();

                stockConversionPreview.textContent =
                    `${packsReceived} pack` +
                    `${packsReceived !== 1 ? "s" : ""}` +
                    ` × ${packSize} ${normalizedUnit}` +
                    `${packSize !== 1 ? "s" : ""}` +
                    ` = ${totalUnits} ${normalizedUnit}` +
                    `${totalUnits !== 1 ? "s" : ""}` +
                    ` in stock`;

                stockConversionPreview.style.display =
                    "block";

            } else {

                stockConversionPreview.textContent =
                    "";

                stockConversionPreview.style.display =
                    "none";

            }

        }


        if (loosePricePreview) {

            if (
                allowLooseSale &&
                packSize > 1 &&
                sellingPrice > 0
            ) {

                const loosePrice =
                    sellingPrice /
                    packSize;

                loosePricePreview.textContent =
                    `Approx. ${String(
                        unitLabel
                    ).toLowerCase()} price: ` +
                    `Rs. ${formatMoney(
                        loosePrice
                    )}`;

                loosePricePreview.style.display =
                    "block";

            } else {

                loosePricePreview.textContent =
                    "";

                loosePricePreview.style.display =
                    "none";

            }

        }

    }


    // ============================================================
    // INVENTORY LIVE PREVIEW EVENTS
    // ============================================================

    if (inventoryQuantityInput) {

        inventoryQuantityInput.addEventListener(
            "input",
            updateInventoryPreview
        );

    }

    if (inventoryPackSizeInput) {

        inventoryPackSizeInput.addEventListener(
            "input",
            updateInventoryPreview
        );

    }

    if (inventoryUnitInput) {

        inventoryUnitInput.addEventListener(
            "change",
            updateInventoryPreview
        );

    }

    if (inventoryLooseSaleInput) {

        inventoryLooseSaleInput.addEventListener(
            "change",
            updateInventoryPreview
        );

    }

    if (inventorySellingPriceInput) {

        inventorySellingPriceInput.addEventListener(
            "input",
            updateInventoryPreview
        );

    }


    // ============================================================
    // INVENTORY MEDICINE SEARCH
    // ============================================================

    if (
        medicineSearchInput &&
        medicineSearchResults &&
        medicineIdInput
    ) {

        let inventorySearchTimer = null;
        let inventorySearchController = null;


        const hideSearchResults = () => {

            medicineSearchResults.innerHTML =
                "";

            medicineSearchResults.style.display =
                "none";

        };


        const hideNotFound = () => {

            if (medicineNotFound) {
                medicineNotFound.style.display =
                    "none";
            }

        };


        const showSearchMessage = (
            message
        ) => {

            medicineSearchResults.innerHTML =
                "";

            const messageElement =
                document.createElement(
                    "div"
                );

            messageElement.className =
                "p-3 text-muted small";

            messageElement.textContent =
                message;

            medicineSearchResults.appendChild(
                messageElement
            );

            medicineSearchResults.style.display =
                "block";

        };


        const clearMedicineSelection = () => {

            medicineIdInput.value = "";

            selectedInventoryMedicine =
                null;

            setInventoryMode("");

            if (selectedMedicine) {
                selectedMedicine.style.display =
                    "none";
            }

            if (selectedMedicineName) {
                selectedMedicineName.textContent =
                    "";
            }

            if (selectedMedicineMeta) {
                selectedMedicineMeta.textContent =
                    "";
            }

            if (
                selectedMedicineIdentifiers
            ) {
                selectedMedicineIdentifiers.textContent =
                    "";
            }

            if (
                selectedMedicinePackInfo
            ) {
                selectedMedicinePackInfo.textContent =
                    "";
            }

            medicineSearchInput.value = "";

            medicineSearchInput.disabled =
                false;

            if (clearMedicineSearch) {
                clearMedicineSearch.style.display =
                    "none";
            }

            hideSearchResults();
            hideNotFound();
            hideNewMedicineSection();

            updateInventoryPreview();

        };


        const selectMedicine = (
            medicine
        ) => {

            setInventoryMode(
                "existing"
            );

            medicineIdInput.value =
                medicine.id;

            selectedInventoryMedicine =
                medicine;

            hideNewMedicineSection();
            hideNotFound();


            const medicineTitle =
                `${medicine.name}` +
                `${medicine.strength
                    ? ` ${medicine.strength}`
                    : ""
                }`;


            if (selectedMedicineName) {

                selectedMedicineName.textContent =
                    medicineTitle;

            }


            if (selectedMedicineMeta) {

                const meta = [];

                if (medicine.generic_name) {
                    meta.push(
                        medicine.generic_name
                    );
                }

                if (medicine.dosage_form) {
                    meta.push(
                        medicine.dosage_form
                    );
                }

                if (medicine.category) {
                    meta.push(
                        medicine.category
                    );
                }

                selectedMedicineMeta.textContent =
                    meta.join(" • ");

            }


            if (
                selectedMedicineIdentifiers
            ) {

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


            if (
                selectedMedicinePackInfo
            ) {

                const packSize =
                    Math.max(
                        Number(
                            medicine.pack_size ||
                            1
                        ),
                        1
                    );

                const unitLabel =
                    medicine.unit_label ||
                    "Unit";

                const looseSaleText =
                    medicine.allow_loose_sale
                        ? "Loose sale allowed"
                        : "Full-pack sale only";

                selectedMedicinePackInfo.textContent =
                    `Pack: ${packSize} ` +
                    `${unitLabel}` +
                    `${packSize !== 1 ? "s" : ""}` +
                    ` • ${looseSaleText}`;

                selectedMedicinePackInfo.className =
                    medicine.allow_loose_sale
                        ? "small mt-2 text-success"
                        : "small mt-2 text-muted";

            }


            if (selectedMedicine) {

                selectedMedicine.style.display =
                    "block";

            }


            medicineSearchInput.value =
                medicineTitle;

            medicineSearchInput.disabled =
                true;


            if (clearMedicineSearch) {

                clearMedicineSearch.style.display =
                    "block";

            }


            hideSearchResults();

            updateInventoryPreview();

        };


        const renderMedicineResults = (
            results
        ) => {

            medicineSearchResults.innerHTML =
                "";

            hideNotFound();


            if (!results.length) {

                hideSearchResults();

                if (medicineNotFound) {
                    medicineNotFound.style.display =
                        "block";
                }

                return;

            }


            results.forEach(
                (medicine) => {

                    const button =
                        document.createElement(
                            "button"
                        );

                    button.type =
                        "button";

                    button.className =
                        "w-100 border-0 bg-white text-start p-3";

                    button.style.borderBottom =
                        "1px solid #e7eaee";


                    const title =
                        document.createElement(
                            "div"
                        );

                    title.className =
                        "fw-semibold";

                    title.textContent =
                        `${medicine.name}` +
                        `${medicine.strength
                            ? ` ${medicine.strength}`
                            : ""
                        }`;


                    const metaElement =
                        document.createElement(
                            "div"
                        );

                    metaElement.className =
                        "small text-muted mt-1";

                    const meta = [];


                    if (medicine.generic_name) {
                        meta.push(
                            medicine.generic_name
                        );
                    }

                    if (medicine.dosage_form) {
                        meta.push(
                            medicine.dosage_form
                        );
                    }

                    if (medicine.category) {
                        meta.push(
                            medicine.category
                        );
                    }


                    const resultPackSize =
                        Math.max(
                            Number(
                                medicine.pack_size ||
                                1
                            ),
                            1
                        );


                    if (medicine.unit_label) {

                        meta.push(
                            `${resultPackSize} ` +
                            `${medicine.unit_label}` +
                            `${resultPackSize !== 1
                                ? "s"
                                : ""
                            }/pack`
                        );

                    }


                    if (
                        medicine.allow_loose_sale
                    ) {

                        meta.push(
                            "Loose sale"
                        );

                    }


                    metaElement.textContent =
                        meta.join(" • ");


                    button.appendChild(
                        title
                    );

                    button.appendChild(
                        metaElement
                    );


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


                    if (identifiers.length) {

                        const identifierElement =
                            document.createElement(
                                "div"
                            );

                        identifierElement.className =
                            "small text-muted mt-1";

                        identifierElement.textContent =
                            identifiers.join(" • ");

                        button.appendChild(
                            identifierElement
                        );

                    }


                    button.addEventListener(
                        "click",
                        () => {

                            selectMedicine(
                                medicine
                            );

                        }
                    );


                    medicineSearchResults.appendChild(
                        button
                    );

                }
            );


            medicineSearchResults.style.display =
                "block";

        };


        const searchMedicines =
            async (query) => {

                if (
                    inventorySearchController
                ) {

                    inventorySearchController.abort();

                }


                if (
                    !query ||
                    query.length < 2
                ) {

                    hideSearchResults();
                    hideNotFound();

                    return;

                }


                inventorySearchController =
                    new AbortController();


                showSearchMessage(
                    "Searching medicines..."
                );


                try {

                    const searchUrl =
                        `/inventory/search-medicines/` +
                        `?q=${encodeURIComponent(
                            query
                        )}`;


                    const response =
                        await fetch(
                            searchUrl,
                            {
                                method:
                                    "GET",

                                headers: {
                                    "X-Requested-With":
                                        "XMLHttpRequest",
                                },

                                credentials:
                                    "same-origin",

                                signal:
                                    inventorySearchController
                                        .signal,
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

                    if (
                        error.name ===
                        "AbortError"
                    ) {
                        return;
                    }


                    showSearchMessage(
                        "Unable to search medicines. Please try again."
                    );

                }

            };


        medicineSearchInput.addEventListener(
            "input",
            () => {

                const query =
                    medicineSearchInput
                        .value
                        .trim();


                clearTimeout(
                    inventorySearchTimer
                );


                setInventoryMode("");

                medicineIdInput.value =
                    "";

                selectedInventoryMedicine =
                    null;

                hideNewMedicineSection();


                if (medicineNotFound) {
                    medicineNotFound.style.display =
                        "none";
                }


                if (clearMedicineSearch) {

                    clearMedicineSearch.style.display =
                        query
                            ? "block"
                            : "none";

                }


                inventorySearchTimer =
                    setTimeout(
                        () => {

                            searchMedicines(
                                query
                            );

                        },
                        200
                    );

            }
        );


        if (
            createNewMedicineButton
        ) {

            createNewMedicineButton.addEventListener(
                "click",
                () => {

                    showNewMedicineSection();

                }
            );

        }


        if (
            cancelNewMedicineButton
        ) {

            cancelNewMedicineButton.addEventListener(
                "click",
                () => {

                    setInventoryMode("");

                    hideNewMedicineSection();

                    medicineSearchInput.disabled =
                        false;

                    medicineSearchInput.focus();

                    if (
                        medicineSearchInput.value
                            .trim()
                            .length >= 2
                    ) {

                        searchMedicines(
                            medicineSearchInput
                                .value
                                .trim()
                        );

                    }

                }
            );

        }


        if (
            removeSelectedMedicine
        ) {

            removeSelectedMedicine.addEventListener(
                "click",
                () => {

                    clearMedicineSelection();

                    medicineSearchInput.focus();

                }
            );

        }


        if (
            clearMedicineSearch
        ) {

            clearMedicineSearch.addEventListener(
                "click",
                () => {

                    clearMedicineSelection();

                    medicineSearchInput.focus();

                }
            );

        }


        document.addEventListener(
            "click",
            (event) => {

                const clickedResults =
                    medicineSearchResults.contains(
                        event.target
                    );

                const clickedSearch =
                    medicineSearchInput.contains(
                        event.target
                    );

                const clickedClear =
                    clearMedicineSearch &&
                    clearMedicineSearch.contains(
                        event.target
                    );

                if (
                    !clickedResults &&
                    !clickedSearch &&
                    !clickedClear
                ) {

                    hideSearchResults();

                }

            }
        );

    }


    // ============================================================
    // RESTORE INVENTORY FORM AFTER SERVER VALIDATION ERROR
    // ============================================================

    if (
        inventoryEntryTypeInput?.value ===
        "new"
    ) {

        if (newMedicineSection) {

            newMedicineSection.style.display =
                "block";

        }

    }


    updateInventoryPreview();

    // ============================================================
    // SALES / POS
    // ============================================================

    const posPage =
        document.getElementById(
            "posPage"
        );

    if (!posPage) {
        return;
    }

    const searchUrl =
        posPage.dataset.searchUrl;

    const checkoutUrl =
        posPage.dataset.checkoutUrl;

    const receiptUrlTemplate =
        posPage.dataset.receiptUrlTemplate;

    const detailUrlTemplate =
        posPage.dataset.detailUrlTemplate;

    const posSearchInput =
        document.getElementById(
            "posMedicineSearch"
        );

    const posSearchResults =
        document.getElementById(
            "posSearchResults"
        );

    const posSearchStatus =
        document.getElementById(
            "posSearchStatus"
        );

    const posCartItems =
        document.getElementById(
            "posCartItems"
        );

    const posCartEmpty =
        document.getElementById(
            "posCartEmpty"
        );

    const posCartCount =
        document.getElementById(
            "posCartCount"
        );

    const posClearCart =
        document.getElementById(
            "posClearCart"
        );

    const posCustomerName =
        document.getElementById(
            "posCustomerName"
        );

    const posCustomerPhone =
        document.getElementById(
            "posCustomerPhone"
        );

    const posDiscount =
        document.getElementById(
            "posDiscount"
        );

    const posPaymentMethod =
        document.getElementById(
            "posPaymentMethod"
        );

    const posPaidAmount =
        document.getElementById(
            "posPaidAmount"
        );

    const posSubtotal =
        document.getElementById(
            "posSubtotal"
        );

    const posTax =
        document.getElementById(
            "posTax"
        );

    const posDiscountDisplay =
        document.getElementById(
            "posDiscountDisplay"
        );

    const posTotal =
        document.getElementById(
            "posTotal"
        );

    const posCheckoutError =
        document.getElementById(
            "posCheckoutError"
        );

    const posCheckoutButton =
        document.getElementById(
            "posCheckoutButton"
        );

    const posSuccessModal =
        document.getElementById(
            "posSuccessModal"
        );

    const successPrintReceiptButton =
        document.getElementById(
            "posSuccessPrintReceipt"
        );

    const successViewSaleButton =
        document.getElementById(
            "posSuccessViewSale"
        );

    let cart = [];

    let posSearchTimer = null;
    let posSearchController = null;

    // ============================================================
    // POS HELPERS
    // ============================================================

    const cartKey = (
        batchId,
        saleType
    ) => {
        return `${batchId}:${saleType}`;
    };

    const normalizePosProduct = (
        product
    ) => {
        return {
            ...product,

            batch_id:
                Number(
                    product.batch_id
                ),

            stock_units:
                Number(
                    product.stock_units ??
                    product.quantity ??
                    0
                ),

            quantity:
                Number(
                    product.stock_units ??
                    product.quantity ??
                    0
                ),

            pack_size:
                Math.max(
                    Number(
                        product.pack_size ||
                        1
                    ),
                    1
                ),

            full_packs_available:
                Number(
                    product.full_packs_available ||
                    0
                ),

            loose_units_available:
                Number(
                    product.loose_units_available ||
                    0
                ),

            pack_price:
                Number(
                    product.pack_price ??
                    product.selling_price ??
                    0
                ),

            unit_price:
                Number(
                    product.unit_price ??
                    product.selling_price ??
                    0
                ),

            tax_rate:
                Number(
                    product.tax_rate ||
                    0
                ),

            allow_loose_sale:
                Boolean(
                    product.allow_loose_sale
                ),

            unit_label:
                product.unit_label ||
                "Unit",
        };
    };

    const getItemPrice = (
        item
    ) => {
        if (
            item.sale_type ===
            "unit"
        ) {
            return Number(
                item.unit_price
            );
        }

        return Number(
            item.pack_price
        );
    };

    const getItemStockDeduction = (
        item,
        quantity = item.cart_quantity
    ) => {
        const cleanQuantity =
            Math.max(
                Number(quantity || 0),
                0
            );

        if (
            item.sale_type ===
            "pack"
        ) {
            return (
                cleanQuantity *
                item.pack_size
            );
        }

        return cleanQuantity;
    };

    const getBatchCartDeduction = (
        batchId,
        excludeKey = null
    ) => {
        return cart.reduce(
            (total, item) => {
                if (
                    Number(
                        item.batch_id
                    ) !==
                    Number(batchId)
                ) {
                    return total;
                }

                if (
                    excludeKey &&
                    item.key ===
                    excludeKey
                ) {
                    return total;
                }

                return (
                    total +
                    getItemStockDeduction(
                        item
                    )
                );
            },
            0
        );
    };

    const getMaximumQuantity = (
        item
    ) => {
        const otherDeduction =
            getBatchCartDeduction(
                item.batch_id,
                item.key
            );

        const remainingStock =
            Math.max(
                item.stock_units -
                otherDeduction,
                0
            );

        if (
            item.sale_type ===
            "pack"
        ) {
            return Math.floor(
                remainingStock /
                item.pack_size
            );
        }

        return remainingStock;
    };

    const getSaleLabel = (
        item
    ) => {
        if (
            item.sale_type ===
            "pack"
        ) {
            return "Pack";
        }

        return (
            item.unit_label ||
            "Unit"
        );
    };

    const getStockDisplay = (
        product
    ) => {
        if (
            product.stock_display
        ) {
            return product.stock_display;
        }

        const packSize =
            Math.max(
                Number(
                    product.pack_size ||
                    1
                ),
                1
            );

        const stockUnits =
            Number(
                product.stock_units ??
                product.quantity ??
                0
            );

        if (packSize <= 1) {
            return (
                `${stockUnits} ` +
                `${String(
                    product.unit_label ||
                    "unit"
                ).toLowerCase()}`
            );
        }

        const packs =
            Math.floor(
                stockUnits /
                packSize
            );

        const loose =
            stockUnits %
            packSize;

        const parts = [];

        if (packs) {
            parts.push(
                `${packs} pack` +
                `${packs !== 1 ? "s" : ""}`
            );
        }

        if (loose) {
            const label =
                String(
                    product.unit_label ||
                    "unit"
                ).toLowerCase();

            parts.push(
                `${loose} ${label}` +
                `${loose !== 1 ? "s" : ""}`
            );
        }

        return (
            parts.join(", ") ||
            "0"
        );
    };

    // ============================================================
    // POS ERROR
    // ============================================================

    const showCheckoutError = (
        message
    ) => {
        if (!posCheckoutError) {
            return;
        }

        posCheckoutError.textContent =
            message;

        posCheckoutError.classList.remove(
            "d-none"
        );
    };

    const clearCheckoutError = () => {
        if (!posCheckoutError) {
            return;
        }

        posCheckoutError.textContent =
            "";

        posCheckoutError.classList.add(
            "d-none"
        );
    };

    // ============================================================
    // POS TOTALS
    // ============================================================


    const calculateCartTotals = () => {
        let subtotalCents = 0;
        let taxCents = 0;

        cart.forEach((item) => {
            const price = getItemPrice(item);

            const lineSubtotal = toMoney(
                price * item.cart_quantity
            );

            const rate = Number(item.tax_rate || 0);

            // Match backend ROUND_HALF_UP for
            // non-negative monetary amounts.
            const lineTax = toMoney(
                lineSubtotal * rate / 100
            );

            subtotalCents += Math.round(
                lineSubtotal * 100
            );

            taxCents += Math.round(
                lineTax * 100
            );
        });

        const subtotal = subtotalCents / 100;
        const tax = taxCents / 100;

        const discount = toMoney(
            Math.max(
                Number(posDiscount?.value || 0),
                0
            )
        );

        const total = toMoney(
            Math.max(
                subtotal + tax - discount,
                0
            )
        );

        return {
            subtotal,
            tax,
            discount,
            total,
        };
    };


    const renderPosTotals = () => {
        const totals =
            calculateCartTotals();

        if (posSubtotal) {
            posSubtotal.textContent =
                formatMoney(
                    totals.subtotal
                );
        }

        if (posTax) {
            posTax.textContent =
                formatMoney(
                    totals.tax
                );
        }

        if (
            posDiscountDisplay
        ) {
            posDiscountDisplay.textContent =
                formatMoney(
                    totals.discount
                );
        }

        if (posTotal) {
            posTotal.textContent =
                formatMoney(
                    totals.total
                );
        }
    };

    // ============================================================
    // ADD ITEM TO CART
    // ============================================================

    const addProductToCart = (
        product,
        saleType
    ) => {
        clearCheckoutError();

        const normalized =
            normalizePosProduct(
                product
            );

        if (
            saleType === "unit" &&
            !normalized.allow_loose_sale
        ) {
            showCheckoutError(
                `${normalized.name} does not allow loose-unit sales.`
            );

            return;
        }

        if (
            saleType === "unit" &&
            normalized.pack_size <= 1
        ) {
            showCheckoutError(
                `${normalized.name} does not have a separate loose-unit configuration.`
            );

            return;
        }

        const key =
            cartKey(
                normalized.batch_id,
                saleType
            );

        const existing =
            cart.find(
                (item) =>
                    item.key ===
                    key
            );

        if (existing) {
            const maxQuantity =
                getMaximumQuantity(
                    existing
                );

            if (
                existing.cart_quantity >=
                maxQuantity
            ) {
                showCheckoutError(
                    "Insufficient stock for this quantity."
                );

                return;
            }

            existing.cart_quantity +=
                1;

            renderCart();

            return;
        }

        const item = {
            ...normalized,

            key,

            sale_type:
                saleType,

            cart_quantity:
                1,
        };

        const maxQuantity =
            getMaximumQuantity(
                item
            );

        if (maxQuantity < 1) {
            if (
                saleType ===
                "pack"
            ) {
                showCheckoutError(
                    `No complete pack of ${normalized.name} is available.`
                );
            } else {
                showCheckoutError(
                    `No ${normalized.unit_label.toLowerCase()} stock is available.`
                );
            }

            return;
        }

        cart.push(item);

        renderCart();
    };

    // ============================================================
    // CART RENDER
    // ============================================================

    const renderCart = () => {
        if (!posCartItems) {
            return;
        }

        posCartItems.innerHTML =
            "";

        let cartItemCount = 0;

        cart.forEach((item) => {
            cartItemCount +=
                item.cart_quantity;

            const unitPrice =
                getItemPrice(
                    item
                );

            const lineSubtotal =
                unitPrice *
                item.cart_quantity;

            const maximumQuantity =
                getMaximumQuantity(
                    item
                );

            const saleLabel =
                getSaleLabel(
                    item
                );

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "border rounded-3 p-3";

            const looseOption =
                item.allow_loose_sale &&
                    item.pack_size > 1
                    ? `
                        <option
                            value="unit"
                            ${item.sale_type ===
                        "unit"
                        ? "selected"
                        : ""
                    }
                        >
                            ${escapeHtml(
                        item.unit_label
                    )}
                        </option>
                    `
                    : "";

            card.innerHTML = `
                <div class="d-flex justify-content-between gap-3">

                    <div class="flex-grow-1">

                        <div class="fw-semibold">
                            ${escapeHtml(item.name)}

                            ${item.strength
                    ? `
                                        <span class="text-muted">
                                            ${escapeHtml(
                        item.strength
                    )}
                                        </span>
                                    `
                    : ""
                }
                        </div>

                        <div class="small text-muted mt-1">
                            Batch:
                            ${escapeHtml(
                    item.batch_number
                )}
                        </div>

                        <div class="small text-muted">
                            Stock:
                            ${escapeHtml(
                    getStockDisplay(
                        item
                    )
                )}
                        </div>

                    </div>

                    <button
                        type="button"
                        class="
                            btn
                            btn-sm
                            btn-link
                            text-danger
                            p-0
                            pos-remove-item
                        "
                        data-key="${escapeHtml(
                    item.key
                )}"
                        aria-label="Remove item"
                    >
                        <i class="fa-solid fa-xmark"></i>
                    </button>

                </div>

                <div class="row g-2 mt-2">

                    <div class="col-6">

                        <label class="form-label small mb-1">
                            Sell As
                        </label>

                        <select
                            class="
                                form-select
                                form-select-sm
                                pos-sale-type
                            "
                            data-key="${escapeHtml(
                    item.key
                )}"
                        >
                            <option
                                value="pack"
                                ${item.sale_type ===
                    "pack"
                    ? "selected"
                    : ""
                }
                            >
                                Pack
                            </option>

                            ${looseOption}
                        </select>

                    </div>

                    <div class="col-6">

                        <label class="form-label small mb-1">
                            Price
                        </label>

                        <div
                            class="
                                form-control
                                form-control-sm
                                bg-light
                            "
                        >
                            Rs. ${formatMoney(
                    unitPrice
                )}
                            / ${escapeHtml(
                    saleLabel
                )}
                        </div>

                    </div>

                </div>

                <div
                    class="
                        d-flex
                        align-items-center
                        gap-2
                        mt-3
                    "
                >

                    <button
                        type="button"
                        class="
                            btn
                            btn-sm
                            btn-outline-secondary
                            pos-quantity-minus
                        "
                        data-key="${escapeHtml(
                    item.key
                )}"
                    >
                        <i class="fa-solid fa-minus"></i>
                    </button>

                    <input
                        type="number"
                        class="
                            form-control
                            form-control-sm
                            text-center
                            pos-quantity-input
                        "
                        data-key="${escapeHtml(
                    item.key
                )}"
                        min="1"
                        max="${maximumQuantity}"
                        value="${item.cart_quantity}"
                        style="max-width: 85px;"
                    >

                    <button
                        type="button"
                        class="
                            btn
                            btn-sm
                            btn-outline-secondary
                            pos-quantity-plus
                        "
                        data-key="${escapeHtml(
                    item.key
                )}"
                    >
                        <i class="fa-solid fa-plus"></i>
                    </button>

                    <div class="ms-auto text-end">

                        <div class="fw-semibold">
                            Rs.
                            ${formatMoney(
                    lineSubtotal
                )}
                        </div>

                        <div class="small text-muted">
                            ${item.cart_quantity}
                            ${escapeHtml(
                    saleLabel
                )}${item.cart_quantity !== 1
                    ? "s"
                    : ""
                }
                        </div>

                    </div>

                </div>
            `;

            posCartItems.appendChild(
                card
            );
        });

        const hasItems =
            cart.length > 0;

        if (posCartEmpty) {
            posCartEmpty.classList.toggle(
                "d-none",
                hasItems
            );
        }

        if (posClearCart) {
            posClearCart.disabled =
                !hasItems;
        }

        if (posCheckoutButton) {
            posCheckoutButton.disabled =
                !hasItems;
        }

        if (posCartCount) {
            posCartCount.textContent =
                String(
                    cartItemCount
                );
        }

        renderPosTotals();
    };

    // ============================================================
    // CHANGE SALE TYPE
    // ============================================================

    const changeSaleType = (
        oldKey,
        newSaleType
    ) => {
        const item =
            cart.find(
                (cartItem) =>
                    cartItem.key ===
                    oldKey
            );

        if (!item) {
            return;
        }

        if (
            newSaleType ===
            item.sale_type
        ) {
            return;
        }

        if (
            newSaleType === "unit" &&
            !item.allow_loose_sale
        ) {
            showCheckoutError(
                `${item.name} does not allow loose-unit sales.`
            );

            renderCart();

            return;
        }

        if (
            newSaleType === "unit" &&
            item.pack_size <= 1
        ) {
            showCheckoutError(
                `${item.name} does not have a separate loose-unit configuration.`
            );

            renderCart();

            return;
        }

        const newKey =
            cartKey(
                item.batch_id,
                newSaleType
            );

        const existingDestination =
            cart.find(
                (cartItem) =>
                    cartItem.key ===
                    newKey
            );

        const oldSaleType =
            item.sale_type;

        const oldQuantity =
            item.cart_quantity;

        item.sale_type =
            newSaleType;

        item.key =
            newKey;

        const maxQuantity =
            getMaximumQuantity(
                item
            );

        item.sale_type =
            oldSaleType;

        item.key =
            oldKey;

        if (existingDestination) {
            const originalDestinationQuantity =
                existingDestination
                    .cart_quantity;

            cart =
                cart.filter(
                    (cartItem) =>
                        cartItem.key !==
                        oldKey
                );

            existingDestination.cart_quantity +=
                oldQuantity;

            const destinationMax =
                getMaximumQuantity(
                    existingDestination
                );

            if (
                existingDestination
                    .cart_quantity >
                destinationMax
            ) {
                existingDestination.cart_quantity =
                    originalDestinationQuantity;

                cart.push(item);

                showCheckoutError(
                    "The selected sale type would exceed available stock."
                );

                renderCart();

                return;
            }

            clearCheckoutError();

            renderCart();

            return;
        }

        item.sale_type =
            newSaleType;

        item.key =
            newKey;

        if (
            item.cart_quantity >
            maxQuantity
        ) {
            if (maxQuantity < 1) {
                item.sale_type =
                    oldSaleType;

                item.key =
                    oldKey;

                showCheckoutError(
                    "Insufficient stock for the selected sale type."
                );

                renderCart();

                return;
            }

            item.cart_quantity =
                maxQuantity;
        }

        clearCheckoutError();

        renderCart();
    };

    // ============================================================
    // POS SEARCH RESULTS
    // ============================================================

    const renderPosSearchResults = (
        results
    ) => {
        if (!posSearchResults) {
            return;
        }

        posSearchResults.innerHTML =
            "";

        if (!results.length) {
            posSearchResults.innerHTML = `
                <div class="text-center py-5 text-muted">

                    <i
                        class="
                            fa-solid
                            fa-box-open
                            fa-2x
                            mb-3
                        "
                    ></i>

                    <div>
                        No available stock found.
                    </div>

                </div>
            `;

            return;
        }

        results.forEach(
            (rawProduct) => {
                const product =
                    normalizePosProduct(
                        rawProduct
                    );

                const container =
                    document.createElement(
                        "div"
                    );

                container.className =
                    "border rounded-3 p-3 bg-white";

                const availableUnitsAfterCart =
                    Math.max(
                        product.stock_units -
                        getBatchCartDeduction(
                            product.batch_id
                        ),
                        0
                    );

                const availablePacksAfterCart =
                    Math.floor(
                        availableUnitsAfterCart /
                        product.pack_size
                    );

                const canSellPack =
                    availablePacksAfterCart > 0;

                const canSellLoose =
                    product.allow_loose_sale &&
                    product.pack_size > 1 &&
                    availableUnitsAfterCart > 0;

                container.innerHTML = `
                    <div
                        class="
                            d-flex
                            justify-content-between
                            gap-3
                        "
                    >

                        <div class="flex-grow-1">

                            <div class="fw-semibold">

                                ${escapeHtml(
                    product.name
                )}

                                ${product.strength
                        ? `
                                            <span class="text-muted">
                                                ${escapeHtml(
                            product.strength
                        )}
                                            </span>
                                        `
                        : ""
                    }

                            </div>

                            <div class="small text-muted mt-1">

                                ${escapeHtml(
                        product.generic_name ||
                        product.category ||
                        ""
                    )}

                            </div>

                            <div class="small text-muted mt-1">

                                Batch:
                                ${escapeHtml(
                        product.batch_number
                    )}

                                · Exp:
                                ${escapeHtml(
                        product.expiry_date
                    )}

                            </div>

                            <div class="small mt-1">

                                <span class="text-muted">
                                    Stock:
                                </span>

                                <strong>
                                    ${escapeHtml(
                        getStockDisplay(
                            product
                        )
                    )}
                                </strong>

                            </div>

                        </div>

                    </div>

                    <div class="row g-2 mt-2">

                        <div class="${canSellLoose
                        ? "col-md-6"
                        : "col-12"
                    }">

                            <button
                                type="button"
                                class="
                                    btn
                                    btn-outline-primary
                                    w-100
                                    pos-add-pack
                                "
                                ${!canSellPack
                        ? "disabled"
                        : ""
                    }
                            >

                                <div class="fw-semibold">
                                    Add Pack
                                </div>

                                <div class="small">
                                    Rs.
                                    ${formatMoney(
                        product.pack_price
                    )}
                                </div>

                            </button>

                        </div>

                        ${canSellLoose
                        ? `
                                    <div class="col-md-6">

                                        <button
                                            type="button"
                                            class="
                                                btn
                                                btn-outline-success
                                                w-100
                                                pos-add-unit
                                            "
                                        >

                                            <div class="fw-semibold">
                                                Add
                                                ${escapeHtml(
                            product.unit_label
                        )}
                                            </div>

                                            <div class="small">
                                                Rs.
                                                ${formatMoney(
                            product.unit_price
                        )}
                                            </div>

                                        </button>

                                    </div>
                                `
                        : ""
                    }

                    </div>

                    ${!canSellPack &&
                        canSellLoose
                        ? `
                                <div
                                    class="
                                        small
                                        text-warning
                                        mt-2
                                    "
                                >
                                    No complete pack remains.
                                    Loose units can still be sold.
                                </div>
                            `
                        : ""
                    }
                `;

                const packButton =
                    container.querySelector(
                        ".pos-add-pack"
                    );

                const unitButton =
                    container.querySelector(
                        ".pos-add-unit"
                    );

                if (packButton) {
                    packButton.addEventListener(
                        "click",
                        () => {
                            addProductToCart(
                                product,
                                "pack"
                            );
                        }
                    );
                }

                if (unitButton) {
                    unitButton.addEventListener(
                        "click",
                        () => {
                            addProductToCart(
                                product,
                                "unit"
                            );
                        }
                    );
                }

                posSearchResults.appendChild(
                    container
                );
            }
        );
    };

    const searchPosMedicines =
        async () => {
            if (
                !posSearchInput ||
                !posSearchResults
            ) {
                return;
            }

            const query =
                posSearchInput
                    .value
                    .trim();

            if (query.length < 2) {
                if (
                    posSearchController
                ) {
                    posSearchController.abort();
                }

                if (
                    posSearchStatus
                ) {
                    posSearchStatus.textContent =
                        "";
                }

                posSearchResults.innerHTML = `
                    <div class="text-center py-5 text-muted">

                        <i
                            class="
                                fa-solid
                                fa-pills
                                fa-2x
                                mb-3
                            "
                        ></i>

                        <div>
                            Type at least 2 characters to search.
                        </div>

                    </div>
                `;

                return;
            }

            if (
                posSearchController
            ) {
                posSearchController.abort();
            }

            posSearchController =
                new AbortController();

            if (posSearchStatus) {
                posSearchStatus.textContent =
                    "Searching...";
            }

            try {
                const url =
                    `${searchUrl}` +
                    `?q=${encodeURIComponent(
                        query
                    )}`;

                const response =
                    await fetch(
                        url,
                        {
                            method:
                                "GET",

                            headers: {
                                "X-Requested-With":
                                    "XMLHttpRequest",
                            },

                            credentials:
                                "same-origin",

                            signal:
                                posSearchController
                                    .signal,
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to search medicines."
                    );
                }

                const results =
                    data.results ||
                    [];

                if (posSearchStatus) {
                    posSearchStatus.textContent =
                        `${results.length} result(s)`;
                }

                renderPosSearchResults(
                    results
                );
            } catch (error) {
                if (
                    error.name ===
                    "AbortError"
                ) {
                    return;
                }

                if (posSearchStatus) {
                    posSearchStatus.textContent =
                        "";
                }

                posSearchResults.innerHTML = `
                    <div class="alert alert-danger mb-0">
                        ${escapeHtml(
                    error.message
                )}
                    </div>
                `;
            }
        };

    if (posSearchInput) {
        posSearchInput.addEventListener(
            "input",
            () => {
                clearTimeout(
                    posSearchTimer
                );

                posSearchTimer =
                    setTimeout(
                        searchPosMedicines,
                        200
                    );
            }
        );
    }

    // ============================================================
    // CART EVENTS
    // ============================================================

    if (posCartItems) {
        posCartItems.addEventListener(
            "click",
            (event) => {
                const removeButton =
                    event.target.closest(
                        ".pos-remove-item"
                    );

                const minusButton =
                    event.target.closest(
                        ".pos-quantity-minus"
                    );

                const plusButton =
                    event.target.closest(
                        ".pos-quantity-plus"
                    );

                if (removeButton) {
                    const key =
                        removeButton.dataset.key;

                    cart =
                        cart.filter(
                            (item) =>
                                item.key !==
                                key
                        );

                    clearCheckoutError();

                    renderCart();

                    if (
                        posSearchInput?.value
                            .trim()
                            .length >= 2
                    ) {
                        searchPosMedicines();
                    }

                    return;
                }

                if (minusButton) {
                    const key =
                        minusButton.dataset.key;

                    const item =
                        cart.find(
                            (cartItem) =>
                                cartItem.key ===
                                key
                        );

                    if (!item) {
                        return;
                    }

                    item.cart_quantity -=
                        1;

                    if (
                        item.cart_quantity <=
                        0
                    ) {
                        cart =
                            cart.filter(
                                (cartItem) =>
                                    cartItem.key !==
                                    key
                            );
                    }

                    clearCheckoutError();

                    renderCart();

                    if (
                        posSearchInput?.value
                            .trim()
                            .length >= 2
                    ) {
                        searchPosMedicines();
                    }

                    return;
                }

                if (plusButton) {
                    const key =
                        plusButton.dataset.key;

                    const item =
                        cart.find(
                            (cartItem) =>
                                cartItem.key ===
                                key
                        );

                    if (!item) {
                        return;
                    }

                    const maxQuantity =
                        getMaximumQuantity(
                            item
                        );

                    if (
                        item.cart_quantity >=
                        maxQuantity
                    ) {
                        showCheckoutError(
                            "Insufficient stock for this quantity."
                        );

                        return;
                    }

                    item.cart_quantity +=
                        1;

                    clearCheckoutError();

                    renderCart();

                    if (
                        posSearchInput?.value
                            .trim()
                            .length >= 2
                    ) {
                        searchPosMedicines();
                    }
                }
            }
        );

        posCartItems.addEventListener(
            "change",
            (event) => {
                const quantityInput =
                    event.target.closest(
                        ".pos-quantity-input"
                    );

                const saleTypeSelect =
                    event.target.closest(
                        ".pos-sale-type"
                    );

                if (quantityInput) {
                    const key =
                        quantityInput.dataset.key;

                    const item =
                        cart.find(
                            (cartItem) =>
                                cartItem.key ===
                                key
                        );

                    if (!item) {
                        return;
                    }

                    let quantity =
                        Number(
                            quantityInput.value
                        );

                    if (
                        !Number.isInteger(
                            quantity
                        ) ||
                        quantity < 1
                    ) {
                        quantity = 1;
                    }

                    const maxQuantity =
                        getMaximumQuantity(
                            item
                        );

                    if (
                        quantity >
                        maxQuantity
                    ) {
                        quantity =
                            maxQuantity;

                        showCheckoutError(
                            "Quantity adjusted to available stock."
                        );
                    } else {
                        clearCheckoutError();
                    }

                    item.cart_quantity =
                        Math.max(
                            quantity,
                            1
                        );

                    renderCart();

                    if (
                        posSearchInput?.value
                            .trim()
                            .length >= 2
                    ) {
                        searchPosMedicines();
                    }

                    return;
                }

                if (saleTypeSelect) {
                    const key =
                        saleTypeSelect.dataset.key;

                    const saleType =
                        saleTypeSelect.value;

                    changeSaleType(
                        key,
                        saleType
                    );

                    if (
                        posSearchInput?.value
                            .trim()
                            .length >= 2
                    ) {
                        searchPosMedicines();
                    }
                }
            }
        );
    }

    // ============================================================
    // CLEAR CART
    // ============================================================

    if (posClearCart) {
        posClearCart.addEventListener(
            "click",
            () => {
                cart = [];

                clearCheckoutError();

                renderCart();

                if (
                    posSearchInput?.value
                        .trim()
                        .length >= 2
                ) {
                    searchPosMedicines();
                }
            }
        );
    }

    // ============================================================
    // DISCOUNT
    // ============================================================

    if (posDiscount) {
        posDiscount.addEventListener(
            "input",
            () => {
                clearCheckoutError();

                renderPosTotals();
            }
        );
    }

    // ============================================================
    // CHECKOUT
    // ============================================================

    if (posCheckoutButton) {
        posCheckoutButton.addEventListener(
            "click",
            async () => {
                clearCheckoutError();

                if (!cart.length) {
                    showCheckoutError(
                        "Cart is empty."
                    );

                    return;
                }

                const totals =
                    calculateCartTotals();

                if (
                    totals.discount >
                    totals.subtotal +
                    totals.tax
                ) {
                    showCheckoutError(
                        "Discount cannot exceed sale total."
                    );

                    return;
                }

                posCheckoutButton.disabled =
                    true;

                posCheckoutButton.innerHTML = `
                    <span
                        class="
                            spinner-border
                            spinner-border-sm
                            me-2
                        "
                        aria-hidden="true"
                    ></span>

                    Processing...
                `;

                const payload = {
                    items:
                        cart.map(
                            (item) => ({
                                batch_id:
                                    item.batch_id,

                                quantity:
                                    item.cart_quantity,

                                sale_type:
                                    item.sale_type,
                            })
                        ),

                    payment_method:
                        posPaymentMethod
                            ?.value ||
                        "cash",

                    paid_amount:
                        posPaidAmount
                            ?.value ||
                        "0",

                    discount_amount:
                        posDiscount
                            ?.value ||
                        "0",

                    customer_name:
                        posCustomerName
                            ?.value
                            .trim() ||
                        "",

                    customer_phone:
                        posCustomerPhone
                            ?.value
                            .trim() ||
                        "",
                    customer_id:
                        document.getElementById("posSelectedCustomerId")?.value || null,
                };

                try {
                    const response =
                        await fetch(
                            checkoutUrl,
                            {
                                method:
                                    "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "X-CSRFToken":
                                        getCookie(
                                            "csrftoken"
                                        ),
                                },

                                credentials:
                                    "same-origin",

                                body:
                                    JSON.stringify(
                                        payload
                                    ),
                            }
                        );

                    let data;

                    try {
                        data =
                            await response.json();
                    } catch {
                        throw new Error(
                            "Invalid server response."
                        );
                    }

                    if (!response.ok) {
                        throw new Error(
                            data.error ||
                            "Sale could not be completed."
                        );
                    }

                    const invoiceElement =
                        document.getElementById(
                            "posSuccessInvoice"
                        );

                    const successTotal =
                        document.getElementById(
                            "posSuccessTotal"
                        );

                    const successPaid =
                        document.getElementById(
                            "posSuccessPaid"
                        );

                    const successChange =
                        document.getElementById(
                            "posSuccessChange"
                        );

                    if (invoiceElement) {
                        invoiceElement.textContent =
                            data.sale
                                .invoice_number;
                    }

                    if (successTotal) {
                        successTotal.textContent =
                            formatMoney(
                                data.sale
                                    .total_amount
                            );
                    }

                    if (successPaid) {
                        successPaid.textContent =
                            formatMoney(
                                data.sale
                                    .paid_amount
                            );
                    }

                    if (successChange) {
                        successChange.textContent =
                            formatMoney(
                                data.sale
                                    .change_amount
                            );
                    }

                    // ====================================================
                    // SALE SUCCESS ACTION URLS
                    // ====================================================

                    const saleId =
                        data.sale.id;

                    if (
                        successPrintReceiptButton &&
                        receiptUrlTemplate
                    ) {
                        successPrintReceiptButton.href =
                            receiptUrlTemplate.replace(
                                "/0/",
                                `/${saleId}/`
                            );
                    }

                    if (
                        successViewSaleButton &&
                        detailUrlTemplate
                    ) {
                        successViewSaleButton.href =
                            detailUrlTemplate.replace(
                                "/0/",
                                `/${saleId}/`
                            );
                    }

                    cart = [];

                    if (posCustomerName) {
                        posCustomerName.value =
                            "";
                    }

                    if (posCustomerPhone) {
                        posCustomerPhone.value =
                            "";
                    }

                    if (posDiscount) {
                        posDiscount.value =
                            "0";
                    }

                    if (posPaidAmount) {
                        posPaidAmount.value =
                            "0";
                    }

                    renderCart();

                    if (
                        window.bootstrap &&
                        posSuccessModal
                    ) {
                        const modal =
                            window.bootstrap.Modal
                                .getOrCreateInstance(
                                    posSuccessModal
                                );

                        modal.show();
                    }

                    if (posSearchInput) {
                        posSearchInput.value =
                            "";

                        posSearchInput.focus();
                    }

                    if (posSearchStatus) {
                        posSearchStatus.textContent =
                            "";
                    }

                    if (posSearchResults) {
                        posSearchResults.innerHTML = `
                            <div class="text-center py-5 text-muted">

                                <i
                                    class="
                                        fa-solid
                                        fa-pills
                                        fa-2x
                                        mb-3
                                    "
                                ></i>

                                <div>
                                    Search for a medicine to start a sale.
                                </div>

                            </div>
                        `;
                    }
                } catch (error) {
                    showCheckoutError(
                        error.message
                    );
                } finally {
                    posCheckoutButton.innerHTML = `
                        <i
                            class="
                                fa-solid
                                fa-cash-register
                                me-2
                            "
                        ></i>

                        Complete Sale
                    `;

                    posCheckoutButton.disabled =
                        cart.length ===
                        0;
                }
            }
        );
    }

    renderCart();
});

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById(
        "supplier-filter-form"
    );

    const searchInput = document.getElementById(
        "supplier-search"
    );

    const statusSelect = document.getElementById(
        "supplier-status"
    );

    const resultsContainer = document.getElementById(
        "supplier-results"
    );

    const feedback = document.getElementById(
        "supplier-search-feedback"
    );

    if (
        !form ||
        !searchInput ||
        !statusSelect ||
        !resultsContainer ||
        !feedback
    ) {
        return;
    }

    const DEBOUNCE_DELAY = 200;

    let debounceTimer = null;
    let activeController = null;
    let requestSequence = 0;

    function setFeedback(message, isError = false) {
        feedback.textContent = message;
        feedback.hidden = !message;

        feedback.classList.toggle(
            "text-danger",
            isError
        );

        feedback.classList.toggle(
            "text-muted",
            !isError
        );
    }

    function setLoading(isLoading) {
        resultsContainer.setAttribute(
            "aria-busy",
            String(isLoading)
        );

        resultsContainer.style.opacity = isLoading
            ? "0.55"
            : "1";
    }

    function buildUrl(page = 1) {
        const url = new URL(window.location.href);

        const query = searchInput.value.trim();
        const status = statusSelect.value;

        url.searchParams.delete("q");
        url.searchParams.delete("status");
        url.searchParams.delete("page");

        if (query) {
            url.searchParams.set("q", query);
        }

        if (status) {
            url.searchParams.set("status", status);
        }

        if (page > 1) {
            url.searchParams.set("page", String(page));
        }

        return url;
    }

    function clearDebounce() {
        if (debounceTimer !== null) {
            clearTimeout(debounceTimer);
            debounceTimer = null;
        }
    }

    async function loadSuppliers(url, updateHistory = true) {
        // Cancel the previous unfinished request.
        if (activeController) {
            activeController.abort();
        }

        const controller = new AbortController();
        activeController = controller;

        // Unique request ID avoids stale results.
        const currentSequence = ++requestSequence;

        setLoading(true);
        setFeedback("Searching suppliers...");

        try {
            const response = await fetch(url.toString(), {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                signal: controller.signal,
                credentials: "same-origin"
            });

            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }

            const contentType = response.headers.get(
                "content-type"
            ) || "";

            if (!contentType.includes("application/json")) {
                throw new Error(
                    "Unexpected response from server."
                );
            }

            const data = await response.json();

            // Ignore outdated results.
            if (currentSequence !== requestSequence) {
                return;
            }

            resultsContainer.innerHTML = data.html;

            if (updateHistory) {
                window.history.replaceState(
                    null,
                    "",
                    url.toString()
                );
            }

            setFeedback("");

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            if (currentSequence !== requestSequence) {
                return;
            }

            console.error(
                "Supplier search failed:",
                error
            );

            setFeedback(
                "Unable to load suppliers. Please try again.",
                true
            );

        } finally {
            if (currentSequence === requestSequence) {
                setLoading(false);
                activeController = null;
            }
        }
    }

    function scheduleSearch() {
        clearDebounce();

        // Invalidate and cancel current results
        // immediately when the user types.
        requestSequence++;

        if (activeController) {
            activeController.abort();
            activeController = null;
        }

        setLoading(false);
        setFeedback("");

        debounceTimer = setTimeout(() => {
            debounceTimer = null;

            loadSuppliers(buildUrl(1));
        }, DEBOUNCE_DELAY);
    }

    // Live search: 200ms after typing stops.
    searchInput.addEventListener(
        "input",
        scheduleSearch
    );

    // Status filter: no debounce.
    statusSelect.addEventListener("change", () => {
        clearDebounce();
        loadSuppliers(buildUrl(1));
    });

    // Search button / Enter key.
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        clearDebounce();
        loadSuppliers(buildUrl(1));
    });

    // AJAX pagination with event delegation.
    resultsContainer.addEventListener(
        "click",
        (event) => {
            const link = event.target.closest(
                ".supplier-pagination a.page-link"
            );

            if (!link) {
                return;
            }

            // Preserve standard browser interactions.
            if (
                event.button !== 0 ||
                event.ctrlKey ||
                event.metaKey ||
                event.shiftKey ||
                event.altKey
            ) {
                return;
            }

            event.preventDefault();

            clearDebounce();

            const url = new URL(
                link.href,
                window.location.origin
            );

            loadSuppliers(url);
        }
    );

    // Synchronize filters when browser history changes.
    window.addEventListener("popstate", () => {
        clearDebounce();

        const url = new URL(window.location.href);

        searchInput.value = url.searchParams.get("q") || "";

        const savedStatus = url.searchParams.get("status") || "";

        statusSelect.value = (
            savedStatus === "active" ||
            savedStatus === "inactive"
        ) ? savedStatus : "";

        loadSuppliers(url, false);
    });
});

/* ============================================================
   PURCHASE MANAGEMENT — CREATE / EDIT FORM
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const purchasePage = document.getElementById(
        "purchaseFormPage"
    );

    if (!purchasePage) {
        return;
    }

    const purchaseForm = document.getElementById(
        "purchase-order-form"
    );

    const itemsBody = document.getElementById(
        "purchaseItemsBody"
    );

    const addItemButton = document.getElementById(
        "addPurchaseItem"
    );

    const emptyTemplate = document.getElementById(
        "purchaseItemEmptyTemplate"
    );

    const totalFormsInput = document.getElementById(
        "id_items-TOTAL_FORMS"
    );

    const medicineCountElement = document.getElementById(
        "purchaseMedicineCount"
    );

    const totalPacksElement = document.getElementById(
        "purchaseTotalPacks"
    );

    const grossAmountElement = document.getElementById(
        "purchaseGrossAmount"
    );

    const discountAmountElement = document.getElementById(
        "purchaseDiscountAmount"
    );

    const grandTotalElement = document.getElementById(
        "purchaseGrandTotal"
    );

    const errorBox = document.getElementById(
        "purchaseClientError"
    );

    const saveButton = document.getElementById(
        "savePurchaseButton"
    );

    if (
        !purchaseForm ||
        !itemsBody ||
        !addItemButton ||
        !emptyTemplate ||
        !totalFormsInput
    ) {
        console.error(
            "Purchase form initialization failed: " +
            "required HTML elements are missing."
        );

        return;
    }

    /* ========================================================
       HELPERS
       ======================================================== */

    const formatMoney = (value) => {
        const amount = Number(value);

        const safeAmount = Number.isFinite(amount)
            ? amount
            : 0;

        return (
            "Rs. " +
            safeAmount.toLocaleString("en-PK", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })
        );
    };

    const toNumber = (value) => {
        const parsed = Number(value);

        return Number.isFinite(parsed)
            ? parsed
            : 0;
    };

    const findField = (row, fieldName) => {
        return row.querySelector(
            `[name$="-${fieldName}"]`
        );
    };

    const getRows = () => {
        return Array.from(
            itemsBody.querySelectorAll(
                ".purchase-item-row"
            )
        );
    };

    const isRemoved = (row) => {
        const deleteField = findField(
            row,
            "DELETE"
        );

        return (
            row.classList.contains("is-removed") ||
            Boolean(deleteField?.checked)
        );
    };

    const getActiveRows = () => {
        return getRows().filter(
            row => !isRemoved(row)
        );
    };

    const showError = (message) => {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;

        errorBox.classList.remove("d-none");

        errorBox.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    };

    const clearError = () => {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";

        errorBox.classList.add("d-none");
    };

    /* ========================================================
       CALCULATE A SINGLE MEDICINE ROW
       ======================================================== */

    const calculateRow = (row) => {
        if (isRemoved(row)) {
            return {
                packs: 0,
                gross: 0,
                discount: 0,
                total: 0
            };
        }

        const packsInput = findField(
            row,
            "ordered_packs"
        );

        const purchasePriceInput = findField(
            row,
            "purchase_price"
        );

        const discountInput = findField(
            row,
            "discount_amount"
        );

        const packs = toNumber(
            packsInput?.value
        );

        const purchasePrice = toNumber(
            purchasePriceInput?.value
        );

        const discount = toNumber(
            discountInput?.value
        );

        const gross = packs * purchasePrice;

        const total = Math.max(
            0,
            gross - discount
        );

        const lineTotalElement = row.querySelector(
            ".line-total"
        );

        if (lineTotalElement) {
            lineTotalElement.textContent = (
                formatMoney(total)
            );
        }

        return {
            packs,
            gross,
            discount,
            total
        };
    };

    /* ========================================================
       CALCULATE COMPLETE PURCHASE SUMMARY
       ======================================================== */

    const calculatePurchaseSummary = () => {
        const rows = getActiveRows();

        let totalPacks = 0;
        let grossAmount = 0;
        let discountAmount = 0;
        let grandTotal = 0;

        rows.forEach((row) => {
            const result = calculateRow(row);

            totalPacks += result.packs;

            grossAmount += result.gross;

            discountAmount += result.discount;

            grandTotal += result.total;
        });

        if (medicineCountElement) {
            medicineCountElement.textContent = (
                String(rows.length)
            );
        }

        if (totalPacksElement) {
            totalPacksElement.textContent = (
                String(totalPacks)
            );
        }

        if (grossAmountElement) {
            grossAmountElement.textContent = (
                formatMoney(grossAmount)
            );
        }

        if (discountAmountElement) {
            discountAmountElement.textContent = (
                formatMoney(discountAmount)
            );
        }

        if (grandTotalElement) {
            grandTotalElement.textContent = (
                formatMoney(grandTotal)
            );
        }
    };

    /* ========================================================
       ADD NEW MEDICINE ROW
       ======================================================== */

    const addMedicineRow = () => {
        const currentTotal = Number.parseInt(
            totalFormsInput.value,
            10
        );

        if (!Number.isInteger(currentTotal)) {
            showError(
                "Invalid purchase formset configuration."
            );

            return;
        }

        const maxFormsInput = document.getElementById(
            "id_items-MAX_NUM_FORMS"
        );

        const maxForms = maxFormsInput
            ? Number.parseInt(maxFormsInput.value, 10)
            : 1000;

        if (
            Number.isInteger(maxForms) &&
            currentTotal >= maxForms
        ) {
            showError(
                "Maximum medicine rows limit reached."
            );

            return;
        }

        const rowHTML = emptyTemplate.innerHTML.replace(
            /__prefix__/g,
            String(currentTotal)
        );

        const rowContainer = document.createElement(
            "tbody"
        );

        rowContainer.innerHTML = rowHTML.trim();

        const newRow = rowContainer.querySelector(
            ".purchase-item-row"
        );

        if (!newRow) {
            showError(
                "Unable to create the medicine row."
            );

            return;
        }

        itemsBody.appendChild(newRow);

        totalFormsInput.value = String(
            currentTotal + 1
        );

        clearError();

        calculatePurchaseSummary();

        const medicineSelect = findField(
            newRow,
            "medicine"
        );

        if (medicineSelect) {
            medicineSelect.focus();
        }
    };

    /* ========================================================
       REMOVE MEDICINE ROW
       ======================================================== */

    const removeMedicineRow = (row) => {
        const activeRows = getActiveRows();

        if (activeRows.length <= 1) {
            showError(
                "At least one medicine row is required."
            );

            return;
        }

        const deleteField = findField(
            row,
            "DELETE"
        );

        if (!deleteField) {
            showError(
                "Cannot remove this medicine row. " +
                "Formset DELETE field is missing."
            );

            return;
        }

        // Preserve the form index and mark it for deletion.
        // This works for existing items and newly added rows.
        deleteField.checked = true;

        row.classList.add("is-removed");

        clearError();

        calculatePurchaseSummary();
    };

    /* ========================================================
       DUPLICATE MEDICINE VALIDATION
       ======================================================== */

    const hasDuplicateMedicines = () => {
        const selectedMedicines = new Set();

        for (const row of getActiveRows()) {
            const medicineField = findField(
                row,
                "medicine"
            );

            const medicineId = medicineField?.value;

            if (!medicineId) {
                continue;
            }

            if (selectedMedicines.has(medicineId)) {
                return true;
            }

            selectedMedicines.add(medicineId);
        }

        return false;
    };

    /* ========================================================
       FORM VALIDATION
       ======================================================== */

    const validatePurchaseForm = () => {
        const activeRows = getActiveRows();

        if (activeRows.length < 1) {
            showError(
                "Add at least one medicine."
            );

            return false;
        }

        if (hasDuplicateMedicines()) {
            showError(
                "The same medicine cannot be added " +
                "multiple times in one purchase."
            );

            return false;
        }

        for (const row of activeRows) {
            const medicineField = findField(
                row,
                "medicine"
            );

            const packsField = findField(
                row,
                "ordered_packs"
            );

            const purchasePriceField = findField(
                row,
                "purchase_price"
            );

            const sellingPriceField = findField(
                row,
                "selling_price"
            );

            const discountField = findField(
                row,
                "discount_amount"
            );

            if (!medicineField?.value) {
                showError(
                    "Please select a medicine " +
                    "in every active row."
                );

                medicineField?.focus();

                return false;
            }

            const packs = Number(
                packsField?.value
            );

            if (
                !Number.isInteger(packs) ||
                packs < 1
            ) {
                showError(
                    "Pack quantity must be a " +
                    "positive whole number."
                );

                packsField?.focus();

                return false;
            }

            const purchasePrice = Number(
                purchasePriceField?.value
            );

            const sellingPrice = Number(
                sellingPriceField?.value
            );

            const discount = discountField?.value
                ? Number(discountField.value)
                : 0;

            if (
                purchasePriceField?.value === "" ||
                !Number.isFinite(purchasePrice) ||
                purchasePrice < 0
            ) {
                showError(
                    "Enter a valid purchase price."
                );

                purchasePriceField?.focus();

                return false;
            }

            if (
                sellingPriceField?.value === "" ||
                !Number.isFinite(sellingPrice) ||
                sellingPrice < purchasePrice
            ) {
                showError(
                    "Selling price must be greater than " +
                    "or equal to purchase price."
                );

                sellingPriceField?.focus();

                return false;
            }

            if (
                !Number.isFinite(discount) ||
                discount < 0 ||
                discount > packs * purchasePrice
            ) {
                showError(
                    "Discount must be between zero " +
                    "and the medicine's gross amount."
                );

                discountField?.focus();

                return false;
            }
        }

        return true;
    };

    /* ========================================================
       EVENT: ADD MEDICINE
       ======================================================== */

    addItemButton.addEventListener(
        "click",
        addMedicineRow
    );

    /* ========================================================
       EVENT: REMOVE MEDICINE
       ======================================================== */

    itemsBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(
            ".remove-item-btn"
        );

        if (!removeButton) {
            return;
        }

        const row = removeButton.closest(
            ".purchase-item-row"
        );

        if (!row) {
            return;
        }

        removeMedicineRow(row);
    });

    /* ========================================================
       EVENTS: LIVE TOTALS
       ======================================================== */

    itemsBody.addEventListener("input", () => {
        calculatePurchaseSummary();
    });

    itemsBody.addEventListener("change", () => {
        calculatePurchaseSummary();
    });

    /* ========================================================
       EVENT: FORM SUBMISSION
       ======================================================== */

    purchaseForm.addEventListener(
        "submit",
        (event) => {
            clearError();

            if (!validatePurchaseForm()) {
                event.preventDefault();
                return;
            }

            if (saveButton) {
                saveButton.disabled = true;

                saveButton.innerHTML = (
                    '<i class="fa-solid fa-spinner ' +
                    'fa-spin me-2"></i>Saving...'
                );
            }
        }
    );

    /* ========================================================
       INITIAL STATE
       ======================================================== */

    getRows().forEach((row) => {
        const deleteField = findField(
            row,
            "DELETE"
        );

        if (deleteField?.checked) {
            row.classList.add("is-removed");
        }
    });

    calculatePurchaseSummary();

});

// ============================================================
// PHASE 7.8.5 — PURCHASE STOCK RECEIVING FORM
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const page = document.getElementById("purchaseReceivingPage");

    if (!page) {
        return;
    }

    const form = document.getElementById("purchaseReceivingForm");
    const tbody = document.getElementById("receivingItemsBody");

    const addButton = document.getElementById("addReceivingBatch");
    const emptyTemplate = document.getElementById(
        "receivingEmptyRowTemplate"
    );

    const totalFormsInput = document.getElementById(
        "id_receiving-TOTAL_FORMS"
    );

    const batchCountElement = document.getElementById(
        "receivingBatchCount"
    );

    const totalPacksElement = document.getElementById(
        "receivingTotalPacks"
    );

    const medicineCountElement = document.getElementById(
        "receivingMedicineCount"
    );

    const errorElement = document.getElementById(
        "receivingClientError"
    );

    const submitButton = document.getElementById(
        "submitPurchaseReceiving"
    );

    const medicineDataContainer = document.getElementById(
        "receivingMedicineData"
    );

    if (
        !form ||
        !tbody ||
        !addButton ||
        !emptyTemplate ||
        !totalFormsInput ||
        !medicineDataContainer
    ) {
        console.error(
            "Purchase receiving form initialization failed."
        );
        return;
    }

    const MAX_FORMS = 100;

    // --------------------------------------------------------
    // LOAD PURCHASE ITEM DATA
    // --------------------------------------------------------

    const purchaseItems = new Map();

    medicineDataContainer
        .querySelectorAll("[data-item-id]")
        .forEach(function (element) {
            const itemId = element.dataset.itemId;

            purchaseItems.set(itemId, {
                medicineId: element.dataset.medicineId,
                name: element.dataset.medicineName,
                remaining: Number(element.dataset.remaining) || 0,
            });
        });

    // --------------------------------------------------------
    // HELPERS
    // --------------------------------------------------------

    function activeRows() {
        return Array.from(
            tbody.querySelectorAll(".receiving-item-row")
        ).filter(function (row) {
            const deleteInput = row.querySelector(
                'input[name$="-DELETE"]'
            );

            return !deleteInput || !deleteInput.checked;
        });
    }

    function getRowFields(row) {
        return {
            medicine: row.querySelector(
                'select[name$="-purchase_item"]'
            ),

            batch: row.querySelector(
                'input[name$="-batch_number"]'
            ),

            expiry: row.querySelector(
                'input[name$="-expiry_date"]'
            ),

            packs: row.querySelector(
                'input[name$="-received_packs"]'
            ),

            remainingLabel: row.querySelector(
                ".receiving-remaining-label"
            ),

            deleteInput: row.querySelector(
                'input[name$="-DELETE"]'
            ),
        };
    }

    function showError(message) {
        if (!errorElement) {
            return;
        }

        errorElement.textContent = message;
        errorElement.classList.remove("d-none");

        errorElement.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }

    function clearError() {
        if (!errorElement) {
            return;
        }

        errorElement.textContent = "";
        errorElement.classList.add("d-none");
    }

    function todayISO() {
        const now = new Date();

        const year = now.getFullYear();
        const month = String(
            now.getMonth() + 1
        ).padStart(2, "0");

        const day = String(
            now.getDate()
        ).padStart(2, "0");

        return `${year}-${month}-${day}`;
    }

    function initializeRow(row) {
        const fields = getRowFields(row);

        if (fields.expiry) {
            // An expiry date must be later than today.
            const today = todayISO();

            const tomorrow = new Date(
                `${today}T12:00:00`
            );

            tomorrow.setDate(
                tomorrow.getDate() + 1
            );

            const minYear = tomorrow.getFullYear();
            const minMonth = String(
                tomorrow.getMonth() + 1
            ).padStart(2, "0");

            const minDay = String(
                tomorrow.getDate()
            ).padStart(2, "0");

            fields.expiry.min = (
                `${minYear}-${minMonth}-${minDay}`
            );
        }

        if (fields.packs) {
            fields.packs.min = "1";
            fields.packs.step = "1";
        }

        updateRowRemaining(row);
    }

    function updateRowRemaining(row) {
        const fields = getRowFields(row);

        if (
            !fields.medicine ||
            !fields.remainingLabel
        ) {
            return;
        }

        const selectedItem = purchaseItems.get(
            fields.medicine.value
        );

        if (!selectedItem) {
            fields.remainingLabel.textContent = (
                "Select medicine"
            );

            return;
        }

        fields.remainingLabel.textContent = (
            `${selectedItem.remaining} pack(s) available`
        );

        if (fields.packs) {
            fields.packs.max = String(
                selectedItem.remaining
            );
        }
    }

    // --------------------------------------------------------
    // LIVE SUMMARY
    // --------------------------------------------------------

    function updateReceivingSummary() {
        const rows = activeRows();

        let totalPacks = 0;
        let batchCount = 0;

        const selectedMedicines = new Set();

        rows.forEach(function (row) {
            const fields = getRowFields(row);

            if (
                !fields.medicine ||
                !fields.medicine.value
            ) {
                return;
            }

            batchCount += 1;

            selectedMedicines.add(
                fields.medicine.value
            );

            const packs = Number(
                fields.packs ? fields.packs.value : 0
            );

            if (
                Number.isInteger(packs) &&
                packs > 0
            ) {
                totalPacks += packs;
            }

            updateRowRemaining(row);
        });

        if (batchCountElement) {
            batchCountElement.textContent = String(
                batchCount
            );
        }

        if (totalPacksElement) {
            totalPacksElement.textContent = String(
                totalPacks
            );
        }

        if (medicineCountElement) {
            medicineCountElement.textContent = String(
                selectedMedicines.size
            );
        }
    }

    // --------------------------------------------------------
    // ADD BATCH ROW
    // --------------------------------------------------------

    function addReceivingRow() {
        clearError();

        const totalForms = Number(
            totalFormsInput.value
        );

        if (
            !Number.isInteger(totalForms) ||
            totalForms < 0
        ) {
            showError(
                "Invalid formset state. Refresh the page."
            );
            return;
        }

        if (totalForms >= MAX_FORMS) {
            showError(
                "Maximum 100 receiving rows are allowed."
            );
            return;
        }

        const newIndex = totalForms;

        const html = emptyTemplate.innerHTML.replace(
            /__prefix__/g,
            String(newIndex)
        );

        const temporaryBody = document.createElement(
            "tbody"
        );

        temporaryBody.innerHTML = html.trim();

        const newRow = temporaryBody.querySelector(
            ".receiving-item-row"
        );

        if (!newRow) {
            showError(
                "Unable to add a receiving batch row."
            );
            return;
        }

        tbody.appendChild(newRow);

        totalFormsInput.value = String(
            totalForms + 1
        );

        initializeRow(newRow);
        updateReceivingSummary();

        const medicineSelect = newRow.querySelector(
            'select[name$="-purchase_item"]'
        );

        if (medicineSelect) {
            medicineSelect.focus();
        }
    }

    // --------------------------------------------------------
    // REMOVE BATCH ROW
    // --------------------------------------------------------

    function removeReceivingRow(row) {
        clearError();

        const fields = getRowFields(row);

        if (fields.deleteInput) {
            // Django formsets use DELETE markers rather
            // than removing indexed forms from POST.
            fields.deleteInput.checked = true;
            row.classList.add("d-none");
        } else {
            row.remove();
        }

        updateReceivingSummary();
    }

    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    function validateReceivingRows() {
        const rows = activeRows();

        if (!rows.length) {
            return "Add at least one receiving batch.";
        }

        const totalByItem = new Map();
        const seenBatches = new Set();

        let validRowCount = 0;

        for (const row of rows) {
            const fields = getRowFields(row);

            if (
                !fields.medicine ||
                !fields.batch ||
                !fields.expiry ||
                !fields.packs
            ) {
                return (
                    "The receiving form contains an invalid row."
                );
            }

            const itemId = fields.medicine.value;
            const batch = fields.batch.value.trim();
            const expiry = fields.expiry.value;
            const packs = Number(fields.packs.value);

            const isCompletelyEmpty = (
                !itemId &&
                !batch &&
                !expiry &&
                !fields.packs.value
            );

            // A blank extra form is ignored by Django.
            if (isCompletelyEmpty) {
                continue;
            }

            validRowCount += 1;

            if (!itemId || !purchaseItems.has(itemId)) {
                return (
                    "Select a valid medicine in every filled row."
                );
            }

            if (!batch) {
                return (
                    "Enter a batch number for every medicine."
                );
            }

            if (batch.length > 100) {
                return (
                    "Batch numbers cannot exceed 100 characters."
                );
            }

            if (!expiry || expiry <= todayISO()) {
                return (
                    "Every batch needs a future expiry date."
                );
            }

            if (
                !Number.isSafeInteger(packs) ||
                packs < 1
            ) {
                return (
                    "Received packs must be positive whole numbers."
                );
            }

            const item = purchaseItems.get(itemId);

            // Batch uniqueness is per medicine, not
            // per purchase-item row.
            const batchKey = (
                `${item.medicineId}::${batch}`
            );

            if (seenBatches.has(batchKey)) {
                return (
                    `Duplicate batch "${batch}" for ` +
                    `${item.name}.`
                );
            }

            seenBatches.add(batchKey);

            totalByItem.set(
                itemId,
                (totalByItem.get(itemId) || 0) + packs
            );
        }

        if (validRowCount === 0) {
            return (
                "Select at least one medicine and enter "
                + "its receiving details."
            );
        }

        for (const [itemId, receivedPacks] of totalByItem) {
            const item = purchaseItems.get(itemId);

            if (receivedPacks > item.remaining) {
                return (
                    `${item.name}: only ` +
                    `${item.remaining} pack(s) remain, ` +
                    `but ${receivedPacks} pack(s) ` +
                    "were entered."
                );
            }
        }

        return null;
    }

    // --------------------------------------------------------
    // EVENTS
    // --------------------------------------------------------

    addButton.addEventListener(
        "click",
        addReceivingRow
    );

    tbody.addEventListener("click", function (event) {
        const removeButton = event.target.closest(
            ".remove-receiving-row"
        );

        if (!removeButton) {
            return;
        }

        const row = removeButton.closest(
            ".receiving-item-row"
        );

        if (row) {
            removeReceivingRow(row);
        }
    });

    tbody.addEventListener("change", function (event) {
        const row = event.target.closest(
            ".receiving-item-row"
        );

        if (!row) {
            return;
        }

        clearError();
        updateRowRemaining(row);
        updateReceivingSummary();
    });

    tbody.addEventListener("input", function (event) {
        if (
            !event.target.closest(
                ".receiving-item-row"
            )
        ) {
            return;
        }

        clearError();
        updateReceivingSummary();
    });

    form.addEventListener("submit", function (event) {
        clearError();

        const error = validateReceivingRows();

        if (error) {
            event.preventDefault();
            showError(error);
            return;
        }

        // Prevent accidental double-click submissions.
        // Do not disable the submit button until the
        // form data has been captured by the browser.
        if (submitButton) {
            submitButton.classList.add("disabled");
            submitButton.setAttribute(
                "aria-disabled",
                "true"
            );
        }
    });

    // --------------------------------------------------------
    // INITIALIZE EXISTING ROWS
    // --------------------------------------------------------

    tbody.querySelectorAll(
        ".receiving-item-row"
    ).forEach(function (row) {
        initializeRow(row);
    });

    updateReceivingSummary();
});

// ============================================================
// PURCHASE MANAGEMENT — 200ms AJAX LIVE SEARCH AND PAGINATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    // Separate initializer: the earlier POS handler returns early on
    // non-POS pages, so Purchase search must not be nested inside it.
    const form = document.getElementById("purchase-filter-form");
    const searchInput = document.getElementById("purchase-search");
    const statusSelect = document.getElementById("purchase-status");
    const resultsContainer = document.getElementById("purchase-results");
    const feedback = document.getElementById("purchase-search-feedback");

    if (!form || !searchInput || !statusSelect || !resultsContainer || !feedback) {
        return;
    }

    const DEBOUNCE_MS = 200;
    let debounceTimer = null;
    let activeController = null;
    let sequence = 0;

    function setFeedback(message, isError = false) {
        feedback.textContent = message;
        feedback.hidden = !message;
        feedback.classList.toggle("text-danger", isError);
        feedback.classList.toggle("text-muted", !isError);
    }

    function setLoading(loading) {
        resultsContainer.setAttribute("aria-busy", String(loading));
        resultsContainer.style.opacity = loading ? "0.6" : "1";
    }

    function buildUrl(page = 1) {
        const url = new URL(form.action || window.location.href, window.location.origin);
        // Preserve unrelated query parameters without retaining stale filters.
        const currentParams = new URLSearchParams(window.location.search);
        for (const [key, value] of currentParams) {
            if (!["q", "status", "page"].includes(key)) {
                url.searchParams.set(key, value);
            }
        }
        url.searchParams.delete("q");
        url.searchParams.delete("status");
        url.searchParams.delete("page");

        const query = searchInput.value.trim();
        const status = statusSelect.value;
        if (query) url.searchParams.set("q", query);
        if (status) url.searchParams.set("status", status);
        if (page > 1) url.searchParams.set("page", String(page));
        return url;
    }

    function cancelPending() {
        if (debounceTimer !== null) {
            clearTimeout(debounceTimer);
            debounceTimer = null;
        }
        // Invalidate even if the response arrives before abort completes.
        sequence++;
        if (activeController) {
            activeController.abort();
            activeController = null;
        }
        setLoading(false);
    }

    async function loadPurchases(url, historyMode = "replace") {
        cancelPending();
        const controller = new AbortController();
        activeController = controller;
        const mySequence = ++sequence;
        setLoading(true);
        setFeedback("Searching purchase orders...");

        try {
            const response = await fetch(url.toString(), {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                credentials: "same-origin",
                signal: controller.signal
            });

            if (!response.ok) {
                throw new Error(`Request failed (${response.status})`);
            }
            if (!(response.headers.get("content-type") || "").includes("application/json")) {
                throw new Error("Unexpected response. Please check your login session.");
            }

            const data = await response.json();
            if (mySequence !== sequence) return;
            if (typeof data.html !== "string") {
                throw new Error("Invalid purchase results returned by the server.");
            }

            resultsContainer.innerHTML = data.html;
            if (historyMode === "push") {
                window.history.pushState(null, "", url.toString());
            } else if (historyMode === "replace") {
                window.history.replaceState(null, "", url.toString());
            }
            setFeedback("");
        } catch (error) {
            if (error.name === "AbortError" || mySequence !== sequence) return;
            console.error("Purchase AJAX search failed:", error);
            setFeedback("Unable to load purchases. Please retry.", true);
        } finally {
            if (mySequence === sequence) {
                setLoading(false);
                activeController = null;
            }
        }
    }

    // Typing: wait 200ms after the last keystroke, then fetch page 1.
    searchInput.addEventListener("input", () => {
        cancelPending();
        setFeedback("");
        debounceTimer = setTimeout(() => {
            debounceTimer = null;
            loadPurchases(buildUrl(1));
        }, DEBOUNCE_MS);
    });

    // Status filter changes immediately, without waiting 200ms.
    statusSelect.addEventListener("change", () => {
        loadPurchases(buildUrl(1));
    });

    // Search button and Enter key still work, without reloading.
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        loadPurchases(buildUrl(1));
    });

    // Pagination links and Clear Filters work after each DOM replacement.
    resultsContainer.addEventListener("click", (event) => {
        const link = event.target.closest(
            ".purchase-pagination a.page-link, a.purchase-clear-filters"
        );
        if (!link || event.defaultPrevented) return;
        if (event.button !== 0 || event.ctrlKey || event.metaKey ||
            event.shiftKey || event.altKey) return;
        if (link.target && link.target !== "_self") return;

        event.preventDefault();
        const url = new URL(link.href, window.location.href);
        searchInput.value = url.searchParams.get("q") || "";
        statusSelect.value = url.searchParams.get("status") || "";
        loadPurchases(url, "push");
    });

    window.addEventListener("popstate", () => {
        const url = new URL(window.location.href);
        searchInput.value = url.searchParams.get("q") || "";
        const nextStatus = url.searchParams.get("status") || "";
        statusSelect.value = Array.from(statusSelect.options).some(
            (option) => option.value === nextStatus
        ) ? nextStatus : "";
        loadPurchases(url, "none");
    });
});

/* ============================================================
   CUSTOMER MANAGEMENT
   AJAX LIVE SEARCH — 200ms
   FILTERS + PAGINATION + BROWSER HISTORY
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const form = document.getElementById(
        "customer-filter-form"
    );

    const searchInput = document.getElementById(
        "customer-search"
    );

    const statusSelect = document.getElementById(
        "customer-status"
    );

    const typeSelect = document.getElementById(
        "customer-type"
    );

    const resultsContainer = document.getElementById(
        "customer-results"
    );

    const feedback = document.getElementById(
        "customer-search-feedback"
    );

    if (
        !form ||
        !searchInput ||
        !statusSelect ||
        !typeSelect ||
        !resultsContainer ||
        !feedback
    ) {
        return;
    }

    const DELAY = 200;

    let timer = null;
    let controller = null;
    let sequence = 0;

    function showFeedback(message, error = false) {
        feedback.textContent = message;
        feedback.hidden = !message;

        feedback.classList.toggle(
            "text-danger",
            error
        );

        feedback.classList.toggle(
            "text-muted",
            !error
        );
    }

    function setLoading(loading) {
        resultsContainer.setAttribute(
            "aria-busy",
            String(loading)
        );

        resultsContainer.style.opacity = loading
            ? "0.6"
            : "1";
    }

    function buildUrl(page = 1) {
        const url = new URL(
            form.action || window.location.href,
            window.location.origin
        );

        url.searchParams.delete("q");
        url.searchParams.delete("status");
        url.searchParams.delete("type");
        url.searchParams.delete("page");

        const query = searchInput.value.trim();

        if (query) {
            url.searchParams.set("q", query);
        }

        if (statusSelect.value) {
            url.searchParams.set(
                "status",
                statusSelect.value
            );
        }

        if (typeSelect.value) {
            url.searchParams.set(
                "type",
                typeSelect.value
            );
        }

        if (page > 1) {
            url.searchParams.set(
                "page",
                String(page)
            );
        }

        return url;
    }

    function cancelPrevious() {
        if (timer !== null) {
            clearTimeout(timer);
            timer = null;
        }

        sequence++;

        if (controller) {
            controller.abort();
            controller = null;
        }
    }

    async function loadCustomers(
        url,
        historyMode = "replace"
    ) {
        cancelPrevious();

        const currentController = new AbortController();
        controller = currentController;

        const currentSequence = ++sequence;

        setLoading(true);
        showFeedback("Searching customers...");

        try {
            const response = await fetch(
                url.toString(),
                {
                    method: "GET",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    },
                    credentials: "same-origin",
                    signal: currentController.signal
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }

            const contentType =
                response.headers.get("content-type") || "";

            if (!contentType.includes("application/json")) {
                throw new Error(
                    "Unexpected server response."
                );
            }

            const data = await response.json();

            if (currentSequence !== sequence) {
                return;
            }

            if (typeof data.html !== "string") {
                throw new Error(
                    "Invalid customer search response."
                );
            }

            resultsContainer.innerHTML = data.html;

            if (historyMode === "push") {
                window.history.pushState(
                    null,
                    "",
                    url.toString()
                );
            } else if (historyMode === "replace") {
                window.history.replaceState(
                    null,
                    "",
                    url.toString()
                );
            }

            showFeedback("");

        } catch (error) {
            if (
                error.name === "AbortError" ||
                currentSequence !== sequence
            ) {
                return;
            }

            console.error(
                "Customer search failed:",
                error
            );

            showFeedback(
                "Unable to load customers. Please retry.",
                true
            );

        } finally {
            if (currentSequence === sequence) {
                controller = null;
                setLoading(false);
            }
        }
    }

    // 200ms debounce
    searchInput.addEventListener("input", () => {
        cancelPrevious();

        setLoading(false);
        showFeedback("");

        timer = setTimeout(() => {
            timer = null;
            loadCustomers(buildUrl(1));
        }, DELAY);
    });

    // Immediate filtering
    statusSelect.addEventListener("change", () => {
        loadCustomers(buildUrl(1));
    });

    typeSelect.addEventListener("change", () => {
        loadCustomers(buildUrl(1));
    });

    // Search button / Enter
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        loadCustomers(buildUrl(1));
    });

    // AJAX pagination
    resultsContainer.addEventListener("click", (event) => {
        const link = event.target.closest(
            ".customer-pagination a.page-link"
        );

        if (!link) {
            return;
        }

        if (
            event.button !== 0 ||
            event.ctrlKey ||
            event.metaKey ||
            event.shiftKey ||
            event.altKey
        ) {
            return;
        }

        event.preventDefault();

        const url = new URL(
            link.href,
            window.location.href
        );

        loadCustomers(url, "push");
    });

    // Browser Back / Forward
    window.addEventListener("popstate", () => {
        const url = new URL(
            window.location.href
        );

        searchInput.value =
            url.searchParams.get("q") || "";

        const status =
            url.searchParams.get("status") || "";

        statusSelect.value = (
            status === "active" ||
            status === "inactive"
        ) ? status : "";

        const type =
            url.searchParams.get("type") || "";

        const validType = Array.from(
            typeSelect.options
        ).some(option => option.value === type);

        typeSelect.value = validType ? type : "";

        loadCustomers(url, "none");
    });
});

/* ============================================================
   PHASE 8.2 — POS CUSTOMER SELECTION
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const picker = document.getElementById("posCustomerPicker");

    if (!picker) return;

    const search = document.getElementById("posCustomerSearch");
    const results = document.getElementById("posCustomerResults");
    const selected = document.getElementById("posSelectedCustomer");
    const selectedId = document.getElementById("posSelectedCustomerId");
    const clearButton = document.getElementById("posCustomerClear");

    if (!search || !results || !selected || !selectedId || !clearButton) {
        return;
    }

    const searchUrl = picker.dataset.searchUrl;

    let timer = null;
    let controller = null;
    let requestId = 0;

    function cancelPending() {
        clearTimeout(timer);
        requestId++;

        if (controller) {
            controller.abort();
            controller = null;
        }
    }

    function clearSelection(clearSearch = true) {
        selectedId.value = "";
        selected.textContent = "";
        selected.hidden = true;
        results.replaceChildren();

        if (clearSearch) {
            search.value = "";
        }

        picker.dispatchEvent(new CustomEvent(
            "pos:customer-changed",
            {
                bubbles: true,
                detail: { customer: null }
            }
        ));
    }

    function chooseCustomer(customer) {
        cancelPending();

        selectedId.value = String(customer.id);
        search.value = customer.name;

        results.replaceChildren();

        selected.textContent =
            `${customer.code} — ${customer.name}` +
            (customer.phone ? ` | ${customer.phone}` : "");

        selected.hidden = false;

        picker.dispatchEvent(new CustomEvent(
            "pos:customer-changed",
            {
                bubbles: true,
                detail: { customer }
            }
        ));
    }

    function showMessage(message) {
        const item = document.createElement("div");
        item.className = "list-group-item text-muted small";
        item.textContent = message;
        results.replaceChildren(item);
    }

    async function findCustomers(query) {
        cancelPending();

        const currentId = ++requestId;
        const currentController = new AbortController();
        controller = currentController;

        showMessage("Searching...");

        try {
            const url = new URL(searchUrl, window.location.origin);
            url.searchParams.set("q", query);

            const response = await fetch(url, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                signal: currentController.signal
            });

            if (!response.ok) {
                throw new Error("Customer search failed");
            }

            const data = await response.json();

            if (currentId !== requestId) return;

            results.replaceChildren();

            if (!Array.isArray(data.results) || !data.results.length) {
                showMessage("No matching customers found.");
                return;
            }

            data.results.forEach(customer => {
                const button = document.createElement("button");

                button.type = "button";
                button.className =
                    "list-group-item list-group-item-action text-start";

                const name = document.createElement("div");
                name.className = "fw-semibold";
                name.textContent = customer.name;

                const details = document.createElement("small");
                details.className = "text-muted d-block";

                details.textContent = [
                    customer.code,
                    customer.phone,
                    customer.customer_type
                ].filter(Boolean).join(" | ");

                button.append(name, details);

                button.addEventListener("click", () => {
                    chooseCustomer(customer);
                });

                results.appendChild(button);
            });

        } catch (error) {
            if (error.name !== "AbortError" && currentId === requestId) {
                showMessage("Unable to search customers.");
                console.error(error);
            }
        } finally {
            if (currentId === requestId) {
                controller = null;
            }
        }
    }

    search.addEventListener("input", () => {
        cancelPending();
        clearSelection(false);

        const query = search.value.trim();

        if (query.length < 2) {
            results.replaceChildren();
            return;
        }

        timer = setTimeout(() => {
            findCustomers(query);
        }, 200);
    });

    clearButton.addEventListener("click", () => {
        cancelPending();
        clearSelection();
        search.focus();
    });
});

/* ============================================================
   POS CUSTOMER DETAILS AUTO-FILL
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const picker = document.getElementById(
        "posCustomerPicker"
    );

    const nameInput = document.getElementById(
        "posCustomerName"
    );

    const phoneInput = document.getElementById(
        "posCustomerPhone"
    );

    if (!picker || !nameInput || !phoneInput) {
        return;
    }

    picker.addEventListener(
        "pos:customer-changed",
        (event) => {
            const customer = event.detail?.customer;

            if (customer) {
                nameInput.value = customer.name || "";
                phoneInput.value = customer.phone || "";

                nameInput.readOnly = true;
                phoneInput.readOnly = true;
            } else {
                nameInput.value = "";
                phoneInput.value = "";

                nameInput.readOnly = false;
                phoneInput.readOnly = false;
            }

            nameInput.dispatchEvent(
                new Event("input", { bubbles: true })
            );

            phoneInput.dispatchEvent(
                new Event("input", { bubbles: true })
            );
        }
    );
});
