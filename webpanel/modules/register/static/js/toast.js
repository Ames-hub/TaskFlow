function toast(message, type = 'default') {
    // Remove existing toast if present
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.className = 'toast';
    toastElement.textContent = message;

    // Set background colour based on type
    switch (type) {
        case 'success':
            toastElement.style.backgroundColor = '#4caf50';
            break;
        case 'error':
            toastElement.style.backgroundColor = '#f44336';
            break;
        case 'warning':
            toastElement.style.backgroundColor = '#ff9800';
            break;
        default:
            toastElement.style.backgroundColor = '#333';
    }

    // Add to document
    document.body.appendChild(toastElement);

    // Remove toast after animation
    setTimeout(() => {
        toastElement.remove();
    }, 3000);
}