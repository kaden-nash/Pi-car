import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import socket
import threading
import json
from datetime import datetime
from PIL import Image, ImageTk
import urllib.request
import io

class RCCarController:
    def __init__(self, root):
        self.root = root
        self.root.title("RC Car Controller")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2b2b')
        
        # Socket connection
        self.socket = None
        self.connected = False
        
        # Control states
        self.pressed_keys = set()
        
        self.setup_ui()
        self.bind_keys()
        
    def setup_ui(self):
        # Main scrollable frame
        canvas = tk.Canvas(self.root, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Connection section
        self.setup_connection_section()
        
        # Add spacing
        tk.Frame(self.scrollable_frame, height=30, bg='#2b2b2b').pack()
        
        # Control section
        self.setup_control_section()
        
        # Add spacing
        tk.Frame(self.scrollable_frame, height=30, bg='#2b2b2b').pack()
        
        # Video feed section
        self.setup_video_section()
        
        # Add spacing
        tk.Frame(self.scrollable_frame, height=30, bg='#2b2b2b').pack()
        
        # Log section
        self.setup_log_section()
        
    def setup_connection_section(self):
        conn_frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b')
        conn_frame.pack(pady=10)
        
        tk.Label(conn_frame, text="Raspberry Pi Connection", 
                fg='white', bg='#2b2b2b', font=('Arial', 14, 'bold')).pack()
        
        input_frame = tk.Frame(conn_frame, bg='#2b2b2b')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="IP:", fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(input_frame, bg='#404040', fg='white', insertbackground='white')
        self.ip_entry.insert(0, "192.168.200.1")  # Default Pi IP
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(input_frame, text="Port:", fg='white', bg='#2b2b2b').pack(side=tk.LEFT, padx=(20,0))
        self.port_entry = tk.Entry(input_frame, bg='#404040', fg='white', insertbackground='white', width=8)
        self.port_entry.insert(0, "59726")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(input_frame, text="Connect", command=self.connect_to_pi,
                                   bg='#4a90e2', fg='white', padx=20)
        self.connect_btn.pack(side=tk.LEFT, padx=20)
        
        self.status_label = tk.Label(conn_frame, text="Disconnected", 
                                   fg='red', bg='#2b2b2b', font=('Arial', 10))
        self.status_label.pack()
        
    def setup_control_section(self):
        control_frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b')
        control_frame.pack(pady=20)
        
        tk.Label(control_frame, text="Movement Controls (Arrow Keys or WASD)", 
                fg='white', bg='#2b2b2b', font=('Arial', 14, 'bold')).pack()
        
        # Control grid
        grid_frame = tk.Frame(control_frame, bg='#2b2b2b')
        grid_frame.pack(pady=20)
        
        # Up arrow (W)
        self.up_btn = self.create_arrow_button(grid_frame, "↑", "forward", 1, 1)
        
        # Left arrow (A)
        self.left_btn = self.create_arrow_button(grid_frame, "←", "left", 2, 0)
        
        # Down arrow (S)
        self.down_btn = self.create_arrow_button(grid_frame, "↓", "backward", 2, 1)
        
        # Right arrow (D)
        self.right_btn = self.create_arrow_button(grid_frame, "→", "right", 2, 2)
        
    def create_arrow_button(self, parent, text, direction, row, col):
        btn = tk.Button(parent, text=text, font=('Arial', 24), width=4, height=2,
                       bg='#404040', fg='white', activebackground='#ff8c00',
                       relief='raised', bd=3)
        btn.grid(row=row, column=col, padx=10, pady=10)
        
        btn.bind('<Button-1>', lambda e: self.button_press(direction, btn))
        btn.bind('<ButtonRelease-1>', lambda e: self.button_release(direction, btn))
        
        return btn
        
    def setup_video_section(self):
        video_frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b')
        video_frame.pack(pady=20)
        
        tk.Label(video_frame, text="Video Feed", 
                fg='white', bg='#2b2b2b', font=('Arial', 14, 'bold')).pack()
        
        # Placeholder for video feed
        self.video_canvas = tk.Canvas(video_frame, width=640, height=480, 
                                    bg='#1a1a1a', highlightthickness=2, 
                                    highlightbackground='#404040')
        self.video_canvas.pack(pady=10)
        
        # Placeholder text
        self.video_canvas.create_text(320, 240, text="Video Feed Placeholder\n(Camera integration needed)", 
                                    fill='#666666', font=('Arial', 16))
        
    def setup_log_section(self):
        log_frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b')
        log_frame.pack(pady=20, fill='both', expand=True)
        
        header_frame = tk.Frame(log_frame, bg='#2b2b2b')
        header_frame.pack(fill='x')
        
        tk.Label(header_frame, text="Command Log", 
                fg='white', bg='#2b2b2b', font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        self.export_btn = tk.Button(header_frame, text="Export Log", command=self.export_log,
                                  bg='#4a90e2', fg='white', padx=15)
        self.export_btn.pack(side=tk.RIGHT)
        
        # Log text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=120,
                                                bg='#1a1a1a', fg='#00ff00', 
                                                insertbackground='white',
                                                font=('Courier', 10))
        self.log_text.pack(pady=10, fill='both', expand=True)
        
        self.add_log_entry("System", "RC Car Controller initialized")
        
    def bind_keys(self):
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.focus_set()
        
    def on_key_press(self, event):
        key_map = {
            'w': ('forward', self.up_btn),
            'a': ('left', self.left_btn),
            's': ('backward', self.down_btn),
            'd': ('right', self.right_btn),
            'Up': ('forward', self.up_btn),
            'Left': ('left', self.left_btn),
            'Down': ('backward', self.down_btn),
            'Right': ('right', self.right_btn)
        }
        
        key = event.keysym.lower() if event.keysym not in ['Up', 'Down', 'Left', 'Right'] else event.keysym
        
        if key in key_map and key not in self.pressed_keys:
            direction, button = key_map[key]
            self.pressed_keys.add(key)
            self.button_press(direction, button)
            
    def on_key_release(self, event):
        key_map = {
            'w': ('forward', self.up_btn),
            'a': ('left', self.left_btn),
            's': ('backward', self.down_btn),
            'd': ('right', self.right_btn),
            'Up': ('forward', self.up_btn),
            'Left': ('left', self.left_btn),
            'Down': ('backward', self.down_btn),
            'Right': ('right', self.right_btn)
        }
        
        key = event.keysym.lower() if event.keysym not in ['Up', 'Down', 'Left', 'Right'] else event.keysym
        
        if key in key_map and key in self.pressed_keys:
            direction, button = key_map[key]
            self.pressed_keys.remove(key)
            self.button_release(direction, button)
            
    def button_press(self, direction, button):
        button.configure(bg='#ff8c00', relief='sunken')
        self.send_command(direction, "start")
        
    def button_release(self, direction, button):
        button.configure(bg='#404040', relief='raised')

        if self.connected: # prevent double print of error message to log
            self.send_command(direction, "stop")
        
    def connect_to_pi(self):
        if self.connected:
            self.disconnect_from_pi()
            return
            
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((ip, port))
            
            self.connected = True
            self.connect_btn.configure(text="Disconnect", bg='#e74c3c')
            self.status_label.configure(text="Connected", fg='green')
            
            self.add_log_entry("System", f"Connected to {ip}:{port}")
            
            # Start listening thread
            threading.Thread(target=self.listen_for_responses, daemon=True).start()
            
        except Exception as e:
            self.add_log_entry("Error", f"Connection failed: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            
    def disconnect_from_pi(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        
        self.connected = False
        self.connect_btn.configure(text="Connect", bg='#4a90e2')
        self.status_label.configure(text="Disconnected", fg='red')
        self.add_log_entry("System", "Disconnected from Pi")
        
    def send_command(self, direction, action):
        if not self.connected:
            self.add_log_entry("Error", "Not connected to Pi")
            return
            
        try:
            command = {
                "direction": direction,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }
            
            message = json.dumps(command) + "\n"
            self.socket.send(message.encode())
            
            self.add_log_entry("Sent", f"{direction} {action}")
            
        except Exception as e:
            self.add_log_entry("Error", f"Failed to send command: {str(e)}")
            
    def listen_for_responses(self):
        buffer = ""
        try:
            while self.connected:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        try:
                            response = json.loads(line)
                            self.add_log_entry("Received", f"Status: {response.get('status', 'Unknown')}")
                        except json.JSONDecodeError:
                            self.add_log_entry("Received", line.strip())
                            
        except Exception as e:
            self.add_log_entry("Error", f"Connection lost: {str(e)}")
            self.root.after(0, self.disconnect_from_pi)
            
    def add_log_entry(self, type_str, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {type_str}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def export_log(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                self.add_log_entry("System", f"Log exported to {filename}")
                messagebox.showinfo("Export Complete", f"Log saved to {filename}")
                
        except Exception as e:
            self.add_log_entry("Error", f"Export failed: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def start_video(self):
        """Start video stream from Pi"""
        if not self.connected:
            self.add_log_entry("Warning", "Connect to Pi first before starting video")
            return
            
        try:
            ip = self.ip_entry.get()
            video_port = self.video_port_entry.get()
            self.video_url = f"http://{ip}:{video_port}"
            
            self.video_running = True
            self.video_thread = threading.Thread(target=self.video_stream_worker, daemon=True)
            self.video_thread.start()
            
            self.video_btn.configure(text="Stop Video", bg='#e74c3c')
            self.video_status.configure(text="Video: Streaming", fg='green')
            self.add_log_entry("System", f"Video stream started from {self.video_url}")
            
            # Remove placeholder text
            if hasattr(self, 'video_placeholder_text'):
                self.video_canvas.delete(self.video_placeholder_text)
                
        except Exception as e:
            self.add_log_entry("Error", f"Failed to start video: {str(e)}")
            
    def stop_video(self):
        """Stop video streaming"""
        self.video_running = False
        
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1)
            
        self.video_btn.configure(text="Start Video", bg='#4a90e2')
        self.video_status.configure(text="Video: Stopped", fg='red')
        self.add_log_entry("System", "Video stream stopped")
        
        # Clear canvas and show placeholder
        self.video_canvas.delete("all")
        self.video_placeholder_text = self.video_canvas.create_text(
            320, 240, text="Video Feed\nClick 'Start Video' to begin streaming", 
            fill='#666666', font=('Arial', 16))
            
    def video_stream_worker(self):
        """Worker thread for video streaming"""
        while self.video_running:
            try:
                # Request image from MJPEG stream
                response = urllib.request.urlopen(self.video_url, timeout=5)
                content_type = response.headers.get('content-type', '')
                
                if 'multipart' in content_type:
                    # Handle MJPEG multipart stream
                    boundary = content_type.split('boundary=')[1]
                    self.process_mjpeg_stream(response, boundary)
                else:
                    # Handle single image
                    image_data = response.read()
                    self.update_video_frame(image_data)
                    
            except Exception as e:
                if self.video_running:  # Only log if we're supposed to be running
                    self.add_log_entry("Video Error", f"Stream error: {str(e)}")
                break
                
        # Clean up when thread exits
        if self.video_running:
            self.root.after(0, self.stop_video)
            
    def process_mjpeg_stream(self, response, boundary):
        """Process MJPEG multipart stream"""
        boundary = boundary.encode()
        buffer = b''
        
        while self.video_running:
            chunk = response.read(1024)
            if not chunk:
                break
                
            buffer += chunk
            
            # Look for boundary markers
            while boundary in buffer:
                # Find the start of image data
                start_marker = b'\r\n\r\n'
                start_pos = buffer.find(start_marker)
                if start_pos == -1:
                    break
                    
                # Find the end of image data
                end_pos = buffer.find(boundary, start_pos)
                if end_pos == -1:
                    break
                    
                # Extract image data
                image_data = buffer[start_pos + len(start_marker):end_pos]
                if image_data:
                    self.update_video_frame(image_data)
                    
                # Remove processed data from buffer
                buffer = buffer[end_pos:]
                
    def update_video_frame(self, image_data):
        """Update the video canvas with new frame"""
        try:
            # Convert image data to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Resize to fit canvas while maintaining aspect ratio
            canvas_width, canvas_height = 640, 480
            image_width, image_height = image.size
            
            # Calculate scaling factor
            scale_x = canvas_width / image_width
            scale_y = canvas_height / image_height
            scale = min(scale_x, scale_y)
            
            new_width = int(image_width * scale)
            new_height = int(image_height * scale)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(image)
            
            # Update canvas on main thread
            self.root.after(0, self._update_canvas, self.photo, new_width, new_height)
            
        except Exception as e:
            self.add_log_entry("Video Error", f"Frame update error: {str(e)}")
            
    def _update_canvas(self, photo, width, height):
        """Update canvas with new photo (called on main thread)"""
        try:
            self.video_canvas.delete("all")
            
            # Center the image on canvas
            x = (640 - width) // 2
            y = (480 - height) // 2
            
            self.video_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Keep a reference to prevent garbage collection
            self.video_canvas.image = photo
            
        except Exception as e:
            print(f"Canvas update error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RCCarController(root)
    root.mainloop()