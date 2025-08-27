

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // Stop the form from reloading the page

        const formData = new FormData(form);
        const payload = {
            username: formData.get("username"),
            password: formData.get("password"),
        };

        try {
            const response = await fetch("/api/authbook/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                console.log("Registration failed:", response);
            }

            const data = await response.json();

            if (response.status === 400) {
                toast(data['error']);
                return
            }
            console.log("Registration successful:", data);

            // Optionally redirect or show a message
            window.location.href = "/login";
        } catch (err) {
            console.error("Error:", err);
            alert("Registration failed.");
        }
    });
});
