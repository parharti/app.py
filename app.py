from flask import Flask, request, jsonify, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)
MIDDLEWARE_CHAT_URL = "https://server-py-ebxq.onrender.com/chat"


chat_memory = []


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MedPlat Shashakti</title>
  <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #0f9d58;
      --primary-dark: #0c7c46;
      --user-bg: #e6ffe6;
      --bot-bg: #f3f9f4;
      --dark-bg: #121e12;
      --dark-card: #1c2d1c;
      --dark-text: #dff0df;
    }

    body {
      margin: 0;
      font-family: 'Rubik', sans-serif;
      background: linear-gradient(to right, #e8f5e9, #ffffff);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 10px;
      color: #1b1b1b;
    }

    body.dark {
      background: var(--dark-bg);
      color: var(--dark-text);
    }

    .top-bar {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      max-width: 800px;
      margin-bottom: 15px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .brand img {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .brand h1 {
      margin: 0;
      font-size: 22px;
      color: var(--primary);
    }

    .toggle-theme {
      border: 2px solid var(--primary);
      color: var(--primary);
      padding: 6px 14px;
      border-radius: 20px;
      background: none;
      cursor: pointer;
      font-weight: 500;
      transition: 0.3s;
    }

    .toggle-theme:hover {
      background-color: var(--primary);
      color: white;
    }

    .chatbox {
      width: 100%;
      max-width: 800px;
      background: white;
      border-radius: 20px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.08);
      padding: 20px;
      background-color: var(--bot-bg);
    }

    body.dark .chatbox {
      background: var(--dark-card);
    }

    .chat-history {
      max-height: 420px;
      overflow-y: auto;
      padding-right: 10px;
      margin-bottom: 15px;
      display: flex;
      flex-direction: column;
    }

    .message {
      padding: 12px 18px;
      border-radius: 18px;
      margin: 10px 0;
      max-width: fit-content;
      font-size: 15px;
      line-height: 1.5;
      position: relative;
      word-wrap: break-word;
    }

    .user-message {
      background: var(--user-bg);
      margin-left: auto;
      text-align: right;
    }

    .bot-message {
      background: var(--bot-bg);
      margin-right: auto;
    }

    .timestamp {
      font-size: 11px;
      opacity: 0.6;
      margin-top: 4px;
    }

    form {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 10px;
    }

    input[type="text"] {
      flex: 1;
      padding: 14px 20px;
      font-size: 15px;
      border-radius: 25px;
      border: 1px solid #ccc;
      outline: none;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }

    input[type="submit"], .mic-btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px 18px;
      border-radius: 25px;
      font-size: 15px;
      cursor: pointer;
      transition: 0.3s ease;
    }

    input[type="submit"]:hover, .mic-btn:hover {
      background: var(--primary-dark);
    }

    select {
      margin-top: 10px;
      padding: 8px;
      border-radius: 10px;
      border: 1px solid var(--primary);
    }
  </style>
</head>
<body>
  <div class="top-bar">
    <div class="brand">
  <a href="https://www.medplat.in/" target="_blank">
    <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo">
  </a>
  <div>
    <h1>MedPlat Shashakti</h1>
    <p style="margin: 0; font-weight: 500;">Empowering India's Health Warriors 💪</p>
  </div>
</div>

    <button class="toggle-theme" onclick="toggleTheme()">🌙 Toggle Theme</button>
  </div>

  <div class="chatbox">
    <div class="chat-history" id="chat-history">
      {% for msg in chat %}
      <div class="message {{ msg.sender }}-message">
        {{ msg.text }}
        <div class="timestamp">{{ msg.time }}</div>
      </div>
      {% endfor %}
    </div>

    <select id="voice-lang">
      <option value="hi-IN">Hindi</option>
      <option value="gu-IN">Gujarati</option>
      <option value="en-IN" selected>English</option>
    </select>

    <form id="chat-form">
      <input type="text" id="user-input" placeholder="Type your message..." required />
      <input type="submit" value="Send" />
      <button type="button" class="mic-btn" onclick="startListening()">🎤</button>
    </form>
  </div>

  <script>
    const chatForm = document.getElementById("chat-form");
    const chatHistory = document.getElementById("chat-history");
    const userInput = document.getElementById("user-input");
    const voiceLangSelect = document.getElementById("voice-lang");

    function appendMessage(sender, text, time) {
      const msgDiv = document.createElement("div");
      msgDiv.className = `message ${sender}-message`;
      msgDiv.innerHTML = `${text}<div class="timestamp">${time}</div>`;
      chatHistory.appendChild(msgDiv);
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = userInput.value.trim();
      if (!msg) return;

      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      appendMessage("user", msg, now);
      userInput.value = "";

      try {
        const response = await fetch("/send_message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg })
        });

        const botMessages = await response.json();
        botMessages.forEach((m) => appendMessage("bot", m.text, m.time));
      } catch (err) {
        appendMessage("bot", "⚠️ Failed to reach the bot.", now);
      }
    });

    function toggleTheme() {
      document.body.classList.toggle("dark");
    }

    function startListening() {
      const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      recognition.lang = voiceLangSelect.value || "en-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
      };

      recognition.onerror = (event) => {
        alert("🎤 Voice recognition error: " + event.error);
      };

      recognition.start();
    }
  </script>
</body>
</html>

"""



@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, chat=chat_memory)

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    user_msg = data.get("message")
    now = datetime.now().strftime("%H:%M")

    chat_memory.append({"sender": "user", "text": user_msg, "time": now})

    try:
        payload = {"sender": "web_user", "message": user_msg}
        response = requests.post(MIDDLEWARE_CHAT_URL, json=payload, timeout=30)
        response.raise_for_status()
        bot_msgs = response.json()
        responses = []

        for bot_msg in bot_msgs:
            if "text" in bot_msg:
                msg = {
                    "sender": "bot",
                    "text": bot_msg["text"],
                    "time": datetime.now().strftime("%H:%M")
                }
                chat_memory.append(msg)
                responses.append(msg)

        return jsonify(responses)

    except Exception as e:
        error_msg = {
            "sender": "bot",
            "text": f"⚠️ Error: {e}",
            "time": datetime.now().strftime("%H:%M")
        }
        chat_memory.append(error_msg)
        return jsonify([error_msg])

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True, port=3000)
