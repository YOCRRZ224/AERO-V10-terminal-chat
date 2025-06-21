# AERO-V10 TERMINAL SERVER - FINAL FUSED VERSION
import socket, threading, json, os, subprocess, requests, re
from datetime import datetime
from urllib.parse import quote

HOST = '0.0.0.0'
PORT = 55555
ADMIN_IP = '127.0.0.1'  # Your static IP
GEMINI_KEY = "your-gemini-api-key"
WEATHER_KEY = "your-openweather-api-key"
STREAM_URL = "https://abc123.ngrok.io"

clients, nicknames, roles, colors = {}, {}, {}, {}
muted, banned = set(), set()
available_colors = ['red', 'green', 'yellow', 'blue', 'cyan', 'magenta', 'white']
emoji_map = {
    ':bolt:': '⚡', ':fire:': '🔥', ':heart:': '❤️', ':star:': '⭐',
    ':check:': '✔️', ':x:': '❌', ':wave:': '👋', ':smile:': '😄',
    ':boom:': '💥', ':rocket:': '🚀', ':code:': '💻'
}

# Load persistent data
try:
    with open("server_data.json", "r") as f:
        data = json.load(f)
except:
    data = {'todo': [], 'work': [], 'mode': 'radio', 'queue': [], 'is_playing': False}
stations = [
    "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
    "https://icecast.vgtrk.cdnvideo.ru/rrzonam_mp3_128kbps"
]

def broadcast(msg, exclude=None):
    for c in clients:
        if c != exclude:
            try: c.send(msg.encode())
            except: pass

def replace_emojis(text):
    for k, v in emoji_map.items():
        text = text.replace(k, v)
    return text

def send(msg):
    print(msg)
    broadcast(msg)

def stream_from_youtube(query):
    data['is_playing'] = True
    result = subprocess.run(
        f'yt-dlp -g "ytsearch1:{quote(query)}"',
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        link = result.stdout.strip()
        broadcast(f"🎧 Now Playing: {query}\n🔗 Stream: {STREAM_URL}")
        subprocess.run(f"mpv --no-video --httpd-port=8080 \"{link}\"", shell=True)
    data['is_playing'] = False

def stream_from_radio(url):
    data['is_playing'] = True
    broadcast(f"📡 Radio Live\n🔗 Listen: {STREAM_URL}")
    subprocess.run(f"mpv --no-video --httpd-port=8080 \"{url}\"", shell=True)
    data['is_playing'] = False
def handle(client):
    addr = clients[client]
    nick = nicknames[client]
    role = roles.get(client, 'client')

    while True:
        try:
            msg = client.recv(1024).decode().strip()
            if not msg: continue

            if msg.startswith("/nickname "):
                newnick = msg.split(" ", 1)[1]
                nicknames[client] = newnick
                send(f"🔄 {nick} is now known as {newnick}")
                nick = newnick

            elif msg.startswith("/color "):
                color = msg.split(" ", 1)[1]
                if color in available_colors and color not in colors.values():
                    colors[client] = color
                    client.send(f"🎨 Color set to {color}\n".encode())

            elif msg.startswith("/todo "):
                task = msg.split(" ", 1)[1]
                data['todo'].append(task)
                client.send(f"📝 Task added: {task}\n".encode())

            elif msg == "/todo":
                todo = "\n".join(f"- {t}" for t in data['todo'])
                client.send(f"📋 Todo List:\n{todo}\n".encode())

            elif msg.startswith("/newwork "):
                task = msg.split(" ", 1)[1]
                data['work'].append(task)
                client.send(f"🚧 Work added: {task}\n".encode())

            elif msg == "/work":
                tasks = "\n".join(f"- {w}" for w in data['work'])
                client.send(f"📂 Work List:\n{tasks}\n".encode())

            elif msg.startswith("/remwork "):
                target = msg.split(" ", 1)[1]
                if target in data['work']:
                    data['work'].remove(target)
                    client.send(f"🗑️ Removed: {target}\n".encode())

            elif msg.startswith("/radio ") and role == 'admin':
                try:
                    index = int(msg.split(" ")[1]) - 1
                    if 0 <= index < len(stations):
                        threading.Thread(target=stream_from_radio, args=(stations[index],)).start()
                except:
                    client.send("❌ Invalid station number.\n".encode())

            elif msg.startswith("/mode ") and role in ['admin', 'mod']:
                m = msg.split(" ", 1)[1]
                if m in ['radio', 'streaming']:
                    data['mode'] = m
                    send(f"🔁 Mode switched to {m.upper()}")

            elif msg.startswith("!play "):
                query = msg.split(" ", 1)[1]
                if data['mode'] == 'streaming':
                    if not data['is_playing']:
                        threading.Thread(target=stream_from_youtube, args=(query,)).start()
                    else:
                        data['queue'].append(query)
                        send(f"🎶 Queued: {query}")
                else:
                    client.send("⚠️ Use /radio <num> to play stations.\n".encode())

            elif msg == "!skip" and role == 'admin':
                if data['queue']:
                    next_song = data['queue'].pop(0)
                    threading.Thread(target=stream_from_youtube, args=(next_song,)).start()

            elif msg == "/queue":
                q = "\n".join(f"{i+1}. {s}" for i, s in enumerate(data['queue']))
                client.send(f"🎵 Queue:\n{q}\n".encode())

            elif msg.startswith("/send "):
                _, target, path = msg.split(" ", 2)
                if not os.path.exists(path):
                    client.send("❌ File not found.\n".encode())
                    continue
                subprocess.run(["rclone", "copy", path, "gdrive:AERO-V10-uploads"], stdout=subprocess.PIPE)
                link = subprocess.run(["rclone", "link", f"gdrive:AERO-V10-uploads/{os.path.basename(path)}"],
                                      capture_output=True, text=True).stdout.strip()
                if target == "broadcast":
                    send(f"📤 {nick} shared file: {os.path.basename(path)}\n🔗 {link}")
                else:
                    for c, n in nicknames.items():
                        if n == target:
                            c.send(f"📥 {nick} sent you a file: {os.path.basename(path)}\n🔗 {link}".encode())

            elif msg.startswith("!ai "):
                prompt = msg.split(" ", 1)[1]
                res = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers={"Content-Type": "application/json"}
                )
                try:
                    reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                    for line in reply.splitlines():
                        client.send(f"🤖 {line.strip()}\n".encode())
                except:
                    client.send("❌ AI error.\n".encode())

            elif msg.startswith("!joke"):
                joke = requests.get("https://v2.jokeapi.dev/joke/Any?type=single").json()
                client.send(f"😆 {joke.get('joke', 'Error fetching joke')}\n".encode())

            elif msg.startswith("!weather "):
                city = msg.split(" ", 1)[1]
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
                res = requests.get(url).json()
                if res.get("main"):
                    t = res['main']['temp']
                    desc = res['weather'][0]['description']
                    client.send(f"🌦️ Weather in {city.title()}: {t}°C, {desc}\n".encode())
                else:
                    client.send("❌ City not found.\n".encode())

            elif msg.startswith("!calc "):
                expr = msg.split(" ", 1)[1]
                if re.match(r'^[\d\+\-\*\/\.\s]+$', expr):
                    try:
                        result = eval(expr)
                        client.send(f"🧮 {expr} = {result}\n".encode())
                    except:
                        client.send("❌ Invalid calculation.\n".encode())
                else:
                    client.send("⚠️ Unsafe expression.\n".encode())

            else:
                time = datetime.now().strftime("[%H:%M]")
                message = replace_emojis(msg)
                broadcast(f"{time} <{nick}> {message}")

            with open("server_data.json", "w") as f:
                json.dump(data, f)

        except:
            client.close()
            clients.pop(client, None)
            send(f"❌ {nick} disconnected.")
            break

def receive():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("🟢 AERO-V10 Server Live")

    while True:
        client, address = server.accept()
        if address[0] in banned:
            client.send("❌ You are banned.\n".encode())
            client.close()
            continue

        client.send("📡 Nickname: ".encode())
        nick = client.recv(1024).decode().strip()
        clients[client] = address
        nicknames[client] = nick
        roles[client] = 'admin' if address[0] == ADMIN_IP else 'client'

        send(f"✅ {nick} joined")
        threading.Thread(target=handle, args=(client,)).start()

receive()ent] = nick
        roles[client] = 'admin' if address[0] == ADMIN_IP else 'client'

        send(f"✅ {nick} joined")
        threading.Thread(target=handle, args=(client,)).start()

receive()
