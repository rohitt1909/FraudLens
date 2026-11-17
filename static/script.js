
// FraudLens Dashboard

const API = "/api";

let transactions = [];

const numberFormat = new Intl.NumberFormat("en-IN");

const currencyFormat = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});


// Fetch data from Flask API

async function fetchData(endpoint) {

    const response = await fetch(`${API}${endpoint}`);

    if (!response.ok) {
        throw new Error("Unable to fetch data");
    }

    return await response.json();
}


// Load dashboard statistics

async function loadStats() {

    const data = await fetchData("/stats");

    document.getElementById("total-transactions")
        .textContent = numberFormat.format(
            data.total_transactions
        );

    document.getElementById("combined-alerts")
        .textContent = numberFormat.format(
            data.combined_alerts
        );

    document.getElementById("high-risk")
        .textContent = numberFormat.format(
            data.high_risk
        );

    document.getElementById("suspicious-amount")
        .textContent =
            "₹" + (data.suspicious_amount / 10000000)
            .toFixed(2) + " Cr";

    createDetectionChart(data);
}


// Chart settings

if (typeof Chart !== "undefined") {

    Chart.defaults.color = "#94a3b8";
    Chart.defaults.borderColor = "#263449";
    Chart.defaults.font.family = "Inter, Arial, sans-serif";
}


// Risk distribution chart

async function loadRiskChart() {

    const data = await fetchData("/risk-distribution");

    if (typeof Chart === "undefined") return;

    const levels = ["Low", "Medium", "High"];

    const values = levels.map(level => {

        const item = data.find(
            row => row.risk_level === level
        );

        return item ? item.total : 0;
    });

    new Chart(document.getElementById("riskChart"), {

        type: "doughnut",

        data: {
            labels: levels,

            datasets: [{
                data: values,

                backgroundColor: [
                    "#22c55e",
                    "#fbbf24",
                    "#f87171"
                ],

                borderWidth: 0,
                hoverOffset: 8
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",

            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}


// Detection comparison chart

function createDetectionChart(data) {

    if (typeof Chart === "undefined") return;

    new Chart(document.getElementById("detectionChart"), {

        type: "bar",

        data: {
            labels: [
                "Rule Engine",
                "Statistical",
                "Combined"
            ],

            datasets: [{
                label: "Flagged Transactions",

                data: [
                    data.rule_alerts,
                    data.anomalies,
                    data.combined_alerts
                ],

                backgroundColor: [
                    "#38bdf8",
                    "#a78bfa",
                    "#fbbf24"
                ],

                borderRadius: 7
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                }
            },

            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}


// Model performance chart

function createPerformanceChart() {

    if (typeof Chart === "undefined") return;

    new Chart(document.getElementById("performanceChart"), {

        type: "bar",

        data: {
            labels: [
                "Rule Engine",
                "Statistical Model",
                "Combined Model"
            ],

            datasets: [
                {
                    label: "Accuracy",
                    data: [91.55, 96.50, 89.85],
                    backgroundColor: "#38bdf8",
                    borderRadius: 5
                },
                {
                    label: "Precision",
                    data: [36.47, 61.34, 32.33],
                    backgroundColor: "#a78bfa",
                    borderRadius: 5
                },
                {
                    label: "Recall",
                    data: [100, 75.26, 100],
                    backgroundColor: "#22c55e",
                    borderRadius: 5
                },
                {
                    label: "F1 Score",
                    data: [53.44, 67.59, 48.87],
                    backgroundColor: "#fbbf24",
                    borderRadius: 5
                }
            ]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,

                    ticks: {
                        callback: value => value + "%"
                    }
                }
            },

            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}


// Load transactions from database

async function loadTransactions() {

    const risk = document.getElementById("riskFilter").value;

    transactions = await fetchData(
        `/transactions?risk=${encodeURIComponent(risk)}`
    );

    filterTransactions();
}


// Display transactions safely

function renderTransactions(data) {

    const table = document.getElementById("transactionTable");

    table.replaceChildren();

    if (data.length === 0) {

        const row = table.insertRow();
        const cell = row.insertCell();

        cell.colSpan = 9;
        cell.textContent = "No matching transactions found.";

        return;
    }

    data.forEach(transaction => {

        const row = table.insertRow();

        const values = [
            transaction.transaction_id,
            transaction.customer_id,
            currencyFormat.format(transaction.amount),
            transaction.transaction_type,
            transaction.location,
            transaction.risk_score + "/100"
        ];

        values.forEach(value => {
            row.insertCell().textContent = value;
        });

        // Risk level badge

        const riskCell = row.insertCell();

        const badge = document.createElement("span");

        badge.className =
            "risk-badge risk-" +
            transaction.risk_level.toLowerCase();

        badge.textContent = transaction.risk_level;

        riskCell.appendChild(badge);

        // Alert status

        const alertCell = row.insertCell();

        alertCell.textContent =
            transaction.combined_alert
                ? "Flagged"
                : "Clear";

        alertCell.className =
            transaction.combined_alert
                ? "alert-yes"
                : "alert-no";

        // Triggered fraud rules

        row.insertCell().textContent =
            transaction.triggered_rules ||
            "No rules triggered";
    });
}


// Search transactions

function filterTransactions() {

    const search = document.getElementById("searchInput")
        .value.toLowerCase().trim();

    const filtered = transactions.filter(transaction => {

        return [
            transaction.transaction_id,
            transaction.customer_id,
            transaction.transaction_type,
            transaction.location,
            transaction.risk_level
        ].some(value =>
            String(value).toLowerCase().includes(search)
        );
    });

    renderTransactions(filtered);
}


// Live transaction simulator

async function analyzeTransaction(event) {

    event.preventDefault();

    const resultBox =
        document.getElementById("simulationResult");

    const button =
        event.target.querySelector("button");

    const fields = [
        "amount",
        "hour",
        "device_known",
        "location_known",
        "failed_attempts",
        "transactions_last_hour",
        "average_customer_spend"
    ];

    const data = {};

    fields.forEach(field => {

        data[field] = Number(
            document.getElementById(field).value
        );
    });

    button.disabled = true;
    button.textContent = "Analyzing...";

    resultBox.className = "simulation-result";
    resultBox.textContent = "Evaluating transaction...";

    try {

        const response = await fetch(`${API}/analyze`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Analysis failed"
            );
        }

        resultBox.className =
            "simulation-result result-" +
            result.risk_level.toLowerCase();

        resultBox.replaceChildren();

        const heading = document.createElement("h3");

        heading.textContent = "Transaction Risk Assessment";

        resultBox.appendChild(heading);

        const details = [
            ["Risk Score", result.risk_score + "/100"],
            ["Risk Level", result.risk_level],
            ["Anomaly Score", result.anomaly_score],
            [
                "Statistical Anomaly",
                result.statistical_anomaly
                    ? "Detected"
                    : "Not detected"
            ],
            [
                "Final Decision",
                result.combined_alert
                    ? "Flag for Investigation"
                    : "No Alert Generated"
            ],
            [
                "Triggered Rules",
                result.triggered_rules ||
                "No rules triggered"
            ]
        ];

        details.forEach(([label, value]) => {

            const paragraph = document.createElement("p");
            const strong = document.createElement("strong");

            strong.textContent = label + ": ";

            paragraph.appendChild(strong);
            paragraph.appendChild(
                document.createTextNode(value)
            );

            resultBox.appendChild(paragraph);
        });

    } catch (error) {

        resultBox.textContent =
            "Error: " + error.message;

    } finally {

        button.disabled = false;
        button.textContent = "Analyze Transaction";
    }
}


// Sidebar navigation

document.querySelectorAll(".sidebar nav a")
    .forEach(link => {

        link.addEventListener("click", () => {

            document.querySelectorAll(".sidebar nav a")
                .forEach(item =>
                    item.classList.remove("active")
                );

            link.classList.add("active");
        });
    });


// Event listeners

document.getElementById("searchInput")
    .addEventListener("input", filterTransactions);

document.getElementById("riskFilter")
    .addEventListener("change", () => {

        loadTransactions().catch(error => {
            console.error(error);
            alert("Unable to load transactions.");
        });
    });

document.getElementById("simulationForm")
    .addEventListener("submit", analyzeTransaction);


// Initialize dashboard

async function initializeDashboard() {

    try {

        await Promise.all([
            loadStats(),
            loadRiskChart(),
            loadTransactions()
        ]);

        createPerformanceChart();

        console.log("FraudLens dashboard initialized.");

    } catch (error) {

        console.error("Dashboard error:", error);

        alert(
            "Unable to load dashboard. " +
            "Make sure the Flask server is running."
        );
    }
}

initializeDashboard();
