import serial
import time

# Placeholder for the serial port to connect to ODrive
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200

class ODriveUART:
    def __init__(self):
        self.serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    def send_command(self, command):
        self.serial_connection.write(command.encode())

    def read_response(self):
        return self.serial_connection.readline().decode().strip()

    def close_connection(self):
        self.serial_connection.close()

# Example usage
if __name__ == '__main__':
    odrive_uart = ODriveUART()
    try:
        # Send a command to ODrive (example command, to be replaced with actual ones)
        odrive_uart.send_command('example_command\n')
        # Wait for the response
        time.sleep(1)
        # Read the response
        response = odrive_uart.read_response()
        print(f'Response from ODrive: {response}')
    finally:
        odrive_uart.close_connection()