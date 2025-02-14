import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from scanner import NetworkScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

scanner = NetworkScanner(socketio)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_scan')
def handle_scan(data):
    target = data.get('target')
    ports = data.get('ports', '1-1000')
    try:
        scanner.start_scan(target, ports)
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        socketio.emit('scan_error', {'error': str(e)})

@socketio.on('stop_scan')
def handle_stop_scan():
    scanner.stop_scan()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True, log_output=True)