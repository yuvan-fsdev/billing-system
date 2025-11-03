const denominations = [2000, 500, 200, 100, 50, 20, 10, 5, 2, 1];

const state = {
    lastInvoice: null,
};

function createProductRow(rowIndex) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>
            <input type="text" name="product_code_${rowIndex}" placeholder="e.g. NB200" required />
        </td>
        <td>
            <input type="number" name="quantity_${rowIndex}" min="1" value="1" required />
        </td>
        <td class="actions">
            <button type="button" class="link remove-row">Remove</button>
        </td>
    `;
    return tr;
}

function populateDenominations(container) {
    container.innerHTML = "";
    denominations.forEach((value) => {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <label for="den_${value}">₹${value}</label>
            <input id="den_${value}" type="number" min="0" value="0" data-denomination="${value}" />
        `;
        container.appendChild(wrapper);
    });
}

function gatherLineItems(productTable) {
    const rows = [...productTable.querySelectorAll('tbody tr')];
    const items = rows.map((row) => {
        const codeInput = row.querySelector('input[name^="product_code_"]');
        const qtyInput = row.querySelector('input[name^="quantity_"]');
        const product_code = codeInput?.value.trim();
        const quantity = Number(qtyInput?.value || 0);
        if (!product_code) {
            throw new Error("Product code cannot be empty.");
        }
        if (!Number.isInteger(quantity) || quantity < 1) {
            throw new Error("Quantity must be a positive integer.");
        }
        return { product_code, quantity };
    });
    if (items.length === 0) {
        throw new Error("Add at least one line item.");
    }
    return items;
}

function gatherDenominationPayload(denomContainer, paidInput) {
    const counts = {};
    denomContainer.querySelectorAll('input[data-denomination]').forEach((input) => {
        const value = Number(input.dataset.denomination);
        const count = Number(input.value || 0);
        if (count > 0) {
            counts[value] = count;
        }
    });
    const paidAmountRaw = paidInput.value.trim();
    if (!paidAmountRaw) {
        throw new Error("Enter the total paid amount.");
    }
    return {
        counts,
        paid_amount: paidAmountRaw,
    };
}

function renderInvoiceSummary(container, summary) {
    if (!summary) {
        container.innerHTML = "";
        return;
    }

    const lines = summary.lines.map((line) => `
        <tr>
            <td>${line.product_code}</td>
            <td>${line.product_name}</td>
            <td>${line.unit_price}</td>
            <td>${line.quantity}</td>
            <td>${line.tax_percentage}</td>
            <td>${line.purchase_price}</td>
            <td>${line.tax_payable_for_item}</td>
            <td>${line.total_price_of_item}</td>
        </tr>
    `).join("");

    const renderDenoms = (map) => {
        if (!map || Object.keys(map).length === 0) {
            return "<span class=\"muted\">None</span>";
        }
        return Object.entries(map)
            .map(([value, count]) => `<span class="tag">₹${value} × ${count}</span>`)
            .join(" ");
    };

    container.innerHTML = `
        <div class="invoice-summary">
            <h3>Invoice Summary</h3>
            <p class="muted">Purchase ID: <strong>${summary.purchase_id}</strong> · <a href="/invoice/${summary.purchase_id}" target="_blank">View printable invoice</a></p>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Unit</th>
                        <th>Qty</th>
                        <th>Tax %</th>
                        <th>Subtotal</th>
                        <th>Tax</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>${lines}</tbody>
            </table>
            <div class="totals-grid">
                <div><strong>Subtotal</strong><br/>₹${summary.total_price_without_tax}</div>
                <div><strong>Total Tax</strong><br/>₹${summary.total_tax_payable}</div>
                <div><strong>Net Price</strong><br/>₹${summary.net_price}</div>
                <div><strong>Rounded Total</strong><br/>₹${summary.rounded_down_net_price}</div>
                <div><strong>Paid</strong><br/>₹${summary.paid_amount}</div>
                <div><strong>Change Due</strong><br/>₹${summary.balance_payable_to_customer} (Remainder: ₹${summary.change_remainder})</div>
            </div>
            <div>
                <p><strong>Change Denominations:</strong> ${renderDenoms(summary.balance_denomination)}</p>
                <p><strong>Payment Denominations:</strong> ${renderDenoms(summary.payment_denomination)}</p>
            </div>
        </div>
    `;
}

function renderHistory(container, purchases) {
    if (!purchases || purchases.length === 0) {
        container.innerHTML = `<p class="muted">No purchases recorded for this email yet.</p>`;
        return;
    }
    const items = purchases.map((purchase) => `
        <li>
            <div>
                <div><strong>Purchase #${purchase.id}</strong></div>
                <div class="muted">${new Date(purchase.created_at).toLocaleString()}</div>
            </div>
            <div>
                <span class="tag">₹${purchase.grand_total}</span>
                <a href="/invoice/${purchase.id}" target="_blank">Open</a>
            </div>
        </li>
    `).join("");
    container.innerHTML = `<ul>${items}</ul>`;
}

function showStatus(element, message, type = "success") {
    element.classList.remove("success", "error");
    element.textContent = message;
    if (message) {
        element.classList.add(type);
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}

async function handleGenerateBill(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const statusElement = form.querySelector(".status");
    const invoiceContainer = document.getElementById("invoice-output");

    try {
        showStatus(statusElement, "Generating invoice...", "success");
        const emailInput = form.querySelector("#customer-email");
        const paidInput = form.querySelector("#paid-amount");
        const productTable = form.querySelector("#product-table");
        const denomContainer = form.querySelector("#denomination-grid");

        const payload = {
            customer_email: emailInput.value.trim(),
            items: gatherLineItems(productTable),
            denominations: gatherDenominationPayload(denomContainer, paidInput),
        };

        const response = await fetch("/api/billing/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || "Failed to generate invoice.");
        }

        const summary = await response.json();
        state.lastInvoice = summary;
        renderInvoiceSummary(invoiceContainer, summary);
        showStatus(statusElement, "Invoice generated successfully.", "success");
    } catch (error) {
        console.error(error);
        renderInvoiceSummary(invoiceContainer, null);
        showStatus(statusElement, error.message || "Unexpected error occurred.", "error");
    }
}

async function handleHistory(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const statusElement = form.querySelector(".status");
    const resultsContainer = document.getElementById("history-results");
    const email = form.querySelector("#history-email").value.trim();

    if (!email) {
        showStatus(statusElement, "Provide an email address.", "error");
        return;
    }

    try {
        showStatus(statusElement, "Fetching history...", "success");
        const response = await fetch(`/api/purchases/history?email=${encodeURIComponent(email)}`);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || "Failed to load purchase history.");
        }
        const history = await response.json();
        renderHistory(resultsContainer, history);
        showStatus(statusElement, `Found ${history.length} purchase(s).`, "success");
    } catch (error) {
        console.error(error);
        renderHistory(resultsContainer, []);
        showStatus(statusElement, error.message || "Unable to load history.", "error");
    }
}

function initProductRows(table) {
    const tbody = table.querySelector("tbody");
    const addButton = document.getElementById("add-line-item");
    const resetButton = document.getElementById("reset-form");
    let rowCount = 0;

    const addRow = () => {
        const row = createProductRow(rowCount);
        tbody.appendChild(row);
        rowCount += 1;
    };

    if (addButton) {
        addButton.addEventListener("click", () => {
            addRow();
        });
    }

    const clearRows = () => {
        tbody.innerHTML = "";
        rowCount = 0;
        addRow();
    };

    tbody.addEventListener("click", (event) => {
        if (event.target.classList.contains("remove-row")) {
            const row = event.target.closest("tr");
            if (tbody.children.length === 1) {
                row.querySelectorAll("input").forEach((input) => {
                    if (input.type === "number") {
                        input.value = "1";
                    } else {
                        input.value = "";
                    }
                });
                return;
            }
            row.remove();
        }
    });

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            const form = document.getElementById("billing-form");
            form.reset();
            clearRows();
            document.getElementById("invoice-output").innerHTML = "";
            const statusElement = form.querySelector(".status");
            if (statusElement) {
                showStatus(statusElement, "", "success");
            }
        });
    }

    addRow();
}

function initUI() {
    const productTable = document.getElementById("product-table");
    const denominationGrid = document.getElementById("denomination-grid");
    const billingForm = document.getElementById("billing-form");
    const historyForm = document.getElementById("history-form");

    if (productTable) {
        initProductRows(productTable);
    }

    if (denominationGrid) {
        populateDenominations(denominationGrid);
    }

    if (billingForm) {
        billingForm.addEventListener("submit", handleGenerateBill);
    }

    if (historyForm) {
        historyForm.addEventListener("submit", handleHistory);
    }
}

document.addEventListener("DOMContentLoaded", initUI);
