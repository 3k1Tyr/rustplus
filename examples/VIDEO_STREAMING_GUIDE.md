# Video Streaming Guide for Rust+ Cameras

## 🎥 The Problem

**Discord bots CANNOT natively stream video to text channels** like a regular user can.

Discord bots have these limitations:
- ❌ Can't use "Go Live" feature
- ❌ Can't screen share in voice channels
- ❌ Can't send video files to text channels in real-time
- ✅ Can only send/update images and files

## 💡 The Solutions

I've created **3 different approaches** for video streaming. Choose based on your needs:

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **YouTube Live** | ✅ Most reliable<br>✅ Unlimited viewers<br>✅ Works anywhere<br>✅ No setup needed | ⚠️ Public (unless unlisted)<br>⚠️ 10-30s delay | Public surveillance, team viewing |
| **Web Server (HLS)** | ✅ Private<br>✅ Low latency<br>✅ Full control | ⚠️ Requires port forwarding<br>⚠️ Limited viewers | Private surveillance, local network |
| **Image Updates** | ✅ Works in Discord<br>✅ No external tools<br>✅ Easy setup | ⚠️ Not true video<br>⚠️ Low FPS (1-3) | Simple monitoring, low bandwidth |

---

## 📺 Method 1: YouTube Live Streaming (RECOMMENDED)

### Why This Is Best
- ✅ **Most reliable** - YouTube handles all the heavy lifting
- ✅ **Unlimited viewers** - Entire Discord server can watch
- ✅ **No port forwarding** - Works from anywhere
- ✅ **Good quality** - 1080p at 30+ FPS possible
- ✅ **Embedding** - Can embed directly in Discord

### Setup Steps

#### 1. Enable YouTube Live Streaming

1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click "Go Live" (top right)
3. Enable live streaming (may require phone verification)
4. Wait 24 hours for activation (first time only)

#### 2. Get Your Stream Key

1. In YouTube Studio, go to "Go Live"
2. Select "Stream" tab (not webcam)
3. Copy your **Stream Key** (keep this SECRET!)
4. Set stream to "Unlisted" for privacy

#### 3. Configure and Run

```bash
pip install opencv-python ffmpeg-python

# Edit discord_video_stream.py with your credentials
python discord_video_stream.py
```

#### 4. Start Streaming

In Discord:
```
!stream youtube drone YOUR_STREAM_KEY
```

The bot will reply with your YouTube Live URL. Share this in Discord!

#### 5. Watch the Stream

- **In Discord**: Paste the YouTube URL and it auto-embeds
- **Mobile**: YouTube app works perfectly
- **Delay**: 10-30 seconds (normal for live streaming)

### Example Output

```
Bot: 🔴 YouTube Live Stream Started

Camera: drone is now streaming!

Watch Live: https://youtube.com/watch?v=abc123
Quality: 800x600 @ 10 FPS

Stream will appear live in 10-30 seconds
```

### Privacy Options

**Public**: Anyone can find and watch
```yaml
Privacy: Public
```

**Unlisted**: Only people with the link can watch (RECOMMENDED)
```yaml
Privacy: Unlisted
```

**Private**: Only you can watch (not useful for Discord)

### Advanced: Custom Resolution & FPS

Edit `discord_video_stream.py`:

```python
# For HD streaming
RESOLUTION = (1920, 1080)  # 1080p
TARGET_FPS = 30             # Smooth video

# For low bandwidth
RESOLUTION = (640, 480)     # 480p
TARGET_FPS = 15             # Acceptable quality
```

---

## 🌐 Method 2: Local Web Server (HLS)

### Why Use This
- ✅ **Private** - Only accessible on your network
- ✅ **Low latency** - 2-5 second delay
- ✅ **Full control** - Your server, your rules

### Setup Steps

#### 1. Install Dependencies

```bash
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

pip install opencv-python ffmpeg-python
```

#### 2. Start HLS Stream

```bash
python discord_video_stream.py
```

In Discord:
```
!stream web drone 8080
```

Bot replies:
```
🌐 Web Stream Started

Stream URL: http://localhost:8080/stream.m3u8

How to Watch: Open in VLC or HLS player
```

#### 3. Watch the Stream

**Option A: VLC Player**
1. Download [VLC](https://www.videolan.org/)
2. Open Network Stream: `Media → Open Network Stream`
3. Paste: `http://YOUR_IP:8080/stream.m3u8`
4. Click Play

**Option B: Web Browser** (with HLS.js)

Create `player.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Rust+ Camera Stream</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
</head>
<body>
    <video id="video" controls width="800"></video>
    <script>
        var video = document.getElementById('video');
        var videoSrc = 'http://localhost:8080/stream.m3u8';

        if (Hls.isSupported()) {
            var hls = new Hls();
            hls.loadSource(videoSrc);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, function() {
                video.play();
            });
        }
    </script>
</body>
</html>
```

Open `player.html` in browser - stream will play!

**Option C: OBS Studio**

1. Add "Media Source"
2. Input: `http://localhost:8080/stream.m3u8`
3. Now you can record, restream, or add overlays

#### 4. Access from Other Devices

**On Same Network**: Replace `localhost` with your computer's IP

```
http://192.168.1.100:8080/stream.m3u8
```

Find your IP:
- Linux/Mac: `ifconfig` or `ip addr`
- Windows: `ipconfig`

**From Internet** (requires port forwarding):

1. Forward port 8080 on your router
2. Get public IP from [whatismyip.com](https://www.whatismyip.com)
3. Use: `http://YOUR_PUBLIC_IP:8080/stream.m3u8`

⚠️ **Security Warning**: Don't expose without authentication!

---

## 📸 Method 3: Image Updates (Fallback)

If you can't use video streaming, the image update method from the previous bot works well:

```python
# From discord_camera_bot.py
!camera start drone #surveillance
```

**Optimizing for "Video-like" Experience:**

```python
# In discord_camera_bot.py, increase FPS
STREAM_FPS = 3  # Max recommended for Discord (rate limits at ~5/second)
UPDATE_INTERVAL = 1.0 / STREAM_FPS
```

This gives you 3 FPS, which is decent for surveillance (not smooth video, but watchable).

---

## 🚀 Comparison Table

| Feature | YouTube Live | HLS Web Server | Image Updates |
|---------|--------------|----------------|---------------|
| **FPS** | 30+ | 10-30 | 1-3 |
| **Resolution** | Up to 1080p | Up to 1080p | Any |
| **Latency** | 10-30s | 2-5s | <1s |
| **Setup Difficulty** | Easy | Medium | Very Easy |
| **Viewers** | Unlimited | 10-20 | Unlimited |
| **Privacy** | Unlisted option | Fully private | Discord only |
| **Bandwidth** | High | Medium | Low |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 Recommendations by Use Case

### 1. Team Surveillance (Multiple Viewers)
**Use: YouTube Live (Unlisted)**
- Easy for everyone to watch
- Works on mobile
- No technical knowledge needed

### 2. Private Monitoring (Just You)
**Use: HLS Web Server**
- Keep it on your local network
- Low latency
- Full control

### 3. Low Bandwidth / Simple Setup
**Use: Image Updates**
- Already works with previous bot
- No extra dependencies
- Discord rate limit friendly

### 4. Recording for Evidence
**Use: YouTube Live or HLS + OBS**
- YouTube auto-saves streams
- OBS can record HLS streams
- Easy playback later

---

## 🛠️ Troubleshooting

### YouTube Stream Not Appearing

**Problem**: Bot says streaming but YouTube shows "Offline"

**Solutions**:
1. Wait 30 seconds - YouTube needs time to process
2. Check your stream key is correct
3. Make sure live streaming is enabled on your account
4. Verify FFmpeg is installed: `ffmpeg -version`

### High CPU Usage

**Problem**: Computer slowing down during stream

**Solutions**:
1. Lower resolution: `RESOLUTION = (640, 480)`
2. Lower FPS: `TARGET_FPS = 15`
3. Use hardware encoding (if available):
   ```python
   '-c:v', 'h264_nvenc',  # NVIDIA GPU
   '-c:v', 'h264_qsv',    # Intel GPU
   ```

### Stream Stuttering

**Problem**: Video is laggy or freezes

**Solutions**:
1. Check your internet upload speed (need 3-5 Mbps for HD)
2. Lower bitrate in FFmpeg settings
3. Reduce FPS or resolution
4. Ensure Rust+ server connection is stable

### HLS Stream Not Playing

**Problem**: VLC or browser can't open stream

**Solutions**:
1. Check FFmpeg is running: `ps aux | grep ffmpeg`
2. Verify files exist: `ls ./stream/`
3. Try opening `stream.m3u8` directly in VLC
4. Check firewall isn't blocking port 8080

### Discord Rate Limiting (Image Method)

**Problem**: Bot stops updating images

**Solutions**:
1. Lower FPS to 2: `STREAM_FPS = 2`
2. Bot automatically backs off - wait a minute
3. Use video streaming instead of image updates

---

## 💻 Complete Working Example

Here's a complete setup for YouTube Live:

### 1. Install Requirements

```bash
# System dependencies
sudo apt update
sudo apt install ffmpeg python3-pip

# Python packages
pip install discord.py rustplus opencv-python numpy
```

### 2. Run the Bot

```bash
# Edit configuration
nano discord_video_stream.py

# Add your tokens:
# - DISCORD_TOKEN
# - RUST_SERVER_IP, PORT, STEAM_ID, PLAYER_TOKEN
# - YouTube stream key

# Run
python discord_video_stream.py
```

### 3. In Discord

```
# Start camera
!stream youtube drone YOUR_YOUTUBE_STREAM_KEY

# Bot responds with YouTube URL
# Click the URL to watch!

# Stop when done
!stopstream drone
```

### 4. Share with Team

Post the YouTube URL in Discord:
```
🔴 LIVE: Base Surveillance
https://youtube.com/watch?v=abc123

Watching drone camera feed
```

Everyone on your Discord can now watch the live stream!

---

## 🎬 Next Steps

1. **Try YouTube Live first** - It's the easiest and most reliable
2. **Get a YouTube account** ready with live streaming enabled
3. **Test with low settings** first (480p, 15 FPS)
4. **Increase quality** once stable
5. **Set up multiple cameras** using different stream keys

## 📚 Resources

- [YouTube Live Streaming Guide](https://support.google.com/youtube/answer/2474026)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [HLS Streaming Protocol](https://developer.apple.com/streaming/)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook) (for notifications)

## ⚠️ Important Notes

1. **Discord bots can't do native video** - Use external services
2. **YouTube is the easiest** - Recommended for most users
3. **Bandwidth matters** - HD streaming needs good internet
4. **Camera subscriptions expire** - Bot handles auto-resubscribe
5. **Rate limits** - Don't spam streams on/off

---

**Questions?** Check the [main Discord bot README](./DISCORD_SURVEILLANCE_README.md) or ask in the Rust+ Discord!
