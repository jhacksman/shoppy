import time, socket, odrive, threading, queue   
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

last_heartbeat = time.time()
motor_commands = queue.Queue(maxsize=20)

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
    motor_commands.put((0.0, 0.0), block=True)

app = Flask(__name__)

log = app.logger

cors_origins = ["http://localhost:3000", f"http://{socket.gethostname()}.local:3000", "http://192.168.15.18:3000" ]

CORS(app, resources={r"/*": {"origins": cors_origins }})
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

SAFETY_TIMEOUT = 5.0  # 1 second timeout
current_power = 1.0  # Assuming full power is 1.0
DECELERATION_RATE = 0.1  # Reduce power by 10% each step
DECELERATION_INTERVAL = 0.1  # Decelerate every 100ms

def initiate_gradual_stop():
    #print("No command received. Initiating gradual stop.")
    socketio.start_background_task(gradual_stop)

def gradual_stop():
    global current_power, motor_commands, log
    while current_power > 0:
        current_power = max(0, current_power - DECELERATION_RATE)
        motor_commands.put((-current_power, current_power), block=True)
        log.info(f"Reducing power to {current_power}")
        socketio.sleep(DECELERATION_INTERVAL)
    log.info("Gradual stop completed")
    #emit('gradual_stop_completed', broadcast=True)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global log
    try:
        log.info('Client connected')
        emit('connection_status', {'status': 'connected'})
        emit('heartbeat')
    except Exception as e:
        log.error(f"Error handling connection: {str(e)}")
        power_cut()

@socketio.on('disconnect')
def handle_disconnect():
    global log
    power_cut()
    try:
        log.info('Client disconnected')
    except Exception as e:
        log.error(f"Error handling disconnection: {str(e)}")

@socketio.on('heartbeat')
def handle_heartbeat():
    global last_heartbeat, log
    last_heartbeat = time.time()
    socketio.sleep(SAFETY_TIMEOUT*0.95)
    log.info("Heartbeat recv'd")
    emit('heartbeat')

@socketio.on('control_command')
def handle_control_command(message):
    global last_heartbeat, current_power, motor_commands, log
    if time.time() - last_heartbeat > SAFETY_TIMEOUT:
        initiate_gradual_stop()
        disconnect()
        return
    try:
        log.info(f'Received control command: {message} motor queue size: {motor_commands.qsize()}' )
        # Implement actual motor control logic here
        if message.get('motor') != None and not motor_commands.full():
            val = float(message.get('value', 0))
            if abs(val) < 0.1:
                val = 0
            match message.get('motor', 'reset'):
                case 'right':
                    motor_commands.put_nowait((None, val));
                case 'left':
                    motor_commands.put_nowait((-val, None));
                case 'both':
                    motor_commands.put_nowait((-val, val));
                case 'reset':
                    motor_commands.put_nowait((0.0, 0.0));

        current_power = message.get('power', current_power)
        emit('control_response', {'status': 'received', 'power': current_power})
    except Exception as e:
        power_cut()
        log.error(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_connection():
    global last_heartbeat, log
    log.info('Starting connection test',flush=True)
    while True:
        if time.time() - last_heartbeat > SAFETY_TIMEOUT:
            initiate_gradual_stop()
        socketio.sleep(0.5)  # Check every 100ms

def motor_control_consumer(): 
    global motor_commands, log
    while True:
        try:
            drive = odrive.find_any()
            odrive.utils.dump_errors(drive, clear=True)
            drive.reboot()
            del drive
            log.info(f'Found odrive, rebooting...',flush=True)
            drive = odrive.find_any()
            odrive.utils.dump_errors(drive, clear=True)
            log.info(f'Drive initialized', flush=True)
            while True:
                try:
                    cmd = motor_commands.get_nowait()
                    print(f'CMD Tuple {cmd}', flush=True)
                    if cmd[0] != None:
                        drive.axis0.controller.input_vel = cmd[0]
                    if cmd[1] != None:
                        drive.axis1.controller.input_vel = cmd[1]
                except:
                    socketio.sleep(0.05)
        except e as Exception:
            log.error("Could not initilize motor controller, trying again in 10 seconds...")
            log.error(f"\t{e}")
            socket.sleep(10)
        
            


if __name__ == '__main__':
    socketio.start_background_task(check_connection)
    socketio.start_background_task(motor_control_consumer)
    socketio.run(app, host='0.0.0.0')