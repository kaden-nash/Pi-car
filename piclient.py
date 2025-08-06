import asyncio
import json
import logging
from datetime import datetime
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# GPIO imports - TODO: Uncomment when ready to use actual GPIO
# import RPi.GPIO as GPIO

class MotorController:
    def __init__(self):
        # L298N motor controller pin configuration - TODO: Set actual pin numbers
        self.motor_pins = {
            'left_motor': {
                'in1': 18,  # TODO: Set actual GPIO pin for left motor IN1
                'in2': 19,  # TODO: Set actual GPIO pin for left motor IN2
                'enable': 20  # TODO: Set actual GPIO pin for left motor enable (PWM)
            },
            'right_motor': {
                'in1': 21,  # TODO: Set actual GPIO pin for right motor IN1
                'in2': 22,  # TODO: Set actual GPIO pin for right motor IN2
                'enable': 23  # TODO: Set actual GPIO pin for right motor enable (PWM)
            }
        }
        
        self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins for motor control"""
        # TODO: Uncomment and configure GPIO setup
        
        print("GPIO pins configured for L298N motor controller")
        
    def move_forward(self):
        """Move both motors forward"""
        # TODO: Implement GPIO commands for forward movement
        
        print("Motors: Moving forward")
        
    def move_backward(self):
        """Move both motors backward"""
        # TODO: Implement GPIO commands for backward movement
        
        print("Motors: Moving backward")
        
    def turn_left(self):
        """Turn left by stopping left motor, running right motor"""
        # TODO: Implement GPIO commands for left turn
        
        print("Motors: Turning left")
        
    def turn_right(self):
        """Turn right by stopping right motor, running left motor"""
        # TODO: Implement GPIO commands for right turn
        
        print("Motors: Turning right")
        
    def stop(self):
        """Stop all motors"""
        # TODO: Implement GPIO commands to stop all motors
        
        print("Motors: Stopped")
        
    def cleanup(self):
        """Clean up GPIO resources"""
        # TODO: Uncomment when using actual GPIO
        # GPIO.cleanup()
        print("GPIO cleanup completed")

class SensorController:
    def __init__(self):
        # TODO: Define sensor pins (ultrasonic, cameras, etc.)
        self.sensor_pins = {
            'ultrasonic_trigger': 24,  # TODO: Set actual trigger pin
            'ultrasonic_echo': 25      # TODO: Set actual echo pin
        }
        
        self.setup_sensors()
        
    def setup_sensors(self):
        """Initialize sensor GPIO pins"""
        # TODO: Configure sensor pins
        
        print("Sensor pins configured")
        
    def get_distance(self):
        """Get distance from ultrasonic sensor"""
        # TODO: Implement ultrasonic distance measurement
        # Placeholder return value
        return 50.0  # cm
        
    def get_sensor_data(self):
        """Collect all sensor readings"""
        # TODO: Gather data from all connected sensors
        return {
            'distance': self.get_distance(),
            'timestamp': datetime.now().isoformat()
        }

class RCCarServer:
    def __init__(self, host='0.0.0.0', port=8888):
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
                    self.motor_controller.move_forward()
                elif direction == "backward":
                    self.motor_controller.move_backward()
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