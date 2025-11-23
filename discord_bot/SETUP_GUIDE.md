# 📖 Complete Setup Guide

**Step-by-step guide for first-time users**

This guide walks you through every step, from creating a Discord bot to streaming your first camera. No programming experience needed!

---

## 📋 Prerequisites

### What You Need

- ✅ Python 3.8 or higher installed
- ✅ Discord account
- ✅ Rust+ companion app access
- ✅ Active connection to a Rust server
- ✅ At least one camera deployed (drone or CCTV)

### Check Python Installation

```bash
python --version
# Should show: Python 3.8.0 or higher
```

If not installed, download from [python.org](https://www.python.org/downloads/)

---

## 🤖 Part 1: Create Discord Bot

### Step 1: Create Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Enter a name (e.g., "Rust+ Surveillance")
4. Click **"Create"**

### Step 2: Create Bot User

1. In your application, go to **"Bot"** section (left sidebar)
2. Click **"Add Bot"**
3. Confirm by clicking **"Yes, do it!"**
4. You now have a bot! 🎉

### Step 3: Configure Bot

1. **Scroll down to "Privileged Gateway Intents"**
2. **Enable these intents:**
   - ✅ **Message Content Intent** (VERY IMPORTANT!)
   - ✅ Server Members Intent (optional)
3. Click **"Save Changes"**

### Step 4: Get Bot Token

1. In the Bot section, find **"TOKEN"**
2. Click **"Reset Token"** (or "Copy" if visible)
3. Click **"Copy"** to copy your token
4. **⚠️ KEEP THIS SECRET!** Don't share it with anyone!

---

## 🔑 Part 2: Get Rust+ Credentials

### Find Server IP & Port

**Method 1: From Rust+ App**
1. Open Rust+ companion app
2. Connect to your server
3. Server IP and port are shown in app

**Method 2: From In-Game**
1. Press F1 in Rust
2. Type: `client.connect <IP>:<PORT>`
3. Note the IP and port

### Find Your Steam ID

**Method 1: Steam Profile URL**
1. Go to your Steam profile
2. If URL is `steamcommunity.com/profiles/76561198012345678`
3. The number is your Steam ID

**Method 2: SteamID Finder**
1. Go to [steamidfinder.com](https://www.steamidfinder.com/)
2. Enter your Steam profile URL
3. Copy the "steamID64"

### Get Player Token

**Method 1: FCM Listener (Recommended)**

1. Install rustPlusPushReceiver:
   ```bash
   pip install rustPlusPushReceiver
   ```

2. Run FCM listener:
   ```bash
   python -m rustPlusPushReceiver
   ```

3. Connect to server in Rust+
4. Token will be printed in console

**Method 2: Rust+ Documentation**

See the [rustplus documentation](https://github.com/olijeffers0n/rustplus#getting-started) for alternative methods.

---

## 🛠️ Part 3: Install Bot

### Step 1: Download Bot Files

```bash
# Clone the repository
git clone https://github.com/YOUR_REPO/rustplus.git
cd rustplus/discord_bot

# Or download the discord_bot folder directly
```

### Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# This installs:
# - discord.py (Discord bot library)
# - rustplus (Rust+ API wrapper)
# - Pillow (Image processing)
```

### Step 3: Run Setup Wizard

```bash
python setup_wizard.py
```

The wizard will ask you for:

#### Discord Configuration
- **Bot Token:** Paste the token from Part 1
- **Command Prefix:** Enter `!` (or customize)
- **Category Name:** Enter `🎥 SURVEILLANCE` (or customize)

#### Rust+ Server
- **Server IP:** From Part 2
- **Server Port:** Usually `28082`
- **Steam ID:** Your 17-digit Steam ID
- **Player Token:** From Part 2

#### Cameras
For each camera:
- **Camera ID:** e.g., `drone`, `static1`
- **Channel Name:** e.g., `📹-drone`
- **Description:** e.g., "Drone patrol camera"
- **Auto-start:** Yes (recommended)

#### Stream Settings
- **FPS:** `2` (recommended for surveillance)
- **Render Entities:** Yes
- **Entity Distance:** `100` meters

### Step 4: Verify Configuration

After wizard completes, check `config.json`:

```bash
cat config.json
```

Should look like:
```json
{
    "discord_token": "YOUR_TOKEN",
    "rust_server": {
        "ip": "123.45.67.89",
        ...
    },
    "cameras": {
        "drone": { ... }
    }
}
```

---

## 🚀 Part 4: Invite Bot to Discord

### Step 1: Generate Invite URL

1. Go back to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to **"OAuth2"** → **"URL Generator"**

### Step 2: Select Scopes

Under **"Scopes"**, select:
- ✅ **bot**

### Step 3: Select Permissions

Under **"Bot Permissions"**, select:
- ✅ **Manage Channels** (to create surveillance channels)
- ✅ **Send Messages**
- ✅ **Embed Links**
- ✅ **Attach Files**
- ✅ **Read Message History** (optional)
- ✅ **Add Reactions** (optional)

### Step 4: Copy URL and Invite

1. Copy the **"Generated URL"** at the bottom
2. Open the URL in your browser
3. Select your Discord server
4. Click **"Authorize"**
5. Complete the CAPTCHA

Your bot should now appear in your server! (Offline until you start it)

---

## ▶️ Part 5: Start the Bot

### Start Bot

```bash
python rustplus_bot.py
```

### What Should Happen

You should see:
```
============================================================
Rust+ Discord Surveillance Bot
============================================================
✅ Configuration loaded

🚀 Starting bot...

✅ Bot logged in as YourBot#1234
📊 Connected to 1 server(s)
============================================================

🔌 Connecting to Rust+ server...
✅ Connected to Rust+ server: 123.45.67.89:28082

🏗️ Setting up surveillance channels in 'Your Server'...
📁 Creating category: 🎥 SURVEILLANCE
✅ Created category: 🎥 SURVEILLANCE
📺 Creating channel: 📹-drone
✅ Created channel: #📹-drone

✅ Surveillance system ready with 1 cameras!

📹 Starting 1 camera stream(s)...
📡 Subscribing to camera: drone
✅ Camera drone streaming to #📹-drone
```

### Check Discord

1. Go to your Discord server
2. You should see a new category: **🎥 SURVEILLANCE**
3. Under it, channels for each camera
4. Camera feeds should start appearing!

---

## ✅ Part 6: Test the Bot

### Check Status

In any Discord channel, type:
```
!status
```

You should see bot status showing active cameras.

### Control Camera

Try moving the drone:
```
!control drone forward
```

Drone should move forward!

### View Stream

Go to the camera channels (e.g., `#📹-drone`)

You should see:
- Live camera image (updating every 0.5-2 seconds)
- Player count
- Entity count
- Frame count

---

## 🎯 Part 7: Customize (Optional)

### Add More Cameras

1. Deploy more cameras in Rust
2. Edit `config.json`:
   ```json
   "cameras": {
       "drone": { ... },
       "base-front": {
           "channel_name": "📹-front-door",
           "description": "Front entrance CCTV",
           "auto_start": true
       }
   }
   ```
3. Restart bot

### Change Stream Quality

Edit `config.json`:
```json
"stream_settings": {
    "stream_fps": 3,          // Higher = smoother (1-5)
    "render_entities": true,  // Show players/entities
    "entity_render_distance": 150  // Render distance
}
```

### Change Command Prefix

Edit `config.json`:
```json
"command_prefix": "?"  // Use ?status, ?control, etc.
```

---

## 🐛 Common Issues

### "Configuration file not found"

**Problem:** Bot can't find config.json

**Solution:**
```bash
# Make sure you're in the discord_bot folder
cd discord_bot
python rustplus_bot.py
```

---

### "Invalid Discord token"

**Problem:** Bot token is wrong or expired

**Solution:**
1. Go to Discord Developer Portal
2. Bot section → Reset Token
3. Update `config.json` with new token
4. Restart bot

---

### "Failed to connect to Rust+ server"

**Problem:** Can't connect to Rust server

**Solutions:**
1. **Check you're connected to server in-game**
2. **Get fresh player token** (they expire)
3. **Verify IP and port** in config.json
4. **Close other Rust+ apps** (only one connection allowed)

---

### "No permission to create category"

**Problem:** Bot lacks permissions

**Solution:**
1. Re-invite bot with proper permissions (see Part 4)
2. OR: Manually give bot "Manage Channels" role in Discord

---

### "Camera not found"

**Problem:** Camera ID is wrong

**Solution:**
1. Check camera ID in Rust+ app
2. Update `config.json` with correct ID
3. Common IDs: `drone`, `static1`, `static2`

---

### Bot Creates Channels But No Stream

**Problem:** Channels created but no images

**Solutions:**
1. **Wait 5-10 seconds** for first frame
2. **Check camera has view** (not in a wall)
3. **Try restart:** `!restart drone`
4. **Check bot console** for error messages

---

## 📱 Mobile Access

### Control from Discord Mobile

1. Open Discord app
2. Go to surveillance channels
3. See live feeds on mobile!
4. Use commands: `!control drone forward`

Works perfectly on mobile! 📱

---

## 🔄 Keeping Bot Running

### Run in Background (Linux/Mac)

```bash
# Use screen
screen -S rustbot
python rustplus_bot.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r rustbot
```

### Run as Service (Linux)

Create `/etc/systemd/system/rustbot.service`:
```ini
[Unit]
Description=Rust+ Discord Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/discord_bot
ExecStart=/usr/bin/python3 rustplus_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable rustbot
sudo systemctl start rustbot
```

### Run on VPS/Cloud

Upload bot files to a VPS and run it there 24/7!

---

## 🎓 Next Steps

### Learn More
- Read [README.md](README.md) for features
- Check [COMMANDS.md](COMMANDS.md) for all commands
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues

### Advanced Usage
- Set up motion detection alerts
- Integrate with web dashboard
- Add custom commands
- Multi-server support

### Join Community
- Discord: https://discord.gg/nQqJe8qvP8
- GitHub: Report issues and contribute

---

## ✅ Setup Complete!

Congratulations! Your Rust+ surveillance bot is now running! 🎉

You can now:
- ✅ Monitor your base from Discord
- ✅ Control cameras from mobile
- ✅ Get player alerts
- ✅ Share feeds with your team

**Happy Surveillance!** 🎥

---

## 🆘 Need Help?

**Still stuck?**

1. **Check console output** - Bot prints helpful error messages
2. **Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
3. **Join Discord** for community help
4. **Open GitHub issue** with your error message

**Include when asking for help:**
- Bot console output
- Config file (remove sensitive data!)
- What you expected vs what happened

We're here to help! 💙
