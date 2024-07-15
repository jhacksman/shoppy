import time, socket, odrive
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from uart_communication import ODriveUART

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
safety_timer = None
SAFETY_TIMEOUT = 1.0  # 1 second timeout
current_power = 1.0  # Assuming full power is 1.0
DECELERATION_RATE = 0.1  # Reduce power by 10% each step
DECELERATION_INTERVAL = 0.1  # Decelerate every 100ms

def start_safety_timer():
    global safety_timer
    if safety_timer:
        safety_timer.cancel()
    safety_timer = threading.Timer(SAFETY_TIMEOUT, initiate_gradual_stop)
    safety_timer.start()

def initiate_gradual_stop():
    print("No command received. Initiating gradual stop.")
    socketio.start_background_task(gradual_stop)

def gradual_stop():
    global current_power
    while current_power > 0:
        current_power = max(0, current_power - DECELERATION_RATE)
        odrive_uart.set_motor_power(current_power)
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
        start_safety_timer()
    except Exception as e:
        print(f"Error handling connection: {str(e)}")
        power_cut()

@socketio.on('disconnect')
def handle_disconnect():
    power_cut()
    try:
        print('Client disconnected')
        if safety_timer:
            safety_timer.cancel()
        initiate_gradual_stop()
    except Exception as e:
        print(f"Error handling disconnection: {str(e)}")

@socketio.on('control_command')
def handle_control_command(message):
    global current_power
    try:
        print('Received control command:', message)
        # Implement actual motor control logic here
        current_power = message.get('power', current_power)
        odrive_uart.set_motor_power(current_power)
        emit('control_response', {'status': 'received', 'power': current_power})
        start_safety_timer()
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
    socketio.run(app, host='0.0.0.0')

# Temporary crappy stop-if-error case handler
def power_cut():
    global motor_controller
    motor_controller.axis0.controller.input_vel = 0
    motor_controller.axis0.controller.input_vel = 0
