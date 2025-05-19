# Terminal Chat with P2P File Sharing

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/licenses/by-sa/4.0/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p/CONTRIBUTING.md)
[![GitHub Issues](https://img.shields.io/github/issues/YOUR_GITHUB_USERNAME/terminal-chat-p2p)](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p/issues)
[![GitHub Pull Requests](https://img.shields.io/github/pulls/YOUR_GITHUB_USERNAME/terminal-chat-p2p)](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p/pulls)
[![Development Status](https://img.shields.io/badge/Development-Under%20Development-orange)](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p)

🚧 **Under Active Development** 🚧

✨ A simple terminal-based chat application with support for basic messaging and peer-to-peer (P2P) file sharing after server notification. Developed with the collaboration of a helpful AI. Expect ongoing improvements and new features! ✨

## 🤝 Contributing to the Project and the AI

This project thrives on community contributions! If you have ideas for enhancements, bug squashing skills, or exciting new features, fork this repository and submit a pull request. Your involvement not only improves the chat but also provides valuable learning data for the AI, helping it to better understand network intricacies, user-friendly design, and the magic of collaborative coding.

## 🚀 How to Use

Get ready to chat and share files in your terminal with these easy steps:

### Prerequisites

* 🐍 **Python 3.x** is a must-have! Grab it from [https://www.python.org/downloads/](https://www.python.org/downloads/).
* 💻 A dash of terminal or command prompt proficiency.

### Step-by-Step Guide

1.  **Clone the Repository (Get the Code!):**
    If you're looking to contribute or keep a local copy, clone this repository using Git:
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p.git](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p.git)
    cd terminal-chat-p2p
    ```
    *(Remember to replace `YOUR_GITHUB_USERNAME` with the repository owner's GitHub handle.)*

2.  **Download the Scripts:**
    You'll need the `terminal_chat_server.py` and `terminal_chat_client.py` scripts. Download them directly from the repository.

3.  **Start the Server (The Hub):**
    Open your terminal and navigate to the script's location. Fire up the server with:
    ```bash
    python3 terminal_chat_server.py
    ```
    The server will be waiting for connections on `0.0.0.0:12345`.

4.  **Launch the Clients (Join the Conversation!):**
    Open separate terminal windows for each user. Navigate to the script's location and run the client:
    ```bash
    python3 terminal_chat_client.py
    ```

5.  **Say Hello (Enter Your Handle):**
    The client will ask for your chat handle (nickname). Type it in and hit Enter to join the chat.

6.  **Chat Away! (Messaging):**
    Start sending messages to other connected users by typing in your terminal and pressing Enter.

7.  **Command Center (Available Commands):**
    The client understands these commands:
    * `/quit`: 👋 Leave the chat and close the client.
    * `/users`: 👥 See who else is online.
    * `/nick <new_nickname>`: ✍️ Change your nickname.
    * `/sendfile <filepath> <port>`: 📤 Share a file via P2P. Replace `<filepath>` with the file's path and `<port>` with an unused port (1024-65535).
    * `/getfile <filename> <sender_nickname> <sender_ip> <sender_port>`: 📥 Download a shared file. Use the info from the `[SYSTEM]` message.

### ⚙️ Changing the Server IP Address

By default, the server listens on `0.0.0.0`, which means it accepts connections on all available network interfaces of your machine. If you need the server to listen on a specific IP address (e.g., if you have multiple network interfaces or want to restrict access), you can modify the `HOST` variable in the `terminal_chat_server.py` file.

1.  **Open `terminal_chat_server.py`** in a text editor.
2.  **Locate the `HOST` variable** near the beginning of the script:
    ```python
    HOST = '0.0.0.0'
    ```
3.  **Change the value** of `HOST` to the desired IP address. For example, to listen only on the local loopback interface:
    ```python
    HOST = '127.0.0.1'
    ```
    Or, to listen on a specific network IP address of your machine:
    ```python
    HOST = '192.168.1.100'  # Replace with your machine's IP
    ```
4.  **Save the changes** to the file.
5.  **Run the server** again. Make sure all clients connecting to this server are configured to use this new IP address in their `HOST` variable in `terminal_chat_client.py`.

    **Important:** Clients need to know the IP address where the server is running. In the `terminal_chat_client.py` file, you'll find a similar `HOST` variable. **Make sure the `HOST` variable in the client script is set to the correct IP address of the server you want to connect to.**

    ```python
    HOST = '<IP_address_of_server>'  # Replace with the server's IP
    ```

### 📤 P2P File Sharing - Under the Hood

1.  **Initiating Share (Client A):**
    When Client A uses `/sendfile <file> <port>`, the server gets the filename and Client A's IP and port. It then announces to everyone: "Hey! Client A wants to share `<file>` on IP: `<Client A's IP>` Port: `<port>`". Simultaneously, Client A's client starts a mini-server, waiting for someone to connect on that `<port>`.

2.  **Requesting Download (Client B):**
    Client B sees the announcement and uses `/getfile <file> <sender_nick> <sender_ip> <sender_port>`. Client B's client then directly tries to connect to the announced `<sender_ip>` on the announced `<sender_port>`. It politely asks for the `<file>`.

3.  **Transfer in Progress (Direct Connection):**
    Once the connection is established, Client A's mini-server starts sending chunks of the `<file>` directly to Client B. The server isn't involved in this transfer; it's a direct peer-to-peer link!

4.  **Download Complete (File Received):**
    Client B's client receives all the data and saves it as `downloaded_<file>`. The direct connection between A and B is then closed.

## 🐛 Issues and Feature Requests

Spotted a bug? Got a brilliant idea? Head over to the [issues page](https://github.com/YOUR_GITHUB_USERNAME/terminal-chat-p2p/issues) and let us know!

## 📜 License

This project is proudly licensed under the [MIT License](LICENSE).

---

Thank you for joining the Terminal Chat with P2P File Sharing! Your feedback and contributions fuel the project and help the AI learn and grow. Happy chatting and sharing! 
