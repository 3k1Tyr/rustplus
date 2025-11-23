"""
Rust+ Discord Bot - Enhanced Version

Single-channel cameras, smart switches, team chat integration,
and comprehensive event notifications.

Features:
- All cameras in ONE Discord channel (grid view)
- Smart switch control panel
- Team chat integration (bi-directional)
- Event notifications (explosions, deaths, raids, etc.)
- Drone control integration

Author: RustPlus Community
License: MIT
"""

import asyncio
import io
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Set, List

import discord
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont
from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager
from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
from rustplus.structs import Vector
from rustplus.events import (
    ChatEvent,
    TeamEvent,
    EntityEvent,
    ProtobufEvent
)

# ========================
# Configuration Management
# ========================

class Config:
    """Configuration manager with validation"""

    def __init__(self, config_path: str = "config_enhanced.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            print(f"❌ Configuration file not found: {self.config_path}")
            print("Run: python setup_wizard_enhanced.py")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Validate required fields
        required = ['discord_token', 'rust_server']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")

        return config

    def get(self, key: str, default=None):
        """Get config value"""
        return self.config.get(key, default)

# ========================
# Camera Grid Manager
# ========================

class CameraGridManager:
    """Manages multiple cameras in a single Discord message"""

    def __init__(self, channel: discord.TextChannel, camera_managers: Dict[str, CameraManager], config: dict):
        self.channel = channel
        self.camera_managers = camera_managers
        self.message: Optional[discord.Message] = None
        self.config = config
        self.fps = config.get('stream_fps', 2)
        self.update_interval = 1.0 / self.fps
        self.last_update = 0
        self.last_resubscribe = {}

    async def start(self):
        """Initialize grid message"""
        embed = discord.Embed(
            title="📹 Surveillance Grid",
            description="Initializing all cameras...",
            color=discord.Color.blue()
        )
        self.message = await self.channel.send(embed=embed)

        for cam_id in self.camera_managers:
            self.last_resubscribe[cam_id] = time.time()

    async def update(self):
        """Update grid with all camera feeds"""
        if not self.message:
            return

        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return

        # Resubscribe to cameras
        for cam_id, camera_mgr in self.camera_managers.items():
            if current_time - self.last_resubscribe.get(cam_id, 0) > 10:
                try:
                    await camera_mgr.resubscribe()
                    self.last_resubscribe[cam_id] = current_time
                except:
                    pass

        # Get all camera frames
        frames = {}
        total_players = 0

        for cam_id, camera_mgr in self.camera_managers.items():
            if not camera_mgr.has_frame_data():
                continue

            try:
                frame = await camera_mgr.get_frame(render_entities=True)
                if frame:
                    frames[cam_id] = frame

                    # Count players
                    entities = await camera_mgr.get_entities_in_frame()
                    players = [e for e in entities if e.type == 2]
                    total_players += len(players)

            except Exception as e:
                print(f"Error getting frame from {cam_id}: {e}")

        if not frames:
            return

        # Create grid image
        grid_image = self._create_grid_image(frames)

        # Convert to bytes
        img_bytes = io.BytesIO()
        grid_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Create embed
        embed = discord.Embed(
            title="📹 Surveillance Grid",
            color=discord.Color.red() if total_players > 0 else discord.Color.green()
        )

        # Add camera stats
        for cam_id in frames:
            camera_mgr = self.camera_managers[cam_id]
            entities = await camera_mgr.get_entities_in_frame()
            players = [e for e in entities if e.type == 2]

            status = "🔴 ALERT" if players else "🟢 Clear"
            player_info = f"{len(players)} player(s)" if players else "No activity"

            embed.add_field(
                name=f"📷 {cam_id.upper()}",
                value=f"{status} - {player_info}",
                inline=True
            )

        embed.set_image(url="attachment://surveillance_grid.png")
        embed.set_footer(text=f"Updated every {self.update_interval:.1f}s")

        # Update message
        try:
            file = discord.File(img_bytes, filename='surveillance_grid.png')
            await self.message.edit(embed=embed, attachments=[file])
            self.last_update = current_time
        except Exception as e:
            print(f"Error updating grid: {e}")

    def _create_grid_image(self, frames: Dict[str, Image.Image]) -> Image.Image:
        """Create a grid of camera images"""
        if not frames:
            # Return blank image
            return Image.new('RGB', (800, 600), color=(50, 50, 50))

        # Calculate grid size
        num_cameras = len(frames)
        cols = 2 if num_cameras > 1 else 1
        rows = (num_cameras + cols - 1) // cols

        # Frame size (resize all to same size)
        frame_width = 400
        frame_height = 300

        # Create grid
        grid_width = frame_width * cols
        grid_height = frame_height * rows

        grid = Image.new('RGB', (grid_width, grid_height), color=(30, 30, 30))
        draw = ImageDraw.Draw(grid)

        # Place frames in grid
        for idx, (cam_id, frame) in enumerate(frames.items()):
            row = idx // cols
            col = idx % cols

            x = col * frame_width
            y = row * frame_height

            # Resize frame
            resized = frame.resize((frame_width, frame_height))
            grid.paste(resized, (x, y))

            # Draw label
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()

            # Draw background for text
            text_bg = Image.new('RGBA', (frame_width, 30), color=(0, 0, 0, 180))
            grid.paste(text_bg, (x, y), text_bg)

            # Draw camera label
            draw.text((x + 10, y + 5), f"📹 {cam_id.upper()}", fill=(255, 255, 255), font=font)

        return grid

# ========================
# Smart Switch Manager
# ========================

class SmartSwitchManager:
    """Manages smart switches in Discord"""

    def __init__(self, rust_socket: RustSocket, channel: discord.TextChannel, switches: dict):
        self.rust_socket = rust_socket
        self.channel = channel
        self.switches = switches  # {name: entity_id}
        self.message: Optional[discord.Message] = None
        self.states = {}

    async def start(self):
        """Initialize switch control panel"""
        embed = discord.Embed(
            title="⚡ Smart Switch Control",
            description="Loading switch states...",
            color=discord.Color.blue()
        )
        self.message = await self.channel.send(embed=embed)

        # Subscribe to all switches
        for name, entity_id in self.switches.items():
            try:
                await self.rust_socket.set_subscription_to_entity(entity_id, True)
            except Exception as e:
                print(f"Error subscribing to {name}: {e}")

        await self.update_display()

    async def update_display(self):
        """Update switch display"""
        if not self.message:
            return

        # Get switch states
        for name, entity_id in self.switches.items():
            try:
                info = await self.rust_socket.get_entity_info(entity_id)
                if hasattr(info, 'value'):
                    self.states[name] = info.value
            except Exception as e:
                print(f"Error getting {name} state: {e}")
                self.states[name] = None

        # Create embed
        embed = discord.Embed(
            title="⚡ Smart Switch Control",
            description="Control your base switches from Discord",
            color=discord.Color.gold()
        )

        for name, state in self.states.items():
            if state is None:
                status = "❓ Unknown"
                emoji = "⚠️"
            elif state:
                status = "🟢 ON"
                emoji = "💡"
            else:
                status = "🔴 OFF"
                emoji = "⚫"

            entity_id = self.switches[name]
            embed.add_field(
                name=f"{emoji} {name}",
                value=f"{status}\nID: `{entity_id}`",
                inline=True
            )

        embed.set_footer(text="Use !switch <name> <on/off> to control")

        try:
            await self.message.edit(embed=embed)
        except Exception as e:
            print(f"Error updating switch display: {e}")

    async def toggle_switch(self, name: str, value: bool) -> bool:
        """Toggle a switch"""
        if name not in self.switches:
            return False

        entity_id = self.switches[name]

        try:
            await self.rust_socket.set_entity_value(entity_id, value)
            self.states[name] = value
            await self.update_display()
            return True
        except Exception as e:
            print(f"Error toggling {name}: {e}")
            return False

# ========================
# Team Chat Bridge
# ========================

class TeamChatBridge:
    """Bridges Discord and Rust team chat"""

    def __init__(self, rust_socket: RustSocket, channel: discord.TextChannel, bot_user_id: int):
        self.rust_socket = rust_socket
        self.channel = channel
        self.bot_user_id = bot_user_id

    async def send_to_rust(self, message: str, author: str):
        """Send Discord message to Rust team chat"""
        formatted = f"[Discord - {author}] {message}"
        try:
            await self.rust_socket.send_team_message(formatted)
        except Exception as e:
            print(f"Error sending to Rust chat: {e}")

    async def send_to_discord(self, message: str, author: str):
        """Send Rust message to Discord"""
        embed = discord.Embed(
            description=message,
            color=discord.Color.orange()
        )
        embed.set_author(name=f"💬 {author} (Rust)")
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending to Discord: {e}")

# ========================
# Event Notifier
# ========================

class EventNotifier:
    """Sends notifications for game events"""

    def __init__(self, rust_socket: RustSocket, channel: discord.TextChannel):
        self.rust_socket = rust_socket
        self.channel = channel

    async def notify_explosion(self, location: str = "Unknown"):
        """Notify about explosion"""
        embed = discord.Embed(
            title="💥 EXPLOSION DETECTED",
            description=f"Location: {location}",
            color=discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.channel.send("@everyone", embed=embed)
        except:
            pass

    async def notify_player_death(self, player: str):
        """Notify about player death"""
        embed = discord.Embed(
            title="☠️ Team Member Death",
            description=f"{player} has died",
            color=discord.Color.dark_red()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.channel.send(embed=embed)
        except:
            pass

    async def notify_entity_destroyed(self, entity_type: str):
        """Notify about entity destruction"""
        embed = discord.Embed(
            title="🔧 Entity Destroyed",
            description=f"{entity_type} has been destroyed",
            color=discord.Color.orange()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.channel.send(embed=embed)
        except:
            pass

# ========================
# Main Discord Bot
# ========================

class EnhancedRustBot(commands.Bot):
    """Enhanced Discord bot with single-channel cameras"""

    def __init__(self, config: Config):
        # Bot setup
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=config.get('command_prefix', '!'),
            intents=intents,
            description='Enhanced Rust+ Bot - Surveillance, Switches, and Team Chat'
        )

        self.config = config
        self.rust_socket: Optional[RustSocket] = None
        self.camera_grid: Optional[CameraGridManager] = None
        self.switch_manager: Optional[SmartSwitchManager] = None
        self.chat_bridge: Optional[TeamChatBridge] = None
        self.event_notifier: Optional[EventNotifier] = None
        self.camera_managers: Dict[str, CameraManager] = {}

        # Channels
        self.surveillance_channel: Optional[discord.TextChannel] = None
        self.switches_channel: Optional[discord.TextChannel] = None
        self.teamchat_channel: Optional[discord.TextChannel] = None
        self.events_channel: Optional[discord.TextChannel] = None

    async def setup_hook(self):
        """Called when bot starts"""
        self.update_loop.start()
        print("✅ Bot setup hook completed")

    async def on_ready(self):
        """Called when bot is connected to Discord"""
        print("=" * 60)
        print(f"✅ Bot logged in as {self.user}")
        print(f"📊 Connected to {len(self.guilds)} server(s)")
        print("=" * 60)

        # Connect to Rust+
        await self.connect_to_rust()

        # Setup channels
        if self.rust_socket:
            await self.setup_channels()
            await self.start_systems()

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
            print(f"✅ Connected to Rust+ server")

            # Setup event handlers
            await self.setup_event_handlers()

        except Exception as e:
            print(f"❌ Failed to connect: {e}")

    async def setup_event_handlers(self):
        """Setup Rust+ event handlers"""
        # Chat events
        @ChatEvent(self.rust_socket.server_details)
        async def chat_handler(event):
            if self.chat_bridge and event.message.message:
                await self.chat_bridge.send_to_discord(
                    event.message.message,
                    event.message.name
                )

        # Entity events
        @EntityEvent(self.rust_socket.server_details)
        async def entity_handler(event):
            if self.switch_manager:
                await self.switch_manager.update_display()

        print("✅ Event handlers registered")

    async def setup_channels(self):
        """Setup Discord channels"""
        if not self.guilds:
            print("❌ Bot is not in any Discord servers!")
            return

        guild = self.guilds[0]
        category_name = self.config.get('category_name', '🎥 RUST+ CONTROL')

        print(f"\n🏗️ Setting up channels in '{guild.name}'...")

        # Find or create category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            print(f"✅ Created category: {category_name}")

        # Create channels
        channels_to_create = {
            '📹-surveillance': 'surveillance_channel',
            '⚡-switches': 'switches_channel',
            '💬-team-chat': 'teamchat_channel',
            '🚨-events': 'events_channel'
        }

        for channel_name, attr_name in channels_to_create.items():
            channel = discord.utils.get(category.channels, name=channel_name)
            if not channel:
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category
                )
                print(f"✅ Created channel: #{channel_name}")
            setattr(self, attr_name, channel)

        print("✅ All channels ready")

    async def start_systems(self):
        """Start all bot systems"""
        print("\n🚀 Starting bot systems...")

        # Start cameras
        cameras = self.config.get('cameras', {})
        if cameras and self.surveillance_channel:
            for cam_id in cameras:
                try:
                    camera_mgr = await self.rust_socket.get_camera_manager(cam_id)
                    self.camera_managers[cam_id] = camera_mgr
                    print(f"✅ Connected to camera: {cam_id}")
                except Exception as e:
                    print(f"❌ Failed to connect to {cam_id}: {e}")

            if self.camera_managers:
                self.camera_grid = CameraGridManager(
                    self.surveillance_channel,
                    self.camera_managers,
                    self.config.get('stream_settings', {})
                )
                await self.camera_grid.start()
                print(f"✅ Camera grid started with {len(self.camera_managers)} cameras")

        # Start switches
        switches = self.config.get('switches', {})
        if switches and self.switches_channel:
            self.switch_manager = SmartSwitchManager(
                self.rust_socket,
                self.switches_channel,
                switches
            )
            await self.switch_manager.start()
            print(f"✅ Switch manager started with {len(switches)} switches")

        # Start team chat bridge
        if self.teamchat_channel:
            self.chat_bridge = TeamChatBridge(
                self.rust_socket,
                self.teamchat_channel,
                self.user.id
            )
            print("✅ Team chat bridge started")

        # Start event notifier
        if self.events_channel:
            self.event_notifier = EventNotifier(
                self.rust_socket,
                self.events_channel
            )
            print("✅ Event notifier started")

        print("\n✅ All systems operational!")

    @tasks.loop(seconds=0.1)
    async def update_loop(self):
        """Main update loop"""
        if self.camera_grid:
            await self.camera_grid.update()

    async def on_message(self, message):
        """Handle Discord messages"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Bridge team chat
        if message.channel == self.teamchat_channel and self.chat_bridge:
            await self.chat_bridge.send_to_rust(
                message.content,
                message.author.display_name
            )

        # Process commands
        await self.process_commands(message)

    async def on_close(self):
        """Cleanup on shutdown"""
        print("\n🛑 Shutting down...")

        for camera_mgr in self.camera_managers.values():
            try:
                await camera_mgr.exit_camera()
            except:
                pass

        if self.rust_socket:
            await self.rust_socket.disconnect()

        print("✅ Cleanup complete")

# ========================
# Bot Commands
# ========================

@commands.command(name='status')
async def status_command(ctx):
    """Show bot status"""
    bot = ctx.bot

    embed = discord.Embed(
        title="🤖 Enhanced Rust+ Bot Status",
        color=discord.Color.blue()
    )

    # Rust+ connection
    rust_status = "🟢 Connected" if bot.rust_socket else "🔴 Disconnected"
    embed.add_field(name="Rust+ Server", value=rust_status, inline=True)

    # Cameras
    embed.add_field(name="Cameras", value=str(len(bot.camera_managers)), inline=True)

    # Switches
    switch_count = len(bot.switch_manager.switches) if bot.switch_manager else 0
    embed.add_field(name="Smart Switches", value=str(switch_count), inline=True)

    await ctx.send(embed=embed)

@commands.command(name='switch')
async def switch_command(ctx, name: str, state: str):
    """Control a smart switch

    Usage: !switch <name> <on/off>
    """
    bot = ctx.bot

    if not bot.switch_manager:
        await ctx.send("❌ Switch manager not initialized")
        return

    state = state.lower()
    if state not in ['on', 'off']:
        await ctx.send("❌ State must be 'on' or 'off'")
        return

    value = state == 'on'

    if await bot.switch_manager.toggle_switch(name, value):
        await ctx.send(f"✅ Turned {name} {state}")
    else:
        await ctx.send(f"❌ Failed to control {name}")

@commands.command(name='control')
async def control_camera(ctx, camera_id: str, action: str):
    """Control a camera

    Usage: !control <camera_id> <action>
    """
    bot = ctx.bot

    if camera_id not in bot.camera_managers:
        await ctx.send(f"❌ Camera {camera_id} not found")
        return

    camera_mgr = bot.camera_managers[camera_id]
    action = action.lower()

    movement_map = {
        'forward': MovementControls.FORWARD,
        'backward': MovementControls.BACKWARD,
        'left': MovementControls.LEFT,
        'right': MovementControls.RIGHT,
    }

    look_map = {
        'up': Vector(0, 0.3),
        'down': Vector(0, -0.3),
        'lookleft': Vector(-0.3, 0),
        'lookright': Vector(0.3, 0),
    }

    try:
        if action in movement_map:
            await camera_mgr.send_actions([movement_map[action]])
            await asyncio.sleep(0.3)
            await camera_mgr.clear_movement()
            await ctx.send(f"✅ Moved {camera_id} {action}")

        elif action in look_map:
            await camera_mgr.send_mouse_movement(look_map[action])
            await ctx.send(f"✅ Looking {action}")

        elif action == 'fire':
            await camera_mgr.send_actions([MovementControls.FIRE_PRIMARY])
            await asyncio.sleep(0.1)
            await camera_mgr.clear_movement()
            await ctx.send(f"💥 Fired from {camera_id}!")

        else:
            await ctx.send(f"❌ Unknown action: {action}")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

def setup_commands(bot: EnhancedRustBot):
    """Add commands to bot"""
    bot.add_command(status_command)
    bot.add_command(switch_command)
    bot.add_command(control_camera)

# ========================
# Main Entry Point
# ========================

def main():
    """Main entry point"""
    print("=" * 60)
    print("Enhanced Rust+ Discord Bot")
    print("=" * 60)

    # Load configuration
    try:
        config = Config("config_enhanced.json")
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\n📝 Run: python setup_wizard_enhanced.py")
        return

    # Create bot
    bot = EnhancedRustBot(config)
    setup_commands(bot)

    # Run bot
    try:
        print("\n🚀 Starting bot...\n")
        bot.run(config.get('discord_token'))
    except KeyboardInterrupt:
        print("\n\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == '__main__':
    main()
