# Camera System - Potential Improvements

## Critical Issues

### 1. **Manual Subscription Management** (High Priority)
**Current Issue**: Subscriptions expire every ~15 seconds and require manual resubscription.

**Location**: `camera_manager.py:151-162`

**Current Code**:
```python
# User must manually call this every 10-15 seconds
if time.time() - camera_manager.time_since_last_subscribe > 10:
    await camera_manager.resubscribe()
```

**Proposed Improvement**: Auto-resubscription with background task
```python
class CameraManager:
    def __init__(self, ...):
        # ... existing code ...
        self._auto_resubscribe_task = None
        self._subscription_interval = 10  # configurable

    async def _auto_resubscribe_loop(self):
        """Background task to auto-resubscribe"""
        while self._open:
            await asyncio.sleep(self._subscription_interval)
            if self._open:
                try:
                    await self.resubscribe()
                except Exception as e:
                    # Log error, optionally notify via callback
                    if self.on_subscription_error:
                        await self.on_subscription_error(e)

    async def start_auto_resubscribe(self, interval: float = 10):
        """Enable automatic resubscription"""
        self._subscription_interval = interval
        if self._auto_resubscribe_task is None:
            self._auto_resubscribe_task = asyncio.create_task(
                self._auto_resubscribe_loop()
            )

    async def stop_auto_resubscribe(self):
        """Stop automatic resubscription"""
        if self._auto_resubscribe_task:
            self._auto_resubscribe_task.cancel()
            try:
                await self._auto_resubscribe_task
            except asyncio.CancelledError:
                pass
```

**Benefits**:
- Eliminates manual resubscription code
- Prevents accidental disconnections
- Cleaner user code

---

### 2. **Single Camera Limitation** (High Priority)
**Current Issue**: Only ONE camera can be active at once due to class-level singleton.

**Location**: `camera_manager.py:21, 36`

**Current Code**:
```python
class CameraManager:
    ACTIVE_INSTANCE: Union["CameraManager", None] = None  # SINGLETON!

    def __init__(self, ...):
        # ...
        CameraManager.ACTIVE_INSTANCE = self  # Overwrites previous!
```

**WebSocket routing** (`ws.py:258-261`):
```python
if CameraManager.ACTIVE_INSTANCE is not None:
    await CameraManager.ACTIVE_INSTANCE.add_packet(
        app_message.broadcast.camera_rays
    )
```

**Proposed Improvement**: Multi-camera support with camera ID routing
```python
class CameraManager:
    ACTIVE_INSTANCES: Dict[str, "CameraManager"] = {}  # Key: camera_id

    def __init__(self, rust_socket, cam_id: str, cam_info_message: AppCameraInfo):
        self._cam_id = cam_id
        # ... existing code ...
        CameraManager.ACTIVE_INSTANCES[cam_id] = self

    @classmethod
    def get_instance(cls, cam_id: str) -> Optional["CameraManager"]:
        """Get camera manager by ID"""
        return cls.ACTIVE_INSTANCES.get(cam_id)

    async def exit_camera(self):
        """Cleanup and remove from registry"""
        # ... existing cleanup ...
        if self._cam_id in CameraManager.ACTIVE_INSTANCES:
            del CameraManager.ACTIVE_INSTANCES[self._cam_id]
```

**WebSocket update** (`ws.py`):
```python
# Need to extract camera_id from the broadcast message
camera_id = app_message.broadcast.camera_rays.camera_id  # May need proto update
if camera_id in CameraManager.ACTIVE_INSTANCES:
    await CameraManager.ACTIVE_INSTANCES[camera_id].add_packet(
        app_message.broadcast.camera_rays
    )
```

**Benefits**:
- Monitor multiple cameras simultaneously (e.g., drone + CCTV)
- More flexible camera management
- Prevents accidental overwrites

---

### 3. **No Error Handling** (High Priority)
**Current Issue**: No handling for network errors, corrupted packets, or timeouts.

**Location**: `camera_manager.py:38-47`

**Current Code**:
```python
async def add_packet(self, packet: AppCameraRays) -> None:
    self._last_packets.add(packet)
    # No validation!
    # No error handling!
    # Assumes packet is always valid
```

**Proposed Improvement**: Comprehensive error handling
```python
class CameraManager:
    def __init__(self, ...):
        # ... existing code ...
        self.on_error_callback: Optional[Callable] = None
        self.packet_timeout = 5.0  # seconds
        self.last_packet_time = time.time()
        self._error_count = 0

    async def add_packet(self, packet: AppCameraRays) -> None:
        """Add packet with validation and error handling"""
        try:
            # Validate packet
            if packet is None:
                raise ValueError("Received null camera packet")

            if not hasattr(packet, 'ray_data') or len(packet.ray_data) == 0:
                raise ValueError("Invalid or empty ray data")

            # Check timeout
            current_time = time.time()
            if current_time - self.last_packet_time > self.packet_timeout:
                if self.on_error_callback:
                    await self.on_error_callback(
                        CameraTimeoutError(f"No packets for {self.packet_timeout}s")
                    )

            self.last_packet_time = current_time
            self._error_count = 0  # Reset on success

            # Add packet
            self._last_packets.add(packet)

            # Process callbacks
            if len(self.frame_callbacks) > 0:
                frame = await self._create_frame()
                if frame is None:
                    raise ValueError("Failed to create frame from packet")

                for callback in self.frame_callbacks:
                    try:
                        await callback(frame)
                    except Exception as e:
                        # Don't let callback errors break the stream
                        if self.on_error_callback:
                            await self.on_error_callback(e)

        except Exception as e:
            self._error_count += 1
            if self.on_error_callback:
                await self.on_error_callback(e)

            # Auto-reconnect after multiple errors
            if self._error_count > 5:
                await self._handle_connection_failure()
```

---

### 4. **Memory Leaks** (Medium Priority)
**Current Issue**: Frame callbacks are never cleaned up, LimitedQueue size is hardcoded.

**Location**: `camera_manager.py:35, 52`

**Current Code**:
```python
self.frame_callbacks: Set[Callable[[Image.Image], Coroutine]] = set()

def on_frame_received(self, coro):
    self.frame_callbacks.add(coro)  # Never removed!
    return coro
```

**Proposed Improvement**: Callback lifecycle management
```python
class CameraManager:
    def on_frame_received(self, coro):
        """Add callback and return removal function"""
        self.frame_callbacks.add(coro)

        # Return cleanup function
        def remove_callback():
            self.frame_callbacks.discard(coro)

        return coro, remove_callback

    def remove_frame_callback(self, coro):
        """Manually remove a callback"""
        self.frame_callbacks.discard(coro)

    def clear_all_callbacks(self):
        """Remove all callbacks"""
        self.frame_callbacks.clear()

# Usage:
@camera_manager.on_frame_received
async def handler(frame):
    pass

callback, remove = handler
# Later:
remove()  # Clean up
```

---

### 5. **Performance Issues** (Medium Priority)

#### 5a. Sequential Packet Processing
**Location**: `camera_manager.py:73-75`

**Current Code**:
```python
# Processes ALL queued packets sequentially
for i in range(len(self._last_packets)):
    self.parser.handle_camera_ray_data(self._last_packets.get(i))
    self.parser.step()  # Blocking, processes all rays
```

**Issue**: If 6 packets are queued, this processes 6 full frames worth of ray data.

**Proposed Improvement**: Process only necessary packets
```python
async def _create_frame(self, ...):
    if not self._last_packets or len(self._last_packets) == 0:
        return None

    # Only process packets since last render
    # OR just process the latest if incremental updates aren't needed
    latest_packet = self._last_packets.get_last()

    # If ray data is incremental (sample_offset based):
    for packet in self._last_packets:
        self.parser.handle_camera_ray_data(packet)
        self.parser.step()

    # If ray data is complete per packet:
    self.parser.handle_camera_ray_data(latest_packet)
    self.parser.step()

    # Clear processed packets
    self._last_packets.clear()
    self._last_packets.add(latest_packet)
```

#### 5b. Ray Decompression Not Vectorized
**Location**: `camera_parser.py:130-200`

**Current Code**: Processes rays one byte at a time in pure Python

**Proposed Improvement**: Use numpy for batch processing
```python
# Pre-compile common operations
# Use numpy array operations instead of loops
# Consider Cython or numba for critical path
```

#### 5c. Entity Rendering Inefficiency
**Location**: `camera_parser.py:236`

**Current Code**:
```python
random.shuffle(trees)  # Shuffles every frame!
target_trees += trees[:tree_amount - len(target_trees)]
```

**Proposed Improvement**: Cache tree selection, only reshuffle when FOV changes significantly
```python
if abs(self.last_fov - cam_fov) > 5.0:  # Only shuffle on big FOV changes
    random.shuffle(trees)
    self.last_fov = cam_fov
```

---

### 6. **No Frame Rate Control** (Low Priority)
**Current Issue**: Processes every packet immediately, no FPS limiting.

**Proposed Improvement**: Add frame rate limiting
```python
class CameraManager:
    def __init__(self, ...):
        self.target_fps = 30
        self.last_frame_time = 0
        self.frame_interval = 1.0 / self.target_fps

    async def add_packet(self, packet: AppCameraRays):
        self._last_packets.add(packet)

        # Frame rate limiting
        current_time = time.time()
        if current_time - self.last_frame_time < self.frame_interval:
            return  # Skip this frame

        self.last_frame_time = current_time

        # Process callbacks...
```

---

### 7. **No Video Recording Support** (Low Priority)
**Current Issue**: Only individual frame saves, no built-in video streaming.

**Proposed Improvement**: Add video recording capability
```python
import cv2

class CameraManager:
    def __init__(self, ...):
        self._video_writer = None
        self._recording = False

    def start_recording(self, filename: str, fps: int = 30):
        """Start recording camera feed to video file"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        width = self._cam_info_message.width * self.parser.scale_factor
        height = self._cam_info_message.height * self.parser.scale_factor

        self._video_writer = cv2.VideoWriter(
            filename, fourcc, fps, (width, height)
        )
        self._recording = True

    def stop_recording(self):
        """Stop video recording"""
        if self._video_writer:
            self._video_writer.release()
            self._video_writer = None
        self._recording = False

    async def add_packet(self, packet: AppCameraRays):
        # ... existing code ...

        if self._recording and self._video_writer:
            frame_array = np.array(frame.convert('RGB'))
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            self._video_writer.write(frame_bgr)
```

---

### 8. **No Metrics/Monitoring** (Low Priority)
**Current Issue**: No FPS tracking, latency metrics, or packet loss detection.

**Proposed Improvement**: Add performance metrics
```python
class CameraMetrics:
    def __init__(self):
        self.frame_count = 0
        self.packet_count = 0
        self.dropped_packets = 0
        self.avg_frame_time = 0
        self.last_seq_number = 0
        self.start_time = time.time()

    def get_fps(self) -> float:
        elapsed = time.time() - self.start_time
        return self.frame_count / elapsed if elapsed > 0 else 0

    def get_packet_loss_rate(self) -> float:
        total = self.packet_count + self.dropped_packets
        return self.dropped_packets / total if total > 0 else 0

class CameraManager:
    def __init__(self, ...):
        self.metrics = CameraMetrics()

    def get_performance_stats(self) -> dict:
        return {
            'fps': self.metrics.get_fps(),
            'packet_loss': self.metrics.get_packet_loss_rate(),
            'frames_rendered': self.metrics.frame_count,
            'avg_frame_time_ms': self.metrics.avg_frame_time * 1000,
        }
```

---

## Summary of Improvements by Priority

### High Priority
1. ✅ **Auto-resubscription** - Prevents disconnections
2. ✅ **Multi-camera support** - Remove singleton limitation
3. ✅ **Error handling** - Network resilience, validation

### Medium Priority
4. ✅ **Memory management** - Callback cleanup, configurable buffers
5. ✅ **Performance optimization** - Vectorized operations, efficient rendering

### Low Priority
6. ✅ **Frame rate control** - CPU usage optimization
7. ✅ **Video recording** - Built-in recording support
8. ✅ **Metrics** - FPS tracking, latency monitoring

---

## Implementation Effort Estimates

| Improvement | Lines of Code | Complexity | Impact |
|-------------|---------------|------------|--------|
| Auto-resubscription | ~30 | Low | High |
| Multi-camera support | ~50 | Medium | High |
| Error handling | ~80 | Medium | High |
| Callback lifecycle | ~20 | Low | Medium |
| Performance optimization | ~100 | High | Medium |
| Frame rate control | ~15 | Low | Low |
| Video recording | ~40 | Low | Medium |
| Metrics | ~50 | Low | Low |

**Total estimated effort**: ~385 lines of code, 1-2 days of development

---

## Backward Compatibility

All improvements can be implemented with backward compatibility:
- Auto-resubscription: opt-in via `start_auto_resubscribe()`
- Multi-camera: existing code continues to work, new API for multiple cameras
- Error handling: existing code unaffected, new callbacks optional
- Other features: all opt-in via new methods
