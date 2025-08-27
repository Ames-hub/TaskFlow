const toggleBtn = document.getElementById('toggleResolveBtn');

// Initialize button style and text
toggleBtn.classList.add(isResolved ? 'action-unresolve' : 'action-resolve');
toggleBtn.textContent = isResolved ? 'Unresolve' : 'Resolve';

toggleBtn.addEventListener('click', async () => {
  const url = isResolved ? '/api/errors/unresolve' : '/api/errors/resolve';
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bug_id: bugId}) // wrap in quotes
    });

    if (response.ok) {
      // Toggle state
      isResolved = !isResolved;

      // Update button text
      toggleBtn.textContent = isResolved ? 'Unresolve' : 'Resolve';

      // Update button color class
      toggleBtn.classList.toggle('action-resolve');
      toggleBtn.classList.toggle('action-unresolve');

      // Update status badge
      const statusField = document.querySelector('.field span'); // adjust selector if needed
      statusField.textContent = isResolved ? 'Closed' : 'Open';
      statusField.className = isResolved ? 'status-closed' : 'status-open';
    } else {
      const error = await response.json();
      alert('Failed: ' + (error.message || 'Unknown error'));
    }
  } catch (err) {
    alert('Network error: ' + err.message);
  }
});
