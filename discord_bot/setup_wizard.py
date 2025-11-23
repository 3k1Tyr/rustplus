"""
Rust+ Discord Bot - Setup Wizard

Interactive setup wizard for first-time users.
Makes it easy to configure the bot without editing JSON files.

Usage:
    python setup_wizard.py
"""

import json
import os
import sys
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("\n" + "=" * 60)
    print("  Rust+ Discord Surveillance Bot - Setup Wizard")
    print("=" * 60)
    print("\nThis wizard will help you configure the bot step-by-step.")
    print("Don't worry, you can always edit config.json later!\n")

def print_section(title):
    """Print section header"""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")

def get_input(prompt, default=None, required=True):
    """Get user input with validation"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()

        if not user_input and required:
            print("❌ This field is required. Please try again.")
            continue

        return user_input

def get_yes_no(prompt, default=True):
    """Get yes/no input"""
    default_text = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_text}]: ").strip().lower()

        if not response:
            return default

        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("❌ Please answer 'y' or 'n'")

def get_number(prompt, default=None, min_val=None, max_val=None):
    """Get numeric input"""
    while True:
        value = get_input(prompt, default, required=(default is None))

        try:
            num = float(value) if '.' in str(value) else int(value)

            if min_val is not None and num < min_val:
                print(f"❌ Value must be at least {min_val}")
                continue

            if max_val is not None and num > max_val:
                print(f"❌ Value must be at most {max_val}")
                continue

            return num

        except ValueError:
            print("❌ Please enter a valid number")

def setup_discord():
    """Setup Discord bot configuration"""
    print_section("📱 Discord Bot Configuration")

    print("First, you need to create a Discord bot:")
    print("  1. Go to https://discord.com/developers/applications")
    print("  2. Click 'New Application'")
    print("  3. Go to 'Bot' section and click 'Add Bot'")
    print("  4. Enable 'Message Content Intent' under Privileged Gateway Intents")
    print("  5. Copy the bot token\n")

    token = get_input("🔑 Enter your Discord bot token")

    print("\n📝 Customize bot settings:")
    prefix = get_input("Command prefix", default="!")
    category_name = get_input("Category name for cameras", default="🎥 SURVEILLANCE")

    return {
        'discord_token': token,
        'command_prefix': prefix,
        'category_name': category_name
    }

def setup_rust_server():
    """Setup Rust+ server configuration"""
    print_section("🎮 Rust+ Server Configuration")

    print("You need your Rust+ server details:")
    print("  • Server IP and Port (from Rust+ companion app)")
    print("  • Your Steam ID (17 digits)")
    print("  • Player Token (from FCM notifications)")
    print("\n💡 See documentation for help finding these!\n")

    ip = get_input("Server IP address")
    port = get_input("Server port", default="28082")
    steam_id = get_input("Your Steam ID (17 digits)")
    player_token = get_input("Your player token")

    return {
        'ip': ip,
        'port': port,
        'steam_id': steam_id,
        'player_token': player_token
    }

def setup_cameras():
    """Setup camera configuration"""
    print_section("📹 Camera Configuration")

    print("Now let's add your cameras!")
    print("\n💡 Common camera IDs:")
    print("  • 'drone' - Your deployed drone")
    print("  • 'static1', 'static2', etc. - Your CCTV cameras")
    print("  • Station camera IDs (check in-game)\n")

    cameras = {}

    while True:
        camera_id = get_input(f"\nCamera ID (or press Enter to finish)", required=False)

        if not camera_id:
            if not cameras:
                print("❌ You need at least one camera!")
                continue
            break

        print(f"\nConfiguring camera: {camera_id}")

        channel_name = get_input("Discord channel name", default=f"📹-{camera_id}")
        description = get_input("Description", default=f"{camera_id} camera feed")
        auto_start = get_yes_no("Auto-start this camera when bot starts?", default=True)

        cameras[camera_id] = {
            'channel_name': channel_name,
            'description': description,
            'auto_start': auto_start
        }

        print(f"✅ Added camera: {camera_id}")

        if not get_yes_no("\nAdd another camera?", default=True):
            break

    return cameras

def setup_stream_settings():
    """Setup stream quality settings"""
    print_section("⚙️ Stream Settings")

    print("Configure stream quality and performance:\n")

    print("💡 FPS (Frames Per Second):")
    print("  • 1-2 FPS: Low bandwidth, basic monitoring")
    print("  • 2-3 FPS: Recommended for surveillance")
    print("  • 3-5 FPS: Smooth video (higher bandwidth)")
    print("  ⚠️ Discord rate limits at ~5 FPS per channel\n")

    fps = get_number("Stream FPS", default=2, min_val=1, max_val=5)

    render_entities = get_yes_no("Show players and entities in feed?", default=True)

    entity_distance = 100
    if render_entities:
        print("\n💡 Entity render distance:")
        print("  • 50m: Only nearby entities")
        print("  • 100m: Normal range (recommended)")
        print("  • 200m: Far range (may impact performance)\n")
        entity_distance = get_number("Entity render distance (meters)", default=100, min_val=10, max_val=500)

    return {
        'stream_fps': fps,
        'render_entities': render_entities,
        'entity_render_distance': entity_distance
    }

def save_config(config):
    """Save configuration to file"""
    config_path = Path("config.json")

    # Backup existing config
    if config_path.exists():
        backup_path = Path("config.json.backup")
        print(f"\n💾 Backing up existing config to {backup_path}")
        import shutil
        shutil.copy(config_path, backup_path)

    # Save new config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"\n✅ Configuration saved to {config_path}")

def print_next_steps():
    """Print next steps"""
    print("\n" + "=" * 60)
    print("  🎉 Setup Complete!")
    print("=" * 60)

    print("\n📝 Next steps:")
    print("\n1. Invite your bot to your Discord server:")
    print("   • Go to https://discord.com/developers/applications")
    print("   • Select your application")
    print("   • Go to OAuth2 → URL Generator")
    print("   • Select scopes: 'bot'")
    print("   • Select permissions:")
    print("     ✓ Manage Channels")
    print("     ✓ Send Messages")
    print("     ✓ Embed Links")
    print("     ✓ Attach Files")
    print("   • Copy the URL and open it to invite the bot")

    print("\n2. Start the bot:")
    print("   python rustplus_bot.py")

    print("\n3. The bot will automatically:")
    print("   ✓ Create surveillance category")
    print("   ✓ Create channels for each camera")
    print("   ✓ Start streaming cameras")

    print("\n4. Use these commands in Discord:")
    print("   !status - Show bot status")
    print("   !control <camera> <action> - Control camera")
    print("   !restart <camera> - Restart a camera (Admin)")

    print("\n📚 For help, check:")
    print("   • README.md - Complete documentation")
    print("   • SETUP_GUIDE.md - Detailed setup instructions")
    print("   • TROUBLESHOOTING.md - Common issues")

    print("\n" + "=" * 60)
    print("  Happy Surveillance! 🎥")
    print("=" * 60 + "\n")

def main():
    """Main wizard entry point"""
    print_header()

    # Run setup sections
    discord_config = setup_discord()
    rust_server = setup_rust_server()
    cameras = setup_cameras()
    stream_settings = setup_stream_settings()

    # Combine configuration
    config = {
        **discord_config,
        'rust_server': rust_server,
        'cameras': cameras,
        'stream_settings': stream_settings
    }

    # Show summary
    print_section("📋 Configuration Summary")
    print(f"Discord Bot: {'*' * 20}{discord_config['discord_token'][-10:]}")
    print(f"Command Prefix: {discord_config['command_prefix']}")
    print(f"Category: {discord_config['category_name']}")
    print(f"\nRust Server: {rust_server['ip']}:{rust_server['port']}")
    print(f"Steam ID: {rust_server['steam_id']}")
    print(f"\nCameras: {len(cameras)} configured")
    for cam_id in cameras:
        print(f"  • {cam_id} → #{cameras[cam_id]['channel_name']}")
    print(f"\nStream FPS: {stream_settings['stream_fps']}")
    print(f"Render Entities: {stream_settings['render_entities']}")

    # Confirm and save
    if get_yes_no("\n✅ Save this configuration?", default=True):
        save_config(config)
        print_next_steps()
    else:
        print("\n❌ Configuration not saved. Run the wizard again when ready.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
