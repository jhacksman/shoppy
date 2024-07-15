import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from uart_communication import ODriveUART

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

odrive_uart = ODriveUART()

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

@socketio.on('disconnect')
def handle_disconnect():
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
        print(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')