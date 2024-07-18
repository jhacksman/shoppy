import time, socket, odrive, threading, queue   
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from logging import DEBUG

last_heartbeat = time.time()
motor_commands = queue.Queue(maxsize=50)

app = Flask(__name__)

log = app.logger
log.setLevel(DEBUG)

cors_origins = ["http://localhost:3000", f"http://{socket.gethostname()}.local:3000", "http://192.168.15.18:3000" ]

CORS(app, resources={r"/*": {"origins": cors_origins }})
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

SAFETY_TIMEOUT = 5.0  # 5 second timeout
current_power = 1.0  # Assuming full power is 1.0
DECELERATION_RATE = 0.1  # Reduce power by 10% each step
DECELERATION_INTERVAL = 0.1  # Decelerate every 100ms
SPEED_MULTIPLIER = 1 # DO NOT TOUCH THIS IF YOU DONT KNOW WHAT YOUR DOING!!!!!!


is_stopping = False

# Temporary crappy stop-if-error case handler
def power_cut():
    global log
    log.error(f'Error state caused power cut!')
    motor_commands.put((0.0, 0.0), block=True)

def initiate_gradual_stop():
    global is_stopping
    if not is_stopping:
        is_stopping = True
        socketio.start_background_task(gradual_stop)
    else:
        log.info("Discarding stop command, already stopping!")

def gradual_stop():
    global motor_commands, log, is_stopping
    q = list(motor_commands.queue)
    power = (0,0) if motor_commands.empty() else q[0]
    while ((abs(power[0]) > 0.01) or (abs(power[1]) > 0.01)):
        power = (power[0] * min(DECELERATION_RATE,0.9), power[1] * min(DECELERATION_RATE,0.9)) 
        motor_commands.put(power)
        log.info(f"Reducing power to {power}")
        socketio.sleep(DECELERATION_INTERVAL)
    motor_commands.put((0.0,0.0))
    log.info("Gradual stop completed")
    is_stopping = False
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
        emit('ping')
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

@socketio.on('pong')
def handle_heartbeat():
    global last_heartbeat, log
    last_heartbeat = time.time()
    socketio.sleep(SAFETY_TIMEOUT*0.95)
    log.info("Heartbeat pong recv'd")
    emit('ping')

@socketio.on('control_command')
def handle_control_command(message):
    global last_heartbeat, current_power, motor_commands, log, is_stopping
    if time.time() - last_heartbeat > SAFETY_TIMEOUT:
        initiate_gradual_stop()
        disconnect()
        return
    try:
        log.info(f'Received control command: {message} motor queue size: {motor_commands.qsize()}' )
        # Implement actual motor control logic here
        if message.get('motor') != None and not motor_commands.full() and not is_stopping:
            val = float(message.get('value', 0))
            if abs(val) < 0.1:
                val = 0
            match message.get('motor', 'reset'):
                case 'right':
                    motor_commands.put_nowait((None, val));
                case 'left':
                    motor_commands.put_nowait((val, None));
                case 'both':
                    motor_commands.put_nowait((val, val));
                case 'reset':
                    motor_commands.put_nowait((0.0, 0.0));
                    motor_commands.put_nowait((None, None));

        current_power = message.get('power', current_power)
        emit('control_response', {'status': 'received', 'power': current_power})
    except Exception as e:
        power_cut()
        log.error(f"Error handling control command: {str(e)}")
        emit('error', {'message': 'Error processing command'})

def check_connection():
    global last_heartbeat, log
    log.info('Starting connection test')
    while True:
        if time.time() - last_heartbeat > SAFETY_TIMEOUT:
            log.info(f'Disconnected for too long, stopping...')
            initiate_gradual_stop()
        socketio.sleep(1)

def motor_control_consumer(): 
    global motor_commands, log
    while True:
        try:
            log.info("Initilizing ODrive...")
            drive = odrive.find_any()
            drive.axis0.config.watchdog_timeout=2
            drive.axis1.config.watchdog_timeout=2
            drive.axis0.config.enable_watchdog=True
            drive.axis1.config.enable_watchdog=True
            drive.axis0.watchdog_feed()
            drive.axis1.watchdog_feed()
            drive.axis0.requested_state = odrive.utils.AXIS_STATE_CLOSED_LOOP_CONTROL
            drive.axis1.requested_state = odrive.utils.AXIS_STATE_CLOSED_LOOP_CONTROL
            
            odrive.utils.dump_errors(drive, clear=True)
            if (drive.error != 0) or (drive.axis0.error != 0) or (drive.axis1.error != 0):
                drive.reboot()
                log.error("ODrive error... retrying in 5 second...")
                socketio.sleep(5)
                continue
            log.info(f'Drive initialized')
            while True:
                drive.axis0.watchdog_feed()
                drive.axis1.watchdog_feed()
                try:
                    cmd = motor_commands.get(timeout=1)
                    log.debug(f'CMD Tuple {cmd}')
                    log.debug(f'Motor Current {drive.ibus}, Bus Voltage{drive.vbus_voltage}')
                    if cmd[0] != None:
                        drive.axis1.controller.input_vel = -float(cmd[0])*SPEED_MULTIPLIER
                    if cmd[1] != None:
                        # Negated to correct for fliped motor rotation dir
                        drive.axis0.controller.input_vel = float(cmd[1])*SPEED_MULTIPLIER
                    if cmd[0] == None and cmd[1] == None:
                        log.info("Resetting ODrive...")
                        try:
                            drive.reboot()
                            socketio.sleep(5)
                        except Exception as e:
                            log.error(f"Could not reboot ODrive... {e}")
                        break
                except:
                    socketio.sleep(0.5)
        except Exception as e:
            log.error("Could not initilize motor controller, trying again in 2 seconds...")
            log.error(f"{e}")
            socketio.sleep(2)
            continue
        
            


if __name__ == '__main__':
    socketio.start_background_task(check_connection)
    socketio.start_background_task(motor_control_consumer)
    socketio.run(app, host='0.0.0.0')