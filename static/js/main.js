// Bamboo Money - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // HTMX configuration
    document.body.addEventListener('htmx:configRequest', function(evt) {
        // Add CSRF token to all HTMX requests
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            evt.detail.headers['X-CSRFToken'] = csrfToken;
        }
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm before delete actions
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm(element.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});

// Chart.js default configuration
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = '#64748b';
}
