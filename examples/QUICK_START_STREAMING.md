# Quick Start: Video Streaming

## 🎯 Choose Your Method

### Option 1: Web Dashboard (EASIEST) ⭐ RECOMMENDED

**Best for**: Private surveillance, multiple cameras, quick setup

```bash
# Install
pip install rustplus flask flask-socketio

# Edit web_dashboard_stream.py with your credentials
# Add your camera IDs: CAMERA_IDS = ["drone", "static1"]

# Run
python web_dashboard_stream.py

# Open in browser
http://localhost:5000
```

**What you get**:
- Beautiful web interface
- Multiple cameras in grid view
- Real-time updates (5 FPS)
- Control cameras from browser
- Works on phone/tablet
- Share URL with team: `http://YOUR_IP:5000`

---

### Option 2: YouTube Live (BEST QUALITY)

**Best for**: Team viewing, high quality, public streaming

```bash
# Install
pip install rustplus opencv-python ffmpeg-python

# Get YouTube stream key:
# 1. Go to youtube.com/live_dashboard
# 2. Copy stream key

# Run
python discord_video_stream.py
```

**In Discord**:
```
!stream youtube drone YOUR_STREAM_KEY
```

Bot replies with YouTube URL → Click to watch!

**What you get**:
- HD quality (up to 1080p)
- Unlimited viewers
- Works anywhere
- 10-30s delay
- Can record for later

---

### Option 3: Image Updates (SIMPLEST)

**Best for**: Low bandwidth, simple monitoring

```bash
# Already works from previous bot!
python discord_camera_bot.py
```

**In Discord**:
```
!camera start drone #surveillance
```

Images update every 0.5-2 seconds in Discord channel.

---

## 📊 Quick Comparison

| Feature | Web Dashboard | YouTube Live | Image Updates |
|---------|--------------|--------------|---------------|
| **Setup Time** | 5 minutes | 10 minutes | 2 minutes |
| **Video Quality** | Good (5-10 FPS) | Excellent (30+ FPS) | OK (1-3 FPS) |
| **Latency** | Low (1s) | Medium (15s) | Very Low (<1s) |
| **Viewers** | Your network | Unlimited | Unlimited |
| **Privacy** | Private | Unlisted | Discord only |
| **Cost** | Free | Free | Free |
| **Mobile** | ✅ Yes | ✅ Yes | ✅ Yes |

---

## 🚀 I Just Want to See My Camera NOW!

**Fastest way** (30 seconds):

```bash
# 1. Edit credentials in discord_camera_bot.py
# 2. Run:
python discord_camera_bot.py

# 3. In Discord:
!camera start drone
```

Done! Images appear in Discord.

---

## 💡 My Recommendation

**For surveillance**: Use **Web Dashboard**
- Run it on a computer/Raspberry Pi
- Access from anywhere via browser
- Multiple cameras at once
- Best experience

**For team viewing**: Use **YouTube Live**
- Everyone can watch
- No setup for viewers
- Good quality
- Easy to record

**For quick check**: Use **Image Updates**
- No dependencies
- Works right away
- Good enough for monitoring

---

## 🔧 Full Setup Example (Web Dashboard)

```bash
# 1. Install Python packages
pip install rustplus flask flask-socketio pillow

# 2. Edit web_dashboard_stream.py
nano web_dashboard_stream.py

# Change these lines:
RUST_SERVER_IP = "123.45.67.89"
RUST_SERVER_PORT = "28082"
RUST_STEAM_ID = "76561198012345678"
RUST_PLAYER_TOKEN = "1234567890"
CAMERA_IDS = ["drone", "static1", "static2"]

# 3. Run
python web_dashboard_stream.py

# 4. Open browser
http://localhost:5000

# 5. Share with team (find your IP first)
ifconfig  # or ipconfig on Windows
# Share: http://192.168.1.100:5000
```

---

## 🌐 Access from Phone/Other Devices

### On Same WiFi:

1. Find your computer's IP:
   - Linux/Mac: `ifconfig` or `ip addr`
   - Windows: `ipconfig`
   - Look for something like `192.168.1.100`

2. On phone browser, go to:
   ```
   http://192.168.1.100:5000
   ```

### From Internet (Requires Port Forwarding):

1. Forward port 5000 in your router settings
2. Get public IP from [whatismyip.com](https://whatismyip.com)
3. Access: `http://YOUR_PUBLIC_IP:5000`

⚠️ **Security**: Add authentication if exposing to internet!

---

## 🐛 Troubleshooting

### "Can't connect to Rust+ server"
- Check your server IP, port, Steam ID, player token
- Make sure you're connected to the Rust server in-game
- Player token expires when you leave server

### "Camera not found"
- Check camera ID (drone, static1, etc.)
- Make sure camera exists in-game
- You must have permission to view it

### "Page won't load"
- Check firewall isn't blocking port 5000
- Try `http://127.0.0.1:5000` instead of localhost
- Make sure script is running

### "Stream is laggy"
- Lower FPS: `FPS = 2` in script
- Check network connection
- Reduce number of cameras

---

## 📱 Mobile App Alternative

Want a mobile app instead? Consider:
1. Use web dashboard on mobile browser (works great!)
2. Or bookmark the YouTube Live URL
3. Or use Discord app with image updates

---

## ❓ FAQ

**Q: Can multiple people watch?**
A: Yes! All methods support unlimited viewers.

**Q: Do they need Rust+ app?**
A: No! Only you (running the bot) needs credentials.

**Q: Can I record?**
A: Yes! YouTube auto-records. For web dashboard, add screen recording.

**Q: Which method is best?**
A: Web Dashboard for private use, YouTube Live for team/public.

**Q: Does it work with turrets?**
A: Yes! You can control and fire through the camera.

**Q: How many cameras can I watch?**
A: Web Dashboard: Limited by your PC. YouTube: 1 per stream key. Image Updates: Many (uses Discord channels).

---

## 📚 Next Steps

1. **Try web dashboard first** - It's the easiest!
2. **Read full guide**: [VIDEO_STREAMING_GUIDE.md](./VIDEO_STREAMING_GUIDE.md)
3. **Check Discord bot**: [DISCORD_SURVEILLANCE_README.md](./DISCORD_SURVEILLANCE_README.md)
4. **Join Discord** for help: https://discord.gg/nQqJe8qvP8

---

**Ready to start?** Pick a method above and follow the steps! 🚀
