import os
import json
import logging

logger = logging.getLogger('config')

CONFIG_DEFAULTS = {
    "ksef_token": "",
    "nip": "",
    "environment": "prod",
    "default_printer": "",
    "auto_fetch_on_start": True,
    "last_sync": ""
}

def _get_config_path():
    base = os.environ.get('KSEFAPP_BASE_PATH', os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, 'config.json')
    return path

def load_config():
    path = _get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            if not raw:
                return dict(CONFIG_DEFAULTS)
            data = json.loads(raw)
            merged = {**CONFIG_DEFAULTS, **data}
            return merged
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania config.json ({path}): {e}")
            return dict(CONFIG_DEFAULTS)
        except Exception as e:
            logger.error(f"Błąd odczytu config.json ({path}): {e}")
            return dict(CONFIG_DEFAULTS)
    else:
        save_config(CONFIG_DEFAULTS)
        return dict(CONFIG_DEFAULTS)

def save_config(data):
    path = _get_config_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            current = json.loads(raw) if raw else dict(CONFIG_DEFAULTS)
        else:
            current = dict(CONFIG_DEFAULTS)
    except Exception:
        current = dict(CONFIG_DEFAULTS)

    current.update(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
    logger.info(f"Config zapisany: {path}")
    return current

def get_config_value(key, default=None):
    cfg = load_config()
    return cfg.get(key, default)

def get_config_path_info():
    """Return config file path for display in UI."""
    return _get_config_path()

config = load_config()
