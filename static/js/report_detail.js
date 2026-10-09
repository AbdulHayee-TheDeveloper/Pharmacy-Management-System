
"use strict";

/* ==========================================================
   PHARMACARE — DETAILED REPORT CONTROLLER
   Phase 9.8: Server-side pagination and search
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const root = document.getElementById("reportDetailPage");
    if (!root) return;

    const reportType = root.dataset.reportType;
    const summaryApiUrl = root.dataset.apiUrl;
    const rowsApiUrl = root.dataset.rowsUrl || "";
    const csvBaseUrl = root.dataset.exportUrl || "";

    const form = document.getElementById("detailReportFilters");
    const dateFrom = document.getElementById("detailDateFrom");
    const dateTo = document.getElementById("detailDateTo");
    const branch = document.getElementById("detailBranch");

    const loading = document.getElementById("detailLoading");
    const errorBox = document.getElementById("detailError");
    const content = document.getElementById("detailReportContent");

    const searchInput = document.getElementById(
        "detailTableSearch"
    );

    const tableHead = document.getElementById(
        "detailTableHead"
    );

    const tableBody = document.getElementById(
        "detailTableBody"
    );

    const rowCount = document.getElementById(
        "detailRowCount"
    );

    const pageInfo = document.getElementById(
        "detailPageInfo"
    );

    const prevButton = document.getElementById(
        "detailPrev"
    );

    const nextButton = document.getElementById(
        "detailNext"
    );

    const refreshButton = document.getElementById(
        "detailRefresh"
    );

    const csvButton = document.getElementById(
        "detailExport"
    );

    const pdfButton = document.getElementById(
        "detailExportPdf"
    );

    const pdfBaseUrl = pdfButton
        ? pdfButton.getAttribute("href").split("?")[0]
        : "";

    const moneyFormatter = new Intl.NumberFormat("en-PK", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    const countFormatter = new Intl.NumberFormat("en-PK");

    let currentPage = 1;
    let totalPages = 1;
    let currentColumns = [];
    let rowsController = null;
    let summaryController = null;
    let searchTimeout = null;
    let rowsRequestNumber = 0;

    function money(value) {
        const amount = Number(value ?? 0);

        return (
            "Rs. " +
            moneyFormatter.format(
                Number.isFinite(amount) ? amount : 0
            )
        );
    }

    function number(value) {
        const amount = Number(value ?? 0);
        return countFormatter.format(
            Number.isFinite(amount) ? amount : 0
        );
    }

    function text(value) {
        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return "—";
        }

        return String(value);
    }

    function formatDate(value) {
        if (!value) return "—";

        const parsed = new Date(value);

        if (Number.isNaN(parsed.getTime())) {
            return text(value);
        }

        return parsed.toLocaleDateString("en-PK", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        });
    }

    function todayISO(date) {
        const year = date.getFullYear();

        const month = String(
            date.getMonth() + 1
        ).padStart(2, "0");

        const day = String(
            date.getDate()
        ).padStart(2, "0");

        return `${year}-${month}-${day}`;
    }

    function setText(id, value) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = text(value);
        }
    }

    function setError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    function clearError() {
        errorBox.textContent = "";
        errorBox.classList.add("d-none");
    }

    function setLoading(active) {
        loading.classList.toggle("d-none", !active);
        refreshButton.disabled = active;
    }

    function setupFilters() {
        const query = new URLSearchParams(
            window.location.search
        );

        const today = new Date();
        const start = new Date(today);

        start.setDate(start.getDate() - 29);

        if (dateFrom) {
            dateFrom.value = (
                query.get("date_from") || todayISO(start)
            );
        }

        if (dateTo) {
            dateTo.value = (
                query.get("date_to") || todayISO(today)
            );
        }

        if (branch && query.has("branch")) {
            branch.value = query.get("branch");
        }

        if (searchInput && query.has("q")) {
            searchInput.value = query.get("q").slice(0, 100);
        }

        const requestedPage = Number(
            query.get("page") || 1
        );

        currentPage = (
            Number.isSafeInteger(requestedPage)
            && requestedPage > 0
        ) ? requestedPage : 1;
    }

    function validateDates() {
        if (!dateFrom || !dateTo) return;

        if (!dateFrom.value || !dateTo.value) {
            throw new Error("Both dates are required.");
        }

        if (dateFrom.value > dateTo.value) {
            throw new Error(
                "Start date cannot exceed end date."
            );
        }

        const start = new Date(
            dateFrom.value + "T00:00:00"
        );

        const end = new Date(
            dateTo.value + "T00:00:00"
        );

        if (
            Number.isNaN(start.getTime()) ||
            Number.isNaN(end.getTime())
        ) {
            throw new Error("Invalid date selection.");
        }

        if ((end - start) / 86400000 > 365) {
            throw new Error(
                "Maximum date range is 366 days."
            );
        }
    }

    function filterQuery() {
        const query = new URLSearchParams();

        if (dateFrom && dateTo) {
            query.set("date_from", dateFrom.value);
            query.set("date_to", dateTo.value);
        }

        if (branch && branch.value) {
            query.set("branch", branch.value);
        }

        return query;
    }

    function rowsQuery() {
        const query = filterQuery();

        query.set("page", String(currentPage));

        const search = searchInput.value.trim();

        if (search && reportType !== "profit") {
            query.set("q", search);
        }

        return query;
    }

    function updateDownloadLinks() {
        const query = filterQuery().toString();

        if (csvButton && csvBaseUrl) {
            csvButton.href = `${csvBaseUrl}?${query}`;
        }

        if (pdfButton && pdfBaseUrl) {
            pdfButton.href = `${pdfBaseUrl}?${query}`;
        }
    }

    function saveUrlState() {
        const url = new URL(window.location.href);
        const query = rowsQuery();

        if (reportType === "profit") {
            query.delete("page");
            query.delete("q");
        }

        url.search = query.toString();

        window.history.replaceState(
            null,
            "",
            url.toString()
        );
    }

    async function fetchJSON(url, signal) {
        const response = await fetch(url, {
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
            },
            signal,
        });

        if (!response.ok) {
            let message = `HTTP ${response.status}`;

            if (response.status === 403) {
                message = "Access denied.";
            }

            try {
                const payload = await response.json();

                if (payload.error) {
                    message = payload.error;
                }
            } catch (_) {
                // Keep original HTTP error.
            }

            throw new Error(message);
        }

        const payload = await response.json();

        if (!payload.success || !payload.data) {
            throw new Error(
                payload.error || "Invalid report response."
            );
        }

        return payload.data;
    }

    // ------------------------------------------------------
    // KPI CARDS
    // ------------------------------------------------------

    function renderKPIs(cards) {
        const container = document.getElementById(
            "detailKpiContainer"
        );

        container.replaceChildren();

        cards.forEach(card => {
            const column = document.createElement("div");
            column.className = "col-sm-6 col-xl-3";

            const panel = document.createElement("div");
            panel.className = "reports-kpi-card";

            const heading = document.createElement("div");
            heading.className = "reports-kpi-heading";
            heading.textContent = card.label;

            const value = document.createElement("div");
            value.className = "reports-kpi-value";
            value.textContent = card.value;

            const caption = document.createElement("div");
            caption.className = "reports-kpi-caption";
            caption.textContent = card.caption || "";

            panel.append(heading, value, caption);
            column.appendChild(panel);
            container.appendChild(column);
        });
    }

    // ------------------------------------------------------
    // TABLE HELPERS
    // ------------------------------------------------------

    function createCell(value, tag = "td") {
        const cell = document.createElement(tag);
        cell.textContent = text(value);
        return cell;
    }

    function createHeader(columns) {
        tableHead.replaceChildren();

        const row = document.createElement("tr");

        columns.forEach(column => {
            const heading = createCell(
                column.label,
                "th"
            );

            if (column.align === "end") {
                heading.classList.add("text-end");
            }

            row.appendChild(heading);
        });

        tableHead.appendChild(row);
    }

    function renderTableRows(rows) {
        tableBody.replaceChildren();

        if (!rows.length) {
            const row = document.createElement("tr");

            const cell = createCell(
                "No records found."
            );

            cell.colSpan = currentColumns.length;
            cell.className = "text-center text-muted py-4";

            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        rows.forEach(item => {
            const row = document.createElement("tr");

            currentColumns.forEach(column => {
                const cell = createCell(
                    column.value(item)
                );

                if (column.align === "end") {
                    cell.classList.add("text-end");
                }

                row.appendChild(cell);
            });

            tableBody.appendChild(row);
        });
    }

    function configureTable(title, subtitle, columns) {
        setText("detailMainTitle", title);
        setText("detailMainSubtitle", subtitle);

        currentColumns = columns;

        createHeader(columns);
    }

    function updatePagination(pagination) {
        currentPage = pagination.page;
        totalPages = pagination.total_pages;

        rowCount.textContent = (
            `${number(pagination.total_records)} ` +
            "matching record(s)"
        );

        pageInfo.textContent = (
            `Page ${currentPage} of ${totalPages}`
        );

        prevButton.disabled = (
            !pagination.has_previous
        );

        nextButton.disabled = (
            !pagination.has_next
        );
    }

    function renderSecondary(title, rows, columns) {
        const section = document.getElementById(
            "detailSecondarySection"
        );

        const head = document.getElementById(
            "detailSecondaryHead"
        );

        const body = document.getElementById(
            "detailSecondaryBody"
        );

        if (!rows || !rows.length) {
            section.classList.add("d-none");
            return;
        }

        section.classList.remove("d-none");

        setText("detailSecondaryTitle", title);

        head.replaceChildren();
        body.replaceChildren();

        const headerRow = document.createElement("tr");

        columns.forEach(column => {
            const cell = createCell(
                column.label,
                "th"
            );

            if (column.align === "end") {
                cell.classList.add("text-end");
            }

            headerRow.appendChild(cell);
        });

        head.appendChild(headerRow);

        rows.forEach(item => {
            const row = document.createElement("tr");

            columns.forEach(column => {
                const cell = createCell(
                    column.value(item)
                );

                if (column.align === "end") {
                    cell.classList.add("text-end");
                }

                row.appendChild(cell);
            });

            body.appendChild(row);
        });
    }

    function renderNotes(notes) {
        const container = document.getElementById(
            "detailReportNotes"
        );

        container.replaceChildren();

        Object.values(notes || {}).forEach(note => {
            const paragraph = document.createElement("p");

            paragraph.className = "mb-2";
            paragraph.textContent = text(note);

            container.appendChild(paragraph);
        });
    }

    // ------------------------------------------------------
    // SUMMARY RENDERERS
    // ------------------------------------------------------

    function renderSalesSummary(data) {
        const s = data.summary || {};

        renderKPIs([
            {
                label: "Sales Revenue",
                value: money(s.revenue),
            },
            {
                label: "Collected",
                value: money(s.collected),
            },
            {
                label: "Outstanding",
                value: money(s.outstanding),
            },
            {
                label: "Completed Sales",
                value: number(s.sale_count),
            },
            {
                label: "Average Sale",
                value: money(s.average_sale),
            },
            {
                label: "Discounts",
                value: money(s.discounts),
            },
        ]);

        renderSecondary(
            "Top Selling Medicines",
            data.top_medicines,
            [
                {
                    label: "Medicine",
                    value: row => row.medicine_name,
                },
                {
                    label: "Units",
                    align: "end",
                    value: row => number(row.sold_units),
                },
                {
                    label: "Revenue",
                    align: "end",
                    value: row => money(row.line_revenue),
                },
            ]
        );

        renderNotes(data.notes);
    }

    function renderPurchasesSummary(data) {
        const s = data.summary || {};

        renderKPIs([
            {
                label: "Purchase Orders",
                value: number(s.order_count),
            },
            {
                label: "Ordered Value",
                value: money(s.ordered_value),
            },
            {
                label: "Stock Receipts",
                value: number(s.receipt_count),
            },
            {
                label: "Received Packs",
                value: number(s.total_received_packs),
            },
            {
                label: "Received Cost",
                value: money(s.gross_received_cost),
            },
            {
                label: "Discounts",
                value: money(s.discounts),
            },
        ]);

        renderSecondary(
            "Top Suppliers",
            data.top_suppliers,
            [
                {
                    label: "Supplier",
                    value: row => row.supplier__name,
                },
                {
                    label: "Orders",
                    align: "end",
                    value: row => number(row.order_count),
                },
                {
                    label: "Value",
                    align: "end",
                    value: row => money(row.ordered_value),
                },
            ]
        );

        renderNotes(data.notes);
    }

    function renderInventorySummary(data) {
        const s = data.summary || {};

        renderKPIs([
            {
                label: "Cost Value",
                value: money(s.estimated_cost_value),
            },
            {
                label: "Retail Value",
                value: money(s.estimated_retail_value),
            },
            {
                label: "Stock Units",
                value: number(s.units_in_stock),
            },
            {
                label: "Total Batches",
                value: number(s.batch_count),
            },
            {
                label: "Expired",
                value: number(s.expired_batches),
            },
            {
                label: "Expiring Soon",
                value: number(s.expiring_30_days),
            },
            {
                label: "Out of Stock",
                value: number(s.out_of_stock_batches),
            },
            {
                label: "Inactive",
                value: number(s.inactive_batches),
            },
        ]);

        document.getElementById(
            "detailSecondarySection"
        ).classList.add("d-none");

        renderNotes(data.notes);
    }

    function renderProfitSummary(data) {
        const s = data.summary || {};

        renderKPIs([
            {
                label: "Revenue Including Tax",
                value: money(s.revenue_including_tax),
            },
            {
                label: "Net Sales",
                value: money(s.net_sales_excluding_tax),
            },
            {
                label: "Estimated COGS",
                value: money(s.estimated_cogs),
            },
            {
                label: "Estimated Gross Profit",
                value: money(s.estimated_gross_profit),
            },
            {
                label: "Estimated Margin",
                value: `${s.estimated_margin_percent || 0}%`,
            },
            {
                label: "Completed Sales",
                value: number(s.sale_count),
            },
        ]);

        setText(
            "profitWarningText",
            data.warning || (
                "Profit is estimated using current " +
                "batch purchase prices."
            )
        );

        document.getElementById(
            "detailSecondarySection"
        ).classList.add("d-none");

        renderNotes({
            accounting:
                "Historical purchase-cost snapshots " +
                "are not stored on SaleItem.",
        });

        searchInput.disabled = true;
        searchInput.placeholder = (
            "Search is not applicable to a summary report"
        );

        currentColumns = [
            {
                label: "Financial Metric",
                value: row => row.metric,
            },
            {
                label: "Estimated Value",
                align: "end",
                value: row => row.value,
            },
        ];

        configureTable(
            "Estimated Profit Calculation",
            "Provisional financial summary",
            currentColumns
        );

        renderTableRows([
            {
                metric: "Net Sales Excluding Tax",
                value: money(s.net_sales_excluding_tax),
            },
            {
                metric: "Less: Estimated COGS",
                value: money(s.estimated_cogs),
            },
            {
                metric: "Estimated Gross Profit",
                value: money(s.estimated_gross_profit),
            },
            {
                metric: "Estimated Gross Margin",
                value: `${s.estimated_margin_percent || 0}%`,
            },
        ]);

        rowCount.textContent = "4 summary rows";
        pageInfo.textContent = "Summary";

        prevButton.disabled = true;
        nextButton.disabled = true;
    }

    // ------------------------------------------------------
    // SERVER-SIDE TABLE CONFIGURATION
    // ------------------------------------------------------

    function setupColumns() {

        if (reportType === "sales") {
            configureTable(
                "Completed Invoices",
                "Search across all matching sales invoices",
                [
                    {
                        label: "Invoice",
                        value: row => row.invoice_number,
                    },
                    {
                        label: "Date",
                        value: row => formatDate(row.completed_at),
                    },
                    {
                        label: "Customer",
                        value: row => row.customer_name || "Walk-in",
                    },
                    {
                        label: "Branch",
                        value: row => row.branch__name,
                    },
                    {
                        label: "Amount",
                        align: "end",
                        value: row => money(row.total_amount),
                    },
                    {
                        label: "Payment",
                        value: row => row.payment_status,
                    },
                ]
            );
        }

        if (reportType === "purchases") {
            configureTable(
                "Purchase Orders",
                "Search across all matching purchase orders",
                [
                    {
                        label: "Purchase #",
                        value: row => row.purchase_number,
                    },
                    {
                        label: "Date",
                        value: row => formatDate(row.purchase_date),
                    },
                    {
                        label: "Supplier",
                        value: row => row.supplier__name,
                    },
                    {
                        label: "Branch",
                        value: row => row.branch__name,
                    },
                    {
                        label: "Status",
                        value: row => row.status,
                    },
                    {
                        label: "Value",
                        align: "end",
                        value: row => money(row.total_amount),
                    },
                ]
            );
        }

        if (reportType === "inventory") {
            configureTable(
                "Inventory Batches",
                "All batches, paginated from the database",
                [
                    {
                        label: "Medicine",
                        value: row => row.medicine,
                    },
                    {
                        label: "Batch",
                        value: row => row.batch_number,
                    },
                    {
                        label: "Branch",
                        value: row => row.branch,
                    },
                    {
                        label: "Units",
                        align: "end",
                        value: row => number(row.quantity_units),
                    },
                    {
                        label: "Expiry",
                        value: row => formatDate(row.expiry_date),
                    },
                    {
                        label: "Status",
                        value: row => {
                            if (row.expired) return "Expired";
                            if (!row.active) return "Inactive";
                            if (row.quantity_units === 0) {
                                return "Out of Stock";
                            }
                            if (row.expiring_soon) {
                                return "Expiring Soon";
                            }
                            return "Active";
                        },
                    },
                    {
                        label: "Cost Value",
                        align: "end",
                        value: row => money(
                            row.estimated_cost_value
                        ),
                    },
                ]
            );
        }
    }

    // ------------------------------------------------------
    // LOAD SERVER PAGINATED ROWS
    // ------------------------------------------------------

    async function loadRows() {
        if (reportType === "profit") return;

        const requestNumber = ++rowsRequestNumber;

        if (rowsController) {
            rowsController.abort();
        }

        rowsController = new AbortController();

        try {
            validateDates();

            const query = rowsQuery().toString();

            const data = await fetchJSON(
                `${rowsApiUrl}?${query}`,
                rowsController.signal
            );

            if (requestNumber !== rowsRequestNumber) {
                return;
            }

            renderTableRows(data.results || []);
            updatePagination(data.pagination);

            clearError();
            saveUrlState();

        } catch (error) {
            if (error.name === "AbortError") return;

            if (requestNumber === rowsRequestNumber) {
                setError(
                    error.message || "Unable to load records."
                );
            }
        }
    }

    // ------------------------------------------------------
    // LOAD KPI SUMMARY
    // ------------------------------------------------------

    async function loadSummary() {

        if (summaryController) {
            summaryController.abort();
        }

        const controller = new AbortController();
        summaryController = controller;

        try {
            validateDates();

            setLoading(true);
            clearError();

            const query = filterQuery().toString();

            const data = await fetchJSON(
                `${summaryApiUrl}?${query}`,
                controller.signal
            );

            if (controller.signal.aborted) return;

            if (reportType === "sales") {
                renderSalesSummary(data);
            }

            if (reportType === "purchases") {
                renderPurchasesSummary(data);
            }

            if (reportType === "inventory") {
                renderInventorySummary(data);
            }

            if (reportType === "profit") {
                renderProfitSummary(data);
            }

            updateDownloadLinks();
            content.classList.remove("d-none");

            if (reportType === "profit") {
                saveUrlState();
            } else {
                await loadRows();
            }

        } catch (error) {
            if (error.name === "AbortError") return;

            if (!controller.signal.aborted) {
                setError(
                    error.message || "Unable to load report."
                );
            }

        } finally {
            if (summaryController === controller) {
                setLoading(false);
            }
        }
    }

    // ------------------------------------------------------
    // EVENTS
    // ------------------------------------------------------

    form.addEventListener("submit", event => {
        event.preventDefault();

        currentPage = 1;
        searchInput.value = "";

        loadSummary();
    });

    refreshButton.addEventListener("click", () => {
        loadSummary();
    });

    if (reportType !== "profit") {
        searchInput.addEventListener("input", () => {
            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadRows();
            }, 350);
        });

        prevButton.addEventListener("click", () => {
            if (currentPage <= 1) return;

            currentPage--;
            loadRows();
        });

        nextButton.addEventListener("click", () => {
            if (currentPage >= totalPages) return;

            currentPage++;
            loadRows();
        });
    }

    // PDF/CSV use selected date and branch filters.
    // Search intentionally does not restrict exports:
    // exports retain complete selected-period records.

    [csvButton, pdfButton].forEach(button => {
        if (!button) return;

        button.addEventListener("click", event => {
            try {
                validateDates();
                updateDownloadLinks();
            } catch (error) {
                event.preventDefault();
                setError(error.message);
            }
        });
    });

    setupFilters();
    setupColumns();
    loadSummary();
});
