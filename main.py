import sys
import os
import threading
import webview

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

os.environ['KSEFAPP_BASE_PATH'] = get_base_path()

from app import create_app

def start_flask(app):
    app.run(host='127.0.0.1', port=0, debug=False, use_reloader=False)

def find_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

if __name__ == '__main__':
    port = find_free_port()
    app = create_app()

    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    webview.create_window(
        'KSeF Panel',
        f'http://127.0.0.1:{port}',
        width=1280,
        height=860,
        min_size=(1000, 650),
        text_select=True,
    )
    webview.start()
