"""
Discord Camera Surveillance Bot for Rust+

This bot streams camera feeds from Rust+ to Discord channels and allows
control through Discord commands.

Requirements:
    pip install discord.py rustplus

Setup:
    1. Create a Discord bot at https://discord.com/developers/applications
    2. Enable "Message Content Intent" in Bot settings
    3. Get your bot token
    4. Get your Rust+ server details (IP, port, steamID, token)
    5. Run this script

Features:
    - Stream camera feed to Discord channel (as updating images)
    - Control camera movement via Discord commands
    - Multiple camera support (drone, CCTV1, CCTV2, etc.)
    - Auto-resubscription handling
    - FPS limiting to avoid Discord rate limits

Usage:
    !camera start drone #surveillance     - Start streaming drone camera
    !camera stop drone                    - Stop streaming
    !camera move forward                  - Move camera forward
    !camera look left                     - Look left
    !camera fire                          - Fire weapon (if available)
    !camera list                          - List active cameras
"""

import asyncio
import io
import time
from typing import Dict, Optional
import discord
from discord.ext import commands, tasks
from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager
from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
from rustplus.structs import Vector

# ========================
# Configuration
# ========================

DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"

# Rust+ Server Details
RUST_SERVER_IP = "your.server.ip"
RUST_SERVER_PORT = "28082"
RUST_STEAM_ID = "your_steam_id"
RUST_PLAYER_TOKEN = "your_player_token"

# Stream Settings
STREAM_FPS = 2  # Discord rate limit: ~5 images/second per channel
UPDATE_INTERVAL = 1.0 / STREAM_FPS  # seconds between frames

# ========================
# Camera Stream Manager
# ========================

class CameraStream:
    """Manages a single camera stream to a Discord channel"""

    def __init__(
        self,
        camera_manager: CameraManager,
        channel: discord.TextChannel,
        camera_id: str
    ):
        self.camera_manager = camera_manager
        self.channel = channel
        self.camera_id = camera_id
        self.message: Optional[discord.Message] = None
        self.is_streaming = False
        self.last_frame_time = 0
        self.frame_count = 0
        self.last_resubscribe = time.time()

    async def start(self):
        """Start streaming to Discord"""
        self.is_streaming = True
        # Send initial message
        embed = discord.Embed(
            title=f"📹 Camera: {self.camera_id}",
            description="Initializing stream...",
            color=discord.Color.blue()
        )
        self.message = await self.channel.send(embed=embed)

    async def update_frame(self):
        """Send a new frame to Discord"""
        if not self.is_streaming or not self.message:
            return

        # Frame rate limiting
        current_time = time.time()
        if current_time - self.last_frame_time < UPDATE_INTERVAL:
            return

        # Resubscribe if needed (every 10 seconds)
        if current_time - self.last_resubscribe > 10:
            await self.camera_manager.resubscribe()
            self.last_resubscribe = current_time

        # Get frame
        if not self.camera_manager.has_frame_data():
            return

        try:
            frame = await self.camera_manager.get_frame(
                render_entities=True,
                entity_render_distance=100
            )

            if frame is None:
                return

            # Convert PIL Image to bytes
            img_bytes = io.BytesIO()
            frame.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Get entities info
            entities = await self.camera_manager.get_entities_in_frame()
            player_count = sum(1 for e in entities if e.type == 2)

            # Create embed with stats
            embed = discord.Embed(
                title=f"📹 Camera: {self.camera_id}",
                color=discord.Color.green()
            )
            embed.add_field(name="Players Detected", value=str(player_count), inline=True)
            embed.add_field(name="Entities", value=str(len(entities)), inline=True)
            embed.add_field(name="Frames", value=str(self.frame_count), inline=True)
            embed.set_image(url=f"attachment://frame.png")
            embed.set_footer(text=f"Updated every {UPDATE_INTERVAL:.1f}s")

            # Edit message with new frame
            file = discord.File(img_bytes, filename='frame.png')
            await self.message.edit(embed=embed, attachments=[file])

            self.last_frame_time = current_time
            self.frame_count += 1

        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                print(f"Discord rate limit hit, slowing down...")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Error updating frame: {e}")

    async def stop(self):
        """Stop streaming"""
        self.is_streaming = False
        if self.message:
            embed = discord.Embed(
                title=f"📹 Camera: {self.camera_id}",
                description="Stream stopped",
                color=discord.Color.red()
            )
            try:
                await self.message.edit(embed=embed)
            except:
                pass

# ========================
# Discord Bot
# ========================

class RustCameraBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Rust+ Camera Surveillance Bot'
        )

        self.rust_socket: Optional[RustSocket] = None
        self.active_streams: Dict[str, CameraStream] = {}
        self.camera_managers: Dict[str, CameraManager] = {}

    async def setup_hook(self):
        """Called when bot starts"""
        # Start the frame update loop
        self.update_streams.start()

    async def on_ready(self):
        """Called when bot is ready"""
        print(f'Bot logged in as {self.user}')
        print(f'Connecting to Rust+ server...')

        # Connect to Rust+ server
        try:
            self.rust_socket = RustSocket(
                RUST_SERVER_IP,
                RUST_SERVER_PORT,
                RUST_STEAM_ID,
                RUST_PLAYER_TOKEN
            )
            await self.rust_socket.connect()
            print('Connected to Rust+ server!')
        except Exception as e:
            print(f'Failed to connect to Rust+ server: {e}')

    async def on_close(self):
        """Cleanup on shutdown"""
        # Stop all streams
        for stream in self.active_streams.values():
            await stream.stop()

        # Exit all cameras
        for cam_id, camera_mgr in self.camera_managers.items():
            try:
                await camera_mgr.exit_camera()
            except:
                pass

        # Disconnect from Rust+
        if self.rust_socket:
            await self.rust_socket.disconnect()

    @tasks.loop(seconds=0.1)  # Check frequently, but rate limiting in update_frame
    async def update_streams(self):
        """Update all active camera streams"""
        for stream in list(self.active_streams.values()):
            if stream.is_streaming:
                await stream.update_frame()

# ========================
# Commands
# ========================

bot = RustCameraBot()

@bot.command(name='camera')
async def camera_command(ctx, action: str, *args):
    """
    Camera control commands

    Usage:
        !camera start <camera_id> [#channel]
        !camera stop <camera_id>
        !camera move <direction>
        !camera look <direction>
        !camera list
    """

    if not bot.rust_socket:
        await ctx.send("❌ Not connected to Rust+ server")
        return

    action = action.lower()

    # ==================
    # START STREAM
    # ==================
    if action == 'start':
        if len(args) < 1:
            await ctx.send("Usage: `!camera start <camera_id> [#channel]`")
            return

        camera_id = args[0]

        # Get target channel
        if len(args) > 1 and ctx.message.channel_mentions:
            channel = ctx.message.channel_mentions[0]
        else:
            channel = ctx.channel

        # Check if already streaming
        stream_key = f"{camera_id}:{channel.id}"
        if stream_key in bot.active_streams:
            await ctx.send(f"❌ Camera `{camera_id}` is already streaming to {channel.mention}")
            return

        # Subscribe to camera
        try:
            await ctx.send(f"📡 Connecting to camera `{camera_id}`...")

            camera_manager = await bot.rust_socket.get_camera_manager(camera_id)

            # Check for error
            if hasattr(camera_manager, 'error'):
                await ctx.send(f"❌ Failed to connect: {camera_manager.error}")
                return

            # Create stream
            stream = CameraStream(camera_manager, channel, camera_id)
            await stream.start()

            bot.active_streams[stream_key] = stream
            bot.camera_managers[camera_id] = camera_manager

            await ctx.send(f"✅ Camera `{camera_id}` now streaming to {channel.mention}")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ==================
    # STOP STREAM
    # ==================
    elif action == 'stop':
        if len(args) < 1:
            await ctx.send("Usage: `!camera stop <camera_id>`")
            return

        camera_id = args[0]

        # Find and stop stream
        stopped = False
        for key in list(bot.active_streams.keys()):
            if key.startswith(f"{camera_id}:"):
                stream = bot.active_streams[key]
                await stream.stop()
                del bot.active_streams[key]
                stopped = True

        if camera_id in bot.camera_managers:
            await bot.camera_managers[camera_id].exit_camera()
            del bot.camera_managers[camera_id]

        if stopped:
            await ctx.send(f"✅ Stopped camera `{camera_id}`")
        else:
            await ctx.send(f"❌ Camera `{camera_id}` is not streaming")

    # ==================
    # MOVE CAMERA
    # ==================
    elif action == 'move':
        if len(args) < 1:
            await ctx.send("Usage: `!camera move <forward|backward|left|right|jump|duck>`")
            return

        direction = args[0].lower()

        # Map direction to control
        movement_map = {
            'forward': MovementControls.FORWARD,
            'backward': MovementControls.BACKWARD,
            'left': MovementControls.LEFT,
            'right': MovementControls.RIGHT,
            'jump': MovementControls.JUMP,
            'duck': MovementControls.DUCK,
            'sprint': MovementControls.SPRINT,
        }

        if direction not in movement_map:
            await ctx.send(f"❌ Invalid direction. Use: {', '.join(movement_map.keys())}")
            return

        # Send movement to all active cameras (or specify which one)
        moved = False
        for camera_mgr in bot.camera_managers.values():
            if camera_mgr.can_move(CameraMovementOptions.MOVEMENT):
                await camera_mgr.send_actions([movement_map[direction]])
                await asyncio.sleep(0.5)
                await camera_mgr.clear_movement()
                moved = True

        if moved:
            await ctx.send(f"✅ Moving {direction}")
        else:
            await ctx.send("❌ No cameras active or movement not allowed")

    # ==================
    # LOOK DIRECTION
    # ==================
    elif action == 'look':
        if len(args) < 1:
            await ctx.send("Usage: `!camera look <up|down|left|right>`")
            return

        direction = args[0].lower()

        # Map to mouse delta
        look_map = {
            'left': Vector(-0.3, 0),
            'right': Vector(0.3, 0),
            'up': Vector(0, 0.3),
            'down': Vector(0, -0.3),
        }

        if direction not in look_map:
            await ctx.send(f"❌ Invalid direction. Use: {', '.join(look_map.keys())}")
            return

        # Send look to all active cameras
        looked = False
        for camera_mgr in bot.camera_managers.values():
            if camera_mgr.can_move(CameraMovementOptions.MOUSE):
                await camera_mgr.send_mouse_movement(look_map[direction])
                looked = True

        if looked:
            await ctx.send(f"✅ Looking {direction}")
        else:
            await ctx.send("❌ No cameras active or mouse control not allowed")

    # ==================
    # LIST CAMERAS
    # ==================
    elif action == 'list':
        if not bot.active_streams:
            await ctx.send("📹 No cameras currently streaming")
            return

        embed = discord.Embed(
            title="📹 Active Camera Streams",
            color=discord.Color.blue()
        )

        for key, stream in bot.active_streams.items():
            camera_id, channel_id = key.split(':')
            channel = bot.get_channel(int(channel_id))
            embed.add_field(
                name=camera_id,
                value=f"Channel: {channel.mention if channel else 'Unknown'}\nFrames: {stream.frame_count}",
                inline=False
            )

        await ctx.send(embed=embed)

    else:
        await ctx.send(f"❌ Unknown action: {action}\n"
                      "Available: start, stop, move, look, list")

@bot.command(name='fire')
async def fire_command(ctx):
    """Fire the camera's weapon (if available)"""
    fired = False
    for camera_mgr in bot.camera_managers.values():
        if camera_mgr.can_move(CameraMovementOptions.FIRE):
            await camera_mgr.send_actions([MovementControls.FIRE_PRIMARY])
            await asyncio.sleep(0.1)
            await camera_mgr.clear_movement()
            fired = True

    if fired:
        await ctx.send("💥 Fired!")
    else:
        await ctx.send("❌ No cameras with fire capability")

@bot.command(name='entities')
async def entities_command(ctx, camera_id: str = None):
    """List entities visible in camera view"""
    if not bot.camera_managers:
        await ctx.send("❌ No cameras active")
        return

    # Use first camera if not specified
    if camera_id is None:
        camera_id = list(bot.camera_managers.keys())[0]

    if camera_id not in bot.camera_managers:
        await ctx.send(f"❌ Camera `{camera_id}` not active")
        return

    camera_mgr = bot.camera_managers[camera_id]
    entities = await camera_mgr.get_entities_in_frame()

    if not entities:
        await ctx.send("👻 No entities detected")
        return

    embed = discord.Embed(
        title=f"👁️ Entities in {camera_id}",
        color=discord.Color.green()
    )

    players = [e for e in entities if e.type == 2]
    trees = [e for e in entities if e.type == 1]

    if players:
        player_list = '\n'.join([f"• {p.name} (distance: {p.position.z:.1f}m)"
                                 for p in players[:10]])
        embed.add_field(name=f"Players ({len(players)})", value=player_list, inline=False)

    if trees:
        embed.add_field(name="Trees", value=f"{len(trees)} visible", inline=False)

    await ctx.send(embed=embed)

# ========================
# Run Bot
# ========================

if __name__ == '__main__':
    print("Starting Rust+ Camera Bot...")
    print("Make sure to configure DISCORD_TOKEN and Rust+ server details!")
    bot.run(DISCORD_TOKEN)
