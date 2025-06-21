import socket
import threading
import sys

# Connect info
server_ip = input("🔌 Enter server IP (e.g. 127.0.0.1): ")
server_port = int(input("📡 Enter port (e.g. 5555): "))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((server_ip, server_port))
    print("✅ Connected to AERO-V10 Terminal Chat")
    print("Type your message below ⬇️\n")
except:
    print("❌ Connection failed. Check IP and port.")
    sys.exit()

# Listen for messages
def receive():
    while True:
        try:
            msg = client.recv(2048).decode()
            if msg:
                print(msg)
        except:
            print("❌ Server closed the connection.")
            client.close()
            break

# Write messages + echo cleanly
def write():
    while True:
        try:
            msg = input()
            if msg.strip() == "":
                continue
            print(f"You: {msg}")  # Simple echo
            client.send(msg.encode())
        except:
            print("❌ Error sending message.")
            break

# Start threads
threading.Thread(target=receive).start()
threading.Thread(target=write).start()
