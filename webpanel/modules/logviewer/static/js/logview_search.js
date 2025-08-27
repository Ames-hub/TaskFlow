document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search");
    const logLines = document.querySelectorAll(".log-line");

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.toLowerCase();
        logLines.forEach(line => {
            const text = line.textContent.toLowerCase();
            line.style.display = text.includes(query) ? "flex" : "none";
        });
    });
});