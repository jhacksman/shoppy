# Shoppy Robotic Shopping Cart Control Interface

## Introduction
Shoppy is a web-based control interface for a robotic shopping cart, designed to facilitate real-time communication between the user interface and the robot's motors. It ensures precise control and includes safety features such as a gradual stop in case of disconnection or lag.

## Key Features
- Real-time bidirectional communication using WebSockets
- Support for USB gamepad (Xbox compatible), touchscreen, and keyboard inputs
- Display of real-time power values for left and right motors (-1 to 1 range)
- Gradual stop mechanism for safety

## Installation
To set up the Shoppy project, follow these steps:
1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Set up a virtual environment: `python3 -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate`
5. Install the required Python packages: `pip install -r requirements.txt`
6. Start the Flask server: `python3 app.py`
7. Navigate to the `frontend` directory.
8. Install the required Node packages: `npm install`
9. Start the React development server: `npm start`
10. Open your web browser and go to `http://localhost:3000` to view the interface.

## Deploying on Raspberry Pi

To deploy the Shoppy application on a Raspberry Pi:

1. Ensure your Raspberry Pi is set up with Raspberry Pi OS and has internet access.
2. Install Git on your Raspberry Pi if not already installed:
   ```
   sudo apt-get update
   sudo apt-get install git
   ```
3. Clone the repository:
   ```
   git clone https://github.com/jhacksman/shoppy.git
   ```
4. Navigate to the project directory:
   ```
   cd shoppy
   ```
5. Make the deployment script executable:
   ```
   chmod +x deploy_on_pi.sh
   ```
6. Run the deployment script:
   ```
   ./deploy_on_pi.sh
   ```

The script will set up a Python virtual environment, install all necessary dependencies, and start the Flask server.

Note: Ensure that your Raspberry Pi has the required hardware connections for UART communication with the ODrive motor controller.

For any issues during deployment, please refer to the Troubleshooting section or open an issue on the GitHub repository.

## Testing
To test the system:
1. Ensure that both the Flask server (http://127.0.0.1:5000) and React server (http://localhost:3000) are running.
2. Use the interface to send control commands and verify that the robot's motors respond accordingly.
3. Monitor the console for any errors or latency issues.

## Deployment
For deployment on a Raspberry Pi:
1. Transfer the project files to the Raspberry Pi.
2. Repeat the installation steps on the Raspberry Pi.
3. Ensure the Raspberry Pi is connected to the ODrive motor controller.
4. Start the Flask server and ensure it's accessible on the Pi's IP address.
5. Access the interface from any device on the same network as the Pi.

## Safety Features
The Shoppy interface includes a gradual stop mechanism that safely decelerates the robot in case of signal loss. If the control signal is lost for more than 1 second, the system will automatically reduce the power values to zero.

## UI/UX Features
The Shoppy interface is designed with a focus on a top-tier user experience:
- Built with Chakra UI for modern styling
- Supports various control methods including USB gamepad, touchscreen, and keyboard inputs
- Displays real-time power values for the left and right motors
- Provides a responsive and intuitive control experience