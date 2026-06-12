import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
KIWI_MCP_URL = os.environ.get("KIWI_MCP_URL")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("Missing ANTHROPIC_API_KEY in .env")
if not KIWI_MCP_URL:
    raise RuntimeError("Missing KIWI_MCP_URL in .env")

SYSTEM_PROMPT = (
    "You are a flight search assistant. Use the Kiwi tools to search for flights. "
    "Present results sorted by price, showing price, total duration, number of stops, "
    "and airline for each option. When the user asks to compare flights, highlight the "
    "best option for each criterion (cheapest, fastest, fewest stops). "
    "Format your responses using markdown tables where appropriate."
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = Flask(__name__, static_folder="static")
CORS(app)

# One conversation history per server session (single-user dev tool)
conversation: list[dict] = []


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = (data or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "empty message"}), 400

    conversation.append({"role": "user", "content": user_message})

    response = client.beta.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        mcp_servers=[{"type": "url", "url": KIWI_MCP_URL, "name": "kiwi"}],
        messages=conversation,
        betas=["mcp-client-2025-04-04"],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    reply = "\n".join(text_parts) if text_parts else "(no response)"

    conversation.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    conversation.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Flight agent running at http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)
