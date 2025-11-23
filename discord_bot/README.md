# 🎥 Rust+ Discord Surveillance Bot

**Automatically stream Rust+ camera feeds to Discord with auto-created channels!**

Perfect for base surveillance, raid defense, and team coordination. The bot automatically creates Discord channels for each camera and streams live feeds.

![Bot Demo](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue)

---

## ✨ Features

### Automatic Channel Management
- ✅ **Auto-creates Discord category** for surveillance
- ✅ **Auto-creates channels** for each camera
- ✅ **Organizes everything** - no manual setup needed

### Live Streaming
- 📹 **Real-time camera feeds** updated every 0.5-2 seconds
- 🎯 **Entity detection** - Shows players, NPCs, and trees
- 🚨 **Player alerts** - Highlights when players detected
- 📊 **Live stats** - Player count, distance, frame count

### Camera Control
- 🎮 **Full camera control** via Discord commands
- 🔫 **Fire weapons** from turret cameras
- 👁️ **Move and look** around with drone cameras
- ⚡ **Instant response** - Control from Discord mobile

### Multi-Camera Support
- 📺 **Stream multiple cameras** simultaneously
- 🏷️ **Custom channel names** for each camera
- ⚙️ **Individual settings** per camera
- 🔄 **Easy restart** - Restart individual cameras without affecting others

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install discord.py rustplus pillow

# Or use requirements.txt
pip install -r requirements.txt
```

### Step 2: Run Setup Wizard

```bash
python setup_wizard.py
```

The wizard will ask you for:
- Discord bot token
- Rust+ server details
- Camera IDs to monitor
- Stream quality settings

**That's it!** The wizard creates `config.json` automatically.

### Step 3: Invite Bot to Discord

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application → OAuth2 → URL Generator
3. Select scopes: **bot**
4. Select permissions:
   - ✓ Manage Channels
   - ✓ Send Messages
   - ✓ Embed Links
   - ✓ Attach Files
5. Copy the URL and open it to invite your bot

### Step 4: Start the Bot

```bash
python rustplus_bot.py
```

**Done!** The bot will:
1. Connect to your Rust+ server
2. Create surveillance category in Discord
3. Create channel for each camera
4. Start streaming automatically!

---

## 📖 Usage

### Bot Commands

#### `!status`
Show bot status and camera information

```
!status
```

**Output:**
```
🤖 Rust+ Surveillance Bot Status
─────────────────────────────────
Rust+ Server: 🟢 Connected
Active Cameras: 3/3
Total Frames: 1,247

📹 Cameras:
🟢 drone - 432 frames
🟢 base-front - 408 frames
🟢 base-back - 407 frames
```

#### `!control <camera> <action>`
Control a camera

```
!control drone forward
!control drone up
!control base-front fire
```

**Available actions:**
- `forward`, `backward`, `left`, `right` - Move camera
- `up`, `down`, `lookleft`, `lookright` - Look around
- `fire` - Fire weapon (turrets only)
- `jump`, `duck` - Special movements

#### `!restart <camera>` (Admin Only)
Restart a camera if it's stuck

```
!restart drone
```

---

## ⚙️ Configuration

### Config File Structure

The `config.json` file (created by setup wizard) looks like this:

```json
{
    "discord_token": "YOUR_BOT_TOKEN",
    "command_prefix": "!",
    "category_name": "🎥 SURVEILLANCE",
    "rust_server": {
        "ip": "123.45.67.89",
        "port": "28082",
        "steam_id": "76561198012345678",
        "player_token": "1234567890"
    },
    "cameras": {
        "drone": {
            "channel_name": "📹-drone",
            "description": "Drone camera feed",
            "auto_start": true
        },
        "base-front": {
            "channel_name": "📹-front-door",
            "description": "Front entrance",
            "auto_start": true
        }
    },
    "stream_settings": {
        "stream_fps": 2,
        "render_entities": true,
        "entity_render_distance": 100
    }
}
```

### Configuration Options

#### Discord Settings
- `discord_token` - Your Discord bot token
- `command_prefix` - Command prefix (default: `!`)
- `category_name` - Name of surveillance category

#### Rust+ Server
- `ip` - Server IP address
- `port` - Server port (usually `28082`)
- `steam_id` - Your Steam ID (17 digits)
- `player_token` - Your player token from FCM

#### Camera Settings (per camera)
- `channel_name` - Discord channel name
- `description` - Channel description
- `auto_start` - Auto-start on bot launch (true/false)

#### Stream Settings (applies to all cameras)
- `stream_fps` - Frames per second (1-5 recommended)
- `render_entities` - Show players/objects (true/false)
- `entity_render_distance` - Distance in meters to render entities

---

## 📹 How to Find Camera IDs

### Drone
- Deploy a drone in Rust
- Camera ID is: `drone`

### CCTV Cameras
When you deploy a CCTV camera, it gets an ID like:
- `static1` - First CCTV you deployed
- `static2` - Second CCTV
- `static3` - And so on...

### Station Cameras
Some monuments have controllable cameras:
- Check in-game camera list
- Use the camera identifier shown

### Finding IDs
1. Open Rust+ companion app
2. Go to camera section
3. The ID is shown for each camera

---

## 🎯 Example Use Cases

### 1. Base Defense

**Setup:**
```json
"cameras": {
    "front-gate": {"channel_name": "📹-gate", "auto_start": true},
    "roof-turret": {"channel_name": "📹-roof", "auto_start": true},
    "loot-room": {"channel_name": "📹-loot", "auto_start": true}
}
```

**Result:** 3 channels showing all base entrances

### 2. Drone Surveillance

**Setup:**
```json
"cameras": {
    "drone": {
        "channel_name": "📹-drone-patrol",
        "auto_start": true
    }
}
```

**Usage:**
```
!control drone forward  # Scout ahead
!control drone up       # Look around
```

### 3. Raid Monitoring

**Setup:**
```json
"stream_settings": {
    "stream_fps": 3,
    "render_entities": true,
    "entity_render_distance": 200
}
```

Higher FPS + longer distance = better raid detection

---

## 🔒 Security & Privacy

### Protect Your Tokens
- ❌ **Never commit `config.json` to GitHub**
- ❌ **Don't share your Discord bot token**
- ❌ **Keep player token private**

Add to `.gitignore`:
```
config.json
config.json.backup
*.log
```

### Discord Permissions
The bot only needs these permissions:
- Manage Channels (to create surveillance channels)
- Send Messages
- Embed Links
- Attach Files

### Rust+ Limitations
- Only **one bot per player** can connect
- Bot uses **your Rust+ credentials**
- You can't be in-game while bot runs (same player limit)

---

## 🐛 Troubleshooting

### Bot Won't Start

**Problem:** `Configuration file not found`

**Solution:**
```bash
python setup_wizard.py
```

---

**Problem:** `Invalid Discord token`

**Solution:**
1. Check `config.json` - ensure token is correct
2. Get new token from Discord Developer Portal
3. Make sure "Message Content Intent" is enabled

---

### Can't Connect to Rust+

**Problem:** `Failed to connect to Rust+ server`

**Solution:**
1. Verify server IP and port in `config.json`
2. Make sure you're connected to the Rust server in-game
3. Get fresh player token (they expire when you leave server)
4. Check you're not already connected with another Rust+ app

---

### Camera Not Found

**Problem:** `Failed to subscribe to camera: error`

**Solution:**
1. Verify camera ID is correct
2. Make sure camera exists in-game
3. Check you have permission to view the camera
4. Ensure camera isn't already being viewed by another app

---

### No Channels Created

**Problem:** Bot connects but doesn't create channels

**Solution:**
1. Check bot has "Manage Channels" permission
2. Invite bot with proper permissions (see Quick Start)
3. Try `!restart <camera>` command

---

### Stream Is Laggy/Slow

**Problem:** Images update slowly

**Solution:**
1. Lower FPS in config: `"stream_fps": 1`
2. Disable entities: `"render_entities": false`
3. Reduce entity distance: `"entity_render_distance": 50`
4. Check your network connection

---

### Discord Rate Limiting

**Problem:** Bot stops updating images

**Solution:**
- Discord limits ~5 messages/second per channel
- Lower FPS to 2 or less
- Bot will automatically slow down when rate limited

---

## 📊 Performance Tips

### Low Bandwidth
```json
"stream_settings": {
    "stream_fps": 1,
    "render_entities": false
}
```

### Balanced (Recommended)
```json
"stream_settings": {
    "stream_fps": 2,
    "render_entities": true,
    "entity_render_distance": 100
}
```

### High Quality
```json
"stream_settings": {
    "stream_fps": 3,
    "render_entities": true,
    "entity_render_distance": 200
}
```

---

## 🔄 Updating the Bot

### Update Code
```bash
git pull origin discord-bot-integration
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Update Configuration
- Your `config.json` is preserved
- Run `python setup_wizard.py` to reconfigure

---

## 📚 Additional Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup instructions
- **[CONFIGURATION.md](CONFIGURATION.md)** - Advanced configuration
- **[COMMANDS.md](COMMANDS.md)** - Complete command reference
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🤝 Contributing

Found a bug? Have a feature request?

1. Open an issue on GitHub
2. Describe the problem/feature
3. Include your config (remove sensitive data!)

---

## 📝 License

This bot is built on top of the [rustplus](https://github.com/olijeffers0n/rustplus) library.

MIT License - Use freely!

---

## 💬 Support

- **Discord:** Join the Rust+ Discord at https://discord.gg/nQqJe8qvP8
- **Issues:** Report bugs on GitHub
- **Documentation:** Check the `/docs` folder

---

## ⭐ Features Roadmap

- [ ] Web dashboard integration
- [ ] Motion detection alerts
- [ ] Recording/playback
- [ ] Multiple Discord servers
- [ ] Reaction-based camera controls
- [ ] Auto-turret AI targeting

---

**Happy Surveillance!** 🎥

Made with ❤️ by the Rust+ community
