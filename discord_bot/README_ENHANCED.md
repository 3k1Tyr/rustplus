# 🚀 Enhanced Rust+ Discord Bot

**All-in-one surveillance, control, and communication system for Rust+**

NEW in Enhanced Version:
- ✅ **Single Channel** for ALL cameras (grid view - no spam!)
- ✅ **Smart Switch Control** panel
- ✅ **Team Chat Bridge** (Discord ↔ Rust bidirectional)
- ✅ **Event Notifications** (explosions, deaths, etc.)
- ✅ **Drone Control Script** included

---

## 🎯 Key Improvements Over Basic Bot

| Feature | Basic Bot | Enhanced Bot |
|---------|-----------|--------------|
| **Camera Channels** | One per camera (spam!) | **Single grid view** ✨ |
| **Smart Switches** | ❌ Not supported | **✅ Full control panel** |
| **Team Chat** | ❌ No integration | **✅ Bidirectional bridge** |
| **Events** | ❌ No notifications | **✅ Real-time alerts** |
| **Drone Control** | ❌ Manual only | **✅ Automated patrols** |

---

## 📺 Single-Channel Camera Grid

**Problem:** Multiple camera channels spam your Discord server

**Solution:** All cameras in ONE channel with a beautiful grid layout!

### How It Works

Instead of this:
```
❌ Old Way (Basic Bot):
└── 🎥 SURVEILLANCE
    ├── #📹-drone          [separate channel]
    ├── #📹-front-door     [separate channel]
    ├── #📹-loot-room      [separate channel]
    └── #📹-back-door      [separate channel]
```

You get this:
```
✅ Enhanced Bot:
└── 🎥 RUST+ CONTROL
    ├── #📹-surveillance   [ALL cameras in grid view!]
    ├── #⚡-switches       [switch control panel]
    ├── #💬-team-chat      [Discord ↔ Rust chat]
    └── #🚨-events         [event notifications]
```

### Grid View Example

The `#📹-surveillance` channel shows ALL cameras in a 2x2 grid:

```
┌─────────────┬─────────────┐
│  📹 DRONE   │ 📹 FRONT    │
│  🟢 Clear   │ 🔴 2 players│
│             │             │
├─────────────┼─────────────┤
│ 📹 LOOT RM  │ 📹 BACK     │
│ 🟢 Clear    │ 🟢 Clear    │
│             │             │
└─────────────┴─────────────┘
```

**Benefits:**
- No channel spam
- See all cameras at once
- Easier to monitor
- Better for mobile viewing

---

## ⚡ Smart Switch Control Panel

Control your base switches directly from Discord!

### Features

- **Visual Control Panel** - See all switch states at once
- **Quick Toggle** - `!switch lights on`
- **Real-time Updates** - Status updates automatically
- **Entity Subscription** - Gets notified when switches change

### Example

In `#⚡-switches` channel:

```
⚡ Smart Switch Control
──────────────────────────────────────

💡 Main Lights        ⚫ Turrets
🟢 ON                 🔴 OFF
ID: 12345             ID: 12346

💡 Backup Generator   ⚫ Trap Door
🟢 ON                 🔴 OFF
ID: 12347             ID: 12348

Use: !switch <name> <on/off>
```

### Usage

```bash
# Turn on turrets
!switch turrets on

# Turn off lights
!switch lights off

# Check status
!status
```

### Setup

1. Pair switches in Rust+ app
2. Note the entity IDs
3. Add to config during setup wizard:
   ```
   Switch name: lights
   Entity ID: 12345
   ```

---

## 💬 Team Chat Bridge

**Bidirectional** chat between Discord and Rust!

### How It Works

Messages flow both ways:

```
Discord → Rust:
[#team-chat] PlayerName: "Enemy at north!"
    ↓
[Rust Team Chat] [Discord - PlayerName] Enemy at north!
```

```
Rust → Discord:
[Rust Team Chat] ClanMember: "On my way"
    ↓
[#team-chat] 💬 ClanMember (Rust): "On my way"
```

### Features

- **Auto-formatting** - Messages clearly labeled with source
- **Real-time sync** - Instant message delivery
- **Two-way** - Team members without Discord can read Discord messages
- **Smart filtering** - Bot doesn't echo its own messages

### Usage

Just type in `#team-chat` channel - messages automatically go to Rust team chat!

**Example:**
```
Discord User: "Raid incoming from north!"
→ Appears in Rust as: [Discord - Username] Raid incoming from north!
```

---

## 🚨 Event Notifications

Get notified instantly when important events happen!

### Supported Events

- 💥 **Explosions** - Raid alerts with location
- ☠️ **Player Deaths** - Team member deaths
- 🔧 **Entity Destroyed** - Turret/TC destroyed
- 🚪 **Door Opens** (if monitored)
- 📦 **Loot Detected** (via smart alarms)

### Example Notifications

```
🚨 #events

💥 EXPLOSION DETECTED
Location: North Wall
Time: 2 seconds ago
@everyone
──────────────────────

☠️ Team Member Death
PlayerName has died
Time: 5 seconds ago
──────────────────────

🔧 Entity Destroyed
Auto Turret has been destroyed
Time: 10 seconds ago
──────────────────────
```

### Configuration

Enable/disable in setup wizard:
```
Enable event notifications? [Y/n]: y
```

---

## 🚁 Drone Control Script

**NEW:** Automated drone surveillance!

### Features

- **Automated Patrols** - Predefined routes
- **Waypoint System** - Set patrol paths
- **Screenshot Capture** - Auto-screenshot at waypoints
- **360° Scanning** - Area surveillance
- **Interactive Mode** - Manual keyboard control
- **Player Detection** - Alert when players spotted

### Predefined Patrols

#### 1. Base Perimeter
Circles around your base, taking screenshots at each wall.

#### 2. High Altitude Scan
Ascends, scans all directions, descends.

#### 3. Quick Recon
Quick forward scout and return.

### Usage

```bash
# Run standalone
python drone_control.py

# Choose mode:
1. Automated Patrol (Base Perimeter)
2. High Altitude Scan
3. Quick Recon
4. Interactive Control
5. Custom Patrol
```

### Interactive Control

```
🎮 Interactive Drone Control

Commands:
  w - Move forward
  s - Move backward
  a - Strafe left
  d - Strafe right
  space - Move up
  shift - Move down
  q - Look left
  e - Look right
  p - Take screenshot
  scan - 360° scan
  quit - Exit
```

### Custom Patrols

```python
from drone_control import DroneController, PatrolRoute, Waypoint

# Define custom route
my_patrol = PatrolRoute(
    name="Custom Route",
    waypoints=[
        Waypoint("Start", forward_duration=3.0, up_duration=1.0, hover_duration=2.0),
        Waypoint("Mid", forward_duration=5.0, up_duration=0, hover_duration=3.0),
        Waypoint("End", forward_duration=3.0, up_duration=-1.0, hover_duration=2.0),
    ],
    loop=True  # Repeat indefinitely
)

# Execute
await drone.execute_patrol(my_patrol)
```

### Integration with Discord Bot

```python
# In Discord
!control drone forward 3.0
!control drone scan

# Drone moves forward for 3 seconds, then does 360° scan
```

---

## 🚀 Quick Start

### 1. Install

```bash
cd discord_bot
pip install -r requirements.txt
```

### 2. Configure

```bash
python setup_wizard_enhanced.py
```

Answer the prompts:
- Discord bot token
- Rust+ server details
- Camera IDs (drone, static1, etc.)
- Smart switch names and entity IDs
- Enable features (team chat, events)

### 3. Invite Bot

Generate invite URL from Discord Developer Portal with permissions:
- Manage Channels
- Send Messages
- Embed Links
- Attach Files

### 4. Start Bot

```bash
python enhanced_bot.py
```

Bot will:
1. ✅ Create 4 channels
2. ✅ Connect all cameras to grid
3. ✅ Setup switch control panel
4. ✅ Start team chat bridge
5. ✅ Enable event notifications

### 5. Try Drone Control

```bash
python drone_control.py
```

---

## ⚙️ Configuration

### config_enhanced.json Structure

```json
{
    "discord_token": "YOUR_BOT_TOKEN",
    "command_prefix": "!",
    "category_name": "🎥 RUST+ CONTROL",
    "rust_server": {
        "ip": "123.45.67.89",
        "port": "28082",
        "steam_id": "76561198012345678",
        "player_token": "your_token"
    },
    "cameras": {
        "drone": {"enabled": true},
        "static1": {"enabled": true},
        "static2": {"enabled": true}
    },
    "switches": {
        "lights": 12345,
        "turrets": 12346,
        "generator": 12347
    },
    "stream_settings": {
        "stream_fps": 2,
        "render_entities": true,
        "entity_render_distance": 100
    },
    "features": {
        "team_chat_enabled": true,
        "event_notifications_enabled": true
    }
}
```

---

## 🎮 Commands

### Bot Commands

```bash
# Status
!status
  Shows bot status, cameras, switches

# Camera Control
!control <camera> <action>
  !control drone forward
  !control drone up
  !control drone fire

# Switch Control
!switch <name> <on/off>
  !switch lights on
  !switch turrets off

# Restart (Admin only)
!restart <camera>
  !restart drone
```

### Drone Control Commands

See `drone_control.py` for full drone automation.

---

## 📊 Channel Overview

### #📹-surveillance
- **All cameras in grid view**
- Updates every 0.5-2 seconds
- Shows player count per camera
- Highlights cameras with activity

### #⚡-switches
- **Switch control panel**
- Real-time switch states
- Quick toggle commands
- Entity ID reference

### #💬-team-chat
- **Bidirectional chat bridge**
- Discord messages → Rust team chat
- Rust team chat → Discord
- Labeled with source

### #🚨-events
- **Real-time event notifications**
- Explosion alerts (@everyone)
- Death notifications
- Entity destruction alerts

---

## 🎯 Use Cases

### 1. Base Defense
```
📹 Monitor all entrances in grid view
⚡ Control turrets and lights remotely
🚨 Get instant raid alerts
💬 Coordinate with team in real-time
```

### 2. Raid Preparation
```
🚁 Drone scout target base
📸 Auto-screenshot all angles
💬 Plan attack in team chat
⚡ Pre-position switches
```

### 3. Resource Protection
```
📹 Monitor TC and loot rooms
🚨 Alert on door/TC destruction
⚡ Lockdown with automated switches
💬 Call for backup via team chat
```

---

## 🔧 Advanced Features

### Custom Grid Layouts

Edit `enhanced_bot.py` to change grid size:
```python
# In _create_grid_image()
cols = 3  # Change from 2 to 3 columns
```

### Add Custom Events

```python
# In enhanced_bot.py
async def notify_custom_event(self, message: str):
    embed = discord.Embed(
        title="🎯 Custom Event",
        description=message,
        color=discord.Color.purple()
    )
    await self.events_channel.send(embed=embed)
```

### Drone Patrol Integration

Import drone control in Discord bot:
```python
from drone_control import DroneController

# In bot command
@commands.command()
async def patrol(ctx, route_name: str):
    # Execute automated patrol
    await drone.execute_patrol(ROUTES[route_name])
```

---

## 🐛 Troubleshooting

### Grid Not Updating
- Check camera connections: `!status`
- Verify FPS setting (not too high)
- Check console for errors

### Switches Not Working
- Verify entity IDs are correct
- Check subscription status
- Ensure switch is paired in Rust+ app

### Team Chat Not Bridging
- Check teamchat_channel is set
- Verify bot has send permissions
- Check Rust+ connection

### Events Not Firing
- Enable in config: `event_notifications_enabled: true`
- Check events_channel exists
- Verify Rust+ event handlers registered

---

## 📚 Documentation

- **README.md** - Basic bot documentation
- **README_ENHANCED.md** - This file (enhanced features)
- **SETUP_GUIDE.md** - Detailed setup instructions
- **drone_control.py** - Drone automation API docs

---

## 🤝 Contributing

Ideas for future enhancements:
- [ ] Motion detection AI
- [ ] Voice alerts (Discord voice channel)
- [ ] Web dashboard integration
- [ ] Multi-server support
- [ ] Auto-turret targeting
- [ ] Raid replay/recording

---

## 📝 License

MIT License - Use freely!

---

## 💬 Support

- **Discord:** https://discord.gg/nQqJe8qvP8
- **Issues:** GitHub Issues
- **Docs:** Check `/docs` folder

---

**Happy Surveillance!** 🎥

Made with ❤️ by the Rust+ community
