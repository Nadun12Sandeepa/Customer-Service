"""
test_terminal.py — Test the call center agent WITHOUT needing Twilio or a real phone call.
"""

from groq_agent import get_response
from groq import Groq
from config import GROQ_API_KEY

print("=" * 60)
print("  CALL CENTER TERMINAL TEST")
print("=" * 60)

# ── Test 1: Basic API connection (no tools, no streaming) ─────
print("\n[TEST 1] Basic Groq API connection test:")
try:
    _client = Groq(api_key=GROQ_API_KEY)
    _resp = _client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        temperature=1,
        max_completion_tokens=100,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )
    print(f"Agent: {_resp.choices[0].message.content}")
    print("✅ Groq API connection working!")
except Exception as e:
    print(f"❌ Groq API error: {e}")

# ── Test 2: FAQ search (no DB needed) ────────────────────────
print("\n[TEST 2] FAQ / Knowledge base search:")
try:
    reply = get_response(
        user_message="I forgot my password, how do I reset it?",
        history=[],
        caller_phone="+1234567890"
    )
    print(f"Agent: {reply}")
    print("✅ Knowledge base working!")
except Exception as e:
    print(f"❌ Error: {e}")

# ── Test 3: Customer account lookup (needs DB) ────────────────
print("\n[TEST 3] Customer account lookup (requires PostgreSQL):")
try:
    reply = get_response(
        user_message="Hi, can you check my account status?",
        history=[],
        caller_phone="+1234567890"
    )
    print(f"Agent: {reply}")
    print("✅ Database working!")
except Exception as e:
    print(f"❌ DB error (skip if PostgreSQL not set up yet): {e}")

# ── Test 4: Suspended account (needs DB) ─────────────────────
print("\n[TEST 4] Suspended account inquiry (requires PostgreSQL):")
try:
    reply = get_response(
        user_message="Why is my account suspended and how do I fix it?",
        history=[],
        caller_phone="+0987654321"
    )
    print(f"Agent: {reply}")
except Exception as e:
    print(f"❌ DB error (skip if PostgreSQL not set up yet): {e}")

# ── Test 5: Interactive chat mode ────────────────────────────
print("\n[TEST 5] Interactive mode (type 'quit' to exit):")
print("Note: DB tools will fail if PostgreSQL is not set up yet.\n")

history = []
phone   = "+1234567890"

while True:
    try:
        user_input = input("You: ").strip()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break

    if user_input.lower() in ("quit", "exit", "q", ""):
        print("Goodbye!")
        break

    try:
        reply = get_response(user_input, history, phone)
        print(f"Agent: {reply}\n")
        history.append({"role": "user",      "content": user_input})
        history.append({"role": "assistant", "content": reply})
    except Exception as e:
        print(f"Error: {e}\n")