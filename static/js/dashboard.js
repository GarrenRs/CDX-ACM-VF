// Dashboard helper JS
// Adds small UX helpers used throughout the admin dashboard

(function() {
    'use strict';

    // Init Bootstrap tooltips if present
    try {
        const tt = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tt.forEach(el => new bootstrap.Tooltip(el));
    } catch (err) {
        // bootstrap may not be loaded in some contexts; ignore
        console.debug('Tooltip init skipped:', err);
    }

    // Generic data-confirm handler for links/buttons
    document.addEventListener('click', function(e) {
        const el = e.target.closest('[data-confirm]');
        if (!el) return;
        const msg = el.getAttribute('data-confirm') || 'Are you sure?';
        if (!confirm(msg)) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });

    // Copy-to-clipboard helper for elements with .copy-btn and data-copy-target
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.copy-btn');
        if (!btn) return;
        const targetSel = btn.getAttribute('data-copy-target');
        if (!targetSel) return;
        const target = document.querySelector(targetSel);
        if (!target) return;

        const text = target.value ?? target.textContent ?? target.getAttribute('data-copy-text') ?? '';
        if (!navigator.clipboard) {
            // fallback
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); } catch (err) { console.error(err); }
            document.body.removeChild(ta);
        } else {
            navigator.clipboard.writeText(text).catch(err => console.error('Copy failed', err));
        }

        const original = btn.innerHTML;
        btn.textContent = 'Copied';
        setTimeout(() => btn.innerHTML = original, 1500);
    });

    // Simple POST action helper for elements with data-post attribute
    // e.g. <button data-post="/dashboard/item/delete/123" data-confirm="Delete this?">Delete</button>
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('[data-post]');
        if (!btn) return;
        e.preventDefault();
        const url = btn.getAttribute('data-post');
        const confirmMsg = btn.getAttribute('data-confirm');
        if (confirmMsg && !confirm(confirmMsg)) return;

        fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
            .then(resp => {
                if (!resp.ok) throw new Error('Request failed');
                // Prefer reloading to reflect state change
                window.location.reload();
            })
            .catch(err => {
                console.error('POST action failed:', err);
                alert('Action failed. See console for details.');
            });
    });

    // Small helper for sidebar toggles (data-sidebar-toggle)
    document.querySelectorAll('[data-sidebar-toggle]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.classList.toggle('show');
        });
    });

})();
