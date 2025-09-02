const toggleBtn = document.getElementById('toggleResolveBtn');

// Initialize button style and text
toggleBtn.classList.add(isResolved ? 'action-unresolve' : 'action-resolve');
toggleBtn.textContent = isResolved ? 'Unresolve' : 'Resolve';

toggleBtn.addEventListener('click', async () => {
  try {
    let response;
    if (isResolved === true) {
        response = await fetch("/api/errors/unresolve", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_id: bugId })
        });
    }
    else {
        response = await fetch("/api/errors/resolve", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "bug_id": bugId, "response": "Your issue has been resolved." })
        });
    }

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
