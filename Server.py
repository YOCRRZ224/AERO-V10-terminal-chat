import socket, threading, os, json, random, time
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import subprocess
import requests

# Server Setup
HOST = '0.0.0.0'
PORT = 55555
BUFFER = 1024
FIRST_ADMIN_IP = '127.0.0.1'

clients = {}
banned_ips = set()
color_pool = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
used_colors = {}
todo_list = []
work_tracker = []
music_queue = []
now_playing = [None]
current_mode = {'value': 'streaming'}

emoji_map = {
    ':fire': '🔥', ':star': '⭐', ':wave': '👋', ':bolt': '⚡',
    ':heart': '❤️', ':sun': '☀️', ':music': '🎵', ':file': '📁',
    ':ai': '🤖', ':check': '✅'
}
def parse_emojis(text):
    for code, emoji in emoji_map.items():
        text = text.replace(code, emoji)
    return text

def authenticate_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path):
    service = authenticate_drive()
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = uploaded.get('id')
    service.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message.encode())
            except:
                client.close()
                del clients[client]

def clients_color(nick):
    for client in clients:
        if clients[client]['nickname'] == nick:
            return clients[client]['color']
    return 'white'

def format_message(nickname, msg, role):
    ts = datetime.now().strftime("%H:%M")
    parsed = parse_emojis(msg)
    return f"[{ts}] [{role.upper()}] {nickname}: {parsed}"

def save_data():
    with open("server_data.json", "w") as f:
        json.dump({"todo_list": todo_list, "work_tracker": work_tracker}, f)
def receive(client, ip):
    nickname = clients[client]['nickname']
    role = clients[client]['role']
    while True:
        try:
            msg = client.recv(BUFFER).decode('utf-8').strip()
            if not msg:
                raise ConnectionResetError
            if msg.startswith('/'):
                handle_command(client, msg, nickname, role, ip)
            elif msg.startswith('!'):
                handle_plugin(client, msg, nickname)
            else:
                formatted = format_message(nickname, msg, role)
                broadcast(formatted, sender=client)
        except:
            print(f"{nickname} disconnected")
            broadcast(f"🔌 {nickname} has left the chat.")
            client.close()
            del clients[client]
            break

def handle_plugin(client, msg, nickname):
    if msg.startswith('!joke'):
        joke = requests.get("https://v2.jokeapi.dev/joke/Any?type=single").json().get("joke", "No joke found.")
        client.send(f"🤣 Joke: {joke}".encode())

    elif msg.startswith('!weather'):
        query = msg.replace('!weather', '').strip()
        api_key = "YOUR_OPENWEATHER_API"
        if query:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={query}&appid={api_key}&units=metric"
            data = requests.get(url).json()
            if "main" in data:
                weather = f"🌦 {query.title()}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
            else:
                weather = "⚠️ City not found."
            client.send(weather.encode())

    elif msg.startswith('!calc'):
        try:
            expr = msg.replace('!calc', '').strip()
            result = eval(expr)
            client.send(f"🧮 Result: {result}".encode())
        except:
            client.send("❌ Invalid expression.".encode())

    elif msg.startswith('!ascii'):
        text = msg.replace('!ascii', '').strip()
        if text:
            from pyfiglet import figlet_format
            client.send(figlet_format(text).encode())
def handle_command(client, msg, nickname, role, ip):
    args = msg.split()
    cmd = args[0]

    if cmd == '/nickname' and len(args) > 1:
        new_nick = args[1]
        clients[client]['nickname'] = new_nick
        broadcast(f"🔁 {nickname} changed nickname to {new_nick}")

    elif cmd == '/color' and len(args) > 1:
        new_color = args[1]
        taken = any(c['color'] == new_color for c in clients.values())
        if not taken:
            clients[client]['color'] = new_color
            client.send(f"✅ Color set to {new_color}".encode())
        else:
            client.send("❌ Color already taken.".encode())

    elif cmd == '/mute' and role in ['admin', 'mod'] and len(args) > 1:
        target = args[1]
        for c in clients:
            if clients[c]['nickname'] == target:
                clients[c]['muted'] = True
                c.send("🔇 You have been muted.".encode())

    elif cmd == '/ban' and role == 'admin' and len(args) > 1:
        target = args[1]
        for c in list(clients):
            if clients[c]['nickname'] == target:
                c.send("🚫 You’ve been banned.".encode())
                c.close()
                banned_ips.add(ip)
                del clients[c]
                broadcast(f"🚫 {target} was banned by {nickname}")

    elif cmd == '/send' and len(args) > 2:
        target = args[1]
        file_path = args[2]
        if os.path.exists(file_path):
            try:
                link = upload_to_drive(file_path)
                if target == 'all':
                    broadcast(f"📁 {nickname} shared: {link}")
                else:
                    for c in clients:
                        if clients[c]['nickname'] == target:
                            c.send(f"📁 {nickname} sent you a file: {link}".encode())
            except:
                client.send("❌ Upload failed.".encode())
        else:
            client.send("❌ File not found.".encode())

    elif cmd == '/newwork' and len(args) > 1:
        task = " ".join(args[1:])
        work_tracker.append(task)
        save_data()
        broadcast(f"🆕 Work added by {nickname}: {task}")

    elif cmd == '/work':
        if work_tracker:
            for task in work_tracker:
                client.send(f"📌 {task}\n".encode())
        else:
            client.send("📭 No active tasks.".encode())

    elif cmd == '/remwork' and len(args) > 1:
        task = " ".join(args[1:])
        if task in work_tracker:
            work_tracker.remove(task)
            save_data()
            client.send("✅ Work removed.".encode())
        else:
            client.send("❌ Task not found.".encode())

    elif cmd == '/mode' and len(args) > 1 and role in ['admin', 'mod']:
        mode = args[1]
        if mode in ['radio', 'streaming']:
            current_mode['value'] = mode
            broadcast(f"🎛 Mode switched to {mode} by {nickname}")

    elif cmd == '/stations':
        stations = {
            "1": "https://rfcmedia.streamguys1.com/classicrock.mp3",
            "2": "https://stream.zeno.fm/f8w5vv3r1hhvv",
            "3": "https://www.internet-radio.com/servers/tools/playlistgenerator/?u=http://us5.internet-radio.com:8257/listen.pls&t=.pls"
        }
        for k, v in stations.items():
            client.send(f"📻 Station {k}: {v}\n".encode())

    elif cmd == '/queue':
        if music_queue:
            q = "\n".join(f"{i+1}. {title}" for i, (title, _) in enumerate(music_queue))
            client.send(f"🎶 Current Queue:\n{q}".encode())
        else:
            client.send("🎵 Queue is empty.".encode())

    elif cmd == '/help':
        help_text = (
            "📘 Commands:\n"
            "/nickname <newname>\n/color <color>\n/mute <user>\n/ban <user>\n"
            "/send <all|user> <filepath>\n/newwork <task>\n/work\n/remwork <task>\n"
            "/mode <radio|streaming>\n/stations\n/queue\n!play <song>\n!skip\n"
            "!joke, !weather <city>, !calc <expr>, !ascii <text>"
        )
        client.send(help_text.encode())
def accept_connections():
    while True:
        client, addr = server.accept()
        ip = addr[0]

        if ip in banned_ips:
            client.send("🚫 You are banned from AERO-V10.".encode())
            client.close()
            continue

        client.send("👤 Enter your nickname: ".encode())
        nickname = client.recv(BUFFER).decode('utf-8').strip()

        role = 'admin' if ip == FIRST_ADMIN_IP else 'client'
        color = random.choice([c for c in color_pool if c not in used_colors])
        used_colors[color] = nickname

        clients[client] = {
            "nickname": nickname,
            "role": role,
            "color": color,
            "muted": False
        }

        print(f"[+] {nickname} connected from {ip}")
        broadcast(f"✅ {nickname} joined the chat.")
        client.send("🟢 Connected to AERO-V10 Terminal Chat\nType your message below ⬇️".encode())

        thread = threading.Thread(target=receive, args=(client, ip))
        thread.start()

# Server Start
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"🚀 AERO-V10 Server running on {HOST}:{PORT}")
accept_connections()
