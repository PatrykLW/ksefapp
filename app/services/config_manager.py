import os
import json

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
    return os.path.join(base, 'config.json')

def load_config():
    path = _get_config_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        merged = {**CONFIG_DEFAULTS, **data}
        return merged
    return dict(CONFIG_DEFAULTS)

def save_config(data):
    path = _get_config_path()
    current = load_config()
    current.update(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
    return current

def get_config_value(key, default=None):
    cfg = load_config()
    return cfg.get(key, default)

config = load_config()
