from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import logging

from ..services import db
from ..services.config_manager import load_config, save_config
from ..services.ksef_api import KSeFAPI, KSeFError
from ..services.invoice_parser import parse_invoice_xml

bp = Blueprint('invoices', __name__)
logger = logging.getLogger('invoices')

@bp.route('/invoices')
def invoice_list():
    return render_template('invoices.html')

@bp.route('/invoices/tinder')
def tinder_view():
    return render_template('tinder.html')

@bp.route('/invoices/<int:invoice_id>')
def invoice_detail(invoice_id):
    inv = db.get_invoice_by_id(invoice_id)
    if not inv:
        return "Faktura nie znaleziona", 404
    items = []
    if inv.get('xml_content'):
        parsed = parse_invoice_xml(inv['xml_content'])
        if parsed:
            items = parsed.get('items', [])
    return render_template('invoice_detail.html', invoice=inv, items=items)


@bp.route('/api/invoices')
def api_invoice_list():
    filters = {
        'status': request.args.get('status'),
        'invoice_type': request.args.get('type'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'search': request.args.get('search'),
    }
    filters = {k: v for k, v in filters.items() if v}
    invoices = db.get_invoices(filters)
    return jsonify(invoices)

@bp.route('/api/invoices/<int:invoice_id>')
def api_invoice_detail(invoice_id):
    inv = db.get_invoice_by_id(invoice_id)
    if not inv:
        return jsonify({'error': 'Nie znaleziono'}), 404
    return jsonify(inv)

@bp.route('/api/invoices/<int:invoice_id>/status', methods=['POST'])
def api_update_status(invoice_id):
    data = request.get_json()
    new_status = data.get('status', 'new')
    notes = data.get('notes', '')
    db.update_invoice_status(invoice_id, new_status, notes)
    return jsonify({'ok': True})

@bp.route('/api/invoices/tinder/next')
def api_tinder_next():
    invoices = db.get_invoices({'status': 'new', 'limit': 1})
    total = len(db.get_invoices({'status': 'new'}))
    if not invoices:
        return jsonify({'invoice': None, 'remaining': 0})
    inv = invoices[0]
    items = []
    if inv.get('xml_content'):
        parsed = parse_invoice_xml(inv['xml_content'])
        if parsed:
            items = parsed.get('items', [])
    inv['items'] = items
    return jsonify({'invoice': inv, 'remaining': total})

@bp.route('/api/invoices/sync', methods=['POST'])
def api_sync():
    config = load_config()
    token = config.get('ksef_token', '')
    nip = config.get('nip', '')
    env = config.get('environment', 'prod')

    if not token or not nip:
        return jsonify({'ok': False, 'message': 'Brak tokena lub NIP w ustawieniach'}), 400

    data = request.get_json() or {}
    days_back = int(data.get('days_back', 30))
    date_to = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT00:00:00')

    try:
        api = KSeFAPI(token=token, nip=nip, environment=env)
        api.authorize()

        invoice_headers = api.fetch_all_invoices(date_from, date_to)
        fetched_count = 0

        for header in invoice_headers:
            ksef_num = header.get('ksefReferenceNumber', '')
            if not ksef_num:
                continue

            existing = db.get_invoices({'search': ksef_num})
            if existing:
                continue

            try:
                xml_content = api.download_invoice(ksef_num)
                parsed = parse_invoice_xml(xml_content)

                if parsed:
                    invoice_data = {
                        'ksef_number': ksef_num,
                        'invoice_number': parsed.get('invoice_number', ''),
                        'seller_name': parsed.get('seller_name', ''),
                        'seller_nip': parsed.get('seller_nip', ''),
                        'buyer_name': parsed.get('buyer_name', ''),
                        'buyer_nip': parsed.get('buyer_nip', ''),
                        'issue_date': parsed.get('issue_date', ''),
                        'net_amount': parsed.get('net_amount', 0),
                        'vat_amount': parsed.get('vat_amount', 0),
                        'gross_amount': parsed.get('gross_amount', 0),
                        'invoice_type': header.get('_invoice_type', 'purchase'),
                        'xml_content': xml_content,
                    }
                    db.insert_invoice(invoice_data)
                    fetched_count += 1
            except Exception as e:
                logger.warning(f"Nie udało się pobrać faktury {ksef_num}: {e}")

        api.close_session()
        save_config({'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        db.log_sync(fetched_count, 'success')

        return jsonify({
            'ok': True,
            'message': f'Pobrano {fetched_count} nowych faktur (znaleziono {len(invoice_headers)} w KSeF)',
            'fetched': fetched_count,
            'total_found': len(invoice_headers),
        })

    except KSeFError as e:
        db.log_sync(0, 'error', str(e))
        return jsonify({'ok': False, 'message': f'Błąd KSeF: {e}', 'details': str(e.details) if e.details else ''}), 500
    except Exception as e:
        db.log_sync(0, 'error', str(e))
        return jsonify({'ok': False, 'message': f'Błąd: {e}'}), 500
