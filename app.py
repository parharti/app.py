from flask import Flask, request, jsonify, render_template_string, session
import requests
from datetime import datetime
import uuid
import os


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "my-temp-dev-secret")

MIDDLEWARE_CHAT_URL = "https://server-py-ebxq.onrender.com/chat"


chat_memory = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MedPlat: Multilingual AI Health Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg: #f5fff6;
            --card-bg: #ffffff;
            --primary: #34a853;
            --primary-dark: #2a8642;
            --user-bg: #d6f5dd;
            --bot-bg: #e8f5e9;
            --text: #1b1b1b;
        }
        body.dark {
            --bg: #0d1a0d;
            --card-bg: #1c2d1c;
            --user-bg: #2a4d2a;
            --bot-bg: #193319;
            --text: #eafaea;
        }
        body {
            margin: 0;
            padding: 0;
            background: var(--bg);
            font-family: 'Segoe UI', sans-serif;
            color: var(--text);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px 10px;
        }
        h1 {
            color: var(--primary);
            font-size: 2rem;
            margin: 0;
        }
        .brand {
            margin-bottom: 15px;
            text-align: center;
        }
        .toggle-theme {
            margin-bottom: 15px;
            cursor: pointer;
            background: none;
            border: 2px solid var(--primary);
            color: var(--primary);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            transition: 0.3s;
        }
        .toggle-theme:hover {
            background-color: var(--primary);
            color: white;
        }
        .chatbox {
            background: var(--card-bg);
            width: 100%;
            max-width: 700px;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .chat-history {
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .message {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 75%;
            position: relative;
            font-size: 15px;
            line-height: 1.5;
            animation: fadeIn 0.4s ease-in-out;
        }
        .user-message {
            background: var(--user-bg);
            align-self: flex-end;
            float: right;
            clear: both;
            text-align: right;
        }
        .bot-message {
            background: var(--bot-bg);
            align-self: flex-start;
            float: left;
            clear: both;
        }
        .timestamp {
            font-size: 11px;
            color: gray;
            margin-top: 2px;
            text-align: right;
        }
        form {
            display: flex;
            gap: 10px;
        }
        input[type=text] {
            flex: 1;
            padding: 12px;
            font-size: 15px;
            border: 1px solid #ccc;
            border-radius: 25px;
            outline: none;
        }
        input[type=submit], button.mic-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 15px;
            cursor: pointer;
            transition: 0.2s ease;
        }
        input[type=submit]:hover,
        button.mic-btn:hover {
            background: var(--primary-dark);
        }
        #voice-lang {
            margin: 10px 0;
            padding: 6px 12px;
            border-radius: 10px;
            border: 1px solid var(--primary);
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="brand">
        <h1>🩺 Sashakti</h1>
        <p>A Multilingual AI Chatbot to Empower India’s Frontline Health Workers</p>
    </div>
    <button class="toggle-theme" onclick="toggleTheme()">Toggle Dark Mode</button>

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
            <input type="text" id="user-input" placeholder="Type your message..." required autofocus>
            <input type="submit" value="Send">
            <button type="button" class="mic-btn" onclick="startListening()">🎤 Speak</button>
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

        chatForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const msg = userInput.value.trim();
            if (!msg) return;

            const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            appendMessage("user", msg, now);
            userInput.value = "";

            try {
                const response = await fetch("/send_message", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ message: msg })
                });

                const botMessages = await response.json();
                botMessages.forEach(m => appendMessage("bot", m.text, m.time));
            } catch (err) {
                appendMessage("bot", "⚠️ Failed to reach the bot.", now);
            }
        });

        function toggleTheme() {
            document.body.classList.toggle("dark");
        }

        function startListening() {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = voiceLangSelect.value || 'en-IN';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => console.log("🎙️ Listening...");
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                userInput.value = transcript;
            };
            recognition.onerror = (event) => {
                console.error("Voice error:", event.error);
                alert("🎤 Voice recognition error: " + event.error);
            };
            recognition.onend = () => console.log("🛑 Stopped listening.");
            recognition.start();
        }

        chatHistory.scrollTop = chatHistory.scrollHeight;
    </script>
</body>
</html>
"""


@app.before_request
def create_session():
    if "chat_id" not in session:
        session["chat_id"] = str(uuid.uuid4())
        session["chat_memory"] = []

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, chat=session.get("chat_memory", []))

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    user_msg = data.get("message")
    now = datetime.now().strftime("%H:%M")

    chat_history = session.get("chat_memory", [])
    chat_history.append({"sender": "user", "text": user_msg, "time": now})

    try:
        payload = {"sender": session["chat_id"], "message": user_msg}
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
                chat_history.append(msg)
                responses.append(msg)

        session["chat_memory"] = chat_history
        return jsonify(responses)

    except Exception as e:
        error_msg = {
            "sender": "bot",
            "text": f"⚠️ Error: {e}",
            "time": datetime.now().strftime("%H:%M")
        }
        chat_history.append(error_msg)
        session["chat_memory"] = chat_history
        return jsonify([error_msg])

@app.route("/reset", methods=["GET"])
def reset_chat():
    session["chat_memory"] = []
    return "Chat has been reset.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=3000)
