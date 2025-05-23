# Terminal Chat Application

![Project Status](https://img.shields.io/badge/Status-Under%20Development-blue?style=for-the-badge&logo=github)

---

## 🚀 Overview

Welcome to the **Terminal Chat Application**! This project provides a simple yet robust command-line chat experience, allowing users to communicate in real-time and even share files directly within their terminal. Built with Python and WebSockets, it's designed to be lightweight and functional across various Linux-like environments, including Android's Termux.

Whether you're chatting from your mobile phone, an Android TV, or a traditional desktop, this application aims to provide a seamless text-based communication platform.

---

## ✨ Features

This chat application is packed with features to enhance your terminal communication:

* **Real-time Messaging:** Instantaneous message exchange between all connected users.
* **Dynamic Usernames:** Change your display name anytime using the `/nick` command.
* **User Listing:** See who's currently online with the `/list` command.
* **Direct File Sharing:** Send and receive files directly between users, managed by the server.
    * **Initiate Transfers:** Use `/file <recipient_username> <local_file_name>` to start.
    * **Accept/Reject:** Recipients can accept or decline transfers.
    * **Chunked Transfers:** Files are sent in chunks to handle larger data efficiently.
* **User Tagging (Mentions):**
    * **`@username` Mentions:** Tag other users in your messages (e.g., `Hey @Alice, check this out!`).
    * **Private Notifications:** Tagged users receive a private server notification that they've been mentioned.
    * **Client-Side Highlighting:** Your own username will be **highlighted in yellow** in messages where you are tagged, making it easy to spot mentions.
* **Help Command:** A quick `/help` command to list all available actions.
* **Cross-Device Compatibility:** Designed to work well on Termux (Android phones, Android TVs) and standard Linux/macOS environments.

---

## 🚧 Project Status: Under Development

This project is actively under development. While core features are functional, you may encounter bugs, and new features are continually being added. Your feedback and contributions are highly welcome!

---

## 🛠️ Setup and Installation

Setting up the chat application is straightforward. You'll need Python 3 and `pip` installed.

### Prerequisites

* **Python 3.8+:** Ensure Python is installed on both your server and client devices.
* **Termux (for Android devices):** If you're using an Android phone or TV, install Termux from [F-Droid](https://f-droid.org/packages/com.termux/) or the [Play Store](https://play.google.com/store/apps/details?id=com.termux).
* **Internet Connection:** Required for package installation and server/client communication.

### Step-by-Step Installation

Follow these steps on **both** your **Server Device (e.g., Android TV)** and your **Client Device (e.g., Mobile Phone)**.

1.  **Update Termux (if on Android):**
    ```bash
    pkg update && pkg upgrade -y
    ```

2.  **Install Essential System Packages:**
    ```bash
    pkg install python openssl git make
    ```
    * `openssl`: Crucial for secure connections and Python's SSL module.
    * `make`: Required by some Python package build processes.
    * `git`: For easy cloning of this repository.

3.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOCRRZ224/Terminal-chat-with-file-sharing-under-development-
    ```
    *(If you've been directly creating files, just `cd` into your existing project directory.)*

4.  **Create and Activate a Python Virtual Environment:**
    It's always best practice to use a virtual environment to manage dependencies.
    ```bash
    python -m venv my_chat_env
    source my_chat_env/bin/activate
    ```
    You should see `(my_chat_env)` at the beginning of your prompt, indicating the virtual environment is active.

5.  **Install Required Python Libraries:**
    With your virtual environment active, install `websockets`.
    ```bash
    pip install websockets
    ```

6.  **Create `downloads` Directory:**
    This directory will be used for saving received files.
    ```bash
    mkdir downloads
    ```

---

## 🚀 Usage Guide

### 1. Configure the Client

Before starting, you need to tell your **client** where the server is located.

* Open `terminal_chat_client.py` on your **Client Device** (e.g., Mobile Phone) with a text editor (`nano terminal_chat_client.py`).
* Locate the `HOST` variable near the top:
    ```python
    HOST = '127.0.0.1' # <-- Change this to your servers  IP address
    ```
* **Change `'127.0.0.1'` to the actual local IP address of your Server Device (e.g., Android TV).** You can usually find your TV's IP in its Wi-Fi settings (e.g., `192.168.1.105`). If both server and client are on the same device, `127.0.0.1` is correct.
* Save the file.

### 2. Start the Server

On your **Server Device** (e.g., your server device u will use):

* Open Termux.
* Activate your virtual environment: `source my_chat_env/bin/activate`
* Navigate to your project directory.
* Run the server:
    ```bash
    server.py
    ```
    The server will print a message indicating it's started (e.g., `[SERVER] Starting chat server on ws://0.0.0.0:12345`).

    > **Tip for Android TV:** If you're running the server for extended periods, consider using `termux-wake-lock` in a separate Termux session to prevent the device from sleeping and stopping the server.
    > ```bash
    > termux-wake-lock
    > ```

### 3. Start the Client

On your **Client Device** (e.g., Mobile Phone):

* Open Termux.
* Activate your virtual environment: `source my_chat_env/bin/activate`
* Navigate to your project directory.
* Run the client:
    ```bash
    client.py
    ```
    The client will attempt to connect to the server and print a welcome message.

### 4. Chat and Collaborate!

Once connected, you can start sending messages and using commands!

---

## 💡 Commands

Here are the commands you can use in the chat:

* `/nick <new_name>`: Change your username.
    * **Example:** `/nick MyAwesomeName`
* `/list`: Display a list of all currently connected users.
* `/file <recipient_username> <local_file_name_with_extension>`: Initiate a file transfer to another user.
    * **Example:** `/file Alice my_document.pdf`
    * The recipient will be prompted with `[FILE TRANSFER] <sender> wants to send '<file_name>'...`
    * Recipient can then type `/accept <file_id>` or `/reject <file_id>`.
* `/help`: Show a comprehensive list of all available commands.
* `@username message`: Tag a user in your message.
    * **Example:** `Hey @Bob, are you there?`
    * The tagged user will receive a private server notification.
    * If you are the tagged user, `@YOURUSERNAME` will be **highlighted in yellow** in the chat message.

---

## ⚠️ Troubleshooting / Common Issues

* **`No module found name websockets`**:
    * **Reason:** The `websockets` library is not installed in your current Python environment (likely the virtual environment).
    * **Solution:** Activate your virtual environment (`source my_chat_env/bin/activate`) and run `pip install websockets`. Ensure this is done on *both* the server and client devices.
* **`Connection refused` / Client cannot connect**:
    * **Reason 1:** The server is not running, or its IP address/port is incorrect.
    * **Solution 1:** Double-check that `terminal_chat_server.py` is running on your server device.
    * **Reason 2:** The `HOST` IP address in your `terminal_chat_client.py` is incorrect or doesn't match the server's IP.
    * **Solution 2:** Verify the server device's local IP address and update the `HOST` variable in `terminal_chat_client.py` accordingly.
    * **Reason 3:** Firewall issues on the server device or network.
    * **Solution 3:** Ensure no firewalls are blocking port `12345` on your server device.
* **`SSLError` during `pip install`**:
    * **Reason:** Python's SSL module is not correctly configured or linked against necessary system libraries, common in minimalist environments like Termux.
    * **Solution:** Install OpenSSL development libraries and ensure Python is correctly linked:
        ```bash
        pkg update && pkg upgrade -y
        pkg install openssl libssl-dev
        pkg install python # This might re-link Python with updated SSL libs
        # Then retry your pip install command
        ```
* **File Transfer Issues**:
    * Ensure the local file path you're trying to send exists and is accessible.
    * Verify the `downloads` directory exists on the receiving client's device.
    * Confirm both sender and receiver are running the **latest code** with file transfer logic.

---

## 📈 Future Enhancements (Roadmap)

* **Persistent Chat History:** Save messages to a file or database.
* **Private Messaging:** Implement `/msg` or `/dm` for one-on-one conversations.
* **Emoji Support:** Basic emoji rendering.
* **Configurable Settings:** Allow users to set colors, notification preferences, etc.
* **File Transfer Progress Bar:** More visual feedback during large file transfers.
* **Server Admin Commands:** Kick/ban users, announce messages.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

