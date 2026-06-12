import os
import sys
import io
from dotenv import load_dotenv
import anthropic

# Force UTF-8 output on Windows so emoji in flight results don't crash
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
KIWI_MCP_URL = os.environ.get("KIWI_MCP_URL")

if not ANTHROPIC_API_KEY:
    sys.exit("Missing ANTHROPIC_API_KEY in .env")
if not KIWI_MCP_URL:
    sys.exit("Missing KIWI_MCP_URL in .env")

SYSTEM_PROMPT = (
    "You are a flight search assistant. Use the Kiwi tools to search for flights. "
    "Present results sorted by price, showing price, total duration, number of stops, "
    "and airline for each option. When the user asks to compare flights, highlight the "
    "best option for each criterion (cheapest, fastest, fewest stops)."
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversation: list[dict] = []


def chat(user_message: str) -> str:
    conversation.append({"role": "user", "content": user_message})

    response = client.beta.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        mcp_servers=[
            {
                "type": "url",
                "url": KIWI_MCP_URL,
                "name": "kiwi",
            }
        ],
        messages=conversation,
        betas=["mcp-client-2025-04-04"],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    assistant_message = "\n".join(text_parts) if text_parts else "(no text response)"
    conversation.append({"role": "assistant", "content": assistant_message})
    return assistant_message


def main():
    print("Flight Quote Agent (type 'quit' to exit)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        reply = chat(user_input)
        print(f"\nAgent: {reply}\n")


if __name__ == "__main__":
    main()
