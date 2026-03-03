from flask import Blueprint, render_template, jsonify, request
from ..services.config_manager import load_config, save_config
from ..services.ksef_api import KSeFAPI

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

def _mask_token(token):
    if not token or len(token) < 8:
        return token
    return token[:4] + '*' * (len(token) - 8) + token[-4:]
