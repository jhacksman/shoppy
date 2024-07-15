import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

last_command_time = time.time()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    try:
        print('Client connected')
        emit('connection_status', {'status': 'connected'})
    except Exception as e:
        print(f"Error handling connection: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    try:
        print('Client disconnected')
        # TODO: Implement any necessary cleanup or safety measures on disconnect
    except Exception as e:
        print(f"Error handling disconnection: {str(e)}")

@socketio.on('control_command')
def handle_control_command(message):
    global last_command_time
    try:
        print('Received control command:', message)
        # Placeholder for handling control commands
        # TODO: Implement actual motor control logic here
        emit('control_response', {'status': 'received'})
        last_command_time = time.time()
    except Exception as e:
        print(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_inactivity():
    global last_command_time
    while True:
        if time.time() - last_command_time > 1:  # 1 second threshold
            print("No command received for 1 second. Initiating gradual stop.")
            # TODO: Implement gradual stop logic here
            emit('gradual_stop', broadcast=True)
        socketio.sleep(0.1)  # Check every 100ms

if __name__ == '__main__':
    socketio.start_background_task(check_inactivity)
    socketio.run(app, debug=True, host='0.0.0.0')