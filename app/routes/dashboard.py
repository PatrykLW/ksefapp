from flask import Blueprint, render_template, jsonify
from datetime import datetime
from ..services import db
from ..services.config_manager import load_config

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    config = load_config()
    has_token = bool(config.get('ksef_token'))
    if not has_token:
        return render_template('settings.html', config=config, first_run=True)
    return render_template('dashboard.html', config=config)

@bp.route('/api/dashboard/stats')
def dashboard_stats():
    now = datetime.now()
    stats = db.get_stats(month=now.month, year=now.year)
    recent = db.get_invoices({'limit': 5})
    config = load_config()
    return jsonify({
        'stats': stats,
        'recent_invoices': recent,
        'has_token': bool(config.get('ksef_token')),
        'last_sync': config.get('last_sync', ''),
        'month': now.month,
        'year': now.year,
    })
