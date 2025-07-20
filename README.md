# 🚀 AERO-V10 TERMINAL CHAT SYSTEM

<p align="center">
  <img src="https://img.shields.io/badge/Built%20with-Termux-orange?style=for-the-badge&logo=gnu-bash" alt="Termux">
  <img src="https://img.shields.io/badge/WebSocket-Realtime-blue?style=for-the-badge&logo=websocket" alt="WebSocket">
  <img src="https://img.shields.io/badge/Streaming-YouTube%20%26%20Radio-red?style=for-the-badge&logo=mpv" alt="Streaming">
  <img src="https://img.shields.io/github/stars/YOCRRZ224/AERO-V10-terminal-chat?style=for-the-badge&logo=github&label=Stars" alt="Stars">
  <img src="https://img.shields.io/github/forks/YOCRRZ224/AERO-V10-terminal-chat?style=for-the-badge&logo=github&label=Forks" alt="Forks">
  <img src="https://img.shields.io/github/license/YOCRRZ224/AERO-V10-terminal-chat?style=for-the-badge&color=blueviolet" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Terminal-Chat%20System-green?style=flat-square&logo=gnubash" alt="Terminal">
  <img src="https://img.shields.io/badge/Python-3.11+-yellow?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/NGROK-Integrated-brightgreen?style=flat-square&logo=ngrok" alt="ngrok">
  <img src="https://img.shields.io/github/last-commit/YOCRRZ224/AERO-V10-terminal-chat?style=flat-square&logo=git" alt="Last Commit">
  
</p>

  
---
## WAIT WAIT THIS PROJECT IS UNDER DEVLOPMENT CURRENTLY i am working on ngrok and wss so wait some time (but u can try the project many things soon)

## 📸 Live Preview

> _(Replace these with screenshots or terminal gifs)_

| Server UI Banner | Styled Client |
|------------------|---------------|
| ![Server](docs/server_ui.png) | ![Client](docs/client_ui.png) |

---

## ✨ Dynamic Features

| Feature                    | Status ✅ | Description                                                             |
|---------------------------|----------|-------------------------------------------------------------------------|
| Realtime WebSocket Chat   | ✅       | Connects multiple clients using async Python sockets                    |
| Role-Based Access         | ✅       | IP-based Admin/Mod/Client control system                                |
| Music Streaming (YouTube) | ✅       | `!play <song>` via `yt-dlp` + `mpv`                                     |
| Radio Stations            | ✅       | `!stations` & `!playstation <num>` using public internet radio URLs     |
| Music Queue               | ✅       | `/queue` to display currently queued tracks                             |
| Task Management           | ✅       | `/newwork`, `/work`, `/remwork` with persistent storage in JSON         |
| Emoji Shortcodes          | ✅       | `:fire:` → 🔥, `:zap:` → ⚡ etc.                                          |
| Custom Nickname + Colors  | ✅       | `/nick`, `/color` command to personalize client name                    |
| Ngrok Integration         | ✅       | Auto-detect and display public `wss://` address via ngrok API           |
| Plugin Commands           | ✅       | `!joke`, `!ascii`, `!guess`, `!rps`, `!ai`, `!rickroll`, etc.           |
| Admin Controls            | ✅       | `/mute`, `/ban`, `/kick`, `/mode` switch, IP detection                  |
| Persistent Data           | ✅       | Usernames, mutes, todo stored in `server_data.json`                     |
| Cross-Terminal Support    | ✅       | Works on Termux, Pydroid, Android TV, Linux                             |

---

## 🧰 Installation Guide

### 🔧 Prerequisites (Termux / Linux)

```bash
pkg update
pkg install python git curl mpv unzip
pip install websockets termcolor pyfiglet yt-dlp rich
```

### 🛰️ Ngrok Setup

```bash
curl -O https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
chmod +x ngrok
./ngrok config add-authtoken <YOUR_NGROK_TOKEN>
```

Get token here → [https://dashboard.ngrok.com/get-started/setup](https://dashboard.ngrok.com/get-started/setup)

---

## 🚀 Getting Started

### ⏯️ Start Server

```bash
chmod +x start.sh
./start.sh
```

Outputs:
```
✅ Public WebSocket URL: wss://yourid.ngrok-free.app
```

---

### 💬 Run Clients (Other terminal/device)

```bash
python client_ws_aerov10.py
```

Prompt:
```
🌐 WebSocket URL: wss://yourid.ngrok-free.app
🤖 Nickname: yourname
```

---

## 💡 Example Commands

| Type         | Command / Plugin           | Example                        |
|--------------|----------------------------|--------------------------------|
| Chat Message | -                          | Hello World                    |
| Music        | `!play hello`              | Play YouTube audio             |
| Radio        | `!stations`, `!playstation 1` | Listen to SomaFM, etc.         |
| Tasks        | `/newwork ...`, `/work`    | Add/show/remove todos          |
| Admin        | `/mute`, `/ban`, `/kick`   | Requires admin IP              |
| Plugins      | `!ascii`, `!joke`, `!guess`| Fun commands                   |
| Theme        | `/color red`               | Change name color              |

---

## 📂 Folder Structure

```txt
AERO-V10/
├── server_ws_aerov10.py      # WebSocket server logic
├── client_ws_aerov10.py      # Terminal client interface
├── start.sh                  # ngrok-integrated launcher
├── ngrok                     # Binary
├── server_data.json          # Auto-generated persistent data
├── docs/                     # Screenshots, GIFs
│   ├── server_ui.png
│   └── client_ui.png
└── README.md                 # You're here
```

---

## ❓ FAQ

### Can I use the same phone as server + client?
✅ Yes! Just open two Termux sessions. One runs server, one runs client.

### Music isn't playing?
Install `mpv` via Termux:
```bash
pkg install mpv
```

### Is it encrypted?
Currently, no. Public WebSocket over TLS via ngrok is secure by tunnel, but not end-to-end.

### How do I become admin?
Set your IP in `FIRST_ADMIN_IP` in the server file.

---

## 🧠 Roadmap

- [ ] GUI Version (DearPyGui)
- [ ] Encrypted Messaging (E2E)
- [ ] Web Frontend (React + Flask WebSocket)
- [ ] Client Themes / Skins
- [ ] Plugin Folder Loader

---

## 🙏 Credits

**Lead Developer:** [YOCRRZ](https://github.com/YOCRRZ224)  
**Assisted by:** [ChatGPT (OpenAI)](https://openai.com/chatgpt)

> Terminal power 💻 + Music + Code = AERO-V10.

---

## 📜 License

MIT — free to modify, improve, remix, or fork!  
Please give credits when sharing 
