document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', async (event) => {
        event.preventDefault();  // stop normal form post

        // collect form data
        const formData = new FormData(form);
        let username = String(formData.get('username'));
        const payload = {
            username: username,
            password: formData.get('password'),
        };

        try {
            const response = await fetch('/api/user/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok && result.token) {
                // set cookies instead of localStorage
                const expireTime = new Date(Date.now() + 2 * 60 * 60 * 1000).toUTCString(); // 2 hours
                document.cookie = `sessionKey=${result.token}; expires=${expireTime}; path=/; SameSite=Strict`;
                document.cookie = `username=${username}; expires=${expireTime}; path=/; SameSite=Strict`;

                // redirect or update UI
                window.location.href = '/';
            } else {
                toast(result.message || 'Login failed. Check your credentials.');
            }
        } catch (err) {
            console.error('Login error:', err);
            toast('Unable to reach server. Please try again later.');
        }
    });
});
