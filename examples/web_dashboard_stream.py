"""
Web Dashboard for Rust+ Camera Surveillance

This creates a web dashboard that displays multiple camera feeds simultaneously.
Accessible from any device on your network (or internet with port forwarding).

This is a SIMPLER alternative to Discord video streaming that gives you:
- Multiple camera views in one page
- Real-time updates (WebSocket)
- Works on mobile
- Easy to share with team (just send them the URL)

Requirements:
    pip install rustplus flask flask-socketio pillow

Usage:
    python web_dashboard_stream.py

    Then open: http://localhost:5000
"""

import asyncio
import base64
import io
import time
from typing import Dict, List
from threading import Thread

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager

# ========================
# Configuration
# ========================

RUST_SERVER_IP = "your.server.ip"
RUST_SERVER_PORT = "28082"
RUST_STEAM_ID = "your_steam_id"
RUST_PLAYER_TOKEN = "your_player_token"

# Camera IDs to monitor
CAMERA_IDS = ["drone"]  # Add more: ["drone", "static1", "static2"]

# Stream settings
FPS = 5  # 5 FPS is smooth enough for surveillance
WEB_PORT = 5000

# ========================
# Flask App
# ========================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rustplus_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
rust_socket = None
camera_managers: Dict[str, CameraManager] = {}
is_streaming = False

# ========================
# HTML Dashboard Template
# ========================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Rust+ Surveillance Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #fff;
            padding: 20px;
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #ff4444;
            text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }

        .camera-feed {
            background: #2a2a2a;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            border: 2px solid #333;
        }

        .camera-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #44ff44;
            box-shadow: 0 0 10px #44ff44;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .camera-image {
            width: 100%;
            height: auto;
            display: block;
            background: #000;
            min-height: 300px;
        }

        .camera-info {
            padding: 15px;
            background: #222;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }

        .info-item {
            text-align: center;
        }

        .info-label {
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }

        .info-value {
            font-size: 18px;
            font-weight: bold;
            color: #fff;
        }

        .controls {
            padding: 15px;
            background: #2a2a2a;
            border-top: 1px solid #333;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }

        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }

        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        .no-cameras {
            text-align: center;
            padding: 40px;
            color: #888;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2a2a2a;
            padding: 10px 20px;
            border-radius: 5px;
            border: 2px solid #44ff44;
            box-shadow: 0 0 20px rgba(68, 255, 68, 0.3);
        }

        .offline {
            border-color: #ff4444;
            box-shadow: 0 0 20px rgba(255, 68, 68, 0.3);
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">
        <span id="status-text">Connecting...</span>
    </div>

    <h1>🎮 Rust+ Surveillance Dashboard</h1>

    <div class="grid" id="camera-grid">
        <div class="no-cameras">
            <h2>No cameras active</h2>
            <p>Waiting for camera feeds...</p>
        </div>
    </div>

    <script>
        const socket = io();
        const cameras = new Map();

        socket.on('connect', function() {
            document.getElementById('status-text').textContent = '🟢 Connected';
            document.getElementById('connection-status').classList.remove('offline');
        });

        socket.on('disconnect', function() {
            document.getElementById('status-text').textContent = '🔴 Disconnected';
            document.getElementById('connection-status').classList.add('offline');
        });

        socket.on('camera_frame', function(data) {
            const { camera_id, frame, entities, fps, frame_count } = data;

            if (!cameras.has(camera_id)) {
                createCameraFeed(camera_id);
            }

            updateCameraFeed(camera_id, frame, entities, fps, frame_count);
        });

        function createCameraFeed(camera_id) {
            const grid = document.getElementById('camera-grid');

            // Remove "no cameras" message
            if (cameras.size === 0) {
                grid.innerHTML = '';
            }

            const feedHtml = `
                <div class="camera-feed" id="camera-${camera_id}">
                    <div class="camera-header">
                        <span>📹 ${camera_id}</span>
                        <div class="status"></div>
                    </div>
                    <img class="camera-image" id="image-${camera_id}" src="" alt="Loading...">
                    <div class="camera-info">
                        <div class="info-item">
                            <div class="info-label">Players</div>
                            <div class="info-value" id="players-${camera_id}">0</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Entities</div>
                            <div class="info-value" id="entities-${camera_id}">0</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">FPS</div>
                            <div class="info-value" id="fps-${camera_id}">0</div>
                        </div>
                    </div>
                    <div class="controls">
                        <button onclick="sendCommand('${camera_id}', 'forward')">↑ Forward</button>
                        <button onclick="sendCommand('${camera_id}', 'backward')">↓ Back</button>
                        <button onclick="sendCommand('${camera_id}', 'left')">← Left</button>
                        <button onclick="sendCommand('${camera_id}', 'right')">→ Right</button>
                    </div>
                </div>
            `;

            grid.insertAdjacentHTML('beforeend', feedHtml);
            cameras.set(camera_id, true);
        }

        function updateCameraFeed(camera_id, frame, entities, fps, frame_count) {
            document.getElementById(`image-${camera_id}`).src = 'data:image/png;base64,' + frame;

            const players = entities.filter(e => e.type === 2).length;
            document.getElementById(`players-${camera_id}`).textContent = players;
            document.getElementById(`entities-${camera_id}`).textContent = entities.length;
            document.getElementById(`fps-${camera_id}`).textContent = fps.toFixed(1);
        }

        function sendCommand(camera_id, command) {
            socket.emit('camera_command', { camera_id, command });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template_string(DASHBOARD_HTML)

@socketio.on('camera_command')
def handle_camera_command(data):
    """Handle camera control commands from web UI"""
    camera_id = data.get('camera_id')
    command = data.get('command')

    if camera_id not in camera_managers:
        return

    # Execute command in async context
    asyncio.run_coroutine_threadsafe(
        execute_camera_command(camera_id, command),
        asyncio_loop
    )

async def execute_camera_command(camera_id: str, command: str):
    """Execute camera movement command"""
    from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
    from rustplus.structs import Vector

    camera_mgr = camera_managers.get(camera_id)
    if not camera_mgr:
        return

    movement_map = {
        'forward': MovementControls.FORWARD,
        'backward': MovementControls.BACKWARD,
        'left': MovementControls.LEFT,
        'right': MovementControls.RIGHT,
    }

    if command in movement_map and camera_mgr.can_move(CameraMovementOptions.MOVEMENT):
        await camera_mgr.send_actions([movement_map[command]])
        await asyncio.sleep(0.3)
        await camera_mgr.clear_movement()

# ========================
# Camera Streaming Logic
# ========================

async def stream_camera(camera_id: str):
    """Stream a single camera to web dashboard"""
    global camera_managers

    try:
        print(f"📹 Connecting to camera: {camera_id}")
        camera_mgr = await rust_socket.get_camera_manager(camera_id)

        if hasattr(camera_mgr, 'error'):
            print(f"❌ Failed to connect to {camera_id}: {camera_mgr.error}")
            return

        camera_managers[camera_id] = camera_mgr
        print(f"✅ Connected to camera: {camera_id}")

        # Stream loop
        frame_interval = 1.0 / FPS
        last_resubscribe = time.time()
        frame_count = 0
        last_fps_time = time.time()
        fps_counter = 0
        current_fps = 0

        while is_streaming:
            try:
                # Resubscribe periodically
                if time.time() - last_resubscribe > 10:
                    await camera_mgr.resubscribe()
                    last_resubscribe = time.time()

                # Get frame
                if not camera_mgr.has_frame_data():
                    await asyncio.sleep(0.1)
                    continue

                frame = await camera_mgr.get_frame(render_entities=True)
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # Convert to base64
                img_buffer = io.BytesIO()
                frame.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

                # Get entities
                entities = await camera_mgr.get_entities_in_frame()
                entity_list = [
                    {'type': e.type, 'name': e.name, 'distance': e.position.z}
                    for e in entities
                ]

                # Calculate FPS
                fps_counter += 1
                if time.time() - last_fps_time >= 1.0:
                    current_fps = fps_counter
                    fps_counter = 0
                    last_fps_time = time.time()

                # Send to web clients
                socketio.emit('camera_frame', {
                    'camera_id': camera_id,
                    'frame': img_base64,
                    'entities': entity_list,
                    'fps': current_fps,
                    'frame_count': frame_count
                })

                frame_count += 1
                await asyncio.sleep(frame_interval)

            except Exception as e:
                print(f"Error streaming {camera_id}: {e}")
                await asyncio.sleep(1)

    except Exception as e:
        print(f"Failed to start camera {camera_id}: {e}")

async def start_all_cameras():
    """Start streaming all configured cameras"""
    global rust_socket, is_streaming

    try:
        # Connect to Rust+
        print("🔌 Connecting to Rust+ server...")
        rust_socket = RustSocket(
            RUST_SERVER_IP,
            RUST_SERVER_PORT,
            RUST_STEAM_ID,
            RUST_PLAYER_TOKEN
        )
        await rust_socket.connect()
        print("✅ Connected to Rust+ server")

        is_streaming = True

        # Start all cameras
        tasks = [stream_camera(camera_id) for camera_id in CAMERA_IDS]
        await asyncio.gather(*tasks)

    except Exception as e:
        print(f"❌ Error: {e}")

# ========================
# Async Event Loop Management
# ========================

asyncio_loop = None

def run_async_loop():
    """Run asyncio event loop in separate thread"""
    global asyncio_loop
    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_until_complete(start_all_cameras())

# ========================
# Main
# ========================

if __name__ == '__main__':
    print("=" * 60)
    print("Rust+ Surveillance Web Dashboard")
    print("=" * 60)
    print(f"\n📹 Cameras to monitor: {', '.join(CAMERA_IDS)}")
    print(f"🌐 Dashboard will be available at: http://localhost:{WEB_PORT}")
    print(f"📱 Access from other devices: http://YOUR_IP:{WEB_PORT}")
    print("\nMake sure to configure:")
    print("  - RUST_SERVER_IP, PORT, STEAM_ID, PLAYER_TOKEN")
    print("  - CAMERA_IDS (drone, static1, etc.)")
    print("=" * 60)

    # Start async loop in background thread
    async_thread = Thread(target=run_async_loop, daemon=True)
    async_thread.start()

    # Give it time to connect
    time.sleep(3)

    # Start web server
    print(f"\n🚀 Starting web server on port {WEB_PORT}...")
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False)
