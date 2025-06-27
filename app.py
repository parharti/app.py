from flask import Flask, request, jsonify, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)
MIDDLEWARE_CHAT_URL = "http://localhost:8080/chat"
chat_memory = []


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MedPlat Multilingual Chatbot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg: #f4f4f9;
            --card-bg: #ffffff;
            --primary: #4b2aad;
            --primary-dark: #3a2089;
            --user-bg: #d8d3f7;
            --bot-bg: #f1f1f1;
            --text: #333;
        }
        body.dark {
            --bg: #121212;
            --card-bg: #1e1e1e;
            --user-bg: #3f3c78;
            --bot-bg: #2a2a2a;
            --text: #eaeaea;
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
        h2 {
            color: var(--primary);
            margin-bottom: 10px;
        }
        .toggle-theme {
            margin-top: -15px;
            margin-bottom: 10px;
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
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
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
            line-height: 1.5;
            position: relative;
            font-size: 15px;
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
    </style>
</head>
<body>
    <h2>Chat with MedPlat Bot 🌐</h2>
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

    recognition.onstart = () => {
        console.log("Voice recognition started. Speak...");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Transcript:", transcript);
        userInput.value = transcript;
    };

    recognition.onerror = (event) => {
        console.error("Voice recognition error:", event.error);
        alert('Voice recognition error: ' + event.error);
    };

    recognition.onend = () => {
        console.log("Voice recognition ended.");
    };

    recognition.start();
}

        chatHistory.scrollTop = chatHistory.scrollHeight;
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
    app.run(debug=True, port=3000)
