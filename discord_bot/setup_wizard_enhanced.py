"""
Enhanced Rust+ Discord Bot - Setup Wizard

Interactive setup for the enhanced bot with:
- Single-channel camera grid
- Smart switch integration
- Team chat bridge
- Event notifications

Usage:
    python setup_wizard_enhanced.py
"""

import json
import sys
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 60)
    print("  Enhanced Rust+ Discord Bot - Setup Wizard")
    print("=" * 60)
    print("\nThis wizard configures the enhanced bot with:")
    print("  ✅ Single-channel camera grid (all cameras in one view)")
    print("  ✅ Smart switch control panel")
    print("  ✅ Team chat bridge (Discord ↔ Rust)")
    print("  ✅ Event notifications\n")


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
            print("❌ This field is required")
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
    """Setup Discord configuration"""
    print("\n" + "─" * 60)
    print("  📱 Discord Bot Configuration")
    print("─" * 60 + "\n")

    print("Create bot at: https://discord.com/developers/applications")
    print("Enable: Message Content Intent\n")

    token = get_input("Discord bot token")
    prefix = get_input("Command prefix", default="!")
    category_name = get_input("Category name", default="🎥 RUST+ CONTROL")

    return {
        'discord_token': token,
        'command_prefix': prefix,
        'category_name': category_name
    }


def setup_rust_server():
    """Setup Rust+ server"""
    print("\n" + "─" * 60)
    print("  🎮 Rust+ Server Configuration")
    print("─" * 60 + "\n")

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
    """Setup cameras"""
    print("\n" + "─" * 60)
    print("  📹 Camera Configuration")
    print("─" * 60 + "\n")

    print("All cameras will be displayed in a SINGLE Discord channel!")
    print("The bot creates a grid view with all camera feeds.\n")

    print("Common camera IDs:")
    print("  • 'drone' - Your drone")
    print("  • 'static1', 'static2' - CCTV cameras\n")

    cameras = {}

    while True:
        camera_id = get_input(f"\nCamera ID (or press Enter to finish)", required=False)

        if not camera_id:
            if not cameras:
                print("❌ You need at least one camera!")
                continue
            break

        cameras[camera_id] = {
            'enabled': True
        }

        print(f"✅ Added camera: {camera_id}")

        if not get_yes_no("\nAdd another camera?", default=True):
            break

    return cameras


def setup_switches():
    """Setup smart switches"""
    print("\n" + "─" * 60)
    print("  ⚡ Smart Switch Configuration")
    print("─" * 60 + "\n")

    print("Smart switches appear in a control panel channel.")
    print("You can toggle them with: !switch <name> <on/off>\n")

    print("To find entity IDs:")
    print("  1. Pair device in Rust+ app")
    print("  2. Note the entity ID shown\n")

    if not get_yes_no("Do you want to add smart switches?", default=True):
        return {}

    switches = {}

    while True:
        name = get_input(f"\nSwitch name (or press Enter to finish)", required=False)

        if not name:
            break

        entity_id = get_number(f"Entity ID for {name}")

        switches[name] = entity_id
        print(f"✅ Added switch: {name} (ID: {entity_id})")

        if not get_yes_no("\nAdd another switch?", default=True):
            break

    return switches


def setup_stream_settings():
    """Setup stream settings"""
    print("\n" + "─" * 60)
    print("  ⚙️ Stream Settings")
    print("─" * 60 + "\n")

    print("Grid update FPS:")
    print("  • 1-2 FPS: Low bandwidth")
    print("  • 2-3 FPS: Recommended")
    print("  • 3-5 FPS: Smooth (higher load)\n")

    fps = get_number("Stream FPS", default=2, min_val=1, max_val=5)
    render_entities = get_yes_no("Show players/entities in feeds?", default=True)

    return {
        'stream_fps': fps,
        'render_entities': render_entities,
        'entity_render_distance': 100
    }


def setup_features():
    """Setup optional features"""
    print("\n" + "─" * 60)
    print("  🚀 Additional Features")
    print("─" * 60 + "\n")

    team_chat = get_yes_no("Enable team chat bridge? (Discord ↔ Rust)", default=True)
    event_notifications = get_yes_no("Enable event notifications?", default=True)

    return {
        'team_chat_enabled': team_chat,
        'event_notifications_enabled': event_notifications
    }


def save_config(config):
    """Save configuration"""
    config_path = Path("config_enhanced.json")

    # Backup existing
    if config_path.exists():
        backup = Path("config_enhanced.json.backup")
        import shutil
        shutil.copy(config_path, backup)
        print(f"\n💾 Backed up existing config to {backup}")

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

    print("\n1. Invite bot to Discord:")
    print("   • OAuth2 → URL Generator")
    print("   • Scopes: bot")
    print("   • Permissions:")
    print("     ✓ Manage Channels")
    print("     ✓ Send Messages")
    print("     ✓ Embed Links")
    print("     ✓ Attach Files")

    print("\n2. Start the bot:")
    print("   python enhanced_bot.py")

    print("\n3. Bot will create 4 channels:")
    print("   📹 #surveillance - Camera grid (ALL cameras in one view!)")
    print("   ⚡ #switches - Smart switch control panel")
    print("   💬 #team-chat - Bidirectional Discord ↔ Rust chat")
    print("   🚨 #events - Event notifications")

    print("\n4. Commands:")
    print("   !status - Show bot status")
    print("   !switch <name> <on/off> - Control switch")
    print("   !control <camera> <action> - Control camera")

    print("\n5. Try the drone control:")
    print("   python drone_control.py")

    print("\n" + "=" * 60)
    print("  Happy Surveillance! 🎥")
    print("=" * 60 + "\n")


def main():
    """Main wizard"""
    print_header()

    # Run setup
    discord_config = setup_discord()
    rust_server = setup_rust_server()
    cameras = setup_cameras()
    switches = setup_switches()
    stream_settings = setup_stream_settings()
    features = setup_features()

    # Combine configuration
    config = {
        **discord_config,
        'rust_server': rust_server,
        'cameras': cameras,
        'switches': switches,
        'stream_settings': stream_settings,
        'features': features
    }

    # Show summary
    print("\n" + "─" * 60)
    print("  📋 Configuration Summary")
    print("─" * 60)
    print(f"\nDiscord: {'*' * 20}{discord_config['discord_token'][-10:]}")
    print(f"Rust Server: {rust_server['ip']}:{rust_server['port']}")
    print(f"\nCameras: {len(cameras)} configured")
    for cam_id in cameras:
        print(f"  • {cam_id}")
    print(f"\nSwitches: {len(switches)} configured")
    for name, entity_id in switches.items():
        print(f"  • {name} (ID: {entity_id})")
    print(f"\nFeatures:")
    print(f"  • Team Chat: {'✅' if features['team_chat_enabled'] else '❌'}")
    print(f"  • Event Notifications: {'✅' if features['event_notifications_enabled'] else '❌'}")

    # Confirm
    if get_yes_no("\n✅ Save this configuration?", default=True):
        save_config(config)
        print_next_steps()
    else:
        print("\n❌ Configuration not saved")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
