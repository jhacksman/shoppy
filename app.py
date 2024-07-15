import time, socket, odrive, threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from uart_communication import ODriveUART

motor_controller = None
last_heartbeat = time.time()

# Comment out ODrive initialization for testing purposes
# try:
#     motor_controller = odrive.find_any()
#     motor_controller.clear_errors()
#     motor_controller.axis0.controller.input_vel = 0
#     motor_controller.axis1.controller.input_vel = 0
# except Exception as e:
#     print(f"Could not find the motor driver!\n\t{e}")
#     exit(-1)

# Temporary crappy stop-if-error case handler
def power_cut():
    global motor_controller
    if motor_controller:
        motor_controller.axis0.controller.input_vel = 0
        motor_controller.axis1.controller.input_vel = 0

app = Flask(__name__)

cors_origins = ["http://localhost:3000", f"http://{socket.gethostname()}.local:3000" ]

CORS(app, resources={r"/*": {"origins": cors_origins }})
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

SAFETY_TIMEOUT = 1.0  # 1 second timeout
current_power = 1.0  # Assuming full power is 1.0
DECELERATION_RATE = 0.1  # Reduce power by 10% each step
DECELERATION_INTERVAL = 0.1  # Decelerate every 100ms

def initiate_gradual_stop():
    print("No command received. Initiating gradual stop.")
    socketio.start_background_task(gradual_stop)

def gradual_stop():
    global current_power, motor_controller
    while current_power > 0:
        current_power = max(0, current_power - DECELERATION_RATE)
        if motor_controller:
            motor_controller.axis0.controller.input_vel = -current_power
            motor_controller.axis1.controller.input_vel = current_power
        print(f"Reducing power to {current_power}")
        socketio.sleep(DECELERATION_INTERVAL)
    print("Gradual stop completed")
    emit('gradual_stop_completed', broadcast=True)

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
    except Exception as e:
        print(f"Error handling disconnection: {str(e)}")

@socketio.on('heartbeat')
def handle_heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()

@socketio.on('control_command')
def handle_control_command(message):
    global last_heartbeat, current_power, motor_controller
    if time.time() - last_heartbeat > SAFETY_TIMEOUT:
        initiate_gradual_stop()
        disconnect()
        return
    try:
        print('Received control command:', message)
        # Implement actual motor control logic here
        if message.get('motor') != None and motor_controller:
            val = float(message.get('value', 0))
            if abs(val) < 0.1:
                val = 0
            match message.get('motor', 'reset'):
                case 'right':
                    motor_controller.axis0.controller.input_vel = val
                case 'left':
                    motor_controller.axis1.controller.input_vel = -val
                case 'both':
                    motor_controller.axis0.controller.input_vel = val
                    motor_controller.axis1.controller.input_vel = -val
                case 'reset':
                    motor_controller.axis0.controller.input_vel = 0
                    motor_controller.axis1.controller.input_vel = 0

        current_power = message.get('power', current_power)
        emit('control_response', {'status': 'received', 'power': current_power})
    except Exception as e:
        power_cut()
        print(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_connection():
    global last_heartbeat
    while True:
        if time.time() - last_heartbeat > SAFETY_TIMEOUT:
            initiate_gradual_stop()
        socketio.sleep(0.1)  # Check every 100ms

if __name__ == '__main__':
    socketio.start_background_task(check_connection)
    socketio.run(app, host='0.0.0.0')