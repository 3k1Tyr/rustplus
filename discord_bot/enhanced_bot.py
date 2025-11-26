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
import logging
import os
import sys
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
from rustplus.annotations import (
    ChatEvent,
    TeamEvent,
    EntityEvent,
    ProtobufEvent
)

# Import detection system
from camera_detection import (
    CameraDetectionManager,
    DetectionDatabase
)

# ========================
# Logging Setup
# ========================

def setup_logging(log_level=logging.INFO):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'enhanced_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set discord.py logging to WARNING to reduce noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)

    return logging.getLogger('rustplus_bot')

# Initialize logger
logger = setup_logging()

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
            logger.error(f"Configuration file not found: {self.config_path}")
            logger.info("Run: python setup_wizard_enhanced.py")
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
# Permission System
# ========================

def has_permission(ctx, config: Config) -> tuple[bool, str]:
    """
    Check if user has permission to execute control commands

    Returns:
        tuple: (has_permission, reason)
    """
    # Get permission config
    allowed_roles = config.get('permissions', {}).get('allowed_roles', [])
    allowed_users = config.get('permissions', {}).get('allowed_users', [])

    # If no permissions configured, default to admin-only
    if not allowed_roles and not allowed_users:
        if ctx.author.guild_permissions.administrator:
            return True, "Administrator"
        return False, "No permissions configured. Administrators only."

    # Check user ID whitelist
    if ctx.author.id in allowed_users:
        return True, "User whitelist"

    # Check role whitelist
    if ctx.guild and hasattr(ctx.author, 'roles'):
        user_role_names = [role.name for role in ctx.author.roles]
        for role_name in allowed_roles:
            if role_name in user_role_names:
                return True, f"Role: {role_name}"

    # Check admin as fallback
    if ctx.author.guild_permissions.administrator:
        return True, "Administrator"

    return False, "Missing required role or user permission"

def require_permission(config: Config):
    """
    Decorator for commands that require permissions

    Usage:
        @require_permission(config)
        @commands.command()
        async def my_command(ctx):
            pass
    """
    def decorator(func):
        async def wrapper(ctx, *args, **kwargs):
            has_perm, reason = has_permission(ctx, config)
            if not has_perm:
                await ctx.send(f"❌ Permission denied: {reason}")
                logger.warning(f"Permission denied for {ctx.author} ({ctx.author.id}): {reason}")
                return
            logger.info(f"Permission granted for {ctx.author} ({ctx.author.id}): {reason}")
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

# ========================
# Rate Limiter
# ========================

class RateLimiter:
    """Simple rate limiter for Discord API calls"""

    def __init__(self, max_calls: int = 5, period: float = 1.0):
        """
        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()

        # Remove old calls outside the period
        self.calls = [call_time for call_time in self.calls if call_time > now - self.period]

        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                # Cleanup again after sleeping
                now = time.time()
                self.calls = [call_time for call_time in self.calls if call_time > now - self.period]

        # Record this call
        self.calls.append(time.time())

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
        # Rate limiter: 4 updates per second max (conservative)
        self.rate_limiter = RateLimiter(max_calls=4, period=1.0)

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
                logger.error(f"Error getting frame from {cam_id}: {e}", exc_info=True)

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

        # Update message with rate limiting
        try:
            # Respect rate limits
            await self.rate_limiter.acquire()

            file = discord.File(img_bytes, filename='surveillance_grid.png')
            await self.message.edit(embed=embed, attachments=[file])
            self.last_update = current_time
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited despite our protection
                logger.warning(f"Hit Discord rate limit: {e}")
                await asyncio.sleep(2)  # Back off
            else:
                logger.error(f"Discord HTTP error updating grid: {e}")
        except Exception as e:
            logger.error(f"Error updating camera grid: {e}", exc_info=True)

    def _get_font(self, size: int = 20) -> ImageFont.FreeTypeFont:
        """Get font with cross-platform support"""
        import platform

        font_paths = {
            'Linux': [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            ],
            'Darwin': [  # macOS
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial.ttf',
            ],
            'Windows': [
                'C:\\Windows\\Fonts\\arialbd.ttf',
                'C:\\Windows\\Fonts\\arial.ttf',
                'C:\\Windows\\Fonts\\calibrib.ttf',
            ]
        }

        system = platform.system()
        paths = font_paths.get(system, [])

        for path in paths:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

        # Fallback to default font
        logger.warning(f"Could not load TrueType font on {system}, using default font")
        return ImageFont.load_default()

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
            font = self._get_font(20)

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
        self.rate_limiter = RateLimiter(max_calls=4, period=1.0)

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
                logger.error(f"Error subscribing to switch {name}: {e}", exc_info=True)

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
                logger.warning(f"Error getting {name} state: {e}")
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

        # Update message with rate limiting
        try:
            await self.rate_limiter.acquire()  # Respect rate limits
            await self.message.edit(embed=embed)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited despite our protection
                logger.warning(f"Hit Discord rate limit on switch display: {e}")
                await asyncio.sleep(2)  # Back off
            else:
                logger.error(f"Discord HTTP error updating switch display: {e}")
        except Exception as e:
            logger.error(f"Error updating switch display: {e}", exc_info=True)

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
            logger.error(f"Error toggling {name}: {e}", exc_info=True)
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
        self.rate_limiter = RateLimiter(max_calls=4, period=1.0)

    async def send_to_rust(self, message: str, author: str):
        """Send Discord message to Rust team chat"""
        formatted = f"[Discord - {author}] {message}"
        try:
            await self.rust_socket.send_team_message(formatted)
        except Exception as e:
            logger.error(f"Error sending to Rust chat: {e}", exc_info=True)

    async def send_to_discord(self, message: str, author: str):
        """Send Rust message to Discord"""
        embed = discord.Embed(
            description=message,
            color=discord.Color.orange()
        )
        embed.set_author(name=f"💬 {author} (Rust)")
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.rate_limiter.acquire()  # Respect rate limits
            await self.channel.send(embed=embed)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Hit Discord rate limit on team chat: {e}")
                await asyncio.sleep(2)  # Back off
            else:
                logger.error(f"Discord HTTP error sending team chat: {e}")
        except Exception as e:
            logger.error(f"Error sending to Discord: {e}", exc_info=True)

# ========================
# Event Notifier
# ========================

class EventNotifier:
    """
    Sends notifications for game events

    ⚠️ WARNING: This is a PLANNED FEATURE - NOT FULLY IMPLEMENTED

    The notification methods exist but are NOT automatically triggered because:
    1. Explosion detection requires parsing protobuf binary data or map markers
    2. Death detection requires monitoring team member status changes
    3. Entity destruction requires comparing entity states over time

    To implement these features, you would need to:
    - Parse AppBroadcast.entity_changed for entity destruction events
    - Monitor team_info for member deaths (offline status changes)
    - Parse AppBroadcast for explosion markers (requires protobuf knowledge)
    - Add polling loops to check for state changes

    Currently these methods can be called manually, but NO automatic detection is implemented.
    """

    def __init__(self, rust_socket: RustSocket, channel: discord.TextChannel):
        self.rust_socket = rust_socket
        self.channel = channel
        self.rate_limiter = RateLimiter(max_calls=4, period=1.0)

    async def notify_explosion(self, location: str = "Unknown"):
        """Notify about explosion"""
        embed = discord.Embed(
            title="💥 EXPLOSION DETECTED",
            description=f"Location: {location}",
            color=discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.rate_limiter.acquire()  # Respect rate limits
            await self.channel.send("@everyone", embed=embed)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Hit Discord rate limit on explosion notification: {e}")
            else:
                logger.error(f"Discord HTTP error sending explosion notification: {e}")
        except Exception as e:
            logger.error(f"Error sending explosion notification: {e}", exc_info=True)

    async def notify_player_death(self, player: str):
        """Notify about player death"""
        embed = discord.Embed(
            title="☠️ Team Member Death",
            description=f"{player} has died",
            color=discord.Color.dark_red()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.rate_limiter.acquire()  # Respect rate limits
            await self.channel.send(embed=embed)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Hit Discord rate limit on death notification: {e}")
            else:
                logger.error(f"Discord HTTP error sending death notification: {e}")
        except Exception as e:
            logger.error(f"Error sending death notification: {e}", exc_info=True)

    async def notify_entity_destroyed(self, entity_type: str):
        """Notify about entity destruction"""
        embed = discord.Embed(
            title="🔧 Entity Destroyed",
            description=f"{entity_type} has been destroyed",
            color=discord.Color.orange()
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await self.rate_limiter.acquire()  # Respect rate limits
            await self.channel.send(embed=embed)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Hit Discord rate limit on entity destroyed notification: {e}")
            else:
                logger.error(f"Discord HTTP error sending entity destroyed notification: {e}")
        except Exception as e:
            logger.error(f"Error sending entity destroyed notification: {e}", exc_info=True)

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

        # Detection system
        self.detection_db: Optional[DetectionDatabase] = None
        self.detection_manager: Optional[CameraDetectionManager] = None

        # Channels
        self.surveillance_channel: Optional[discord.TextChannel] = None
        self.switches_channel: Optional[discord.TextChannel] = None
        self.teamchat_channel: Optional[discord.TextChannel] = None
        self.events_channel: Optional[discord.TextChannel] = None

    async def setup_hook(self):
        """Called when bot starts"""
        self.update_loop.start()
        logger.info("✅ Bot setup hook completed")

    async def on_ready(self):
        """Called when bot is connected to Discord"""
        logger.info("=" * 60)
        logger.info(f"✅ Bot logged in as {self.user}")
        logger.info(f"📊 Connected to {len(self.guilds)} server(s)")
        logger.info("=" * 60)

        # Connect to Rust+
        await self.connect_to_rust()

        # Setup channels
        if self.rust_socket:
            await self.setup_channels()
            await self.start_systems()

    async def connect_to_rust(self):
        """Connect to Rust+ server"""
        logger.info("🔌 Connecting to Rust+ server...")

        rust_config = self.config.get('rust_server')

        try:
            self.rust_socket = RustSocket(
                rust_config['ip'],
                rust_config['port'],
                rust_config['steam_id'],
                rust_config['player_token']
            )
            await self.rust_socket.connect()
            logger.info(f"✅ Connected to Rust+ server: {rust_config['ip']}:{rust_config['port']}")

            # Setup event handlers
            await self.setup_event_handlers()

        except Exception as e:
            logger.error(f"❌ Failed to connect to Rust+ server: {e}", exc_info=True)
            logger.warning("⚠️ Bot will continue but camera features won't work")

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

        logger.info("✅ Event handlers registered")

    async def setup_channels(self):
        """Setup Discord channels"""
        if not self.guilds:
            logger.error("❌ Bot is not in any Discord servers!")
            return

        guild = self.guilds[0]
        category_name = self.config.get('category_name', '🎥 RUST+ CONTROL')

        logger.info(f"\n🏗️ Setting up channels in '{guild.name}'...")

        # Find or create category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            logger.info(f"✅ Created category: {category_name}")

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
                logger.info(f"✅ Created channel: #{channel_name}")
            setattr(self, attr_name, channel)

        logger.info("✅ All channels ready")

    async def start_systems(self):
        """Start all bot systems"""
        logger.info("\n🚀 Starting bot systems...")

        # Start cameras
        cameras = self.config.get('cameras', {})
        if cameras and self.surveillance_channel:
            for cam_id in cameras:
                try:
                    camera_mgr = await self.rust_socket.get_camera_manager(cam_id)
                    self.camera_managers[cam_id] = camera_mgr
                    logger.info(f"✅ Connected to camera: {cam_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to connect to {cam_id}: {e}")

            if self.camera_managers:
                self.camera_grid = CameraGridManager(
                    self.surveillance_channel,
                    self.camera_managers,
                    self.config.get('stream_settings', {})
                )
                await self.camera_grid.start()
                logger.info(f"✅ Camera grid started with {len(self.camera_managers)} cameras")

        # Start switches
        switches = self.config.get('switches', {})
        if switches and self.switches_channel:
            self.switch_manager = SmartSwitchManager(
                self.rust_socket,
                self.switches_channel,
                switches
            )
            await self.switch_manager.start()
            logger.info(f"✅ Switch manager started with {len(switches)} switches")

        # Start team chat bridge
        if self.teamchat_channel:
            self.chat_bridge = TeamChatBridge(
                self.rust_socket,
                self.teamchat_channel,
                self.user.id
            )
            logger.info("✅ Team chat bridge started")

        # Start event notifier
        if self.events_channel:
            self.event_notifier = EventNotifier(
                self.rust_socket,
                self.events_channel
            )
            logger.warning("⚠️ Event notifier initialized but automatic event detection is NOT implemented")
            logger.info("Event notification methods can be called manually but won't trigger automatically")

        # Start detection system
        if self.config.get('detection_system', {}).get('enabled', False):
            try:
                self.detection_db = DetectionDatabase("discord_bot/camera_detections.db")
                self.detection_manager = CameraDetectionManager(
                    self.rust_socket,
                    self.switch_manager,
                    self.detection_db
                )
                await self.detection_manager.start()
                logger.info("✅ Camera detection system started")
            except Exception as e:
                logger.error(f"Failed to start detection system: {e}", exc_info=True)

        logger.info("\n✅ All systems operational!")

    async def _process_camera_detections(self):
        """Process camera entities for detection system"""
        try:
            for cam_id, camera_mgr in self.camera_managers.items():
                if camera_mgr.has_frame_data():
                    entities = await camera_mgr.get_entities_in_frame()
                    if entities:
                        await self.detection_manager.process_camera_frame(
                            cam_id, entities, camera_position=None
                        )
        except Exception as e:
            logger.error(f"Error processing camera detections: {e}", exc_info=True)

    @tasks.loop(seconds=0.1)
    async def update_loop(self):
        """Main update loop"""
        if self.camera_grid:
            await self.camera_grid.update()

        # Process camera detections
        if self.detection_manager:
            await self._process_camera_detections()

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
        logger.info("\n🛑 Shutting down...")

        # Stop detection manager
        if self.detection_manager:
            try:
                await self.detection_manager.stop()
                logger.info("Detection manager stopped")
            except Exception as e:
                logger.warning(f"Error stopping detection manager: {e}")

        # Close detection database
        if self.detection_db:
            try:
                self.detection_db.close()
                logger.info("Detection database closed")
            except Exception as e:
                logger.warning(f"Error closing detection database: {e}")

        for camera_mgr in self.camera_managers.values():
            try:
                await camera_mgr.exit_camera()
            except Exception as e:
                logger.warning(f"Error closing camera: {e}")

        if self.rust_socket:
            await self.rust_socket.disconnect()

        logger.info("✅ Cleanup complete")

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

    # Permission check
    has_perm, reason = has_permission(ctx, bot.config)
    if not has_perm:
        await ctx.send(f"❌ Permission denied: {reason}")
        logger.warning(f"Permission denied for {ctx.author} ({ctx.author.id}) on switch command: {reason}")
        return

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
        logger.info(f"{ctx.author} switched {name} to {state}")
    else:
        await ctx.send(f"❌ Failed to control {name}")

@commands.command(name='control')
async def control_camera(ctx, camera_id: str, action: str):
    """Control a camera

    Usage: !control <camera_id> <action>
    """
    bot = ctx.bot

    # Permission check
    has_perm, reason = has_permission(ctx, bot.config)
    if not has_perm:
        await ctx.send(f"❌ Permission denied: {reason}")
        logger.warning(f"Permission denied for {ctx.author} ({ctx.author.id}) on camera control: {reason}")
        return

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
            logger.info(f"{ctx.author} moved camera {camera_id} {action}")

        elif action in look_map:
            await camera_mgr.send_mouse_movement(look_map[action])
            await ctx.send(f"✅ Looking {action}")
            logger.info(f"{ctx.author} looked {action} on camera {camera_id}")

        elif action == 'fire':
            await camera_mgr.send_actions([MovementControls.FIRE_PRIMARY])
            await asyncio.sleep(0.1)
            await camera_mgr.clear_movement()
            await ctx.send(f"💥 Fired from {camera_id}!")
            logger.info(f"{ctx.author} fired from camera {camera_id}")

        else:
            await ctx.send(f"❌ Unknown action: {action}")
            logger.warning(f"{ctx.author} attempted unknown camera action: {action}")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        logger.error(f"Error in camera control for {ctx.author}: {e}", exc_info=True)

# ========================
# Detection Commands
# ========================

@commands.command(name='detections')
async def detections_command(ctx, camera_id: str = None):
    """Show current camera detections with distances

    Usage:
        !detections          - Show all camera detections
        !detections drone    - Show specific camera detections
    """
    bot = ctx.bot

    if not bot.detection_manager:
        await ctx.send("❌ Detection system is not enabled")
        return

    detections = bot.detection_manager.get_current_detections(camera_id)

    if not detections or not any(detections.values()):
        await ctx.send("🟢 No detections on cameras")
        return

    embed = discord.Embed(
        title="🎯 Camera Detections",
        description="Current entities detected on cameras",
        color=discord.Color.red()
    )

    for cam_id, entities in detections.items():
        if not entities:
            continue

        # Separate team and enemies
        enemies = [e for e in entities if not e.is_team_member]
        team = [e for e in entities if e.is_team_member]

        lines = []

        if enemies:
            lines.append("**⚠️ ENEMIES:**")
            for idx, entity in enumerate(sorted(enemies, key=lambda e: e.distance), start=1):
                lines.append(f"{idx}. {entity.name or 'Unknown'} - **{entity.distance:.1f}m**")

        if team:
            lines.append("\n**✅ Team:**")
            for entity in team:
                lines.append(f"• {entity.name} - {entity.distance:.1f}m")

        if not lines:
            lines.append("🟢 Clear")

        embed.add_field(
            name=f"📷 {cam_id.upper()}",
            value="\n".join(lines),
            inline=False
        )

    # Add detection counts
    if bot.detection_manager.session_detection_counts:
        counts = []
        for cam, count in bot.detection_manager.session_detection_counts.items():
            counts.append(f"{cam}: {count} enemies")
        embed.set_footer(text="Session counts: " + ", ".join(counts))

    await ctx.send(embed=embed)

@commands.command(name='trigger')
async def trigger_command(ctx, action: str = None, *args):
    """Manage distance-based triggers

    Usage:
        !trigger add <camera> <count> <distance> <switch>
        !trigger list [camera]
        !trigger remove <id>
        !trigger reset [camera]

    Examples:
        !trigger add drone 1 30 turrets
        !trigger add drone 2 50 lights
        !trigger list
        !trigger list drone
        !trigger remove 1
        !trigger reset drone
    """
    bot = ctx.bot

    # Permission check
    has_perm, reason = has_permission(ctx, bot.config)
    if not has_perm:
        await ctx.send(f"❌ Permission denied: {reason}")
        return

    if not bot.detection_manager:
        await ctx.send("❌ Detection system is not enabled")
        return

    if not action:
        await ctx.send("❌ Usage: `!trigger <add|list|remove|reset>`\nSee `!help trigger` for details")
        return

    action = action.lower()

    # ADD TRIGGER
    if action == 'add':
        if len(args) < 4:
            await ctx.send("❌ Usage: `!trigger add <camera> <count> <distance> <switch>`")
            return

        camera_id = args[0]
        try:
            detection_count = int(args[1])
            distance_threshold = float(args[2])
            switch_name = args[3]
        except ValueError:
            await ctx.send("❌ Invalid count or distance value")
            return

        if camera_id not in bot.camera_managers:
            await ctx.send(f"❌ Camera '{camera_id}' not found")
            return

        success = await bot.detection_manager.add_trigger(
            camera_id, detection_count, distance_threshold, switch_name
        )

        if success:
            await ctx.send(
                f"✅ Trigger added:\n"
                f"Camera: **{camera_id}**\n"
                f"Detection #{detection_count} at ≤{distance_threshold}m → {switch_name}"
            )
            logger.info(f"{ctx.author} added trigger: {camera_id} #{detection_count} @ {distance_threshold}m → {switch_name}")
        else:
            await ctx.send(f"❌ Failed to add trigger (check switch name)")

    # LIST TRIGGERS
    elif action == 'list':
        camera_id = args[0] if args else None

        triggers = bot.detection_db.get_triggers(camera_id)

        if not triggers:
            msg = f"No triggers configured"
            if camera_id:
                msg += f" for camera '{camera_id}'"
            await ctx.send(msg)
            return

        embed = discord.Embed(
            title="🎯 Distance Triggers",
            color=discord.Color.blue()
        )

        for trigger in triggers:
            status = "✅ Enabled" if trigger.enabled else "❌ Disabled"
            embed.add_field(
                name=f"ID {trigger.trigger_id} - {trigger.camera_id.upper()}",
                value=(
                    f"Detection #{trigger.detection_count}\n"
                    f"Distance: ≤{trigger.distance_threshold}m\n"
                    f"Switch: {trigger.switch_name}\n"
                    f"Status: {status}"
                ),
                inline=True
            )

        await ctx.send(embed=embed)

    # REMOVE TRIGGER
    elif action == 'remove':
        if not args:
            await ctx.send("❌ Usage: `!trigger remove <id>`")
            return

        try:
            trigger_id = int(args[0])
        except ValueError:
            await ctx.send("❌ Invalid trigger ID")
            return

        bot.detection_db.disable_trigger(trigger_id)

        # Remove from runtime cache
        for cam_id in bot.detection_manager.triggers:
            bot.detection_manager.triggers[cam_id] = [
                t for t in bot.detection_manager.triggers[cam_id]
                if t.trigger_id != trigger_id
            ]

        await ctx.send(f"✅ Trigger {trigger_id} disabled")
        logger.info(f"{ctx.author} disabled trigger {trigger_id}")

    # RESET DETECTION COUNTS
    elif action == 'reset':
        camera_id = args[0] if args else None
        bot.detection_manager.reset_detection_counts(camera_id)

        if camera_id:
            await ctx.send(f"✅ Reset detection count for {camera_id}")
        else:
            await ctx.send("✅ Reset all detection counts")
        logger.info(f"{ctx.author} reset detection counts")

    else:
        await ctx.send(f"❌ Unknown action '{action}'\nUse: add, list, remove, reset")

@commands.command(name='history')
async def history_command(ctx, camera_id: str = None, limit: int = 10):
    """View detection history from database

    Usage:
        !history               - Last 10 detections (all cameras)
        !history drone         - Last 10 detections (drone camera)
        !history drone 20      - Last 20 detections (drone camera)
    """
    bot = ctx.bot

    if not bot.detection_db:
        await ctx.send("❌ Detection system is not enabled")
        return

    limit = min(limit, 50)  # Cap at 50

    detections = bot.detection_db.get_recent_detections(camera_id, limit, enemies_only=True)

    if not detections:
        await ctx.send("📊 No detection history found")
        return

    embed = discord.Embed(
        title="📊 Detection History",
        description=f"Last {len(detections)} enemy detections",
        color=discord.Color.orange()
    )

    lines = []
    for detection in detections[:20]:  # Show max 20 in embed
        time_str = detection['timestamp'].strftime("%H:%M:%S")
        triggered = f" → {detection['triggered_switch']}" if detection['triggered_switch'] else ""
        lines.append(
            f"`{time_str}` **{detection['camera_id']}** - "
            f"{detection['player_name']} @ {detection['distance']:.1f}m{triggered}"
        )

    embed.description += "\n\n" + "\n".join(lines)

    # Add stats
    stats = bot.detection_db.get_stats(camera_id)
    embed.add_field(
        name="📈 Statistics",
        value=(
            f"Total: {stats['total_detections']}\n"
            f"Enemies: {stats['enemy_detections']}\n"
            f"Avg Distance: {stats['avg_distance']}m\n"
            f"Range: {stats['min_distance']}-{stats['max_distance']}m"
        ),
        inline=False
    )

    await ctx.send(embed=embed)

def setup_commands(bot: EnhancedRustBot):
    """Add commands to bot"""
    bot.add_command(status_command)
    bot.add_command(switch_command)
    bot.add_command(control_camera)
    bot.add_command(detections_command)
    bot.add_command(trigger_command)
    bot.add_command(history_command)

# ========================
# Main Entry Point
# ========================

def main():
    """Main entry point"""
    import signal
    import sys
    import traceback

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

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        print("\n\n🛑 Received shutdown signal...")
        # Schedule bot close
        asyncio.run(bot.close())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run bot with error recovery
    try:
        print("\n🚀 Starting bot...\n")
        bot.run(config.get('discord_token'))
    except KeyboardInterrupt:
        print("\n\n⏹️ Bot stopped by user")
    except discord.LoginFailure:
        print("\n❌ Invalid Discord token!")
        print("Please check your config_enhanced.json file")
    except discord.PrivilegedIntentsRequired:
        print("\n❌ Missing required intents!")
        print("Enable 'Message Content Intent' in Discord Developer Portal")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nFull error details:")
        traceback.print_exc()
    finally:
        print("\n👋 Bot shutdown complete")

if __name__ == '__main__':
    main()
