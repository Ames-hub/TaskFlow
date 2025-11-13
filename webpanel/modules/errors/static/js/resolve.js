const toggleBtn = document.getElementById('toggleResolveBtn');
const adminMsgBox = document.getElementById('adminResponse');
const sendMsgBtn = document.getElementById('SendMsgBtn');
const resolveNoMsgBtn = document.getElementById('ToggleResolveNoMsgBtn');
const delbtn = document.getElementById('DeleteBtn');
const statusEl = document.getElementById('bugStatus');

// Ensure initial classes/text reflect current state
function applyState() {
  // Button label + colour
  toggleBtn.textContent = isResolved ? 'Unresolve' : 'Resolve';
  toggleBtn.classList.remove('action-resolve', 'action-unresolve');
  toggleBtn.classList.add(isResolved ? 'action-unresolve' : 'action-resolve');

  // Other buttons enabled only when bug is open (not resolved)
  const disabled = isResolved;
  sendMsgBtn.disabled = disabled;
  resolveNoMsgBtn.disabled = disabled;
  delbtn.disabled = disabled;

  // Status badge/text
  if (statusEl) {
    // keep case consistent with your backend if you want; here we normalize
    statusEl.textContent = isResolved ? 'closed' : 'open';
    statusEl.classList.remove('status-open', 'status-closed');
    statusEl.classList.add(isResolved ? 'status-closed' : 'status-open');
  }
}

// On load, sync UI with server-provided state
applyState();

toggleBtn.addEventListener('click', async () => {
  const goingToResolve = !isResolved;

  if (!confirm(goingToResolve ? 'Mark this bug as resolved?' : 'Mark this bug as open (unresolve)?')) {
    return;
  }

  try {
    let response;
    if (goingToResolve) {
      // Resolve with message (default if empty)
      let AdminMsg = adminMsgBox.value.trim();
      if (!AdminMsg) {
        AdminMsg = 'Your issue has been resolved by project maintainers.';
      }
      response = await fetch('/api/errors/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_id: bugId, response: AdminMsg })
      });
    } else {
      // Unresolve
      response = await fetch('/api/errors/unresolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_id: bugId })
      });
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      alert('Failed: ' + (error.message || 'Unknown error'));
      return;
    }

    // Flip state *after* success, then update UI based on the new state
    isResolved = !isResolved;
    applyState();
  } catch (err) {
    alert('Network error: ' + err.message);
  }
});

resolveNoMsgBtn.addEventListener('click', async () => {
  if (isResolved) {
    alert('Bug is already resolved.');
    return;
  }
  if (!confirm('Resolve without sending a message?')) {
    return;
  }

  try {
    const response = await fetch('/api/errors/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bug_id: bugId, response: '<NO_CONTENT>' })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      alert('Failed: ' + (error.message || 'Unknown error'));
      return;
    }

    isResolved = true;
    applyState();
  } catch (err) {
    alert('Network error: ' + err.message);
  }
});

sendMsgBtn.addEventListener('click', async () => {
  const AdminMsg = adminMsgBox.value.trim();
  if (!AdminMsg) {
    alert('Please enter a message before sending.');
    return;
  }
  try {
    const response = await fetch('/api/errors/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bug_id: bugId, response: AdminMsg })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      alert('Failed: ' + (error.message || 'Unknown error'));
      return;
    }

    alert('Message sent.');
    adminMsgBox.value = '';
  } catch (err) {
    alert('Network error: ' + err.message);
  }
});
