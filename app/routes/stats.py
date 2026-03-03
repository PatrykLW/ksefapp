import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, Response
from ..services import db

bp = Blueprint('stats', __name__)

@bp.route('/stats')
def stats_page():
    return render_template('stats.html')

@bp.route('/api/stats')
def api_stats():
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', None, type=int)

    if month:
        stats = db.get_stats(month=month, year=year)
    else:
        stats = db.get_stats()

    monthly = db.get_monthly_stats(year)
    top_sellers = db.get_top_contractors(limit=10, invoice_type='purchase')
    top_buyers = db.get_top_contractors(limit=10, invoice_type='sales')

    return jsonify({
        'stats': stats,
        'monthly': monthly,
        'top_sellers': top_sellers,
        'top_buyers': top_buyers,
        'year': year,
    })

@bp.route('/api/stats/export')
def api_export_csv():
    filters = {
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'invoice_type': request.args.get('type'),
    }
    filters = {k: v for k, v in filters.items() if v}
    invoices = db.get_invoices(filters)

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Numer KSeF', 'Numer faktury', 'Data wystawienia', 'Typ',
        'Sprzedawca', 'NIP sprzedawcy', 'Nabywca', 'NIP nabywcy',
        'Netto', 'VAT', 'Brutto', 'Status'
    ])
    for inv in invoices:
        writer.writerow([
            inv.get('ksef_number', ''),
            inv.get('invoice_number', ''),
            inv.get('issue_date', ''),
            'Sprzedaż' if inv.get('invoice_type') == 'sales' else 'Zakup',
            inv.get('seller_name', ''),
            inv.get('seller_nip', ''),
            inv.get('buyer_name', ''),
            inv.get('buyer_nip', ''),
            f"{inv.get('net_amount', 0):.2f}",
            f"{inv.get('vat_amount', 0):.2f}",
            f"{inv.get('gross_amount', 0):.2f}",
            inv.get('status', ''),
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=faktury_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
