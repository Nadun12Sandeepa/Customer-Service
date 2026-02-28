"""
app.py — Complete voice call center using Twilio + Groq.

Every message between caller and system happens through REAL VOICE:
  - Caller speaks  → Twilio STT → text sent here
  - Agent replies  → text sent back → Twilio TTS → caller hears voice

Endpoints:
  POST /incoming-call  → fired when someone calls your Twilio number
  POST /handle-speech  → fired after Twilio converts caller speech to text
  POST /call-status    → fired when call ends (for logging)
  GET  /test           → health check
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from groq_agent import get_response
from database import get_history, save_turn

app = Flask(__name__)

# ── Voice Settings ────────────────────────────────────────────
# Free Twilio voices: "alice", "man", "woman"
# Natural voices (Twilio Neural): "Polly.Joanna", "Polly.Matthew", "Polly.Amy"
AGENT_VOICE    = "Polly.Joanna"
AGENT_LANGUAGE = "en-US"
SPEECH_TIMEOUT = "auto"
INPUT_TIMEOUT  = 8


@app.route("/incoming-call", methods=["POST"])
def incoming_call():
    """
    Entry point fired when someone calls your Twilio number.
    Plays a greeting and starts listening for caller's voice.
    """
    caller_phone = request.form.get("From", "unknown")
    print(f"\nIncoming call from: {caller_phone}")

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/handle-speech",
        method="POST",
        timeout=INPUT_TIMEOUT,
        speech_timeout=SPEECH_TIMEOUT,
        language=AGENT_LANGUAGE,
        enhanced=True
    )
    gather.say(
        "Hello! Thank you for calling our support center. How can I help you today?",
        voice=AGENT_VOICE,
        language=AGENT_LANGUAGE
    )
    response.append(gather)

    response.say("I didn't hear anything. Please call back when ready.", voice=AGENT_VOICE)
    response.hangup()

    return str(response)


@app.route("/handle-speech", methods=["POST"])
def handle_speech():
    """
    Called every time the caller finishes speaking.
    Twilio already converted voice to text (STT).
    We process it with Groq and send text back.
    Twilio converts that text back to voice (TTS) for the caller.
    """
    user_speech  = request.form.get("SpeechResult", "").strip()
    caller_phone = request.form.get("From", "unknown")
    confidence   = request.form.get("Confidence", "?")

    print(f"\n[{caller_phone}] Caller said: '{user_speech}' (confidence: {confidence})")

    response = VoiceResponse()

    # If STT returned nothing, ask caller to repeat
    if not user_speech:
        gather = Gather(
            input="speech",
            action="/handle-speech",
            method="POST",
            timeout=INPUT_TIMEOUT,
            speech_timeout=SPEECH_TIMEOUT,
            language=AGENT_LANGUAGE,
            enhanced=True
        )
        gather.say("I didn't catch that. Could you please repeat?", voice=AGENT_VOICE)
        response.append(gather)
        return str(response)

    # Load past conversation from DB for memory
    history = get_history(caller_phone)

    # Get Groq agent response (agentic tool-calling loop)
    print(f"  Processing with Groq...")
    try:
        reply = get_response(user_speech, history, caller_phone)
    except Exception as e:
        print(f"  Groq error: {e}")
        reply = "I'm sorry, I'm having a technical issue. Please hold for a moment."

    print(f"  Agent reply: '{reply}'")

    # Save conversation to DB
    try:
        save_turn(caller_phone, user_speech, reply)
    except Exception as e:
        print(f"  DB warning: {e}")

    # Send reply as voice + keep listening for next caller message
    gather = Gather(
        input="speech",
        action="/handle-speech",
        method="POST",
        timeout=INPUT_TIMEOUT,
        speech_timeout=SPEECH_TIMEOUT,
        language=AGENT_LANGUAGE,
        enhanced=True
    )
    # THIS is where text becomes voice -- Twilio TTS
    gather.say(reply, voice=AGENT_VOICE, language=AGENT_LANGUAGE)
    response.append(gather)

    # If caller is silent after agent finishes speaking
    gather2 = Gather(
        input="speech",
        action="/handle-speech",
        method="POST",
        timeout=INPUT_TIMEOUT,
        speech_timeout=SPEECH_TIMEOUT,
        language=AGENT_LANGUAGE,
        enhanced=True
    )
    gather2.say("Is there anything else I can help you with?", voice=AGENT_VOICE)
    response.append(gather2)

    # End call gracefully if still no response
    response.say("Thank you for calling. Have a great day. Goodbye!", voice=AGENT_VOICE)
    response.hangup()

    return str(response)


@app.route("/call-status", methods=["POST"])
def call_status():
    """Logs when a call ends."""
    print(f"\nCall ended: {request.form.get('From')} | "
          f"Status: {request.form.get('CallStatus')} | "
          f"Duration: {request.form.get('CallDuration', 0)}s")
    return "", 204


@app.route("/test", methods=["GET"])
def test():
    """Health check."""
    return {"status": "Call center running", "voice": AGENT_VOICE, "model": "openai/gpt-oss-120b"}


if __name__ == "__main__":
    print("=" * 50)
    print("  AI VOICE CALL CENTER")
    print("=" * 50)
    print(f"  Voice : {AGENT_VOICE}")
    print(f"  Model : openai/gpt-oss-120b")
    print()
    print("  To go live:")
    print("  1. python app.py")
    print("  2. ngrok http 5000")
    print("  3. Paste ngrok URL into Twilio webhook")
    print("  4. Call your Twilio number!")
    print("=" * 50)
    app.run(debug=True, port=5000)