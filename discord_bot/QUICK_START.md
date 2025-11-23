# ⚡ Quick Start - 5 Minute Setup

**Get your surveillance bot running in 5 minutes!**

---

## 📦 Installation (1 minute)

```bash
cd discord_bot
pip install -r requirements.txt
```

---

## ⚙️ Configuration (3 minutes)

### Run the Setup Wizard

```bash
python setup_wizard.py
```

Answer the questions:

1. **Discord bot token** → Get from [Discord Developer Portal](https://discord.com/developers/applications)
2. **Rust+ server IP** → From Rust+ app
3. **Steam ID** → Your 17-digit Steam ID
4. **Player token** → From FCM listener
5. **Camera IDs** → `drone`, `static1`, etc.

Done! Configuration saved to `config.json`

---

## 🚀 Start Bot (1 minute)

### 1. Invite Bot to Discord

Generate invite URL:
1. Go to Discord Developer Portal
2. OAuth2 → URL Generator
3. Select `bot` scope
4. Select permissions:
   - Manage Channels
   - Send Messages
   - Embed Links
   - Attach Files
5. Copy URL and invite bot

### 2. Start the Bot

```bash
python rustplus_bot.py
```

✅ **Done!** Check Discord for your surveillance channels!

---

## 🎯 Usage

### View Status
```
!status
```

### Control Camera
```
!control drone forward
!control drone fire
```

### Restart Camera
```
!restart drone
```

---

## 📺 What You Get

The bot will automatically:
1. ✅ Create `🎥 SURVEILLANCE` category
2. ✅ Create channel for each camera
3. ✅ Start streaming live feeds
4. ✅ Show player detection alerts

---

## 🆘 Problems?

### Bot won't start?
```bash
# Make sure config.json exists
ls config.json

# If not, run wizard again
python setup_wizard.py
```

### Can't connect to Rust+?
- Make sure you're connected to server in-game
- Get fresh player token (they expire)
- Close other Rust+ apps

### No channels created?
- Check bot has "Manage Channels" permission
- Re-invite bot with correct permissions

---

## 📚 Learn More

- **Full Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Features:** [README.md](README.md)
- **Help:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**That's it!** You now have 24/7 surveillance of your Rust base! 🎥

**Questions?** Join the Discord: https://discord.gg/nQqJe8qvP8
