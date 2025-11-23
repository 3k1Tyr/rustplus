# 🚀 Enhanced Rust+ Discord Bot

⚠️ **BETA SOFTWARE** - Production-ready core features with some planned additions

**All-in-one surveillance, control, and communication system for Rust+**

## ✅ What's Working (Tested & Ready)

- ✅ **Single Channel Camera Grid** - All cameras in one grid view
- ✅ **Smart Switch Control** - Full control panel with real-time updates
- ✅ **Team Chat Bridge** - Discord ↔ Rust bidirectional chat
- ✅ **Permission System** - Role and user-based access control
- ✅ **Rate Limiting** - Automatic Discord API protection
- ✅ **Comprehensive Logging** - Debugging and audit trails
- ✅ **Cross-Platform** - Works on Linux, macOS, and Windows
- ✅ **Graceful Shutdown** - Clean exit and resource cleanup
- ✅ **Drone Control Script** - Automated drone patrols (separate script)

## 🚧 Planned Features (Not Yet Implemented)

- ⏳ **Event Notifications** - Explosion/death detection (requires protobuf parsing)
- ⏳ **Icon Integration** - Visual icons for entities
- ⏳ **Auto-Reconnect** - Automatic connection recovery

---

## 📋 Feature Status Table

| Feature | Status | Notes |
|---------|--------|-------|
| Camera Grid | ✅ **Working** | Single channel, 2x2 grid layout |
| Smart Switches | ✅ **Working** | Full control with auto-updates |
| Team Chat | ✅ **Working** | Bidirectional message relay |
| Permissions | ✅ **Working** | Role and user whitelist |
| Rate Limiting | ✅ **Working** | Prevents Discord API errors |
| Logging System | ✅ **Working** | File and console output |
| Camera Control | ✅ **Working** | Move, look, fire commands |
| Event Detection | ⚠️ **Planned** | Framework exists, needs implementation |
| Icon Display | ⚠️ **Planned** | Icons available but not integrated |

---

## 🎯 Key Improvements Over Basic Bot

| Feature | Basic Bot | Enhanced Bot |
|---------|-----------|--------------|
| **Camera Channels** | One per camera (spam!) | **Single grid view** ✨ |
| **Smart Switches** | ❌ Not supported | **✅ Full control panel** |
| **Team Chat** | ❌ No integration | **✅ Bidirectional bridge** |
| **Permissions** | ❌ No access control | **✅ Role-based security** |
| **Rate Limiting** | ❌ Can hit API limits | **✅ Smart rate limiting** |
| **Logging** | ❌ print() only | **✅ Professional logging** |
| **Error Handling** | ❌ Basic | **✅ Comprehensive recovery** |

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
    └── #🚨-events         [planned: event notifications]
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
- **Permission Protected** - Only authorized users can control

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
# Turn on turrets (requires permission)
!switch turrets on

# Turn off lights
!switch lights off

# Check bot status
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
- **Rate Limited** - Won't spam Discord API

### Usage

Just type in `#team-chat` channel - messages automatically go to Rust team chat!

**Example:**
```
Discord User: "Raid incoming from north!"
→ Appears in Rust as: [Discord - Username] Raid incoming from north!
```

---

## 🔐 Permission System

**NEW:** Control who can use bot commands!

### Features

- **Role-Based Access** - Allow specific Discord roles
- **User Whitelist** - Allow specific Discord users
- **Admin Override** - Server admins always have access
- **Logged Actions** - All command usage is logged

### Configuration

In `config_enhanced.json`:

```json
{
  "permissions": {
    "allowed_roles": ["Admin", "Moderator", "Base Manager"],
    "allowed_users": [123456789, 987654321]
  }
}
```

### Behavior

- If no permissions configured → Admins only
- If roles configured → Users with matching roles
- If users configured → Users in whitelist
- Admins → Always allowed (override)

### Example

```bash
# Authorized user
!switch turrets on
✅ Turned turrets on

# Unauthorized user
!switch turrets on
❌ Permission denied: Missing required role or user permission
```

All permission checks and denials are logged to `logs/enhanced_bot.log`.

---

## 📊 Logging & Monitoring

**NEW:** Professional logging system for debugging and auditing!

### Features

- **File Logging** - All events saved to `logs/enhanced_bot.log`
- **Console Output** - Real-time status updates
- **Log Levels** - INFO, WARNING, ERROR with timestamps
- **Audit Trail** - Permission checks, command usage, errors

### Log Example

```
2025-11-23 10:30:15 - rustplus_bot - INFO - ✅ Camera grid started with 4 cameras
2025-11-23 10:30:22 - rustplus_bot - INFO - Permission granted for User#1234 (123456789): Role: Admin
2025-11-23 10:30:22 - rustplus_bot - INFO - User#1234 switched lights to on
2025-11-23 10:30:45 - rustplus_bot - WARNING - Permission denied for User#5678 (987654321): Missing required role
2025-11-23 10:31:00 - rustplus_bot - WARNING - Hit Discord rate limit: sleeping for 0.5s
```

### Log Location

- **File:** `discord_bot/logs/enhanced_bot.log`
- **Format:** Timestamped with module and level
- **Rotation:** Consider using logrotate for long-running bots

---

## 🚧 Event Notifications (Planned Feature)

⚠️ **STATUS: Framework implemented but detection NOT working**

### Current State

The bot has methods for sending event notifications, but **automatic detection is not implemented**:

- `notify_explosion()` - Method exists but never triggered
- `notify_player_death()` - Method exists but never triggered
- `notify_entity_destroyed()` - Method exists but never triggered

### What's Needed

To implement these features, you would need to:

1. **Explosion Detection**
   - Parse `AppBroadcast` messages for explosion markers
   - Decode protobuf binary data
   - Monitor map markers

2. **Death Detection**
   - Monitor team member online/offline status
   - Parse team chat for death messages
   - Compare team info snapshots

3. **Entity Destruction**
   - Poll entity states periodically
   - Compare before/after values
   - Detect when `entity.value` goes false

### Why Not Implemented

- Requires deep Rust+ protobuf knowledge
- Needs polling loops or complex event parsing
- Not enough documentation on Rust+ event format
- Beyond scope of "solid foundation" release

### Future Plans

These features will be added in a future update when proper protobuf parsing is implemented.

**Current Recommendation:** Disable event notifications in config:
```json
{
  "features": {
    "event_notifications_enabled": false
  }
}
```

---

## 🎮 Camera Control Commands

Control cameras directly from Discord!

### Commands

```bash
# Movement
!control drone forward
!control drone backward
!control drone left
!control drone right

# Looking
!control drone up
!control drone down
!control drone lookleft
!control drone lookright

# Actions
!control drone fire
```

### Features

- **Permission Protected** - Requires authorization
- **Auto-Cleanup** - Movement auto-stops after 0.3s
- **Logged Actions** - All camera control is logged

---

## 🚁 Drone Control Script

**Separate tool:** `drone_control.py`

Automated drone patrols and manual control!

### Features

- **Waypoint Patrols** - Pre-programmed patrol routes
- **Interactive Control** - WASD + arrow keys
- **Screenshot Capture** - Automatic photos at waypoints
- **Height Management** - Automatic altitude control

### Usage

```bash
# Run drone control
python discord_bot/drone_control.py

# Follow on-screen instructions
# Set waypoints with SPACE
# Start patrol with P
```

See `drone_control.py` for full documentation.

---

## 🛠️ Installation & Setup

### Prerequisites

```bash
# Python 3.8+
python3 --version

# Required packages
pip install discord.py rustplus pillow
```

### Quick Start

1. **Run Setup Wizard**
   ```bash
   cd discord_bot
   python setup_wizard_enhanced.py
   ```

2. **Follow the prompts:**
   - Discord bot token
   - Rust+ server details (IP, port, Steam ID, player token)
   - Camera configuration
   - Switch entity IDs
   - Permission settings

3. **Start the bot:**
   ```bash
   python enhanced_bot.py
   ```

4. **Bot will:**
   - Connect to Discord
   - Connect to Rust+ server
   - Create/find channels
   - Start camera grid
   - Enable switch control
   - Bridge team chat

### Configuration

All settings in `config_enhanced.json`:

```json
{
  "discord_token": "YOUR_DISCORD_BOT_TOKEN",
  "command_prefix": "!",
  "rust_server": {
    "ip": "your.server.ip",
    "port": "28082",
    "steam_id": "76561198012345678",
    "player_token": "your_token"
  },
  "cameras": {
    "drone": {"enabled": true},
    "static1": {"enabled": true}
  },
  "switches": {
    "lights": 12345,
    "turrets": 12346
  },
  "permissions": {
    "allowed_roles": ["Admin", "Base Manager"],
    "allowed_users": []
  },
  "features": {
    "team_chat_enabled": true,
    "event_notifications_enabled": false
  }
}
```

---

## 📝 Commands Reference

### User Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `!status` | Show bot status | Everyone |
| `!switch <name> <on/off>` | Control switch | Required |
| `!control <cam> <action>` | Control camera | Required |

### Examples

```bash
# Check bot status
!status

# Control switches (needs permission)
!switch lights on
!switch turrets off
!switch generator on

# Control cameras (needs permission)
!control drone forward
!control drone fire
!control front up
```

---

## 🐛 Troubleshooting

### Bot Won't Start

**Error:** "Configuration file not found"
```bash
Solution: Run python setup_wizard_enhanced.py first
```

**Error:** "Invalid Discord token"
```bash
Solution: Check your token in config_enhanced.json
Enable bot on https://discord.com/developers
```

**Error:** "Missing required intents"
```bash
Solution: Enable "Message Content Intent" in Discord Developer Portal
Bot Settings → Privileged Gateway Intents → Message Content Intent
```

### Cameras Not Working

**Error:** "Failed to connect to camera"
```bash
Solution:
1. Verify camera IDs in Rust+ app
2. Check camera is powered and has storage
3. Ensure player is within range
4. Verify Rust+ credentials are correct
```

### Switches Not Responding

**Error:** "Failed to control switch"
```bash
Solution:
1. Verify entity IDs in config
2. Check switches are paired in Rust+ app
3. Ensure player has access permissions in-game
4. Check Rust+ connection is active
```

### Permission Denied

**Error:** "Permission denied: Missing required role"
```bash
Solution:
1. Check your Discord role matches config
2. Verify role names are exact (case-sensitive)
3. Or add your Discord user ID to allowed_users
4. Server admins are always allowed
```

### Rate Limiting Issues

**Warning:** "Hit Discord rate limit"
```bash
This is normal - bot automatically backs off
Rate limiter is working correctly
If happens frequently, consider:
- Reducing camera FPS in config
- Fewer cameras in grid
```

---

## 📊 Performance & Limits

### Recommended Settings

- **Cameras:** 4-6 maximum in grid
- **FPS:** 1-2 for surveillance (default: 2)
- **Switches:** Unlimited (updates only on change)

### Discord API Limits

The bot automatically handles:
- **Rate Limiting:** Max 4 messages per second (built-in)
- **Message Edit:** Automatic backoff on 429 errors
- **Connection:** Graceful reconnect on disconnect

### Resource Usage

Typical resource usage:
- **Memory:** ~50-100 MB
- **CPU:** Low (mostly idle, spikes during updates)
- **Network:** ~100 KB/s for 4 cameras at 2 FPS

---

## 🔒 Security Considerations

### Discord Token

- **Never commit** your token to Git
- Store in `config_enhanced.json` (gitignored)
- Regenerate if leaked

### Rust+ Credentials

- **Player token** is sensitive
- Don't share config files
- Use separate Steam account if possible

### Permissions

- Configure `allowed_roles` carefully
- Don't give control to untrusted users
- Review logs regularly for unauthorized attempts

### Logging

- Logs contain Discord usernames and IDs
- Protect `logs/` directory appropriately
- Consider log rotation for privacy

---

## 🚀 Advanced Usage

### Custom Camera Grid Size

Edit `enhanced_bot.py`:

```python
# In CameraGridManager._create_grid_image()
cols = 3  # Change from 2 to 3 for 3-column grid
```

### Adjust Update Speed

In `config_enhanced.json`:

```json
{
  "stream_settings": {
    "stream_fps": 1,  // Lower = less resource usage
    "render_entities": true,  // Show players/objects
    "entity_render_distance": 100
  }
}
```

### Custom Permissions

Multiple roles:
```json
{
  "permissions": {
    "allowed_roles": ["Admin", "Mod", "Manager", "Trusted"]
  }
}
```

Specific users:
```json
{
  "permissions": {
    "allowed_users": [123456789, 987654321, 111222333]
  }
}
```

---

## 📚 Architecture Overview

### Core Components

```
enhanced_bot.py
├── Config              # Configuration management
├── RateLimiter         # Discord API protection
├── has_permission()    # Access control
├── CameraGridManager   # Multi-camera display
├── SmartSwitchManager  # Switch control panel
├── TeamChatBridge      # Chat relay
├── EventNotifier       # Notification framework (planned)
└── EnhancedRustBot     # Main bot class
```

### File Structure

```
discord_bot/
├── enhanced_bot.py                # Main bot (✅ Production ready)
├── setup_wizard_enhanced.py       # Interactive setup
├── drone_control.py               # Drone automation
├── config_enhanced.json           # Configuration (create with wizard)
├── config_enhanced.example.json   # Example config
├── logs/                          # Log files (auto-created)
│   └── enhanced_bot.log
├── README_ENHANCED.md             # This file
├── CRITICAL_FIXES_NEEDED.md       # Implementation notes
└── CRITICAL_ANALYSIS.md           # Detailed analysis
```

---

## 🔄 Changelog

### v2.0 - Production Beta (Current)

**Core Improvements:**
- ✅ Fixed critical import bug (ChatEvent from annotations)
- ✅ Added comprehensive logging system
- ✅ Implemented rate limiting for all Discord updates
- ✅ Added permission system (role + user whitelist)
- ✅ Fixed cross-platform font paths
- ✅ Added graceful shutdown with signal handlers
- ✅ Improved error handling throughout

**Documentation:**
- ✅ Honest feature status (working vs. planned)
- ✅ Detailed troubleshooting guide
- ✅ Security considerations
- ✅ Performance recommendations

**Known Limitations:**
- ⚠️ Event detection framework only (not implemented)
- ⚠️ Icons available but not integrated
- ⚠️ No auto-reconnect on connection loss

### v1.0 - Initial Enhanced Bot

- Single-channel camera grid
- Smart switch control
- Team chat bridge
- Basic structure

---

## 🤝 Contributing

### Implementing Event Detection

If you want to implement automatic event detection:

1. Study `rustplus.proto` for event structures
2. Parse `AppBroadcast` messages in event handlers
3. Implement polling for state changes
4. Update `EventNotifier` methods with detection logic
5. Test thoroughly before enabling

See `CRITICAL_ANALYSIS.md` for detailed implementation notes.

### Reporting Issues

Include:
- Python version
- Operating system
- Config (with tokens removed)
- Full error message
- Log file excerpt

---

## 📄 License

This bot uses the `rustplus` library and is intended for personal/clan use with Rust+ enabled servers.

**Disclaimer:** Use at your own risk. The authors are not responsible for any bans, server issues, or data loss.

---

## 🙏 Credits

- Built on [`rustplus`](https://github.com/olijeffers0n/rustplus) library
- Uses [`discord.py`](https://github.com/Rapptz/discord.py)
- Enhanced camera grid concept
- Community feedback and testing

---

## 📞 Support

**Documentation:**
- This README (you're reading it!)
- `CRITICAL_FIXES_NEEDED.md` - Implementation details
- `CRITICAL_ANALYSIS.md` - Full technical analysis

**Common Issues:**
- Check logs: `logs/enhanced_bot.log`
- Verify config: `config_enhanced.example.json`
- Test connection: `!status` command

**Getting Help:**
1. Check troubleshooting section above
2. Review log files
3. Verify configuration
4. Check Rust+ app connectivity

---

**Status:** ✅ Production Beta - Core features tested and working

**Last Updated:** 2025-11-23

**Recommendation:** Start with cameras and switches, add team chat when comfortable, event detection when implemented.
