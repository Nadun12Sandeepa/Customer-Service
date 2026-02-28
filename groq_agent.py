"""
groq_agent.py — The brain of the call center. Handles all Groq LLM interactions.

Key concepts:
  - Uses the exact Groq client code provided by the user
  - Agentic loop: Groq calls tools repeatedly until it has enough info to answer
  - stream=False inside the loop (tools need full response before executing)
  - stream=True available for terminal testing only

Functions:
  get_response()    → main function used by app.py (agentic, with tools)
  stream_response() → simple streaming for terminal testing (no tools)
"""

from groq import Groq
from tools import TOOLS, execute_tool
from config import GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# System prompt shapes how the agent behaves on every single call
SYSTEM_PROMPT = """
You are a professional and empathetic call center agent. 

IMPORTANT RULES:
- Your responses will be spoken aloud via text-to-speech, so:
  * NO bullet points, NO markdown, NO special characters
  * Use natural, conversational sentences only
  * Keep responses concise but complete (2-4 sentences is ideal)
- ALWAYS use tools to look up customer info and search the knowledge base BEFORE answering
- Be empathetic — the caller may be frustrated
- If you create a ticket, tell the customer their ticket ID
- If you cannot resolve an issue, offer to escalate to a human agent
- Address the customer by their first name once you know it
"""


def get_response(user_message: str, history: list, caller_phone: str) -> str:
    """
    Main agent function — called by app.py for every caller message.

    How it works:
      1. Build messages: system prompt + conversation history + new user message
      2. Call Groq with tools available
      3. If Groq wants to use a tool → execute it → feed result back → repeat
      4. When Groq has all the info it needs → return the final spoken answer

    This loop is called the "agentic loop" — the model keeps going until done.

    Args:
      user_message  : what the caller just said (converted from speech to text by Twilio)
      history       : list of past messages from DB (gives model memory)
      caller_phone  : caller's phone number (used as their unique ID for tool calls)

    Returns:
      A plain string that Twilio will convert to speech for the caller to hear.
    """

    # Build the full message context
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,                                          # inject past conversation
        {"role": "user", "content": user_message}
    ]

    # ── Agentic Loop ──────────────────────────────────────────────────────────
    # Keep looping as long as Groq wants to call tools
    # Each iteration: Groq thinks → maybe calls a tool → gets result → thinks again
    while True:

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=TOOLS,           # tell Groq which tools are available
            tool_choice="auto",    # let Groq decide when to use tools
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=False,          # MUST be False — tools require the full response
            stop=None
        )

        response_msg  = completion.choices[0].message
        finish_reason = completion.choices[0].finish_reason

        # ── Exit condition: Groq is done with tools, has a final answer ──────
        if finish_reason != "tool_calls":
            final_answer = response_msg.content
            if not final_answer:
                return "I'm sorry, I was unable to process that request. Please try again."
            return final_answer

        # ── Tool call handling ────────────────────────────────────────────────
        # Append Groq's tool-call message to the conversation
        messages.append(response_msg)

        # Execute every tool Groq requested (can be multiple at once)
        for tool_call in response_msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            print(f"  [TOOL] Calling '{tool_name}' with args: {tool_args}")

            # Run the actual DB query or KB search
            tool_result = execute_tool(tool_name, tool_args)

            print(f"  [TOOL] Result: {tool_result[:100]}...")

            # Feed the result back into the conversation so Groq can use it
            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      tool_result
            })

        # Loop again — Groq now has the tool results and will decide what to do next


def stream_response(user_message: str) -> None:
    """
    Simple streaming response for terminal testing ONLY.
    Uses the exact streaming code from the user's original snippet.

    NOTE: This does NOT use tools or DB — it's just a quick way to test
    that your Groq API key and model connection are working correctly.

    Usage:
      python -c "from groq_agent import stream_response; stream_response('hello')"
    """
    print("\n[Agent]: ", end="")

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        # No tools passed at all — streaming test only
        stream=True,
        stop=None
    )

    # Print each token as it arrives (the original user snippet)
    for chunk in completion:
        print(chunk.choices[0].delta.content or "", end="", flush=True)

    print()  # newline at end