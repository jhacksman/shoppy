import React, { useState, useEffect, useCallback } from 'react';
import { ChakraProvider, Box, VStack, HStack, Text, Slider, SliderTrack, SliderFilledTrack, SliderThumb, Button, useColorModeValue, Alert, AlertIcon } from '@chakra-ui/react';
import { io } from 'socket.io-client';

const socket = io('http://127.0.0.1:5000', {
  transports: ['websocket'],
  cors: {
    origin: 'http://localhost:3000',
    methods: ["GET", "POST"]
  },
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
});

function App() {
  const [leftMotorPower, setLeftMotorPower] = useState(0);
  const [rightMotorPower, setRightMotorPower] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [gradualStop, setGradualStop] = useState(false);
  const [isGamepadConnected, setIsGamepadConnected] = useState(false);
  const [controlMethod, setControlMethod] = useState('sliders');

  const bgColor = useColorModeValue("gray.100", "gray.700");
  const textColor = useColorModeValue("gray.800", "white");
  const sliderColor = useColorModeValue("blue.500", "blue.200");

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    });

    socket.on('disconnect', (reason) => {
      console.log('Disconnected from WebSocket server:', reason);
      setIsConnected(false);
    });

    socket.on('control_response', (data) => {
      console.log('Received response:', data);
      if (data.motor === 'left') {
        setLeftMotorPower(data.value);
      } else if (data.motor === 'right') {
        setRightMotorPower(data.value);
      }
    });

    socket.on('gradual_stop', () => {
      console.log('Gradual stop initiated');
      setGradualStop(true);
    });

    socket.on('connection_status', (data) => {
      console.log('Connection status:', data);
    });

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('control_response');
      socket.off('gradual_stop');
      socket.off('connection_status');
    };
  }, []);

  const handleControlInputChange = useCallback((value, motor) => {
    if (isConnected) {
      if (motor === 'left') {
        setLeftMotorPower(value);
      } else if (motor === 'right') {
        setRightMotorPower(value);
      }
      socket.emit('control_command', { motor, value });
      setGradualStop(false);
    } else {
      console.error('Not connected to server');
    }
  }, [isConnected]);

  const handleStop = () => {
    setLeftMotorPower(0);
    setRightMotorPower(0);
    socket.emit('control_command', { motor: 'both', value: 0 });
  };

  const handleStart = () => {
    // You can define a default starting power or use the current values
    const startPower = 0.5;
    setLeftMotorPower(startPower);
    setRightMotorPower(startPower);
    socket.emit('control_command', { motor: 'both', value: startPower });
  };

  const handleReset = () => {
    setLeftMotorPower(0);
    setRightMotorPower(0);
    socket.emit('control_command', { motor: 'reset', value: 0 });
  };


  const handleGamepadConnect = (event) => {
    setIsGamepadConnected(true);
    setControlMethod('gamepad');
    console.log('Gamepad connected:', event.gamepad);
  };

  const handleGamepadDisconnect = (event) => {
    setIsGamepadConnected(false);
    handleStop();
    handleControlInputChange();
    console.log('Gamepad disconnected:', event.gamepad);
  };

  const applyDeadZone = (value) => {
    return Math.abs(value) < DEAD_ZONE ? 0 : value;
  };

  useEffect(() => {
    const handleKeyDown = (event) => {
      console.log('Key pressed:', event.key);
      let newLeftMotorPower = leftMotorPower;
      let newRightMotorPower = rightMotorPower;
      switch(event.key.toLowerCase()) {
        case 'f':
          newLeftMotorPower = Math.min(leftMotorPower + 0.1, 1);
          console.log('Increasing left power');
          break;
        case 'v':
          newLeftMotorPower = Math.max(leftMotorPower - 0.1, -1);
          console.log('Decreasing left power');
          break;
        case 'j':
          newRightMotorPower = Math.min(rightMotorPower + 0.1, 1);
          console.log('Increasing right power');
          break;
        case 'n':
          newRightMotorPower = Math.max(rightMotorPower - 0.1, -1);
          console.log('Decreasing right power');
          break;
        default:
          return;
      }
      console.log('New power values:', { left: newLeftMotorPower, right: newRightMotorPower });
      setLeftMotorPower(newLeftMotorPower);
      setRightMotorPower(newRightMotorPower);
      setControlMethod('keyboard');
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('gamepadconnected', handleGamepadConnect);
    window.addEventListener('gamepaddisconnected', handleGamepadDisconnect);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('gamepadconnected', handleGamepadConnect);
      window.removeEventListener('gamepaddisconnected', handleGamepadDisconnect);
    };
  }, [leftMotorPower, rightMotorPower]);

  return (
    <ChakraProvider>
      <Box minH="100vh" bg={bgColor} color={textColor} p={[4, 6, 8]}>
        <VStack spacing={8} align="stretch">
          <Text fontSize={["3xl", "4xl", "5xl"]} fontWeight="bold" textAlign="center">Shoppy Control Interface</Text>
          <Box>
            <Text fontSize="lg" mb={2}>Connection Status: {isConnected ? 'Connected' : 'Disconnected'}</Text>
            {gradualStop && (
              <Alert status="warning" mb={4}>
                <AlertIcon />
                Gradual stop initiated due to inactivity
              </Alert>
            )}
          </Box>
          <HStack spacing={[4, 6, 8]} justify="center" flexWrap="wrap">
            <VStack spacing={4} minW={["200px", "250px", "300px"]}>
              <Text fontSize={["lg", "xl", "2xl"]}>Left Motor Power</Text>
              <Slider
                aria-label="left-motor-slider"
                value={leftMotorPower}
                min={-1}
                max={1}
                step={0.1}
                onChange={(value) => handleControlInputChange(value, 'left')}
                w="100%"
                isDisabled={!isConnected}
              >
                <SliderTrack h="10px">
                  <SliderFilledTrack bg={sliderColor} />
                </SliderTrack>
                <SliderThumb boxSize={6} />
              </Slider>
              <Text fontSize="md">{leftMotorPower.toFixed(2)}</Text>
            </VStack>
            <VStack spacing={4} minW={["200px", "250px", "300px"]}>
              <Text fontSize={["lg", "xl", "2xl"]}>Right Motor Power</Text>
              <Slider
                aria-label="right-motor-slider"
                value={rightMotorPower}
                min={-1}
                max={1}
                step={0.1}
                onChange={(value) => handleControlInputChange(value, 'right')}
                w="100%"
                isDisabled={!isConnected}
              >
                <SliderTrack h="10px">
                  <SliderFilledTrack bg={sliderColor} />
                </SliderTrack>
                <SliderThumb boxSize={6} />
              </Slider>
              <Text fontSize="md">{rightMotorPower.toFixed(2)}</Text>
            </VStack>
          </HStack>
          <HStack justify="center" spacing={4}>
            <Button colorScheme="red" onClick={handleStop} size="lg" isDisabled={!isConnected}>Stop</Button>
            <Button colorScheme="green" onClick={handleStart} size="lg" isDisabled={!isConnected}>Start</Button>
            <Button colorScheme="gray" onClick={handleReset} size="lg" isDisabled={!isConnected}>Reset</Button>
          </HStack>
          <HStack spacing={4}>
            <Button onClick={handleGamepadConnect} isDisabled={isGamepadConnected}>Connect Gamepad</Button>
            <Button onClick={handleGamepadDisconnect}>Disconnect</Button>
          </HStack>
        </VStack>
      </Box>
    </ChakraProvider>
  );
}

export default App;