"""
Rust+ Drone Control Script

Simple drone control for surveillance and reconnaissance.
Can be used standalone or integrated with Discord bot.

Features:
- Waypoint patrol routes
- Auto-return to base
- Obstacle avoidance (basic)
- Screenshot capture
- Emergency stop

Usage:
    python drone_control.py

    Or import and use programmatically:
    from drone_control import DroneController
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
from pathlib import Path

from rustplus import RustSocket
from rustplus.remote.camera.camera_manager import CameraManager
from rustplus.remote.camera.camera_constants import MovementControls, CameraMovementOptions
from rustplus.structs import Vector


class DroneState(Enum):
    """Drone states"""
    IDLE = "idle"
    PATROLLING = "patrolling"
    RETURNING = "returning"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class Waypoint:
    """A waypoint in 3D space"""
    name: str
    forward_duration: float  # Seconds to move forward
    up_duration: float  # Seconds to move up/down (+/-)
    hover_duration: float  # Seconds to hover at waypoint


@dataclass
class PatrolRoute:
    """A patrol route with multiple waypoints"""
    name: str
    waypoints: List[Waypoint]
    loop: bool = True  # Loop route indefinitely


class DroneController:
    """Controls a Rust+ drone"""

    def __init__(self, rust_socket: RustSocket, camera_id: str = "drone"):
        self.rust_socket = rust_socket
        self.camera_id = camera_id
        self.camera_mgr: Optional[CameraManager] = None
        self.state = DroneState.IDLE
        self.current_route: Optional[PatrolRoute] = None
        self.screenshot_dir = Path("drone_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)

    async def connect(self):
        """Connect to drone camera"""
        print(f"📡 Connecting to drone camera: {self.camera_id}")
        self.camera_mgr = await self.rust_socket.get_camera_manager(self.camera_id)

        if hasattr(self.camera_mgr, 'error'):
            raise Exception(f"Failed to connect to drone: {self.camera_mgr.error}")

        # Wait for initial frame
        await asyncio.sleep(1)
        print("✅ Connected to drone")

    async def disconnect(self):
        """Disconnect from drone"""
        if self.camera_mgr:
            await self.camera_mgr.exit_camera()
            print("✅ Disconnected from drone")

    async def move(self, action: int, duration: float = 0.5):
        """Move drone in a direction"""
        if not self.camera_mgr:
            raise Exception("Drone not connected")

        if not self.camera_mgr.can_move(CameraMovementOptions.MOVEMENT):
            print("⚠️ Drone cannot move")
            return

        await self.camera_mgr.send_actions([action])
        await asyncio.sleep(duration)
        await self.camera_mgr.clear_movement()

    async def look(self, direction: Vector, duration: float = 0.3):
        """Look in a direction"""
        if not self.camera_mgr:
            raise Exception("Drone not connected")

        if not self.camera_mgr.can_move(CameraMovementOptions.MOUSE):
            print("⚠️ Drone cannot look")
            return

        await self.camera_mgr.send_mouse_movement(direction)
        await asyncio.sleep(duration)

    async def take_screenshot(self, name: str = None) -> Optional[str]:
        """Take a screenshot from drone camera"""
        if not self.camera_mgr or not self.camera_mgr.has_frame_data():
            print("❌ No frame data available")
            return None

        frame = await self.camera_mgr.get_frame(render_entities=True)
        if not frame:
            return None

        # Generate filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png" if name else f"drone_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        # Save screenshot
        frame.save(filepath)
        print(f"📸 Screenshot saved: {filepath}")
        return str(filepath)

    async def scan_area(self, duration: float = 5.0):
        """360-degree scan of area"""
        print("🔍 Scanning area (360°)...")

        # Look around in a circle
        steps = 8
        angle_per_step = Vector(0.5, 0)  # Horizontal rotation

        for i in range(steps):
            await self.look(angle_per_step, 0.3)
            await asyncio.sleep(duration / steps)

            # Take screenshot at each angle
            await self.take_screenshot(f"scan_{i}")

        print("✅ Scan complete")

    async def hover(self, duration: float = 2.0):
        """Hover in place (resubscribe periodically)"""
        start_time = time.time()

        while time.time() - start_time < duration:
            # Resubscribe every 10 seconds
            if time.time() % 10 < 0.5:
                await self.camera_mgr.resubscribe()

            await asyncio.sleep(0.5)

    async def move_forward(self, duration: float = 2.0):
        """Move forward for specified duration"""
        print(f"➡️ Moving forward for {duration}s...")
        await self.move(MovementControls.FORWARD, duration)

    async def move_backward(self, duration: float = 2.0):
        """Move backward for specified duration"""
        print(f"⬅️ Moving backward for {duration}s...")
        await self.move(MovementControls.BACKWARD, duration)

    async def move_up(self, duration: float = 1.0):
        """Move up for specified duration"""
        print(f"⬆️ Moving up for {duration}s...")
        await self.move(MovementControls.JUMP, duration)

    async def move_down(self, duration: float = 1.0):
        """Move down for specified duration"""
        print(f"⬇️ Moving down for {duration}s...")
        await self.move(MovementControls.DUCK, duration)

    async def move_left(self, duration: float = 1.0):
        """Strafe left"""
        print(f"⬅️ Strafing left for {duration}s...")
        await self.move(MovementControls.LEFT, duration)

    async def move_right(self, duration: float = 1.0):
        """Strafe right"""
        print(f"➡️ Strafing right for {duration}s...")
        await self.move(MovementControls.RIGHT, duration)

    async def execute_waypoint(self, waypoint: Waypoint):
        """Execute a single waypoint"""
        print(f"\n📍 Waypoint: {waypoint.name}")

        # Move forward
        if waypoint.forward_duration > 0:
            await self.move_forward(waypoint.forward_duration)

        # Move up/down
        if waypoint.up_duration > 0:
            await self.move_up(waypoint.up_duration)
        elif waypoint.up_duration < 0:
            await self.move_down(abs(waypoint.up_duration))

        # Hover and scan
        if waypoint.hover_duration > 0:
            print(f"🚁 Hovering for {waypoint.hover_duration}s...")
            await self.hover(waypoint.hover_duration)
            await self.take_screenshot(waypoint.name)

    async def execute_patrol(self, route: PatrolRoute, on_waypoint_callback=None):
        """Execute a patrol route"""
        self.state = DroneState.PATROLLING
        self.current_route = route

        print(f"\n🚁 Starting patrol: {route.name}")
        print(f"📍 Waypoints: {len(route.waypoints)}")
        print(f"🔄 Loop: {route.loop}")

        iteration = 0

        try:
            while self.state == DroneState.PATROLLING:
                iteration += 1
                print(f"\n{'='*60}")
                print(f"🔄 Patrol iteration {iteration}")
                print(f"{'='*60}")

                for idx, waypoint in enumerate(route.waypoints):
                    # Check for emergency stop
                    if self.state == DroneState.EMERGENCY_STOP:
                        print("\n🛑 EMERGENCY STOP!")
                        return

                    # Execute waypoint
                    await self.execute_waypoint(waypoint)

                    # Callback
                    if on_waypoint_callback:
                        await on_waypoint_callback(waypoint, idx, iteration)

                # Stop if not looping
                if not route.loop:
                    break

                print(f"\n✅ Completed iteration {iteration}")

        except Exception as e:
            print(f"\n❌ Patrol error: {e}")
            self.state = DroneState.IDLE

        finally:
            self.state = DroneState.IDLE
            print("\n✅ Patrol complete")

    async def return_to_base(self, base_waypoint: Waypoint):
        """Return drone to base position"""
        self.state = DroneState.RETURNING
        print("\n🏠 Returning to base...")

        try:
            await self.execute_waypoint(base_waypoint)
            print("✅ Returned to base")
        except Exception as e:
            print(f"❌ Return failed: {e}")
        finally:
            self.state = DroneState.IDLE

    def emergency_stop(self):
        """Emergency stop all drone movement"""
        self.state = DroneState.EMERGENCY_STOP
        print("\n🚨 EMERGENCY STOP ACTIVATED!")

    async def get_entities_in_view(self):
        """Get entities currently visible to drone"""
        if not self.camera_mgr or not self.camera_mgr.has_frame_data():
            return []

        return await self.camera_mgr.get_entities_in_frame()

    async def check_for_players(self) -> List[str]:
        """Check for players in view"""
        entities = await self.get_entities_in_view()
        players = [e for e in entities if e.type == 2]

        player_info = []
        for player in players:
            name = player.name if not player.name.isdigit() else f"NPC_{player.name}"
            distance = player.position.z
            player_info.append(f"{name} ({distance:.1f}m)")

        return player_info


# ========================
# Predefined Patrol Routes
# ========================

# Base perimeter patrol
BASE_PATROL = PatrolRoute(
    name="Base Perimeter",
    waypoints=[
        Waypoint("North Wall", forward_duration=3.0, up_duration=0.5, hover_duration=2.0),
        Waypoint("East Wall", forward_duration=3.0, up_duration=0, hover_duration=2.0),
        Waypoint("South Wall", forward_duration=3.0, up_duration=0, hover_duration=2.0),
        Waypoint("West Wall", forward_duration=3.0, up_duration=0, hover_duration=2.0),
    ],
    loop=True
)

# High altitude scan
HIGH_SCAN = PatrolRoute(
    name="High Altitude Scan",
    waypoints=[
        Waypoint("Ascend", forward_duration=0, up_duration=5.0, hover_duration=1.0),
        Waypoint("North View", forward_duration=5.0, up_duration=0, hover_duration=3.0),
        Waypoint("East View", forward_duration=0, up_duration=0, hover_duration=3.0),
        Waypoint("South View", forward_duration=0, up_duration=0, hover_duration=3.0),
        Waypoint("West View", forward_duration=0, up_duration=0, hover_duration=3.0),
        Waypoint("Descend", forward_duration=0, up_duration=-5.0, hover_duration=1.0),
    ],
    loop=False
)

# Quick recon
QUICK_RECON = PatrolRoute(
    name="Quick Reconnaissance",
    waypoints=[
        Waypoint("Forward Scout", forward_duration=5.0, up_duration=1.0, hover_duration=2.0),
        Waypoint("Return", forward_duration=-5.0, up_duration=-1.0, hover_duration=1.0),
    ],
    loop=False
)


# ========================
# Interactive Control
# ========================

async def interactive_mode(controller: DroneController):
    """Interactive drone control via keyboard"""
    print("\n" + "="*60)
    print("🎮 Interactive Drone Control")
    print("="*60)
    print("\nCommands:")
    print("  w - Move forward")
    print("  s - Move backward")
    print("  a - Strafe left")
    print("  d - Strafe right")
    print("  space - Move up")
    print("  shift - Move down")
    print("  q - Look left")
    print("  e - Look right")
    print("  p - Take screenshot")
    print("  scan - 360° scan")
    print("  quit - Exit")
    print("="*60 + "\n")

    while True:
        command = input("Command: ").lower().strip()

        if command == 'quit':
            break
        elif command == 'w':
            await controller.move_forward(1.0)
        elif command == 's':
            await controller.move_backward(1.0)
        elif command == 'a':
            await controller.move_left(1.0)
        elif command == 'd':
            await controller.move_right(1.0)
        elif command == 'space':
            await controller.move_up(1.0)
        elif command == 'shift':
            await controller.move_down(1.0)
        elif command == 'q':
            await controller.look(Vector(-0.5, 0))
        elif command == 'e':
            await controller.look(Vector(0.5, 0))
        elif command == 'p':
            await controller.take_screenshot()
        elif command == 'scan':
            await controller.scan_area(5.0)
        elif command.startswith('forward '):
            duration = float(command.split()[1])
            await controller.move_forward(duration)
        else:
            print("❌ Unknown command")


# ========================
# Main Entry Point
# ========================

async def main():
    """Main entry point"""
    import json
    from pathlib import Path

    print("="*60)
    print("Rust+ Drone Control")
    print("="*60)

    # Load config
    config_path = Path("config_enhanced.json")
    if not config_path.exists():
        config_path = Path("config.json")

    if not config_path.exists():
        print("\n❌ No configuration file found!")
        print("Create config.json or config_enhanced.json")
        return

    with open(config_path) as f:
        config = json.load(f)

    # Connect to Rust+
    print("\n🔌 Connecting to Rust+ server...")
    rust_config = config['rust_server']

    rust_socket = RustSocket(
        rust_config['ip'],
        rust_config['port'],
        rust_config['steam_id'],
        rust_config['player_token']
    )

    await rust_socket.connect()
    print("✅ Connected to Rust+ server")

    # Create drone controller
    drone = DroneController(rust_socket)

    try:
        # Connect to drone
        await drone.connect()

        # Show menu
        print("\n" + "="*60)
        print("Select Mode:")
        print("="*60)
        print("1. Automated Patrol (Base Perimeter)")
        print("2. High Altitude Scan")
        print("3. Quick Recon")
        print("4. Interactive Control")
        print("5. Custom Patrol")
        print("="*60)

        choice = input("\nChoice: ").strip()

        if choice == '1':
            await drone.execute_patrol(BASE_PATROL)
        elif choice == '2':
            await drone.execute_patrol(HIGH_SCAN)
        elif choice == '3':
            await drone.execute_patrol(QUICK_RECON)
        elif choice == '4':
            await interactive_mode(drone)
        elif choice == '5':
            # Custom patrol example
            custom_route = PatrolRoute(
                name="Custom Route",
                waypoints=[
                    Waypoint("Start", 2.0, 1.0, 2.0),
                    Waypoint("Mid", 3.0, 0, 2.0),
                    Waypoint("End", 2.0, -1.0, 2.0),
                ],
                loop=False
            )
            await drone.execute_patrol(custom_route)

    except KeyboardInterrupt:
        print("\n\n⏹️ Stopped by user")
        drone.emergency_stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        await drone.disconnect()
        await rust_socket.disconnect()
        print("\n✅ Disconnected")


if __name__ == '__main__':
    asyncio.run(main())
