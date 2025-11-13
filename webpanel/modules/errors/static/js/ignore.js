document.addEventListener('DOMContentLoaded', () => {
  const deleteBtn = document.getElementById('DeleteBtn');
  if (!deleteBtn) return;

  deleteBtn.addEventListener('click', async () => {
    if (!confirm('Ignore this bug (mark resolved) without notifying the reporter?')) {
      return;
    }
    try {
      const response = await fetch('/api/errors/ignore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_id: bugId })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        alert('Failed: ' + (error.message || 'Unknown error'));
        return;
      }

      // Set new state and let the shared UI updater take care of everything
      isResolved = true;
      applyState();
    } catch (err) {
      alert('Network error: ' + err.message);
    }
  });
});
