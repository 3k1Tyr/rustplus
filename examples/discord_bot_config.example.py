"""
Configuration file for Discord Camera Bot

Copy this to discord_bot_config.py and fill in your details
"""

# ========================
# Discord Bot Settings
# ========================

# Get this from https://discord.com/developers/applications
# 1. Create New Application
# 2. Go to Bot section
# 3. Enable "Message Content Intent"
# 4. Copy token
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# ========================
# Rust+ Server Settings
# ========================

# Get these from your Rust+ companion app or FCM listener
# See: https://github.com/olijeffers0n/rustplus

RUST_SERVER_IP = "your.server.ip.here"     # Server IP address
RUST_SERVER_PORT = "28082"                  # Default Rust+ port
RUST_STEAM_ID = "76561198012345678"        # Your Steam ID (17 digits)
RUST_PLAYER_TOKEN = "1234567890"           # Your player token (from FCM)

# ========================
# Stream Settings
# ========================

# Discord has rate limits (~5 messages/second per channel)
# Recommended: 1-3 FPS for surveillance, avoid Discord rate limits
STREAM_FPS = 2

# Auto-resubscribe interval (seconds)
# Camera subscriptions expire after ~15 seconds
RESUBSCRIBE_INTERVAL = 10

# Entity render settings
RENDER_ENTITIES = True
ENTITY_RENDER_DISTANCE = 100  # meters
MAX_ENTITIES = 50

# ========================
# Camera IDs
# ========================

# Common camera IDs in Rust:
# - "drone" - Your deployed drone
# - "static1", "static2", etc. - Static CCTV cameras you deployed
# - Station camera IDs (find these in-game)

# You can define preset cameras here
PRESET_CAMERAS = {
    "drone": "My surveillance drone",
    "base1": "Main entrance CCTV",
    "base2": "Back door CCTV",
}
