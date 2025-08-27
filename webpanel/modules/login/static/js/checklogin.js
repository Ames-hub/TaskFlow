// Function to get a cookie by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Get sessionKey from cookies instead of localStorage
const sessionKey = getCookie('sessionKey');

if (sessionKey) {
    fetch('/api/token/check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: sessionKey })
    })
        .then(response => response.json())
        .then(data => {
            if (!data['verified']) {
                // Clear cookie (not as simple as localStorage)
                document.cookie = "sessionKey=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.log('error', error);
        });
} else {
    console.log('no session key');
    window.location.href = '/login';
}
