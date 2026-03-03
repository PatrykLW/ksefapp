document.addEventListener('DOMContentLoaded', function() {
    highlightCurrentNav();
    checkConnection();
});

function highlightCurrentNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (path === href || (href !== '/' && path.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

async function checkConnection() {
    const dot = document.getElementById('connection-dot');
    const status = document.getElementById('sidebar-status');
    try {
        const resp = await fetch('/api/settings');
        const data = await resp.json();
        if (data.ksef_token) {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-green-400';
            dot.title = 'Token skonfigurowany';
            status.textContent = 'NIP: ' + (data.nip || 'Nie ustawiony');
        } else {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-yellow-400';
            dot.title = 'Brak tokena';
            status.textContent = 'Brak tokena KSeF';
        }
    } catch(e) {
        dot.className = 'w-2.5 h-2.5 rounded-full bg-red-400';
        status.textContent = 'Błąd połączenia';
    }
}

async function syncInvoices() {
    const modal = document.getElementById('sync-modal');
    const msg = document.getElementById('sync-message');
    modal.classList.remove('hidden');
    msg.textContent = 'Łączenie z KSeF...';

    try {
        const resp = await fetch('/api/invoices/sync', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({days_back: 30})
        });
        const data = await resp.json();
        modal.classList.add('hidden');

        if (data.ok) {
            showToast(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch(e) {
        modal.classList.add('hidden');
        showToast('Błąd synchronizacji: ' + e.message, 'error');
    }
}

async function printAllNew() {
    try {
        const resp = await fetch('/api/print/all-new', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const data = await resp.json();
        showToast(data.message, data.ok ? 'success' : 'error');
    } catch(e) {
        showToast('Błąd drukowania: ' + e.message, 'error');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast');
    container.innerHTML = `<div class="toast toast-${type}">${message}</div>`;
    container.classList.remove('hidden');
    setTimeout(() => container.classList.add('hidden'), 3000);
}

function formatMoney(value) {
    if (value === null || value === undefined) return '0,00 PLN';
    return new Intl.NumberFormat('pl-PL', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value) + ' PLN';
}
