const filters = document.getElementById('filters');
const tbody = document.getElementById('bugBody');

const statusClasses = {
    open: "status-open",
    inprogress: "status-inprogress",
    closed: "status-closed"
};
const severityClasses = {
    low: "sev-low",
    medium: "sev-medium",
    high: "sev-high",
    critical: "sev-critical"
};

async function loadBugs() {
    try {
        const res = await fetch("/api/errors/list");
        const bugs = await res.json();
        renderBugs(bugs);
    } catch (err) {
        console.error("Failed to fetch bugs:", err);
    }
}

function renderBugs(bugs) {
    tbody.innerHTML = "";
    bugs.forEach(bug => {
        const tr = document.createElement("tr");
        tr.dataset.status = bug.status.toLowerCase();
        tr.dataset.severity = bug.severity.toLowerCase();

        tr.innerHTML = `
            <td><a href="/bot/errors/${bug.id}">${bug.id}</a></td>
            <td><a href="/bot/errors/${bug.id}">${bug.title}</a></td>
            <td><span class="badge ${severityClasses[bug.severity.toLowerCase()] || ''}">
                ${bug.severity}
            </span></td>
            <td><span class="badge ${statusClasses[bug.status.toLowerCase()] || ''}">
                ${bug.status.charAt(0).toUpperCase() + bug.status.slice(1)}
            </span></td>
        `;
        tbody.appendChild(tr);
    });
    applyFilters();
}

function applyFilters() {
    const activeStatus = [...filters.querySelectorAll('input[name="status"]:checked')].map(cb => cb.value.toLowerCase());
    const activeSeverity = [...filters.querySelectorAll('input[name="severity"]:checked')].map(cb => cb.value.toLowerCase());

    tbody.querySelectorAll("tr").forEach(row => {
        const status = row.dataset.status;
        const severity = row.dataset.severity;
        row.style.display = (activeStatus.includes(status) && activeSeverity.includes(severity)) ? "" : "none";
    });
}

filters.addEventListener("change", applyFilters);
loadBugs();