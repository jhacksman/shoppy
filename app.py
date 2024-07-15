import time, socket, odrive, threading
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

# Temporary crappy stop-if-error case handler
def power_cut():
    global motor_controller
    motor_controller.axis0.controller.input_vel = 0
    motor_controller.axis0.controller.input_vel = 0

app = Flask(__name__)

cors_origins = ["http://localhost:3000", f"http://{socket.gethostname()}.local:3000" ]

CORS(app, resources={r"/*": {"origins": cors_origins }})
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

last_command_time = time.time()
safety_timer_cutoff = time.monotonic()
SAFETY_TIMEOUT = 1.0  # 1 second timeout
current_power = 1.0  # Assuming full power is 1.0
DECELERATION_RATE = 0.1  # Reduce power by 10% each step
DECELERATION_INTERVAL = 0.1  # Decelerate every 100ms

def start_safety_timer_cutoff():
    global safety_timer_cutoff
    now = time.monotonic()
    if safety_timer_cutoff - SAFETY_TIMEOUT < now:
        safety_timer_cutoff = now + SAFETY_TIMEOUT
        

def initiate_gradual_stop():
    print("No command received. Initiating gradual stop.")
    socketio.start_background_task(gradual_stop)

def gradual_stop():
    global current_power, motor_controller
    while current_power > 0:
        current_power = max(0, current_power - DECELERATION_RATE)
        motor_controller.axis0.controller.input_vel = current_power
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

@socketio.on('control_command')
def handle_control_command(message):
    global current_power, motor_controller
    try:
        print('Received control command:', message)
        # Implement actual motor control logic here
        if message.get('motor') and message.get('value'):
            val = float(message.get('value'))
            print(val)
            match message.get('motor'):
                case 'right':
                    motor_controller.axis0.controller.input_vel = val
                case 'left':
                    motor_controller.axis1.controller.input_vel = val
                case 'both':
                    motor_controller.axis0.controller.input_vel = val
                    motor_controller.axis1.controller.input_vel = val
                case 'reset':
                    motor_controller.axis0.controller.input_vel = 0
                    motor_controller.axis1.controller.input_vel = 0

        current_power = message.get('power', current_power)
        emit('control_response', {'status': 'received', 'power': current_power})
    except Exception as e:
        power_cut()
        print(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_inactivity():
    global last_command_time
    while True:
        if time.time() - last_command_time > SAFETY_TIMEOUT:  # 1 second threshold
            print("No command received for 1 second. Initiating gradual stop.")
            # TODO: Implement gradual stop logic here
            emit('gradual_stop', broadcast=True)
        socketio.sleep(0.1)  # Check every 100ms

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')


