
"use strict";

/* ===========================================================
   PHARMACARE — REPORTS DASHBOARD
   =========================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("reportsDashboard");

    if (!root) return;

    const form = document.getElementById("reportsFilterForm");
    const dateFrom = document.getElementById("reportDateFrom");
    const dateTo = document.getElementById("reportDateTo");
    const branch = document.getElementById("reportBranch");

    const loading = document.getElementById("reportsLoading");
    const errorBox = document.getElementById("reportsError");
    const content = document.getElementById("reportsContent");

    const refreshBtn = document.getElementById("refreshReports");

    let salesChart = null;
    let paymentChart = null;
    let activeController = null;
    let requestSequence = 0;

    const moneyFormatter = new Intl.NumberFormat("en-PK", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    const numberFormatter = new Intl.NumberFormat("en-PK");

    const COLORS = [
        "#0f766e",
        "#14b8a6",
        "#2563eb",
        "#f59e0b",
        "#8b5cf6",
        "#ef4444"
    ];

    function money(value) {
        const amount = Number(value ?? 0);
        return `Rs. ${moneyFormatter.format(
            Number.isFinite(amount) ? amount : 0
        )}`;
    }

    function number(value) {
        return numberFormatter.format(Number(value ?? 0));
    }

    function setText(id, value) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = value;
        }
    }

    function localISODate(date) {
        const year = date.getFullYear();
        const month = String(
            date.getMonth() + 1
        ).padStart(2, "0");

        const day = String(
            date.getDate()
        ).padStart(2, "0");

        return `${year}-${month}-${day}`;
    }

    function setQuickRange(range) {
        const end = new Date();
        const start = new Date(end);

        if (range === "today") {
            // Start and end both today.
        } else {
            const days = Number(range) || 30;
            start.setDate(
                start.getDate() - (days - 1)
            );
        }

        dateFrom.value = localISODate(start);
        dateTo.value = localISODate(end);

        loadReports();
    }

    function initializeDates() {
        const params = new URLSearchParams(
            window.location.search
        );

        const today = new Date();
        const start = new Date(today);

        start.setDate(start.getDate() - 29);

        dateFrom.value = (
            params.get("date_from")
            || localISODate(start)
        );

        dateTo.value = (
            params.get("date_to")
            || localISODate(today)
        );

        if (branch && params.has("branch")) {
            branch.value = params.get("branch");
        }
    }

    function getFilters() {
        const params = new URLSearchParams();

        params.set("date_from", dateFrom.value);
        params.set("date_to", dateTo.value);

        if (branch && branch.value) {
            params.set("branch", branch.value);
        }

        return params;
    }

    function validateFilters() {
        if (!dateFrom.value || !dateTo.value) {
            throw new Error(
                "Please select both report dates."
            );
        }

        if (dateFrom.value > dateTo.value) {
            throw new Error(
                "Start date cannot be after end date."
            );
        }

        const start = new Date(
            dateFrom.value + "T00:00:00"
        );

        const end = new Date(
            dateTo.value + "T00:00:00"
        );

        const days = Math.round(
            (end - start) / 86400000
        );

        if (days > 365) {
            throw new Error(
                "Maximum report range is 366 days."
            );
        }
    }

    function toggleLoading(isLoading) {
        loading.classList.toggle(
            "d-none",
            !isLoading
        );

        refreshBtn.disabled = isLoading;

        if (isLoading) {
            content.setAttribute(
                "aria-busy",
                "true"
            );
        } else {
            content.removeAttribute("aria-busy");
        }
    }

    function clearError() {
        errorBox.classList.add("d-none");
        errorBox.textContent = "";
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    function updateExportLinks() {
        const query = getFilters().toString();

        const mapping = [
            ["exportSales", "salesExport"],
            ["exportPurchases", "purchasesExport"],
            ["exportInventory", "inventoryExport"]
        ];

        mapping.forEach(([id, attribute]) => {
            const element = document.getElementById(id);
            const base = root.dataset[attribute];

            if (element && base) {
                element.href = `${base}?${query}`;
            }
        });

        const reportLinks = [
            "viewSalesReport",
            "viewPurchasesReport",
            "viewInventoryReport",
            "viewProfitReport"
        ];

        reportLinks.forEach(id => {
            const link = document.getElementById(id);

            if (!link) return;

            const url = new URL(
                link.href,
                window.location.origin
            );

            url.search = query;

            link.href = url.toString();
        });
    }

    function updateKPIs(data) {
        const sales = data.sales || {};
        const purchases = data.purchases || {};
        const inventory = data.inventory || {};

        setText("kpiRevenue", money(sales.revenue));
        setText("kpiCollected", money(sales.collected));
        setText(
            "kpiOutstanding",
            money(sales.outstanding)
        );

        setText(
            "kpiPurchases",
            money(purchases.ordered_value)
        );

        setText(
            "kpiSalesCount",
            number(sales.sale_count)
        );

        setText(
            "kpiAverageSale",
            money(sales.average_sale)
        );

        setText(
            "kpiStockValue",
            money(inventory.estimated_cost_value)
        );

        setText(
            "kpiExpiring",
            number(inventory.expiring_30_days)
        );

        setText(
            "statBatches",
            number(inventory.batch_count)
        );

        setText(
            "statStockUnits",
            number(inventory.units_in_stock)
        );

        setText(
            "statOutOfStock",
            number(inventory.out_of_stock_batches)
        );

        setText(
            "statExpired",
            number(inventory.expired_batches)
        );
    }

    function addEmptyTableRow(tbody, columns, message) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = columns;
        cell.className = "text-center text-muted py-4";
        cell.textContent = message;

        row.appendChild(cell);
        tbody.appendChild(row);
    }

    function renderTable(tbodyId, rows, mapper) {
        const tbody = document.getElementById(tbodyId);

        if (!tbody) return;

        tbody.replaceChildren();

        if (!Array.isArray(rows) || rows.length === 0) {
            addEmptyTableRow(
                tbody,
                3,
                "No records found for selected filters."
            );
            return;
        }

        rows.forEach(item => {
            const row = document.createElement("tr");

            mapper(item).forEach((value, index) => {
                const cell = document.createElement("td");

                if (index > 0) {
                    cell.className = "text-end";
                }

                cell.textContent = String(value ?? "");
                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });
    }

    function updateTables(data) {
        renderTable(
            "topMedicinesBody",
            data.top_medicines,
            item => [
                item.medicine_name || "Unknown Medicine",
                number(item.sold_units),
                money(item.line_revenue)
            ]
        );

        renderTable(
            "topSuppliersBody",
            data.top_suppliers,
            item => [
                item.supplier__name || "Unknown Supplier",
                number(item.order_count),
                money(item.ordered_value)
            ]
        );
    }

    function destroyCharts() {
        if (salesChart) {
            salesChart.destroy();
            salesChart = null;
        }

        if (paymentChart) {
            paymentChart.destroy();
            paymentChart = null;
        }
    }

    function showChartFallback(id, message) {
        const element = document.getElementById(id);

        if (!element) return;

        element.textContent = message;
        element.classList.remove("d-none");
    }

    function hideChartFallback(id) {
        const element = document.getElementById(id);

        if (!element) return;

        element.classList.add("d-none");
    }

    function renderSalesChart(dailySales) {
        const canvas = document.getElementById(
            "salesTrendChart"
        );

        const rows = Array.isArray(dailySales)
            ? dailySales
            : [];

        const hasRevenue = rows.some(
            item => Number(item.revenue || 0) > 0
        );

        if (!hasRevenue) {
            showChartFallback(
                "salesChartEmpty",
                "No completed sales in this period."
            );
            return;
        }

        hideChartFallback("salesChartEmpty");

        salesChart = new Chart(canvas, {
            type: "line",

            data: {
                labels: rows.map(item => item.day),

                datasets: [
                    {
                        label: "Revenue",
                        data: rows.map(
                            item => Number(item.revenue || 0)
                        ),
                        borderColor: "#0f766e",
                        backgroundColor: "rgba(15,118,110,.10)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: rows.length > 45 ? 0 : 3,
                        borderWidth: 2
                    },
                    {
                        label: "Collected",
                        data: rows.map(
                            item => Number(item.collected || 0)
                        ),
                        borderColor: "#2563eb",
                        backgroundColor: "#2563eb",
                        tension: 0.3,
                        pointRadius: rows.length > 45 ? 0 : 3,
                        borderWidth: 2
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: "bottom"
                    },
                    tooltip: {
                        callbacks: {
                            label: context =>
                                `${context.dataset.label}: ${money(
                                    context.parsed.y
                                )}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value =>
                                Number(value).toLocaleString("en-PK")
                        }
                    }
                }
            }
        });
    }

    function renderPaymentChart(methods) {
        const canvas = document.getElementById(
            "paymentMethodChart"
        );

        const rows = Array.isArray(methods)
            ? methods.filter(
                item => Number(item.revenue || 0) > 0
            )
            : [];

        if (rows.length === 0) {
            showChartFallback(
                "paymentChartEmpty",
                "No checkout payment data."
            );
            return;
        }

        hideChartFallback("paymentChartEmpty");

        const labels = {
            cash: "Cash",
            card: "Card",
            bank_transfer: "Bank Transfer",
            mobile_wallet: "Mobile Wallet",
            credit: "Credit",
            mixed: "Mixed"
        };

        paymentChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: rows.map(
                    item => labels[item.payment_method]
                        || item.payment_method
                ),
                datasets: [{
                    data: rows.map(
                        item => Number(item.revenue)
                    ),
                    backgroundColor: COLORS,
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        position: "bottom"
                    },
                    tooltip: {
                        callbacks: {
                            label: context =>
                                `${context.label}: ${money(
                                    context.parsed
                                )}`
                        }
                    }
                }
            }
        });
    }

    function updateCharts(data) {
        destroyCharts();

        if (typeof Chart === "undefined") {
            showChartFallback(
                "salesChartEmpty",
                "Chart library unavailable. Tables and KPIs remain available."
            );

            showChartFallback(
                "paymentChartEmpty",
                "Chart library unavailable."
            );

            return;
        }

        renderSalesChart(data.daily_sales);

        // Payment method data comes from the
        // dedicated Sales Report endpoint.
        // Loaded separately below.
    }

    async function updatePaymentChart(query, signal) {
        const url = (
            root.dataset.salesUrl
            + "?"
            + query
        );

        if (!root.dataset.salesUrl) return;

        const response = await fetch(url, {
            signal,
            credentials: "same-origin",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Payment report request failed (${response.status}).`
            );
        }

        const payload = await response.json();

        if (!payload.success) {
            throw new Error(
                payload.error || "Payment report unavailable."
            );
        }

        if (paymentChart) {
            paymentChart.destroy();
            paymentChart = null;
        }

        if (typeof Chart !== "undefined") {
            renderPaymentChart(
                payload.data.payment_methods
            );
        }
    }

    async function loadReports() {
        const sequence = ++requestSequence;

        if (activeController) {
            activeController.abort();
        }

        activeController = new AbortController();
        const signal = activeController.signal;

        clearError();

        try {
            validateFilters();

            const query = getFilters().toString();

            toggleLoading(true);

            const url = (
                root.dataset.dashboardUrl
                + "?"
                + query
            );

            const response = await fetch(url, {
                signal,
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                }
            });

            if (!response.ok) {
                let message = (
                    `Report request failed (${response.status}).`
                );

                if (response.status === 403) {
                    message = (
                        "You do not have permission to view "
                        + "these reports."
                    );
                }

                try {
                    const errorData = await response.json();

                    if (errorData.error) {
                        message = errorData.error;
                    }
                } catch (_) {
                    // Keep the original status message.
                }

                throw new Error(message);
            }

            const payload = await response.json();

            if (!payload.success) {
                throw new Error(
                    payload.error || "Unable to load reports."
                );
            }

            if (sequence !== requestSequence) return;

            updateKPIs(payload.data);
            updateTables(payload.data);
            updateCharts(payload.data);

            await updatePaymentChart(query, signal);

            if (sequence !== requestSequence) return;

            updateExportLinks();

            const pageUrl = new URL(
                window.location.href
            );

            pageUrl.search = query;

            window.history.replaceState(
                null,
                "",
                pageUrl.toString()
            );

        } catch (error) {
            if (error.name === "AbortError") return;

            if (sequence === requestSequence) {
                showError(
                    error.message || "Unexpected error."
                );
            }

        } finally {
            if (sequence === requestSequence) {
                toggleLoading(false);
            }
        }
    }

    form.addEventListener("submit", event => {
        event.preventDefault();
        loadReports();
    });

    refreshBtn.addEventListener("click", loadReports);

    document.querySelectorAll(
        "[data-report-range]"
    ).forEach(button => {
        button.addEventListener("click", () => {
            setQuickRange(
                button.dataset.reportRange
            );
        });
    });

    initializeDates();
    updateExportLinks();
    loadReports();
});

"use strict";

/* ==========================================================
   PHARMACARE — DASHBOARD PDF EXPORT FILTERS
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const dashboard = document.getElementById(
        "reportsDashboard"
    );

    if (!dashboard) return;

    const dateFrom = document.getElementById(
        "reportDateFrom"
    );

    const dateTo = document.getElementById(
        "reportDateTo"
    );

    const branch = document.getElementById(
        "reportBranch"
    );

    const links = [
        "pdfSales",
        "pdfPurchases",
        "pdfInventory",
        "pdfProfit",
    ];

    links.forEach(id => {

        const link = document.getElementById(id);

        if (!link) return;

        const baseUrl = link.getAttribute("href");

        link.addEventListener("click", event => {

            const query = new URLSearchParams();

            if (dateFrom && dateTo) {

                if (
                    !dateFrom.value ||
                    !dateTo.value ||
                    dateFrom.value > dateTo.value
                ) {
                    event.preventDefault();

                    alert(
                        "Please select a valid date range."
                    );

                    return;
                }

                query.set(
                    "date_from",
                    dateFrom.value
                );

                query.set(
                    "date_to",
                    dateTo.value
                );
            }

            if (branch && branch.value) {
                query.set("branch", branch.value);
            }

            const url = new URL(
                baseUrl,
                window.location.origin
            );

            url.search = query.toString();

            link.href = url.toString();
        });
    });
});
