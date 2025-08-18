import asyncio
import json
import logging
from datetime import datetime
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import RPi.GPIO as GPIO

# NOTE: Johnson IP: 192.168.1.55

class MotorController:
    def __init__(self):
        self.motor_pins_front = {
            'left_motor': {
                'Cw': 7,
                'CCw': 16,
            },
            'right_motor': {
                'Cw': 11, 
                'CCw': 13,
            }
        }

        self.motor_pins_back = {
            'left_motor': {
                'Cw': 33,
                'CCw': 29,
            },
            'right_motor': {
                'Cw': 37,  
                'CCw': 36,
            }
        }
        
        # Track current motor states for safety
        self.motor_states = {
            'front_left': 'stopped',
            'front_right': 'stopped',
            'back_left': 'stopped',
            'back_right': 'stopped'
        }
        
        self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins for motor control"""
        try:
            # Set GPIO mode to BCM (Broadcom pin numbering)
            GPIO.setmode(GPIO.BOARD)
            
            # Disable GPIO warnings (for production)
            GPIO.setwarnings(False)
            
            # Setup all pins as outputs with initial LOW state
            all_pins = []
            
            # Collect all pins from front motors
            for motor in self.motor_pins_front.values():
                all_pins.extend(motor.values())
                
            # Collect all pins from back motors  
            for motor in self.motor_pins_back.values():
                all_pins.extend(motor.values())
            
            # Setup each pin as output, starting LOW (motors stopped)
            for pin in all_pins:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            
            print(f"GPIO pins configured for motor controller: {all_pins}")
            print("All motors initialized to STOPPED state")
            
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            raise
        
    def _set_motor(self, motor_pins, direction):
        """
        Set a single motor's direction
        motor_pins: dict with 'Cw' and 'CCw' pin numbers
        direction: 'forward', 'backward', or 'stop'
        """
        cw_pin = motor_pins['Cw']
        ccw_pin = motor_pins['CCw']
        
        if direction == 'forward':
            GPIO.output(cw_pin, GPIO.HIGH)
            GPIO.output(ccw_pin, GPIO.LOW)
        elif direction == 'backward':
            GPIO.output(cw_pin, GPIO.LOW)
            GPIO.output(ccw_pin, GPIO.HIGH)
        elif direction == 'stop':
            GPIO.output(cw_pin, GPIO.LOW)
            GPIO.output(ccw_pin, GPIO.LOW)
        # else:
        #     raise ValueError(f"Invalid direction: {direction}")
    
    def move_forward(self):
        """Move all motors forward"""

        try:
            # Set all motors to move forward
            self._set_motor(self.motor_pins_front['left_motor'], 'forward')
            self._set_motor(self.motor_pins_front['right_motor'], 'backward')
            self._set_motor(self.motor_pins_back['left_motor'], 'forward')
            self._set_motor(self.motor_pins_back['right_motor'], 'backward')
            
            # Update states
            self.motor_states['front_left'] = 'moving_forward'
            self.motor_states['front_right'] = 'moving_backward'
            self.motor_states['back_left'] = 'moving_forward'
            self.motor_states['back_right'] = 'moving_backward'
        except Exception as e:
            print(f"Error in move_forward: {e}")
            self.stop()


        print("Motors: Moving forward")
        
    def move_backward(self):
        """Move all motors backward"""

        try:
            # Set all motors to move forward
            self._set_motor(self.motor_pins_front['left_motor'], 'backward')
            self._set_motor(self.motor_pins_front['right_motor'], 'forward')
            self._set_motor(self.motor_pins_back['left_motor'], 'backward')
            self._set_motor(self.motor_pins_back['right_motor'], 'forward')
            
            # Update states
            self.motor_states['front_left'] = 'moving_backward'
            self.motor_states['front_right'] = 'moving_forward'
            self.motor_states['back_left'] = 'moving_backward'
            self.motor_states['back_right'] = 'moving_forward'
        except Exception as e:
            print(f"Error in move_forward: {e}")
            self.stop()

        print("Motors: Moving backward")
        
    def turn_left(self):
        print("Motors: Turning left")
        try:
            # Set all motors to move forward
            self._set_motor(self.motor_pins_front['left_motor'], 'backward')
            self._set_motor(self.motor_pins_front['right_motor'], 'backward')
            self._set_motor(self.motor_pins_back['left_motor'], 'backward')
            self._set_motor(self.motor_pins_back['right_motor'], 'backward')
            
            # Update states
            self.motor_states['front_left'] = 'moving_backward'
            self.motor_states['front_right'] = 'moving_backward'
            self.motor_states['back_left'] = 'moving_backward'
            self.motor_states['back_right'] = 'moving_backward'
        except Exception as e:
            print(f"Error in move_forward: {e}")

        
    def turn_right(self):
        print("Motors: Turning right")
        try:
            # Set all motors to move forward
            self._set_motor(self.motor_pins_front['left_motor'], 'forward')
            self._set_motor(self.motor_pins_front['right_motor'], 'forward')
            self._set_motor(self.motor_pins_back['left_motor'], 'forward')
            self._set_motor(self.motor_pins_back['right_motor'], 'forward')
            
            # Update states
            self.motor_states['front_left'] = 'moving_forward'
            self.motor_states['front_right'] = 'moving_forward'
            self.motor_states['back_left'] = 'moving_forward'
            self.motor_states['back_right'] = 'moving_forward'
        except Exception as e:
            print(f"Error in move_forward: {e}")
            self.stop()
            self.stop()

        
    def stop(self):
        """Stop all motors immediately"""
        try:
            # Stop all motors
            self._set_motor(self.motor_pins_front['left_motor'], 'stop')
            self._set_motor(self.motor_pins_front['right_motor'], 'stop')
            self._set_motor(self.motor_pins_back['left_motor'], 'stop')
            self._set_motor(self.motor_pins_back['right_motor'], 'stop')
            
            # Update states
            for key in self.motor_states:
                self.motor_states[key] = 'stopped'
            
            print("Motors: Stopped")
            
        except Exception as e:
            print(f"Error in stop: {e}")
            # Try to force all pins LOW as emergency stop
            try:
                all_pins = []
                for motor in self.motor_pins_front.values():
                    all_pins.extend(motor.values())
                for motor in self.motor_pins_back.values():
                    all_pins.extend(motor.values())
                
                for pin in all_pins:
                    GPIO.output(pin, GPIO.LOW)
            except:
                pass  # Last resort attempt
        
    def get_motor_status(self):
        """Get current status of all motors"""
        return self.motor_states.copy()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            print("Cleaning up GPIO resources...")
            
            # First stop all motors
            self.stop()
            
            # Small delay to ensure motors have stopped
            time.sleep(0.1)
            
            # Clean up GPIO
            GPIO.cleanup()
            
            print("GPIO cleanup completed")
            
        except Exception as e:
            print(f"Error during GPIO cleanup: {e}")

class SensorController:
    def __init__(self):
        self.sensor_pins = {
        }
        
        self.setup_sensors()
        
    def setup_sensors(self):
        """Initialize sensor GPIO pins"""
        
        print("Sensor pins configured")
        
    def get_distance(self):
        """Get distance from ultrasonic sensor"""
        # Placeholder return value
        return 50.0  # cm
        
    def get_sensor_data(self):
        """Collect all sensor readings"""
        return {
            'distance': self.get_distance(),
            'timestamp': datetime.now().isoformat()
        }

class RCCarServer:
    def __init__(self, host='0.0.0.0', port=59726):
        self.host = host
        self.port = port
        self.motor_controller = MotorController()
        self.sensor_controller = SensorController()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Active connections
        self.clients = set()
        
    async def handle_client(self, reader, writer):
        """Handle individual client connections"""
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"Client connected: {client_addr}")
        self.clients.add(writer)
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                    
                message = data.decode().strip()
                if message:
                    await self.process_command(message, writer)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"Client disconnected: {client_addr}")
            
    async def process_command(self, message, writer):
        """Process incoming commands from client"""
        try:
            command = json.loads(message)
            direction = command.get('direction')
            action = command.get('action')
            
            self.logger.info(f"Received command: {direction} {action}")
            
            # Execute motor commands
            if action == "start":
                if direction == "forward":
                    self.motor_controller.move_forwards() 
                elif direction == "backward":
                    self.motor_controller.move_backwards()
                elif direction == "left":
                    self.motor_controller.turn_left()
                elif direction == "right":
                    self.motor_controller.turn_right()
            elif action == "stop":
                self.motor_controller.stop()
                
            # Send response back to client
            response = {
                'status': 'success',
                'command': f"{direction} {action}",
                'timestamp': datetime.now().isoformat(),
                'sensor_data': self.sensor_controller.get_sensor_data()
            }
            
            response_json = json.dumps(response) + "\n"
            writer.write(response_json.encode())
            await writer.drain()
            
        except json.JSONDecodeError:
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON command',
                'timestamp': datetime.now().isoformat()
            }
            response_json = json.dumps(error_response) + "\n"
            writer.write(response_json.encode())
            await writer.drain()
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            response_json = json.dumps(error_response) + "\n"
            writer.write(response_json.encode())
            await writer.drain()
            
    async def broadcast_sensor_data(self):
        """Periodically broadcast sensor data to all clients"""
        while True:
            if self.clients:
                sensor_data = {
                    'type': 'sensor_update',
                    'data': self.sensor_controller.get_sensor_data()
                }
                
                message = json.dumps(sensor_data) + "\n"
                disconnected_clients = set()
                
                for client in self.clients:
                    try:
                        client.write(message.encode())
                        await client.drain()
                    except Exception:
                        disconnected_clients.add(client)
                        
                # Remove disconnected clients
                self.clients -= disconnected_clients
                
            await asyncio.sleep(5)  # Send sensor data every second
            
    async def start_server(self):
        """Start the asyncio server"""
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        self.logger.info(f"RC Car server started on {self.host}:{self.port}")
        
        # Start sensor data broadcasting task
        sensor_task = asyncio.create_task(self.broadcast_sensor_data())
        
        async with server:
            try:
                await server.serve_forever()
            except KeyboardInterrupt:
                self.logger.info("Server shutdown requested")
            finally:
                sensor_task.cancel()
                self.motor_controller.cleanup()
                
    def run(self):
        """Run the server"""
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")

class CameraController:
    def __init__(self):
        self.camera = None
        self.streaming = False
        self.frame_buffer = None
        
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            
            # Configure camera for 640x480 at 30fps
            config = self.camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                controls={"FrameRate": 30}
            )
            self.camera.configure(config)
            print("Raspberry Pi camera initialized successfully")
            
        except ImportError:
            print("Warning: picamera2 not available, using test pattern")
            self.camera = None
        except Exception as e:
            print(f"Warning: Camera initialization failed: {e}, using test pattern")
            self.camera = None
        
    def start_camera(self):
        """Start camera capture"""
        if self.camera:
            try:
                self.camera.start()
                self.streaming = True
                print("Raspberry Pi camera started")
            except Exception as e:
                print(f"Error starting camera: {e}")
                self.streaming = False
        else:
            self.streaming = True
            print("Test pattern started (no camera available)")
        
    def stop_camera(self):
        """Stop camera capture"""
        if self.camera and self.streaming:
            try:
                self.camera.stop()
                print("Raspberry Pi camera stopped")
            except Exception as e:
                print(f"Error stopping camera: {e}")
        else:
            print("Test pattern stopped")
            
        self.streaming = False
        
    def capture_frame(self):
        """Capture a single frame as JPEG bytes"""
        if self.camera and self.streaming:
            try:
                # Capture frame as numpy array
                frame = self.camera.capture_array()
                
                # Convert RGB to BGR for OpenCV (if using cv2)
                # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Convert to JPEG using PIL (more reliable than cv2)
                import io
                from PIL import Image
                
                # Convert numpy array to PIL Image
                image = Image.fromarray(frame)
                
                # Compress to JPEG
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85, optimize=True)
                return buffer.getvalue()
                
            except Exception as e:
                print(f"Error capturing frame: {e}")
                return self._generate_test_frame()
        else:
            # Fallback to test pattern
            return self._generate_test_frame()
            
    def _generate_test_frame(self):
        """Generate test pattern when camera unavailable"""
        import io
        from PIL import Image, ImageDraw
        
        # Create test image
        img = Image.new('RGB', (640, 480), color='black')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"RC Car Camera\nTime: {time.strftime('%H:%M:%S')}", 
                 fill='white')
        draw.rectangle([100, 100, 540, 380], outline='green', width=3)
        draw.text((320, 240), "TEST FEED", fill='red', anchor='mm')
        
        # Convert to JPEG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()

class MJPEGStreamHandler(BaseHTTPRequestHandler):
    def __init__(self, camera_controller, *args, **kwargs):
        self.camera_controller = camera_controller
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request for MJPEG stream"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 
                           'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            
            try:
                while True:
                    # Get frame from camera
                    frame_data = self.camera_controller.capture_frame()
                    
                    if frame_data:
                        # Send multipart boundary
                        self.wfile.write(b'--jpgboundary\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n')
                        self.wfile.write(f'Content-Length: {len(frame_data)}\r\n\r\n'.encode())
                        
                        # Send image data
                        self.wfile.write(frame_data)
                        self.wfile.write(b'\r\n')
                        
                    time.sleep(1/30)  # 30 FPS
                    
            except Exception as e:
                print(f"Stream error: {e}")
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass

class StreamingServer:
    def __init__(self, camera_controller, port=8090):
        self.camera_controller = camera_controller
        self.port = port
        self.server = None
        
    def start(self):
        """Start the MJPEG streaming server"""
        def handler(*args, **kwargs):
            return MJPEGStreamHandler(self.camera_controller, *args, **kwargs)
            
        self.server = HTTPServer(('0.0.0.0', self.port), handler)
        
        # Start camera
        self.camera_controller.start_camera()
        
        print(f"MJPEG stream available at http://0.0.0.0:{self.port}")
        
        # Run server in thread
        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        
    def stop(self):
        """Stop the streaming server"""
        if self.server:
            self.server.shutdown()
            self.camera_controller.stop_camera()

if __name__ == "__main__":
    server = RCCarServer()
    server.run()