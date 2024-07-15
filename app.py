from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('control_command')
def handle_control_command(message):
    # Placeholder for handling control commands
    print('Received control command:', message)
    # Emit the response back to the client
    emit('control_response', {'status': 'received'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')