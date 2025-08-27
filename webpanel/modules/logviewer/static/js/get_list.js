document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");
    const container = document.querySelector(".log-links");

    async function fetchLogs(query = "") {
        const url = query
            ? `/api/bot/logs/list?search=${encodeURIComponent(query)}`
            : `/api/bot/logs/list`;

        try {
            const res = await fetch(url);
            const data = await res.json();
            if (!data.success) {
                console.error("Failed to load logs");
                container.innerHTML = "<p>No logs found.</p>";
                return;
            }

            container.innerHTML = "";
            Object.keys(data.logs).forEach(fileName => {
                const log = data.logs[fileName];
                const card = document.createElement("a");
                card.href = `/bot/logs/${encodeURIComponent(fileName)}`;
                card.className = "log-card";
                card.textContent = `${fileName} (${formatSize(log.size)})`;
                container.appendChild(card);
            });
        } catch (err) {
            console.error("Error fetching logs:", err);
            container.innerHTML = "<p>Error loading logs.</p>";
        }
    }

    function formatSize(bytes) {
        if (!bytes) return "Unknown size";
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    // Trigger search on button click
    searchButton.addEventListener("click", () => fetchLogs(searchInput.value.trim()));

    // Trigger search on Enter key
    searchInput.addEventListener("keypress", e => {
        if (e.key === "Enter") fetchLogs(searchInput.value.trim());
    });

    // Initial load (no search filter)
    fetchLogs();
});
