
# 🚀 AERO-V10 Terminal Chat

An advanced terminal chat designed for programmers, offering a unique chatting experience directly within the terminal. Enjoy seamless communication while you code, with features like music streaming and much more.

[![Stars](https://img.shields.io/github/stars/YOCRRZ224/AERO-V10-terminal-chat?style=social)](https://github.com/YOCRRZ224/AERO-V10-terminal-chat/stargazers)
[![Forks](https://img.shields.io/github/forks/YOCRRZ224/AERO-V10-terminal-chat?style=social)](https://github.com/YOCRRZ224/AERO-V10-terminal-chat/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
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
  
  ![👁️ Views](https://komarev.com/ghpvc/?username=YOCRRZ224&label=👁️%20Views&color=161B22&style=flat-square&labelColor=0d1117)
</p>
# ✨ Key Features & Benefits

*   **Terminal-Based Chat:** Chat directly from your terminal, minimizing context switching.
*   **Music Streaming:** Listen to music while coding, directly through the chat interface (YouTube and Radio).
*   **Real-time Communication:** Uses WebSocket for instant messaging.
*   **Customizable:** Offers configurable settings to personalize your chat experience.
*   **User Authentication:** Secure user accounts with password hashing.
*   **Avatars & Stickers:** Enhance your chat with personalized avatars and stickers.
*   **PWA Support:** Installable as a Progressive Web App for a native-like experience.

## 🛠️ Prerequisites & Dependencies

Before you begin, ensure you have the following installed:

*   **Python:** (version 3.6 or higher)
*   **pip:** Python package installer
*   **Flask:** Python web framework
*   **Flask-SocketIO:** WebSocket integration for Flask
*   **Werkzeug:** Python WSGI utility library
*   **requests:** Python HTTP library
*   **beautifulsoup4:** Python library for pulling data out of HTML and XML files
*   **yt-dlp:** YouTube download and processing library
*   **Termux:** (If running on Android)
*   Any other dependencies listed in `main.py`

## 📦 Installation & Setup Instructions

Follow these steps to get the AERO-V10 Terminal Chat up and running:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/YOCRRZ224/AERO-V10-terminal-chat.git
    cd AERO-V10-terminal-chat
    ```

2.  **Create a virtual environment (optional but recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate.bat  # On Windows
    ```

3.  **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt # Create requirements.txt with all dependencies needed from main.py by manually copying them, flask, flask-socketio etc..
    ```

4.  **Set up the database:**

    The application uses an SQLite database. The `main.py` file contains the database initialization logic.  No specific setup required; it will be created automatically.

5.  **Configure the application:**

    Adjust the settings in `main.py` to suit your needs. This includes setting the secret key, allowed file extensions, etc.

6.  **Run the application:**

    ```bash
    python main.py
    ```

7.  **Access the chat:**

    Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address shown in the terminal output).

## 💻 Usage Examples & API Documentation

### Example Usage

1.  **Register a new user:**
    *   Navigate to the registration page.
    *   Enter a username and password.

2.  **Log in:**
    *   Use your registered credentials to log in.

3.  **Start chatting:**
    *   Type your message in the input field and press Enter to send.

4.  **Use commands:**
    *   Explore available commands within the chat interface (e.g., for playing music).

### API Documentation (Sockets)

The application uses Socket.IO for real-time communication. Here's a brief overview:

*   `connect`: Event emitted when a client connects.
*   `disconnect`: Event emitted when a client disconnects.
*   `message`: Event for sending and receiving chat messages.
*   `join`: Event for joining a specific chat room.
*   `leave`: Event for leaving a chat room.

## ⚙️ Configuration Options

You can configure the following aspects of the application:

*   **`SECRET_KEY`:**  A secret key for securing the session.  Set this in `main.py`.
*   **`UPLOAD_FOLDER`:**  The directory for storing uploaded files (avatars, etc.).
*   **`ALLOWED_EXTENSIONS`:**  A list of allowed file extensions for uploads.
*   **Database:**  The database connection can be modified in the `main.py` file if you want to use a different database.

## 🤝 Contributing Guidelines

We welcome contributions from the community! Here's how you can contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Implement your changes.
4.  Test your changes thoroughly.
5.  Submit a pull request with a clear description of your changes.

## 📜 License Information

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

*   The Flask framework.
*   The Socket.IO library.
*   The yt-dlp library.
*   All other dependencies used in this project.
*   
[![Star History Chart](https://api.star-history.com/svg?repos=YOCRRZ224/AERO-V10-terminal-chat&type=Timeline)](https://www.star-history.com/#YOCRRZ224/AERO-V10-terminal-chat&Timeline&LogScale)
