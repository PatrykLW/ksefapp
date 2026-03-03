from flask import Blueprint, render_template, jsonify, request
from ..services.config_manager import load_config, save_config
from ..services.ksef_api import KSeFAPI
from ..services import db

bp = Blueprint('settings', __name__)

@bp.route('/settings')
def settings_page():
    config = load_config()
    return render_template('settings.html', config=config, first_run=False)

@bp.route('/settings/help')
def help_token():
    return render_template('help_token.html')

@bp.route('/api/settings', methods=['GET'])
def api_get_settings():
    config = load_config()
    config['ksef_token_masked'] = _mask_token(config.get('ksef_token', ''))
    return jsonify(config)

@bp.route('/api/settings', methods=['POST'])
def api_save_settings():
    data = request.get_json()
    allowed_keys = ['ksef_token', 'nip', 'environment', 'default_printer', 'auto_fetch_on_start']
    filtered = {k: v for k, v in data.items() if k in allowed_keys}
    saved = save_config(filtered)
    return jsonify({'ok': True, 'config': saved})

@bp.route('/api/settings/test', methods=['POST'])
def api_test_connection():
    config = load_config()
    data = request.get_json() or {}

    token = data.get('ksef_token') or config.get('ksef_token', '')
    nip = data.get('nip') or config.get('nip', '')
    env = data.get('environment') or config.get('environment', 'prod')

    if not token or not nip:
        return jsonify({'ok': False, 'message': 'Podaj token KSeF i NIP'})

    api = KSeFAPI(token=token, nip=nip, environment=env)
    ok, message = api.test_connection()
    return jsonify({'ok': ok, 'message': message})

# --- Vehicles API ---

@bp.route('/api/vehicles')
def api_get_vehicles():
    vehicles = db.get_vehicles()
    return jsonify(vehicles)

@bp.route('/api/vehicles', methods=['POST'])
def api_add_vehicle():
    data = request.get_json()
    plate = data.get('plate', '').strip()
    brand = data.get('brand', '').strip()
    model = data.get('model', '').strip()
    fuel_type = data.get('fuel_type', 'diesel').strip()
    if not plate:
        return jsonify({'ok': False, 'message': 'Podaj tablicę rejestracyjną'}), 400
    db.add_vehicle(plate, brand, model, fuel_type)
    return jsonify({'ok': True, 'message': f'Dodano pojazd {plate}'})

@bp.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
def api_update_vehicle(vehicle_id):
    data = request.get_json()
    plate = data.get('plate', '').strip()
    brand = data.get('brand', '').strip()
    model = data.get('model', '').strip()
    fuel_type = data.get('fuel_type', 'diesel').strip()
    if not plate:
        return jsonify({'ok': False, 'message': 'Podaj tablicę rejestracyjną'}), 400
    db.update_vehicle(vehicle_id, plate, brand, model, fuel_type)
    return jsonify({'ok': True})

@bp.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def api_delete_vehicle(vehicle_id):
    db.delete_vehicle(vehicle_id)
    return jsonify({'ok': True})


def _mask_token(token):
    if not token or len(token) < 8:
        return token
    return token[:4] + '*' * (len(token) - 8) + token[-4:]
