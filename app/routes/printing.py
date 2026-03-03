from flask import Blueprint, render_template, jsonify, request
from ..services import db
from ..services.printer_service import get_printers, print_html, print_invoices_batch
from ..services.invoice_parser import parse_invoice_xml, invoice_to_html
from ..services.config_manager import load_config

bp = Blueprint('printing', __name__)

@bp.route('/print')
def print_page():
    return render_template('print.html')

@bp.route('/api/printers')
def api_printers():
    printers = get_printers()
    config = load_config()
    default = config.get('default_printer', '')
    return jsonify({'printers': printers, 'default_printer': default})

@bp.route('/api/print', methods=['POST'])
def api_print():
    data = request.get_json()
    invoice_ids = data.get('invoice_ids', [])
    printer_name = data.get('printer', None)

    if not invoice_ids:
        return jsonify({'ok': False, 'message': 'Nie wybrano faktur'}), 400

    html_contents = []
    for inv_id in invoice_ids:
        inv = db.get_invoice_by_id(inv_id)
        if not inv:
            continue

        if inv.get('xml_content'):
            parsed = parse_invoice_xml(inv['xml_content'])
            if parsed:
                html = invoice_to_html(parsed)
                html_contents.append((inv_id, html))

    if not html_contents:
        return jsonify({'ok': False, 'message': 'Brak faktur do wydruku'}), 400

    success_count = 0
    error_count = 0
    for inv_id, html in html_contents:
        ok, msg = print_html(html, printer_name)
        if ok:
            success_count += 1
            db.mark_invoice_printed(inv_id)
        else:
            error_count += 1

    return jsonify({
        'ok': True,
        'message': f'Wydrukowano {success_count} faktur' + (f', błędy: {error_count}' if error_count else ''),
        'success': success_count,
        'errors': error_count,
    })

@bp.route('/api/print/all-new', methods=['POST'])
def api_print_all_new():
    data = request.get_json() or {}
    printer_name = data.get('printer', None)
    invoices = db.get_invoices({'status': 'new'})

    if not invoices:
        invoices = db.get_invoices()
    unprinted = [i for i in invoices if not i.get('printed')]

    if not unprinted:
        return jsonify({'ok': False, 'message': 'Brak niewydrukowanych faktur'}), 400

    html_contents = []
    for inv in unprinted:
        if inv.get('xml_content'):
            parsed = parse_invoice_xml(inv['xml_content'])
            if parsed:
                html_contents.append((inv['id'], invoice_to_html(parsed)))

    success_count = 0
    for inv_id, html in html_contents:
        ok, _ = print_html(html, printer_name)
        if ok:
            success_count += 1
            db.mark_invoice_printed(inv_id)

    return jsonify({
        'ok': True,
        'message': f'Wydrukowano {success_count} z {len(html_contents)} faktur',
        'success': success_count,
    })

@bp.route('/api/print/preview/<int:invoice_id>')
def api_print_preview(invoice_id):
    inv = db.get_invoice_by_id(invoice_id)
    if not inv or not inv.get('xml_content'):
        return "Brak danych faktury", 404
    parsed = parse_invoice_xml(inv['xml_content'])
    if not parsed:
        return "Nie udało się sparsować faktury", 500
    return invoice_to_html(parsed)
