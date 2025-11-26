"""
Camera Detection System

Features:
1. Distance measurement and smart switch triggers
2. SQLite database for tracking detected players
"""

import asyncio
import logging
import math
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger('camera_detection')


# ========================
# Data Structures
# ========================

@dataclass
class DetectedEntity:
    """Represents a detected entity from camera"""
    entity_id: int
    name: str
    entity_type: int
    distance: float
    position_x: float
    position_y: float
    position_z: float
    timestamp: float
    is_team_member: bool


@dataclass
class DistanceTrigger:
    """Distance-based trigger configuration"""
    trigger_id: int
    camera_id: str
    detection_count: int  # Trigger on Nth detection
    distance_threshold: float  # Distance in meters
    switch_name: str
    switch_entity_id: int
    enabled: bool = True


# ========================
# Detection Database
# ========================

class DetectionDatabase:
    """SQLite database for tracking camera detections"""

    def __init__(self, db_path: str = "camera_detections.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._setup_database()

    def _setup_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Detections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                camera_id TEXT NOT NULL,
                entity_id INTEGER,
                player_name TEXT,
                entity_type INTEGER,
                distance REAL NOT NULL,
                position_x REAL,
                position_y REAL,
                position_z REAL,
                is_team_member INTEGER NOT NULL,
                triggered_switch TEXT
            )
        """)

        # Triggers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT NOT NULL,
                detection_count INTEGER NOT NULL,
                distance_threshold REAL NOT NULL,
                switch_name TEXT NOT NULL,
                switch_entity_id INTEGER NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at REAL NOT NULL,
                UNIQUE(camera_id, detection_count)
            )
        """)

        # Trigger activations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trigger_activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                camera_id TEXT NOT NULL,
                player_name TEXT,
                distance REAL NOT NULL,
                success INTEGER NOT NULL,
                FOREIGN KEY (trigger_id) REFERENCES triggers(id)
            )
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_timestamp
            ON detections(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_camera
            ON detections(camera_id, timestamp DESC)
        """)

        self.conn.commit()
        logger.info(f"Detection database initialized: {self.db_path}")

    def log_detection(self, camera_id: str, entity: DetectedEntity,
                     triggered_switch: Optional[str] = None):
        """Log a detection to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO detections
            (timestamp, camera_id, entity_id, player_name, entity_type,
             distance, position_x, position_y, position_z, is_team_member, triggered_switch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.timestamp,
            camera_id,
            entity.entity_id,
            entity.name,
            entity.entity_type,
            entity.distance,
            entity.position_x,
            entity.position_y,
            entity.position_z,
            1 if entity.is_team_member else 0,
            triggered_switch
        ))
        self.conn.commit()

    def add_trigger(self, camera_id: str, detection_count: int,
                   distance_threshold: float, switch_name: str,
                   switch_entity_id: int) -> int:
        """Add a new distance trigger"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO triggers
            (camera_id, detection_count, distance_threshold, switch_name,
             switch_entity_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (camera_id, detection_count, distance_threshold, switch_name,
              switch_entity_id, time.time()))
        self.conn.commit()
        return cursor.lastrowid

    def get_triggers(self, camera_id: Optional[str] = None,
                    enabled_only: bool = True) -> List[DistanceTrigger]:
        """Get all triggers, optionally filtered by camera"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM triggers WHERE 1=1"
        params = []

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        if enabled_only:
            query += " AND enabled = 1"

        query += " ORDER BY camera_id, detection_count"

        cursor.execute(query, params)

        triggers = []
        for row in cursor.fetchall():
            triggers.append(DistanceTrigger(
                trigger_id=row[0],
                camera_id=row[1],
                detection_count=row[2],
                distance_threshold=row[3],
                switch_name=row[4],
                switch_entity_id=row[5],
                enabled=bool(row[6])
            ))

        return triggers

    def disable_trigger(self, trigger_id: int):
        """Disable a trigger"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE triggers SET enabled = 0 WHERE id = ?", (trigger_id,))
        self.conn.commit()

    def log_trigger_activation(self, trigger_id: int, camera_id: str,
                               player_name: str, distance: float, success: bool):
        """Log when a trigger is activated"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trigger_activations
            (trigger_id, timestamp, camera_id, player_name, distance, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (trigger_id, time.time(), camera_id, player_name, distance, 1 if success else 0))
        self.conn.commit()

    def get_recent_detections(self, camera_id: Optional[str] = None,
                             limit: int = 50,
                             enemies_only: bool = False) -> List[Dict]:
        """Get recent detections"""
        cursor = self.conn.cursor()

        query = """
            SELECT timestamp, camera_id, player_name, distance,
                   is_team_member, triggered_switch
            FROM detections
            WHERE 1=1
        """
        params = []

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        if enemies_only:
            query += " AND is_team_member = 0"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        detections = []
        for row in cursor.fetchall():
            detections.append({
                'timestamp': datetime.fromtimestamp(row[0]),
                'camera_id': row[1],
                'player_name': row[2] or 'Unknown',
                'distance': row[3],
                'is_team_member': bool(row[4]),
                'triggered_switch': row[5]
            })

        return detections

    def get_stats(self, camera_id: Optional[str] = None) -> Dict:
        """Get detection statistics"""
        cursor = self.conn.cursor()

        where_clause = ""
        params = []
        if camera_id:
            where_clause = "WHERE camera_id = ?"
            params = [camera_id]

        cursor.execute(f"""
            SELECT
                COUNT(*) as total_detections,
                COUNT(DISTINCT player_name) as unique_players,
                AVG(distance) as avg_distance,
                MIN(distance) as min_distance,
                MAX(distance) as max_distance,
                SUM(CASE WHEN is_team_member = 0 THEN 1 ELSE 0 END) as enemy_detections
            FROM detections
            {where_clause}
        """, params)

        row = cursor.fetchone()
        return {
            'total_detections': row[0],
            'unique_players': row[1],
            'avg_distance': round(row[2], 2) if row[2] else 0,
            'min_distance': round(row[3], 2) if row[3] else 0,
            'max_distance': round(row[4], 2) if row[4] else 0,
            'enemy_detections': row[5]
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ========================
# Camera Detection Manager
# ========================

class CameraDetectionManager:
    """Manages distance-based detection and triggers for cameras"""

    def __init__(self, rust_socket, switch_manager, database: DetectionDatabase):
        self.rust_socket = rust_socket
        self.switch_manager = switch_manager
        self.database = database

        # Tracking
        self.camera_detections: Dict[str, List[DetectedEntity]] = {}
        self.session_detection_counts: Dict[str, int] = {}  # Per-camera enemy count
        self.known_team_members: Set[str] = set()

        # Configuration
        self.triggers: Dict[str, List[DistanceTrigger]] = {}  # camera_id -> triggers

        # Polling
        self.update_interval = 2.0  # seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the detection manager"""
        logger.info("Starting camera detection manager...")

        # Load triggers from database
        self.triggers = {}
        for trigger in self.database.get_triggers():
            if trigger.camera_id not in self.triggers:
                self.triggers[trigger.camera_id] = []
            self.triggers[trigger.camera_id].append(trigger)

        logger.info(f"Loaded {sum(len(t) for t in self.triggers.values())} triggers")

        # Start update loop
        self._running = True
        self._task = asyncio.create_task(self._update_loop())

    async def stop(self):
        """Stop the detection manager"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _update_loop(self):
        """Main detection update loop"""
        while self._running:
            try:
                await self._update_team_info()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in detection update loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _update_team_info(self):
        """Update cached team member names"""
        try:
            team_info = await self.rust_socket.get_team_info()
            if hasattr(team_info, 'members'):
                self.known_team_members = {member.name for member in team_info.members}
                logger.debug(f"Updated team members: {self.known_team_members}")
        except Exception as e:
            logger.warning(f"Failed to update team info: {e}")

    def calculate_distance(self, pos1_x: float, pos1_y: float, pos1_z: float,
                          pos2_x: float = 0, pos2_y: float = 0, pos2_z: float = 0) -> float:
        """Calculate 3D distance between two points"""
        dx = pos1_x - pos2_x
        dy = pos1_y - pos2_y
        dz = pos1_z - pos2_z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    async def process_camera_frame(self, camera_id: str, entities: List,
                                   camera_position: Optional[tuple] = None):
        """
        Process camera entities and check for triggers

        Args:
            camera_id: ID of the camera
            entities: List of Entity objects from AppCameraRays
            camera_position: Optional (x, y, z) tuple for camera position
        """
        if not entities:
            return

        current_time = time.time()
        detected_entities = []

        for entity in entities:
            # Skip if no name (probably not a player)
            if not entity.name:
                continue

            # Calculate distance from camera (or origin if camera pos unknown)
            if camera_position:
                distance = self.calculate_distance(
                    entity.position.x, entity.position.y, entity.position.z,
                    camera_position[0], camera_position[1], camera_position[2]
                )
            else:
                # Distance from origin
                distance = self.calculate_distance(
                    entity.position.x, entity.position.y, entity.position.z
                )

            # Check if team member
            is_team = entity.name in self.known_team_members

            detected = DetectedEntity(
                entity_id=entity.entity_id,
                name=entity.name,
                entity_type=entity.type,
                distance=distance,
                position_x=entity.position.x,
                position_y=entity.position.y,
                position_z=entity.position.z,
                timestamp=current_time,
                is_team_member=is_team
            )

            detected_entities.append(detected)

            # Log non-team members to database
            if not is_team:
                self.database.log_detection(camera_id, detected)
                logger.info(f"Enemy detected on {camera_id}: {entity.name} at {distance:.1f}m")

        # Update camera detections
        self.camera_detections[camera_id] = detected_entities

        # Check triggers for enemies only
        await self._check_triggers(camera_id,
                                   [e for e in detected_entities if not e.is_team_member])

    async def _check_triggers(self, camera_id: str, enemy_entities: List[DetectedEntity]):
        """Check if any triggers should fire"""
        if camera_id not in self.triggers:
            return

        if camera_id not in self.session_detection_counts:
            self.session_detection_counts[camera_id] = 0

        # Sort by distance (closest first)
        enemy_entities.sort(key=lambda e: e.distance)

        for idx, entity in enumerate(enemy_entities, start=1):
            detection_num = self.session_detection_counts[camera_id] + idx

            # Check each trigger for this detection count
            for trigger in self.triggers[camera_id]:
                if not trigger.enabled:
                    continue

                if trigger.detection_count == detection_num:
                    # Check distance threshold
                    if entity.distance <= trigger.distance_threshold:
                        await self._activate_trigger(trigger, camera_id, entity)

        # Update detection count
        self.session_detection_counts[camera_id] += len(enemy_entities)

    async def _activate_trigger(self, trigger: DistanceTrigger,
                                camera_id: str, entity: DetectedEntity):
        """Activate a trigger (turn on switch)"""
        logger.info(
            f"TRIGGER ACTIVATED: {camera_id} detection #{trigger.detection_count} "
            f"- {entity.name} at {entity.distance:.1f}m → {trigger.switch_name}"
        )

        success = False
        try:
            # Activate the switch
            if self.switch_manager:
                success = await self.switch_manager.toggle_switch(trigger.switch_name, True)
                if success:
                    logger.info(f"✅ Switch '{trigger.switch_name}' activated")
                else:
                    logger.error(f"❌ Failed to activate switch '{trigger.switch_name}'")
        except Exception as e:
            logger.error(f"Error activating trigger: {e}", exc_info=True)

        # Log trigger activation
        self.database.log_trigger_activation(
            trigger.trigger_id, camera_id, entity.name, entity.distance, success
        )

        # Update detection log with triggered switch
        self.database.log_detection(camera_id, entity, trigger.switch_name)

    def get_current_detections(self, camera_id: Optional[str] = None) -> Dict:
        """Get current detections for display"""
        if camera_id:
            return {camera_id: self.camera_detections.get(camera_id, [])}
        return self.camera_detections

    def reset_detection_counts(self, camera_id: Optional[str] = None):
        """Reset detection counts for camera(s)"""
        if camera_id:
            self.session_detection_counts[camera_id] = 0
            logger.info(f"Reset detection count for {camera_id}")
        else:
            self.session_detection_counts.clear()
            logger.info("Reset all detection counts")

    async def add_trigger(self, camera_id: str, detection_count: int,
                         distance_threshold: float, switch_name: str) -> bool:
        """Add a new distance trigger"""
        # Get switch entity ID
        if not self.switch_manager or switch_name not in self.switch_manager.switches:
            logger.error(f"Switch '{switch_name}' not found")
            return False

        switch_entity_id = self.switch_manager.switches[switch_name]

        # Add to database
        trigger_id = self.database.add_trigger(
            camera_id, detection_count, distance_threshold,
            switch_name, switch_entity_id
        )

        # Add to runtime cache
        trigger = DistanceTrigger(
            trigger_id=trigger_id,
            camera_id=camera_id,
            detection_count=detection_count,
            distance_threshold=distance_threshold,
            switch_name=switch_name,
            switch_entity_id=switch_entity_id,
            enabled=True
        )

        if camera_id not in self.triggers:
            self.triggers[camera_id] = []
        self.triggers[camera_id].append(trigger)

        logger.info(
            f"Added trigger: {camera_id} detection #{detection_count} "
            f"at {distance_threshold}m → {switch_name}"
        )
        return True
