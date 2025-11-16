"""
Discord Video Streaming for Rust+ Cameras

Discord bots have LIMITED video streaming capabilities. This file shows 3 approaches:

1. FFmpeg + Voice Channel (Experimental) - Stream to Discord voice channel
2. YouTube Live Stream - Stream to YouTube, embed in Discord
3. Local Web Server - Stream via HLS/WebRTC, share URL in Discord

Requirements:
    pip install discord.py rustplus opencv-python ffmpeg-python flask flask-socketio

    # System dependencies:
    sudo apt install ffmpeg  # Linux
    brew install ffmpeg      # macOS
"""

import asyncio
import io
import subprocess
import time
import cv2
import numpy as np
from typing import Optional
from PIL import Image

import discord
from discord.ext import commands, tasks
from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager

# ========================
# Configuration
# ========================

DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
RUST_SERVER_IP = "your.server.ip"
RUST_SERVER_PORT = "28082"
RUST_STEAM_ID = "your_steam_id"
RUST_PLAYER_TOKEN = "your_player_token"

# Stream settings
TARGET_FPS = 10  # 10 FPS for smooth video
RESOLUTION = (800, 600)  # Width x Height

# ========================
# APPROACH 1: FFmpeg + Discord Voice Channel
# ========================
# NOTE: This is experimental. Discord bots have limited video streaming support.
# This approach streams to a voice channel but may not work reliably.

class FFmpegVideoStreamer:
    """Stream camera feed to Discord voice channel using FFmpeg"""

    def __init__(self, camera_manager: CameraManager, voice_client):
        self.camera_manager = camera_manager
        self.voice_client = voice_client
        self.is_streaming = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None

    async def start_stream(self):
        """Start FFmpeg video stream to Discord voice channel"""
        self.is_streaming = True

        # FFmpeg command to create video stream
        # This creates a virtual video device that Discord can read
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',           # Input format: raw video frames
            '-pix_fmt', 'rgb24',        # Pixel format
            '-s', f'{RESOLUTION[0]}x{RESOLUTION[1]}',  # Resolution
            '-r', str(TARGET_FPS),      # Frame rate
            '-i', '-',                  # Read from stdin
            '-vcodec', 'libx264',       # H.264 encoder
            '-preset', 'ultrafast',     # Fast encoding
            '-tune', 'zerolatency',     # Low latency
            '-f', 'matroska',           # Output format
            '-'                         # Output to stdout
        ]

        # Start FFmpeg process
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start frame capture loop
        asyncio.create_task(self._capture_frames())

        print("⚠️ WARNING: Discord bot video streaming is experimental!")
        print("This may not work as expected. Consider using YouTube Live instead.")

    async def _capture_frames(self):
        """Capture frames from camera and pipe to FFmpeg"""
        frame_interval = 1.0 / TARGET_FPS

        while self.is_streaming:
            try:
                # Get frame from camera
                if not self.camera_manager.has_frame_data():
                    await asyncio.sleep(0.1)
                    continue

                frame = await self.camera_manager.get_frame()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # Convert PIL Image to numpy array
                frame_array = np.array(frame.resize(RESOLUTION))

                # Convert to RGB24 format
                if frame_array.shape[2] == 4:  # RGBA
                    frame_array = frame_array[:, :, :3]

                # Write frame to FFmpeg stdin
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.write(frame_array.tobytes())
                    self.ffmpeg_process.stdin.flush()

                # Maintain frame rate
                await asyncio.sleep(frame_interval)

            except Exception as e:
                print(f"Error capturing frame: {e}")
                await asyncio.sleep(1)

    def stop_stream(self):
        """Stop the video stream"""
        self.is_streaming = False
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None


# ========================
# APPROACH 2: YouTube Live Stream
# ========================
# This is the RECOMMENDED approach for reliable video streaming

class YouTubeLiveStreamer:
    """Stream camera feed to YouTube Live, then share in Discord"""

    def __init__(self, camera_manager: CameraManager, youtube_stream_key: str):
        self.camera_manager = camera_manager
        self.youtube_stream_key = youtube_stream_key
        self.is_streaming = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None

    async def start_stream(self) -> str:
        """
        Start streaming to YouTube Live

        Returns:
            YouTube Live URL to share in Discord
        """
        self.is_streaming = True

        # YouTube RTMP server
        rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{self.youtube_stream_key}"

        # FFmpeg command for YouTube streaming
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-r', str(TARGET_FPS),
            '-i', '-',                      # Input from stdin

            # Video encoding for YouTube
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-b:v', '2500k',                # 2.5 Mbps bitrate
            '-maxrate', '2500k',
            '-bufsize', '5000k',
            '-pix_fmt', 'yuv420p',
            '-g', str(TARGET_FPS * 2),      # Keyframe interval

            # Audio (silent, required by YouTube)
            '-f', 'lavfi',
            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-c:a', 'aac',
            '-b:a', '128k',

            # Output
            '-f', 'flv',
            rtmp_url
        ]

        # Start FFmpeg
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start frame capture
        asyncio.create_task(self._capture_frames())

        # Return YouTube Live URL
        # You'll need to get this from your YouTube Studio
        return "https://youtube.com/watch?v=YOUR_STREAM_ID"

    async def _capture_frames(self):
        """Capture frames and send to YouTube"""
        frame_interval = 1.0 / TARGET_FPS
        last_resubscribe = time.time()

        while self.is_streaming:
            try:
                # Resubscribe to camera periodically
                if time.time() - last_resubscribe > 10:
                    await self.camera_manager.resubscribe()
                    last_resubscribe = time.time()

                # Get frame
                if not self.camera_manager.has_frame_data():
                    await asyncio.sleep(0.1)
                    continue

                frame = await self.camera_manager.get_frame()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # Convert to numpy array
                frame_array = np.array(frame.resize(RESOLUTION))
                if frame_array.shape[2] == 4:
                    frame_array = frame_array[:, :, :3]

                # Write to FFmpeg
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.write(frame_array.tobytes())
                    self.ffmpeg_process.stdin.flush()

                await asyncio.sleep(frame_interval)

            except Exception as e:
                print(f"Streaming error: {e}")
                await asyncio.sleep(1)

    def stop_stream(self):
        """Stop YouTube stream"""
        self.is_streaming = False
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()


# ========================
# APPROACH 3: Local Web Server with HLS
# ========================
# Stream to local web server, users access via browser

class LocalWebStreamer:
    """Stream to local HLS server, accessible via web browser"""

    def __init__(self, camera_manager: CameraManager, output_dir: str = "./stream"):
        self.camera_manager = camera_manager
        self.output_dir = output_dir
        self.is_streaming = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None

    async def start_stream(self, port: int = 8080) -> str:
        """
        Start HLS stream on local web server

        Returns:
            URL to access stream
        """
        import os
        os.makedirs(self.output_dir, exist_ok=True)

        self.is_streaming = True

        # FFmpeg HLS streaming
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-r', str(TARGET_FPS),
            '-i', '-',

            # HLS output
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-f', 'hls',
            '-hls_time', '2',
            '-hls_list_size', '5',
            '-hls_flags', 'delete_segments',
            f'{self.output_dir}/stream.m3u8'
        ]

        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start frame capture
        asyncio.create_task(self._capture_frames())

        # Start simple HTTP server (in separate thread)
        asyncio.create_task(self._start_http_server(port))

        return f"http://localhost:{port}/stream.m3u8"

    async def _capture_frames(self):
        """Capture frames for HLS stream"""
        frame_interval = 1.0 / TARGET_FPS
        last_resubscribe = time.time()

        while self.is_streaming:
            try:
                if time.time() - last_resubscribe > 10:
                    await self.camera_manager.resubscribe()
                    last_resubscribe = time.time()

                if not self.camera_manager.has_frame_data():
                    await asyncio.sleep(0.1)
                    continue

                frame = await self.camera_manager.get_frame()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue

                frame_array = np.array(frame.resize(RESOLUTION))
                if frame_array.shape[2] == 4:
                    frame_array = frame_array[:, :, :3]

                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.write(frame_array.tobytes())
                    self.ffmpeg_process.stdin.flush()

                await asyncio.sleep(frame_interval)

            except Exception as e:
                print(f"Streaming error: {e}")
                await asyncio.sleep(1)

    async def _start_http_server(self, port: int):
        """Start simple HTTP server for HLS files"""
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import threading

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=self.output_dir, **kwargs)

        server = HTTPServer(('0.0.0.0', port), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        print(f"📡 HLS server started on port {port}")

    def stop_stream(self):
        """Stop HLS stream"""
        self.is_streaming = False
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()


# ========================
# Discord Bot with Video Streaming
# ========================

class VideoStreamBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

        self.rust_socket: Optional[RustSocket] = None
        self.streamers = {}

    async def on_ready(self):
        print(f'Bot logged in as {self.user}')

        # Connect to Rust+
        try:
            self.rust_socket = RustSocket(
                RUST_SERVER_IP,
                RUST_SERVER_PORT,
                RUST_STEAM_ID,
                RUST_PLAYER_TOKEN
            )
            await self.rust_socket.connect()
            print('✅ Connected to Rust+ server')
        except Exception as e:
            print(f'❌ Failed to connect: {e}')

bot = VideoStreamBot()

@bot.command(name='stream')
async def stream_command(ctx, method: str, camera_id: str, *args):
    """
    Start video streaming

    Usage:
        !stream youtube drone <stream_key>
        !stream web drone [port]
        !stream voice drone
    """

    if not bot.rust_socket:
        await ctx.send("❌ Not connected to Rust+")
        return

    method = method.lower()

    # Subscribe to camera
    try:
        await ctx.send(f"📡 Connecting to camera `{camera_id}`...")
        camera_manager = await bot.rust_socket.get_camera_manager(camera_id)

        if hasattr(camera_manager, 'error'):
            await ctx.send(f"❌ Failed: {camera_manager.error}")
            return

        # Wait for frame data
        await asyncio.sleep(2)

        if method == 'youtube':
            if len(args) < 1:
                await ctx.send("❌ Usage: `!stream youtube drone <stream_key>`")
                return

            stream_key = args[0]
            streamer = YouTubeLiveStreamer(camera_manager, stream_key)
            youtube_url = await streamer.start_stream()

            bot.streamers[camera_id] = streamer

            embed = discord.Embed(
                title="🔴 YouTube Live Stream Started",
                description=f"Camera `{camera_id}` is now streaming to YouTube!",
                color=discord.Color.red()
            )
            embed.add_field(name="Watch Live", value=f"[Click Here]({youtube_url})", inline=False)
            embed.add_field(name="Quality", value=f"{RESOLUTION[0]}x{RESOLUTION[1]} @ {TARGET_FPS} FPS", inline=True)
            embed.set_footer(text="Stream will appear live in 10-30 seconds")

            await ctx.send(embed=embed)

        elif method == 'web':
            port = int(args[0]) if len(args) > 0 else 8080

            streamer = LocalWebStreamer(camera_manager)
            stream_url = await streamer.start_stream(port)

            bot.streamers[camera_id] = streamer

            embed = discord.Embed(
                title="🌐 Web Stream Started",
                description=f"Camera `{camera_id}` is streaming via HLS",
                color=discord.Color.blue()
            )
            embed.add_field(name="Stream URL", value=stream_url, inline=False)
            embed.add_field(name="How to Watch",
                          value="Open in VLC or use HLS player in browser",
                          inline=False)
            embed.set_footer(text=f"Stream at {RESOLUTION[0]}x{RESOLUTION[1]} @ {TARGET_FPS} FPS")

            await ctx.send(embed=embed)

        elif method == 'voice':
            await ctx.send("⚠️ Voice channel video streaming is experimental and may not work.\n"
                          "Consider using `!stream youtube` or `!stream web` instead.")

        else:
            await ctx.send(f"❌ Unknown method: {method}\n"
                          "Available: `youtube`, `web`, `voice`")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='stopstream')
async def stop_stream_command(ctx, camera_id: str):
    """Stop video stream"""
    if camera_id in bot.streamers:
        bot.streamers[camera_id].stop_stream()
        del bot.streamers[camera_id]
        await ctx.send(f"✅ Stopped stream for `{camera_id}`")
    else:
        await ctx.send(f"❌ No active stream for `{camera_id}`")

if __name__ == '__main__':
    print("=" * 60)
    print("Rust+ Video Streaming Bot")
    print("=" * 60)
    print("\n⚠️  IMPORTANT NOTES:")
    print("1. YouTube Live is the RECOMMENDED method (most reliable)")
    print("2. Discord bot video streaming has LIMITED support")
    print("3. Web streaming requires port forwarding for remote access")
    print("\nMake sure FFmpeg is installed:")
    print("  - Linux: sudo apt install ffmpeg")
    print("  - macOS: brew install ffmpeg")
    print("  - Windows: Download from ffmpeg.org")
    print("=" * 60)

    bot.run(DISCORD_TOKEN)
