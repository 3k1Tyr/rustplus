# CRITICAL FIXES REQUIRED

**Status:** ⚠️ **BOT WILL NOT RUN WITHOUT THESE FIXES**

---

## 🔴 FIX #1: Import Error (CRITICAL)

**File:** `enhanced_bot.py`
**Lines:** 33-38

**BROKEN CODE:**
```python
from rustplus.events import (
    ChatEvent,
    TeamEvent,
    EntityEvent,
    ProtobufEvent
)
```

**FIXED CODE:**
```python
from rustplus.annotations import (
    ChatEvent,
    TeamEvent,
    EntityEvent,
    ProtobufEvent
)
```

**Why:** Event decorators are in `rustplus.annotations`, not `rustplus.events`

**Impact:** Bot crashes immediately on import with `ImportError`

---

## 🔴 FIX #2: Event Handlers Don't Actually Work (CRITICAL)

**File:** `enhanced_bot.py`
**Lines:** 490-507

**PROBLEM:** Events are registered but NEVER TRIGGER because:
1. Handlers are defined in async method (wrong scope)
2. No actual event listening setup
3. Event decorators expect different server_details format

**WHAT'S MISSING:**

The current code sets up handlers but Rust+ needs to actively poll for events:

```python
# MISSING: Event polling loop
@tasks.loop(seconds=0.5)
async def poll_events(self):
    """Poll for Rust+ events"""
    if not self.rust_socket:
        return

    try:
        # Get team chat
        chat_messages = await self.rust_socket.get_team_chat()
        if isinstance(chat_messages, list):
            for msg in chat_messages:
                if self.chat_bridge:
                    await self.chat_bridge.send_to_discord(
                        msg.message,
                        msg.name
                    )
    except Exception as e:
        print(f"Error polling events: {e}")
```

**OR** Use the event handler correctly with proper WebSocket monitoring.

---

## 🔴 FIX #3: Event Detection Not Implemented

**File:** `enhanced_bot.py`
**Class:** `EventNotifier`

**PROBLEM:** Methods exist but are NEVER CALLED:
- `notify_explosion()` - never called
- `notify_player_death()` - never called
- `notify_entity_destroyed()` - never called

**WHAT'S NEEDED:**

1. **For Explosion Detection:**
```python
# Need to parse map markers or protobuf for explosions
@ProtobufEvent(self.rust_socket.server_details)
async def on_protobuf(event):
    # Parse raw bytes
    # Look for explosion markers
    # This requires understanding Rust+ protobuf format deeply
    pass
```

2. **For Death Detection:**
```python
# Need to monitor team member list changes
@TeamEvent(self.rust_socket.server_details)
async def on_team_change(event):
    # Compare before/after team member status
    # Detect when member goes offline suddenly
    pass
```

3. **For Entity Destruction:**
```python
# Already have EntityEvent, but need to check for destruction
@EntityEvent(self.rust_socket.server_details)
async def on_entity_change(event):
    if event.entity_changed.value == False:  # Example
        # Entity destroyed
        await self.event_notifier.notify_entity_destroyed("Smart Switch")
```

**REALITY:** Rust+ API has limited event support. Some events may require:
- Polling entity states
- Comparing map markers
- Monitoring team chat for death messages
- Parsing protobuf binary data

---

## 🟡 FIX #4: No Rate Limiting (HIGH PRIORITY)

**File:** `enhanced_bot.py`
**Method:** `CameraGridManager.update()`

**PROBLEM:** Discord limits to ~5 messages/second per channel. Camera grid updates could hit this.

**QUICK FIX:**
```python
class CameraGridManager:
    def __init__(self, ...):
        self.last_update = 0
        self.min_update_interval = 0.5  # Maximum 2 updates/second

    async def update(self):
        current_time = time.time()

        # Rate limit: minimum 0.5 seconds between updates
        if current_time - self.last_update < self.min_update_interval:
            return

        # ... existing update code ...

        self.last_update = current_time
```

---

## 🟡 FIX #5: Font Path Issues (CROSS-PLATFORM)

**File:** `enhanced_bot.py`
**Method:** `_create_grid_image()`

**PROBLEM:** Hardcoded Linux font path

**FIXED CODE:**
```python
def _get_font(self, size: int = 20):
    """Get font with cross-platform support"""
    import platform

    font_paths = {
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
        ],
        'Windows': [
            'C:\\Windows\\Fonts\\arial.ttf',
            'C:\\Windows\\Fonts\\arialbd.ttf',
        ]
    }

    system = platform.system()
    paths = font_paths.get(system, [])

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    # Fallback to default
    return ImageFont.load_default()
```

---

## 🟡 FIX #6: Missing Permission Checks

**File:** `enhanced_bot.py`
**All Commands**

**PROBLEM:** Anyone can control switches and cameras

**QUICK FIX:**
```python
from discord.ext import commands

# Add to config
ADMIN_ROLES = ['Admin', 'Moderator', 'Base Manager']

@commands.command(name='switch')
@commands.has_any_role(*ADMIN_ROLES)  # ADD THIS
async def switch_command(ctx, name: str, state: str):
    # Existing code
    pass

# OR use user whitelist
ALLOWED_USERS = [123456789, 987654321]  # Discord user IDs

@commands.command(name='switch')
async def switch_command(ctx, name: str, state: str):
    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("❌ You don't have permission to control switches")
        return

    # Existing code
```

---

## 🟡 FIX #7: No Graceful Shutdown

**File:** `enhanced_bot.py`
**Function:** `main()`

**FIXED CODE:**
```python
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
        return

    # Create bot
    bot = EnhancedRustBot(config)
    setup_commands(bot)

    # Setup signal handlers for graceful shutdown
    import signal

    def shutdown_handler(signum, frame):
        print("\n\n🛑 Shutting down gracefully...")
        asyncio.create_task(bot.close())
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Run bot
    try:
        print("\n🚀 Starting bot...\n")
        bot.run(config.get('discord_token'))
    except KeyboardInterrupt:
        print("\n\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
```

---

## 📋 CHECKLIST BEFORE USING BOT

- [ ] Fix import error (rustplus.annotations)
- [ ] Understand event detection limitations
- [ ] Add rate limiting
- [ ] Fix font paths for your OS
- [ ] Add permission checks
- [ ] Test with actual Rust+ server
- [ ] Add error logging
- [ ] Document what events actually work
- [ ] Add BETA warning to README
- [ ] Create minimal working example first

---

## ⚠️ DISCLAIMER

**This bot is BETA quality and has known issues:**

1. Event notifications (explosions, deaths) require manual implementation
2. Icon integration is not complete
3. Some features are framework only (need actual detection code)
4. Requires testing on real Rust+ server
5. May have undiscovered bugs

**Recommendation:** Start with basic features (camera grid, switch control) and add advanced features incrementally after testing.

---

## 🔧 MINIMAL WORKING VERSION

For a quick working version, focus on:

1. ✅ Camera grid (works with fix #1)
2. ✅ Smart switches (works if entity IDs correct)
3. ⚠️ Team chat (needs polling or proper event setup)
4. ❌ Event notifications (needs implementation)
5. ✅ Drone control (standalone script works)

**Test this order:**
1. Camera grid only
2. Add switch control
3. Add team chat polling
4. Add custom event detection

---

## 📝 QUICK PATCH FILE

Create `fix_imports.patch`:
```diff
--- a/discord_bot/enhanced_bot.py
+++ b/discord_bot/enhanced_bot.py
@@ -30,7 +30,7 @@ from rustplus import RustSocket
 from rustplus.remote.camera.camera_manager import CameraManager
 from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
 from rustplus.structs import Vector
-from rustplus.events import (
+from rustplus.annotations import (
     ChatEvent,
     TeamEvent,
     EntityEvent,
```

Apply with: `git apply fix_imports.patch`

---

**END OF CRITICAL FIXES**

**Status:** These fixes are REQUIRED before the bot can run.
