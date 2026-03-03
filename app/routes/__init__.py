from .dashboard import bp as dashboard_bp
from .invoices import bp as invoices_bp
from .printing import bp as printing_bp
from .settings import bp as settings_bp
from .stats import bp as stats_bp

def register_routes(app):
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(printing_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(stats_bp)
