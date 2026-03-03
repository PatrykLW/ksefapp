document.addEventListener('DOMContentLoaded', loadDashboard);

async function loadDashboard() {
    try {
        const resp = await fetch('/api/dashboard/stats');
        const data = await resp.json();

        document.getElementById('stat-sales-count').textContent = data.stats.sales.cnt;
        document.getElementById('stat-sales-gross').textContent = formatMoney(data.stats.sales.gross);
        document.getElementById('stat-purchases-count').textContent = data.stats.purchases.cnt;
        document.getElementById('stat-purchases-gross').textContent = formatMoney(data.stats.purchases.gross);
        document.getElementById('stat-new-count').textContent = data.stats.new_count;
        document.getElementById('stat-unprinted').textContent = data.stats.unprinted_count;
        document.getElementById('last-sync-time').textContent = data.last_sync || 'Nigdy';

        renderRecentInvoices(data.recent_invoices);
    } catch(e) {
        console.error('Dashboard load error:', e);
    }
}

function renderRecentInvoices(invoices) {
    const container = document.getElementById('recent-invoices-table');

    if (!invoices || !invoices.length) {
        container.innerHTML = `
            <div class="text-center py-8">
                <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <p class="text-gray-400 text-sm">Brak faktur. Kliknij "Pobierz faktury" aby zsynchronizować z KSeF.</p>
            </div>`;
        return;
    }

    const statusColors = {
        'new': 'bg-blue-100 text-blue-700',
        'accepted': 'bg-green-100 text-green-700',
        'rejected': 'bg-red-100 text-red-700',
        'flagged': 'bg-yellow-100 text-yellow-700'
    };
    const statusLabels = {'new': 'Nowa', 'accepted': 'OK', 'rejected': 'Odrzucona', 'flagged': 'Sprawdź'};

    let html = '<table class="w-full text-sm"><tbody>';
    invoices.forEach(inv => {
        const contractor = inv.invoice_type === 'sales' ? inv.buyer_name : inv.seller_name;
        const typeIcon = inv.invoice_type === 'sales' ? '↑' : '↓';
        const typeColor = inv.invoice_type === 'sales' ? 'text-green-600' : 'text-red-500';

        html += `<tr class="border-b last:border-0 hover:bg-gray-50">
            <td class="py-2.5 pr-3"><span class="${typeColor} font-bold">${typeIcon}</span></td>
            <td class="py-2.5">
                <a href="/invoices/${inv.id}" class="text-ksef-600 hover:underline font-medium">${inv.invoice_number || inv.ksef_number}</a>
                <p class="text-xs text-gray-400">${contractor || '-'}</p>
            </td>
            <td class="py-2.5 text-right font-medium">${formatMoney(inv.gross_amount)}</td>
            <td class="py-2.5 text-right">
                <span class="px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[inv.status] || ''}">${statusLabels[inv.status] || inv.status}</span>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}
