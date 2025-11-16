# Discord Surveillance Bot for Rust+

Stream live camera feeds from Rust+ to Discord with full camera control.

## 📋 Features

- ✅ **Live camera streaming** to Discord channels (images updated every 0.5-2 seconds)
- ✅ **Camera control** via Discord commands (movement, looking, firing)
- ✅ **Multiple cameras** - Stream multiple cameras to different channels
- ✅ **Entity detection** - Shows players and trees in view
- ✅ **Auto-resubscription** - Handles Rust+ 15-second timeout automatically
- ✅ **Multi-viewer** - Multiple Discord users can watch the same stream

## 🎯 Use Cases

1. **Base Security** - Monitor your base from Discord while away
2. **Raid Defense** - Watch for raiders and control turrets
3. **Team Coordination** - Share camera view with your team
4. **Reconnaissance** - Scout areas with drones remotely
5. **Turret Control** - Control auto-turrets via camera

## 📦 Installation

### 1. Install Dependencies

```bash
pip install discord.py rustplus
```

### 2. Get Discord Bot Token

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Go to "Bot" section
4. Click "Add Bot"
5. **IMPORTANT**: Enable "Message Content Intent" under "Privileged Gateway Intents"
6. Copy the bot token

### 3. Get Rust+ Credentials

You need your Rust+ server details:
- **Server IP & Port** - Get from Rust+ companion app
- **Steam ID** - Your 17-digit Steam ID
- **Player Token** - Get from FCM notifications (see [rustplus docs](https://github.com/olijeffers0n/rustplus))

### 4. Configure the Bot

Edit `discord_camera_bot.py` and fill in:

```python
DISCORD_TOKEN = "your_discord_bot_token"
RUST_SERVER_IP = "your.server.ip"
RUST_SERVER_PORT = "28082"
RUST_STEAM_ID = "your_steam_id"
RUST_PLAYER_TOKEN = "your_player_token"
```

### 5. Invite Bot to Your Server

1. Go to OAuth2 → URL Generator in Discord Developer Portal
2. Select scopes: `bot`
3. Select permissions: `Send Messages`, `Embed Links`, `Attach Files`
4. Copy the URL and open it to invite bot to your server

## 🚀 Usage

### Start the Bot

```bash
python discord_camera_bot.py
```

### Discord Commands

#### Start Camera Stream

```
!camera start <camera_id> [#channel]
```

Examples:
```
!camera start drone                    # Stream drone to current channel
!camera start drone #surveillance      # Stream drone to #surveillance
!camera start static1 #base-cam       # Stream CCTV to #base-cam
```

**Common Camera IDs:**
- `drone` - Your deployed drone
- `static1`, `static2` - Your CCTV cameras
- Station cameras (find ID in-game)

#### Stop Stream

```
!camera stop <camera_id>
```

#### Control Camera

```
!camera move <direction>
```

Directions: `forward`, `backward`, `left`, `right`, `jump`, `duck`, `sprint`

```
!camera look <direction>
```

Directions: `up`, `down`, `left`, `right`

#### Fire Weapon

```
!fire
```

Fires the camera's weapon (if it has one, like auto-turret)

#### List Active Streams

```
!camera list
```

#### View Entities

```
!entities [camera_id]
```

Shows list of players and objects detected in camera view

## 📸 Example Usage Session

```
# Start surveillance of your base
!camera start drone #surveillance

# Camera is now streaming to #surveillance channel
# Image updates every 0.5 seconds showing live feed

# Move the camera to look around
!camera look left
!camera move forward

# Check what's visible
!entities drone
# Shows: "PlayerName (distance: 45.2m)"

# Shoot at raiders!
!fire

# Stop when done
!camera stop drone
```

## 🎮 Advanced: Multiple Cameras

You can run **multiple cameras simultaneously** to different channels:

```
!camera start drone #surveillance-drone
!camera start static1 #surveillance-front
!camera start static2 #surveillance-back
```

Now you have 3 camera feeds in 3 different Discord channels!

## 🌐 Multi-Viewer Support (Your Question!)

### Can Multiple Players View the Same Camera?

**Answer: YES, with this Discord bot!**

Here's how it works:

### The Rust+ Limitation

Rust+ has a **server-side limitation**: Only **ONE client** can subscribe to a camera at a time.

- ❌ Player A subscribes to "drone" → Player B tries to subscribe → Player A gets disconnected
- ❌ Two Rust+ apps cannot view the same camera simultaneously

### The Discord Bot Solution

The Discord bot acts as a **single Rust+ client** but **broadcasts to multiple Discord users**:

```
Rust+ Server (Camera)
       ↓
   [One subscription]
       ↓
   Discord Bot
       ↓
   [Multicasts to Discord]
       ↓
  ┌────┴────┬────────┬────────┐
  ↓         ↓        ↓        ↓
User A   User B   User C   User D
```

**Benefits:**
- ✅ Entire Discord server can watch the same camera feed
- ✅ Only the bot needs Rust+ credentials
- ✅ Team members without Rust+ app can still watch
- ✅ No one gets kicked off the camera

**Limitations:**
- The bot uses YOUR Rust+ credentials (your camera access)
- Only you (the bot owner) can be "in-game" while bot runs
- Controls affect all viewers (anyone can send `!camera move forward`)

### Multi-Camera vs Multi-Viewer

My earlier improvement suggestion was about **multi-camera** (different issue):

| Feature | What It Does | Current Support |
|---------|--------------|-----------------|
| **Multi-Camera** | ONE player watches MULTIPLE cameras (drone + CCTV1 + CCTV2) | ⚠️ Requires code changes (my suggestion) |
| **Multi-Viewer** | MULTIPLE players watch ONE camera | ✅ Works now with Discord bot! |

**Current bot**: Supports multi-viewer (many Discord users watching)

**With my improvements**: Would also support multi-camera (bot watches drone + CCTV1 + CCTV2 simultaneously)

## 🔒 Security Considerations

### Who Can Control Cameras?

By default, **anyone in your Discord server** can send commands to control cameras.

To restrict access, add role checks:

```python
@bot.command(name='camera')
@commands.has_role("Rust Admin")  # Only users with "Rust Admin" role
async def camera_command(ctx, action: str, *args):
    # ... existing code ...
```

Or restrict to specific users:

```python
ALLOWED_USERS = [123456789012345678, 987654321098765432]  # Discord user IDs

@bot.command(name='camera')
async def camera_command(ctx, action: str, *args):
    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("❌ You don't have permission")
        return
    # ... existing code ...
```

### Protecting Your Rust+ Credentials

- Never commit your token to GitHub
- Use environment variables:

```python
import os
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
RUST_PLAYER_TOKEN = os.getenv('RUST_PLAYER_TOKEN')
```

Run with:
```bash
export DISCORD_TOKEN="your_token"
export RUST_PLAYER_TOKEN="your_token"
python discord_camera_bot.py
```

## 🐛 Troubleshooting

### "Not connected to Rust+ server"

- Check your server IP, port, Steam ID, and player token
- Make sure you're connected to the Rust server in-game
- Token expires if you leave the server - get a new one

### "Failed to connect to camera"

- Camera ID might be wrong - check in-game
- You might not have permission to view that camera
- Camera might already be in use by another Rust+ client

### Discord Rate Limits

Discord limits ~5 image updates per second per channel.

If you get rate limited:
- Reduce `STREAM_FPS` in config (recommended: 2 FPS)
- The bot automatically handles rate limits with backoff

### Bot Lag / Slow Updates

- Reduce entities rendered: `ENTITY_RENDER_DISTANCE = 50`
- Lower FPS: `STREAM_FPS = 1`
- Check your network connection to Rust server

## 🎨 Customization Ideas

### 1. Motion Detection Alerts

```python
@camera_manager.on_frame_received
async def detect_motion(frame):
    entities = await camera_manager.get_entities_in_frame()
    players = [e for e in entities if e.type == 2]

    if players:
        # Alert the Discord channel!
        await alert_channel.send(f"🚨 {len(players)} players detected!")
```

### 2. Recording

Add video recording when players detected:

```python
import cv2

if players_detected:
    start_recording("raid_detected.mp4")
```

### 3. Multiple Discord Servers

Run the bot on multiple Discord servers to share your camera with different teams.

### 4. Web Dashboard

Use Flask/FastAPI to create a web dashboard showing all cameras in a grid.

## 📚 Resources

- [Rust+ API Docs](https://github.com/olijeffers0n/rustplus)
- [Discord.py Docs](https://discordpy.readthedocs.io/)
- [Getting Player Token](https://github.com/liamcottle/rustplus.js#get-server-id-and-player-token)

## 💡 Tips

- **Use dedicated Discord channel** for camera feeds (they update frequently)
- **Set low FPS** (1-2) for surveillance to save bandwidth
- **Create multiple bots** if you have multiple Rust accounts (to watch more cameras)
- **Use voice chat** to coordinate while watching camera feeds
- **Pin important frames** in Discord for later review

## 🤝 Contributing

This is an example implementation. Feel free to:
- Add reaction controls (click 👈 to look left)
- Implement slash commands instead of `!` prefix
- Add database to store favorite camera positions
- Create web streaming alternative

## ⚖️ License

This example is provided as-is. Use responsibly and follow Discord's and Rust's Terms of Service.

---

**Questions?** Open an issue or ask in the Rust+ Discord: https://discord.gg/nQqJe8qvP8
