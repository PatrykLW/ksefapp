let currentInvoice = null;
let itemsVisible = false;

document.addEventListener('DOMContentLoaded', loadNextInvoice);

document.addEventListener('keydown', function(e) {
    if (!currentInvoice) return;
    switch(e.key) {
        case 'Enter': tinderAction('accepted'); break;
        case 'Escape': tinderAction('rejected'); break;
        case '?': tinderAction('flagged'); break;
        case 'p': case 'P': tinderPrint(); break;
    }
});

async function loadNextInvoice() {
    const loading = document.getElementById('tinder-loading');
    const content = document.getElementById('tinder-content');
    const empty = document.getElementById('tinder-empty');
    const actions = document.getElementById('tinder-actions');
    const card = document.getElementById('tinder-card');

    loading.classList.remove('hidden');
    content.classList.add('hidden');
    empty.classList.add('hidden');
    card.className = 'bg-white rounded-2xl shadow-lg border p-6 transition-all duration-300 transform';
    card.classList.remove('ring-2', 'ring-red-400');

    try {
        const resp = await fetch('/api/invoices/tinder/next');
        const data = await resp.json();

        loading.classList.add('hidden');

        if (!data.invoice) {
            empty.classList.remove('hidden');
            actions.classList.add('hidden');
            document.getElementById('tinder-counter').textContent = 'Brak nowych faktur';
            currentInvoice = null;
            return;
        }

        currentInvoice = data.invoice;
        actions.classList.remove('hidden');
        content.classList.remove('hidden');

        document.getElementById('tinder-counter').textContent =
            `Pozostało ${data.remaining} faktur do przeglądu`;

        const inv = data.invoice;
        document.getElementById('tinder-invoice-number').textContent = inv.invoice_number || 'Brak numeru';
        document.getElementById('tinder-ksef-number').textContent = 'KSeF: ' + inv.ksef_number;
        document.getElementById('tinder-gross-amount').textContent = formatMoney(inv.gross_amount);
        document.getElementById('tinder-seller-name').textContent = inv.seller_name || '-';
        document.getElementById('tinder-seller-nip').textContent = 'NIP: ' + (inv.seller_nip || '-');
        document.getElementById('tinder-buyer-name').textContent = inv.buyer_name || '-';
        document.getElementById('tinder-buyer-nip').textContent = 'NIP: ' + (inv.buyer_nip || '-');
        document.getElementById('tinder-net').textContent = formatMoney(inv.net_amount);
        document.getElementById('tinder-vat').textContent = formatMoney(inv.vat_amount);
        document.getElementById('tinder-gross').textContent = formatMoney(inv.gross_amount);
        document.getElementById('tinder-date').textContent = inv.issue_date || '-';

        const badge = document.getElementById('tinder-type-badge');
        if (inv.invoice_type === 'sales') {
            badge.textContent = 'Sprzedaż';
            badge.className = 'inline-block px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700';
        } else {
            badge.textContent = 'Zakup';
            badge.className = 'inline-block px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700';
        }

        const items = inv.items || [];
        const itemsSection = document.getElementById('tinder-items');
        const itemsBody = document.getElementById('tinder-items-body');
        if (items.length > 0) {
            itemsBody.innerHTML = items.map(item =>
                `<tr class="border-t">
                    <td class="p-1.5">${item.name}</td>
                    <td class="p-1.5 text-right">${item.quantity}</td>
                    <td class="p-1.5 text-right">${parseFloat(item.unit_price).toFixed(2)}</td>
                    <td class="p-1.5 text-right font-medium">${parseFloat(item.net_value).toFixed(2)}</td>
                </tr>`
            ).join('');
            document.getElementById('toggle-items-btn').classList.remove('hidden');
        } else {
            document.getElementById('toggle-items-btn').classList.add('hidden');
        }
        itemsSection.classList.add('hidden');
        itemsVisible = false;

        renderFuelWarnings(inv);

    } catch(e) {
        loading.classList.add('hidden');
        showToast('Błąd ładowania: ' + e.message, 'error');
    }
}

async function tinderAction(status) {
    if (!currentInvoice) return;

    const card = document.getElementById('tinder-card');
    const animClass = status === 'rejected' ? 'tinder-slide-left'
                     : status === 'accepted' ? 'tinder-slide-right'
                     : 'tinder-slide-up';
    card.classList.add(animClass);

    await fetch(`/api/invoices/${currentInvoice.id}/status`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status})
    });

    const labels = {'accepted': 'Zaakceptowana', 'rejected': 'Odrzucona', 'flagged': 'Oznaczona do sprawdzenia'};
    showToast(labels[status] || status, status === 'accepted' ? 'success' : status === 'rejected' ? 'error' : 'warning');

    setTimeout(loadNextInvoice, 350);
}

async function tinderPrint() {
    if (!currentInvoice) return;
    try {
        const resp = await fetch('/api/print', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({invoice_ids: [currentInvoice.id]})
        });
        const data = await resp.json();
        showToast(data.message, data.ok ? 'success' : 'error');
    } catch(e) {
        showToast('Błąd drukowania: ' + e.message, 'error');
    }
}

function renderFuelWarnings(inv) {
    const warningsDiv = document.getElementById('tinder-fuel-warnings');
    const okDiv = document.getElementById('tinder-fuel-ok');
    warningsDiv.classList.add('hidden');
    okDiv.classList.add('hidden');
    warningsDiv.innerHTML = '';

    if (!inv.is_fuel_invoice) return;

    const warnings = inv.fuel_warnings || [];
    if (warnings.length > 0) {
        warningsDiv.classList.remove('hidden');
        warningsDiv.innerHTML = warnings.map(w => `
            <div class="bg-red-50 border border-red-300 rounded-lg p-3 mb-2 animate-pulse-once">
                <div class="flex items-start gap-2">
                    <svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                    <span class="text-sm text-red-700 font-medium">${w.message}</span>
                </div>
            </div>`).join('');

        const card = document.getElementById('tinder-card');
        card.classList.add('ring-2', 'ring-red-400');
    } else {
        const matched = inv.fuel_matched_vehicle;
        const plates = (inv.fuel_detected_plates || []).join(', ');
        const fuels = (inv.fuel_detected_fuels || []).join(', ');
        let msg = 'Faktura paliwowa - dane zgodne z bazą pojazdów';
        if (matched) {
            msg = `OK: ${matched.plate} (${matched.brand} ${matched.model}) - ${fuels}`;
        }
        okDiv.classList.remove('hidden');
        document.getElementById('tinder-fuel-ok-text').textContent = msg;
    }
}

function toggleItems() {
    const section = document.getElementById('tinder-items');
    const btn = document.getElementById('toggle-items-btn');
    itemsVisible = !itemsVisible;
    if (itemsVisible) {
        section.classList.remove('hidden');
        btn.textContent = 'Ukryj pozycje';
    } else {
        section.classList.add('hidden');
        btn.textContent = 'Pokaż pozycje';
    }
}
