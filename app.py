import time, socket, odrive
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

motor_controller = None

try:
    motor_controller = odrive.find_any()
except Exception as e:
    print(f"Could not find the motor driver!\n\t{e}")
    exit(-1)

app = Flask(__name__)

cors_origins = ["http://localhost:3000", f"http://{socket.gethostname()}.local:3000" ]

CORS(app, resources={r"/*": {"origins": cors_origins }})
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

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
        power_cut()

@socketio.on('disconnect')
def handle_disconnect():
    power_cut()
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
        power_cut()
        print(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_inactivity():
    global last_command_time
    while True:
        if time.time() - last_command_time > 1:  # 1 second threshold
            print("No command received for 1 second. Initiating gradual stop.")
            # TODO: Implement gradual stop logic here
            power_cut()
            emit('gradual_stop', broadcast=True)
        socketio.sleep(0.1)  # Check every 100ms

if __name__ == '__main__':
    socketio.start_background_task(check_inactivity)
    socketio.run(app, debug=True, host='0.0.0.0')

# Temporary crappy stop-if-error case handler
def power_cut():
    motor_controller.axis0.controller.input_vel = 0
    motor_controller.axis0.controller.input_vel = 0
