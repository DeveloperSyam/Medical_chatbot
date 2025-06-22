from flask import Flask, request, jsonify, send_file
from gemini import generate_medical_response
from dotenv import load_dotenv
import os, sqlite3, requests
from fpdf import FPDF

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # User table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_input TEXT,
                    bot_response TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- Translation Function (LibreTranslate API) ---
def translate_text(text, target_lang='en'):
    try:
        response = requests.post(
            "https://libretranslate.de/translate",
            data={
                'q': text,
                'source': 'auto',
                'target': target_lang,
                'format': 'text'
            }
        )
        if response.status_code == 200:
            return response.json()['translatedText']
        else:
            return text
    except:
        return text

# --- Routes ---

@app.route("/")
def home():
    return app.send_static_file("index.html")

# Register new user
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required."}), 400

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registration successful."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Username already exists."}), 400

# Login user
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()

    if result:
        return jsonify({"success": True, "user_id": result[0]})
    else:
        return jsonify({"success": False, "error": "Invalid credentials."}), 401

# Chat route (requires user_id)
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("question", "")
        target_lang = data.get("lang", "en")
        user_id = data.get("user_id")

        if not user_input or not user_id:
            return jsonify({"success": False, "error": "Question and user_id required."}), 400

        # Translate to English
        translated_input = translate_text(user_input, 'en')

        # AI medical response
        response = generate_medical_response(translated_input)

        # Translate back to user's language if needed
        final_response = translate_text(response, target_lang) if target_lang != 'en' else response

        # Save to chat history
        save_chat(user_id, user_input, final_response)

        return jsonify({"success": True, "response": final_response})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Save chat history to SQLite
def save_chat(user_id, user_input, bot_response):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (user_id, user_input, bot_response) VALUES (?, ?, ?)",
              (user_id, user_input, bot_response))
    conn.commit()
    conn.close()

# Health Tip endpoint
@app.route("/tip")
def health_tip():
    tips = [
        "Stay hydrated by drinking at least 2-3 liters of water daily.",
        "Take a 10-minute walk after meals to improve digestion.",
        "Get 7-8 hours of sleep every night for better immunity.",
        "Wash your hands regularly with soap and water.",
        "Practice deep breathing to reduce stress."
    ]
    import random
    return jsonify({"tip": random.choice(tips)})

# Export user's chat history as PDF
@app.route("/export/<int:user_id>")
def export_pdf(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT user_input, bot_response FROM chat_history WHERE user_id=?", (user_id,))
    chats = c.fetchall()
    conn.close()

    if not chats:
        return jsonify({"success": False, "error": "No chat history found for this user."}), 404

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Medical Chatbot Chat History", ln=True, align='C')
    pdf.ln(10)

    for user_input, bot_response in chats:
        pdf.multi_cell(0, 10, f"User: {user_input}\nBot: {bot_response}\n", border=0)
        pdf.ln(2)

    pdf_path = f"chat_history_user_{user_id}.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True)

# Run server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
































