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
        let subtotal = 0;
        let tax = 0;

        cart.forEach((item) => {
            const price =
                getItemPrice(
                    item
                );

            const lineSubtotal =
                price *
                item.cart_quantity;

            const lineTax =
                lineSubtotal *
                item.tax_rate /
                100;

            subtotal +=
                lineSubtotal;

            tax +=
                lineTax;
        });

        subtotal =
            toMoney(
                subtotal
            );

        tax =
            toMoney(
                tax
            );

        const discount =
            toMoney(
                Math.max(
                    Number(
                        posDiscount
                            ?.value ||
                        0
                    ),
                    0
                )
            );

        const total =
            toMoney(
                Math.max(
                    subtotal +
                    tax -
                    discount,
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
                            ${
                                item.sale_type ===
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

                            ${
                                item.strength
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
                                ${
                                    item.sale_type ===
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

                                ${
                                    product.strength
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

                        <div class="${
                            canSellLoose
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
                                ${
                                    !canSellPack
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

                        ${
                            canSellLoose
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

                    ${
                        !canSellPack &&
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