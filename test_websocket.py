#!/usr/bin/env python3
import time
import socketio

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")

@sio.event
def disconnect():
    print("Disconnected from server")

# Define a custom event for the heartbeat
@sio.event
def heartbeat():
    print("Sent heartbeat message")

# Connect to the Socket.IO server
try:
    print("Attempting to connect to Socket.IO server...")
    sio.connect('http://127.0.0.1:5000', wait_timeout=10)
    print("Successfully connected to Socket.IO server")

    # Emit a heartbeat message
    sio.emit('heartbeat')
    print("Heartbeat message sent")

    # Wait for 2 seconds before disconnecting
    time.sleep(2)
except socketio.exceptions.ConnectionError as e:
    print(f"Failed to connect to Socket.IO server: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

# Disconnect from the Socket.IO server
sio.disconnect()