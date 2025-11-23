"""
Rust+ Discord Surveillance Bot

Auto-creates Discord channels for each camera and streams live feeds.
Perfect for team base surveillance and monitoring.

Features:
- Auto-creates category and channels for cameras
- Live camera streaming to Discord
- Camera control via Discord commands
- Multi-camera support
- Easy first-time setup

Author: RustPlus Community
License: MIT
"""

import asyncio
import io
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Set

import discord
from discord.ext import commands, tasks
from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager
from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
from rustplus.structs import Vector

# ========================
# Configuration Management
# ========================

class Config:
    """Configuration manager with validation"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            print("❌ Configuration file not found!")
            print(f"Please create '{self.config_path}' using setup wizard:")
            print("  python setup_wizard.py")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Validate required fields
        required = ['discord_token', 'rust_server', 'cameras']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")

        return config

    def get(self, key: str, default=None):
        """Get config value"""
        return self.config.get(key, default)

# ========================
# Camera Stream Manager
# ========================

class CameraStream:
    """Manages a camera stream to a Discord channel"""

    def __init__(self, camera_manager: CameraManager, channel: discord.TextChannel,
                 camera_id: str, config: dict):
        self.camera_manager = camera_manager
        self.channel = channel
        self.camera_id = camera_id
        self.message: Optional[discord.Message] = None
        self.is_streaming = False
        self.last_frame_time = 0
        self.frame_count = 0
        self.last_resubscribe = time.time()

        # Stream settings from config
        self.fps = config.get('stream_fps', 2)
        self.update_interval = 1.0 / self.fps
        self.render_entities = config.get('render_entities', True)
        self.entity_distance = config.get('entity_render_distance', 100)

    async def start(self):
        """Start streaming to Discord channel"""
        self.is_streaming = True

        # Send initial message
        embed = discord.Embed(
            title=f"📹 {self.camera_id.upper()}",
            description="🔄 Initializing camera stream...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Rust+ Surveillance System")

        try:
            self.message = await self.channel.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ No permission to send messages in #{self.channel.name}")
            self.is_streaming = False

    async def update_frame(self):
        """Update frame in Discord"""
        if not self.is_streaming or not self.message:
            return

        # Rate limiting
        current_time = time.time()
        if current_time - self.last_frame_time < self.update_interval:
            return

        # Resubscribe to camera (subscriptions expire after ~15 seconds)
        if current_time - self.last_resubscribe > 10:
            try:
                await self.camera_manager.resubscribe()
                self.last_resubscribe = current_time
            except Exception as e:
                print(f"⚠️ Resubscribe failed for {self.camera_id}: {e}")

        # Check for frame data
        if not self.camera_manager.has_frame_data():
            return

        try:
            # Get frame from camera
            frame = await self.camera_manager.get_frame(
                render_entities=self.render_entities,
                entity_render_distance=self.entity_distance
            )

            if frame is None:
                return

            # Convert to bytes
            img_bytes = io.BytesIO()
            frame.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Get entities info
            entities = await self.camera_manager.get_entities_in_frame()
            player_count = sum(1 for e in entities if e.type == 2)
            tree_count = sum(1 for e in entities if e.type == 1)

            # Create embed
            embed = discord.Embed(
                title=f"📹 {self.camera_id.upper()}",
                color=discord.Color.green() if player_count == 0 else discord.Color.red()
            )

            # Add stats
            embed.add_field(name="👥 Players", value=str(player_count), inline=True)
            embed.add_field(name="🌲 Trees", value=str(tree_count), inline=True)
            embed.add_field(name="📊 Frames", value=str(self.frame_count), inline=True)

            # Add player names if detected
            if player_count > 0:
                players = [e for e in entities if e.type == 2]
                player_names = []
                for p in players[:5]:  # Max 5 to avoid spam
                    distance = p.position.z
                    name = p.name if not p.name.isdigit() else "NPC"
                    player_names.append(f"• {name} ({distance:.0f}m)")

                embed.add_field(
                    name="🚨 DETECTED",
                    value="\n".join(player_names),
                    inline=False
                )

            embed.set_image(url=f"attachment://camera_{self.camera_id}.png")
            embed.set_footer(text=f"Updated every {self.update_interval:.1f}s • FPS: {self.fps}")

            # Update message
            file = discord.File(img_bytes, filename=f'camera_{self.camera_id}.png')
            await self.message.edit(embed=embed, attachments=[file])

            self.last_frame_time = current_time
            self.frame_count += 1

        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                print(f"⚠️ Discord rate limit hit for {self.camera_id}, slowing down...")
                await asyncio.sleep(2)
            else:
                print(f"❌ Discord error updating {self.camera_id}: {e}")
        except Exception as e:
            print(f"❌ Error updating frame for {self.camera_id}: {e}")

    async def stop(self):
        """Stop streaming"""
        self.is_streaming = False
        if self.message:
            embed = discord.Embed(
                title=f"📹 {self.camera_id.upper()}",
                description="⏸️ Stream stopped",
                color=discord.Color.red()
            )
            try:
                await self.message.edit(embed=embed, attachments=[])
            except:
                pass

# ========================
# Main Discord Bot
# ========================

class RustPlusSurveillanceBot(commands.Bot):
    """Main Discord bot for Rust+ surveillance"""

    def __init__(self, config: Config):
        # Bot setup
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=config.get('command_prefix', '!'),
            intents=intents,
            description='Rust+ Surveillance Bot - Monitor your base from Discord'
        )

        self.config = config
        self.rust_socket: Optional[RustSocket] = None
        self.active_streams: Dict[str, CameraStream] = {}
        self.camera_managers: Dict[str, CameraManager] = {}
        self.surveillance_category: Optional[discord.CategoryChannel] = None
        self.camera_channels: Dict[str, discord.TextChannel] = {}
        self.setup_complete = False

    async def setup_hook(self):
        """Called when bot starts"""
        self.update_streams.start()
        print("✅ Bot setup hook completed")

    async def on_ready(self):
        """Called when bot is connected to Discord"""
        print("=" * 60)
        print(f"✅ Bot logged in as {self.user}")
        print(f"📊 Connected to {len(self.guilds)} server(s)")
        print("=" * 60)

        # Connect to Rust+ server
        await self.connect_to_rust()

        # Setup surveillance channels
        if self.rust_socket:
            await self.setup_surveillance_channels()
            await self.start_all_cameras()

    async def connect_to_rust(self):
        """Connect to Rust+ server"""
        print("\n🔌 Connecting to Rust+ server...")

        rust_config = self.config.get('rust_server')

        try:
            self.rust_socket = RustSocket(
                rust_config['ip'],
                rust_config['port'],
                rust_config['steam_id'],
                rust_config['player_token']
            )
            await self.rust_socket.connect()
            print(f"✅ Connected to Rust+ server: {rust_config['ip']}:{rust_config['port']}")
        except Exception as e:
            print(f"❌ Failed to connect to Rust+ server: {e}")
            print("⚠️ Bot will continue running but camera features won't work")

    async def setup_surveillance_channels(self):
        """Setup Discord category and channels for cameras"""
        if not self.guilds:
            print("❌ Bot is not in any Discord servers!")
            return

        guild = self.guilds[0]  # Use first server
        print(f"\n🏗️ Setting up surveillance channels in '{guild.name}'...")

        category_name = self.config.get('category_name', '🎥 SURVEILLANCE')

        # Find or create category
        self.surveillance_category = discord.utils.get(guild.categories, name=category_name)

        if not self.surveillance_category:
            print(f"📁 Creating category: {category_name}")
            try:
                self.surveillance_category = await guild.create_category(
                    category_name,
                    reason="Rust+ Surveillance System"
                )
                print(f"✅ Created category: {category_name}")
            except discord.Forbidden:
                print("❌ No permission to create category!")
                return
        else:
            print(f"✅ Found existing category: {category_name}")

        # Create channel for each camera
        cameras = self.config.get('cameras', {})

        for camera_id, camera_config in cameras.items():
            channel_name = camera_config.get('channel_name', f"📹-{camera_id}")

            # Find or create channel
            channel = discord.utils.get(self.surveillance_category.channels, name=channel_name)

            if not channel:
                print(f"📺 Creating channel: {channel_name}")
                try:
                    channel = await guild.create_text_channel(
                        channel_name,
                        category=self.surveillance_category,
                        topic=f"Live feed from {camera_id} camera",
                        reason=f"Rust+ camera stream: {camera_id}"
                    )
                    print(f"✅ Created channel: #{channel_name}")
                except discord.Forbidden:
                    print(f"❌ No permission to create channel: {channel_name}")
                    continue
            else:
                print(f"✅ Found existing channel: #{channel_name}")

            self.camera_channels[camera_id] = channel

        self.setup_complete = True
        print(f"\n✅ Surveillance system ready with {len(self.camera_channels)} cameras!")

    async def start_all_cameras(self):
        """Start streaming all configured cameras"""
        if not self.rust_socket or not self.setup_complete:
            return

        cameras = self.config.get('cameras', {})

        print(f"\n📹 Starting {len(cameras)} camera stream(s)...")

        for camera_id, camera_config in cameras.items():
            if camera_id not in self.camera_channels:
                print(f"⚠️ No channel found for camera: {camera_id}")
                continue

            # Check if auto-start is enabled
            if not camera_config.get('auto_start', True):
                print(f"⏭️ Skipping {camera_id} (auto_start disabled)")
                continue

            try:
                await self.start_camera(camera_id, self.camera_channels[camera_id])
            except Exception as e:
                print(f"❌ Failed to start camera {camera_id}: {e}")

    async def start_camera(self, camera_id: str, channel: discord.TextChannel):
        """Start a single camera stream"""
        try:
            print(f"📡 Subscribing to camera: {camera_id}")

            camera_manager = await self.rust_socket.get_camera_manager(camera_id)

            if hasattr(camera_manager, 'error'):
                print(f"❌ Failed to subscribe to {camera_id}: {camera_manager.error}")
                return

            # Wait for initial frame data
            await asyncio.sleep(1)

            # Create stream
            stream_config = self.config.get('stream_settings', {})
            stream = CameraStream(camera_manager, channel, camera_id, stream_config)
            await stream.start()

            self.active_streams[camera_id] = stream
            self.camera_managers[camera_id] = camera_manager

            print(f"✅ Camera {camera_id} streaming to #{channel.name}")

        except Exception as e:
            print(f"❌ Error starting camera {camera_id}: {e}")

    @tasks.loop(seconds=0.1)
    async def update_streams(self):
        """Update all active camera streams"""
        for stream in list(self.active_streams.values()):
            if stream.is_streaming:
                await stream.update_frame()

    async def on_close(self):
        """Cleanup on shutdown"""
        print("\n🛑 Shutting down bot...")

        # Stop all streams
        for stream in self.active_streams.values():
            await stream.stop()

        # Exit all cameras
        for camera_mgr in self.camera_managers.values():
            try:
                await camera_mgr.exit_camera()
            except:
                pass

        # Disconnect from Rust+
        if self.rust_socket:
            await self.rust_socket.disconnect()

        print("✅ Cleanup complete")

# ========================
# Bot Commands
# ========================

@commands.command(name='status')
async def status_command(ctx):
    """Show bot status and active cameras"""
    bot = ctx.bot

    embed = discord.Embed(
        title="🤖 Rust+ Surveillance Bot Status",
        color=discord.Color.blue()
    )

    # Rust+ connection
    rust_status = "🟢 Connected" if bot.rust_socket else "🔴 Disconnected"
    embed.add_field(name="Rust+ Server", value=rust_status, inline=True)

    # Active streams
    active_count = len([s for s in bot.active_streams.values() if s.is_streaming])
    embed.add_field(name="Active Cameras", value=f"{active_count}/{len(bot.camera_channels)}", inline=True)

    # Total frames
    total_frames = sum(s.frame_count for s in bot.active_streams.values())
    embed.add_field(name="Total Frames", value=str(total_frames), inline=True)

    # List cameras
    if bot.active_streams:
        camera_info = []
        for cam_id, stream in bot.active_streams.items():
            status = "🟢" if stream.is_streaming else "🔴"
            camera_info.append(f"{status} {cam_id} - {stream.frame_count} frames")

        embed.add_field(
            name="📹 Cameras",
            value="\n".join(camera_info),
            inline=False
        )

    embed.set_footer(text=f"Uptime: {int(time.time() - bot.start_time)}s")

    await ctx.send(embed=embed)

@commands.command(name='restart')
@commands.has_permissions(administrator=True)
async def restart_camera(ctx, camera_id: str):
    """Restart a specific camera (Admin only)"""
    bot = ctx.bot

    if camera_id not in bot.camera_channels:
        await ctx.send(f"❌ Unknown camera: {camera_id}")
        return

    await ctx.send(f"🔄 Restarting camera: {camera_id}")

    # Stop existing stream
    if camera_id in bot.active_streams:
        await bot.active_streams[camera_id].stop()
        await bot.camera_managers[camera_id].exit_camera()
        del bot.active_streams[camera_id]
        del bot.camera_managers[camera_id]

    # Start new stream
    await asyncio.sleep(1)
    await bot.start_camera(camera_id, bot.camera_channels[camera_id])

    await ctx.send(f"✅ Camera {camera_id} restarted")

@commands.command(name='control')
async def control_camera(ctx, camera_id: str, action: str):
    """
    Control a camera

    Usage: !control <camera_id> <action>
    Actions: forward, backward, left, right, up, down, fire
    """
    bot = ctx.bot

    if camera_id not in bot.camera_managers:
        await ctx.send(f"❌ Camera {camera_id} is not active")
        return

    camera_mgr = bot.camera_managers[camera_id]
    action = action.lower()

    # Movement controls
    movement_map = {
        'forward': MovementControls.FORWARD,
        'backward': MovementControls.BACKWARD,
        'left': MovementControls.LEFT,
        'right': MovementControls.RIGHT,
        'jump': MovementControls.JUMP,
        'duck': MovementControls.DUCK,
    }

    # Look controls
    look_map = {
        'up': Vector(0, 0.3),
        'down': Vector(0, -0.3),
        'lookleft': Vector(-0.3, 0),
        'lookright': Vector(0.3, 0),
    }

    try:
        if action in movement_map:
            if camera_mgr.can_move(CameraMovementOptions.MOVEMENT):
                await camera_mgr.send_actions([movement_map[action]])
                await asyncio.sleep(0.3)
                await camera_mgr.clear_movement()
                await ctx.send(f"✅ Moved {camera_id} {action}")
            else:
                await ctx.send(f"❌ Camera {camera_id} cannot move")

        elif action in look_map:
            if camera_mgr.can_move(CameraMovementOptions.MOUSE):
                await camera_mgr.send_mouse_movement(look_map[action])
                await ctx.send(f"✅ Looking {action}")
            else:
                await ctx.send(f"❌ Camera {camera_id} cannot look")

        elif action == 'fire':
            if camera_mgr.can_move(CameraMovementOptions.FIRE):
                await camera_mgr.send_actions([MovementControls.FIRE_PRIMARY])
                await asyncio.sleep(0.1)
                await camera_mgr.clear_movement()
                await ctx.send(f"💥 Fired from {camera_id}!")
            else:
                await ctx.send(f"❌ Camera {camera_id} cannot fire")

        else:
            await ctx.send(f"❌ Unknown action: {action}\n"
                          f"Available: {', '.join(list(movement_map.keys()) + list(look_map.keys()) + ['fire'])}")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Add commands to bot
def setup_commands(bot: RustPlusSurveillanceBot):
    """Add commands to bot instance"""
    bot.add_command(status_command)
    bot.add_command(restart_camera)
    bot.add_command(control_camera)
    bot.start_time = time.time()

# ========================
# Main Entry Point
# ========================

def main():
    """Main entry point"""
    print("=" * 60)
    print("Rust+ Discord Surveillance Bot")
    print("=" * 60)

    # Load configuration
    try:
        config = Config("config.json")
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\n📝 Please run the setup wizard first:")
        print("   python setup_wizard.py")
        return

    # Create bot
    bot = RustPlusSurveillanceBot(config)
    setup_commands(bot)

    # Run bot
    try:
        print("\n🚀 Starting bot...\n")
        bot.run(config.get('discord_token'))
    except discord.LoginFailure:
        print("\n❌ Invalid Discord token!")
        print("Please check your config.json file")
    except KeyboardInterrupt:
        print("\n\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == '__main__':
    main()
