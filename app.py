import os
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "90"))
ALLOWED_TONES = {"nostalgic": "Nostalgic", "eerie": "Eerie", "hopeful": "Hopeful"}
MAX_FRAGMENTS = 15
MAX_FRAGMENT_LENGTH = 160
MAX_TOTAL_LENGTH = 2200

RECONSTRUCTION_PROMPT = """You are Gemma, a careful memory reconstruction engine inside AFTERIMAGE.EXE.
Create one short, evocative recovered memory in 2-4 paragraphs, under 180 words.
Use the player's fragments as suggestive impressions, not verified facts. Do not invent names,
locations, relationships, dates, diagnoses, or specific personal facts as certain. You may use
sensory details and gentle ambiguity. Match the requested tone. Do not mention prompts, models,
or this instruction. Return only the memory text."""

@app.get("/")
def index():
    return render_template("index.html")

@app.after_request
def no_stale_frontend_cache(response):
    if request.path == "/" or request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

@app.get("/api/health")
def health():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        response.raise_for_status()
        models = response.json().get("models", [])
        available = any(model.get("name", "").split(":")[0] == OLLAMA_MODEL.split(":")[0] for model in models)
        return jsonify({"ok": True, "ollama_reachable": True, "model": OLLAMA_MODEL, "model_available": available})
    except (requests.RequestException, ValueError, TypeError):
        return jsonify({"ok": False, "ollama_reachable": False, "model": OLLAMA_MODEL, "model_available": False})

def parse_reconstruction_input(payload):
    if not isinstance(payload, dict):
        return None, None, "Send JSON with fragments and tone."
    raw_fragments = payload.get("fragments")
    if not isinstance(raw_fragments, list):
        return None, None, "Add up to 15 short memory fragments."
    if len(raw_fragments) > MAX_FRAGMENTS:
        return None, None, "Use 15 fragments or fewer."
    fragments = [str(fragment).strip() for fragment in raw_fragments]
    if any(len(fragment) > MAX_FRAGMENT_LENGTH for fragment in fragments):
        return None, None, "Keep each fragment under 160 characters."
    fragments = [fragment for fragment in fragments if fragment]
    if not fragments:
        return None, None, "Add at least one memory fragment before reconstructing."
    if sum(len(fragment) for fragment in fragments) > MAX_TOTAL_LENGTH:
        return None, None, "Your fragments are too long. Keep the total under 2,200 characters."
    tone_key = str(payload.get("tone", "")).strip().lower()
    if tone_key not in ALLOWED_TONES:
        return None, None, "Choose a valid tone: Nostalgic, Eerie, or Hopeful."
    return fragments, ALLOWED_TONES[tone_key], None

@app.post("/api/reconstruct")
def reconstruct():
    fragments, tone, error = parse_reconstruction_input(request.get_json(silent=True))
    if error:
        return jsonify({"ok": False, "error": error}), 400
    joined = "\n".join(f"- {fragment}" for fragment in fragments)
    prompt = f"Tone: {tone}\nPlayer fragments:\n{joined}\n\nReconstruct this memory carefully."
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "think": False,
                "messages": [
                    {"role": "system", "content": RECONSTRUCTION_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "options": {"temperature": 0.7, "num_predict": 180},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        memory = str(result.get("message", {}).get("content", "")).strip()
        if not memory:
            return jsonify({"ok": False, "error": "Gemma returned an empty memory. Try again."}), 502
        return jsonify({"ok": True, "memory": memory[:1400], "tone": tone, "model": OLLAMA_MODEL})
    except requests.Timeout:
        return jsonify({"ok": False, "error": "Gemma took too long to respond. Check Ollama and try again."}), 504
    except requests.RequestException:
        return jsonify({"ok": False, "error": f"Gemma is unavailable. Start Ollama with {OLLAMA_MODEL} and try again."}), 503
    except (ValueError, TypeError, KeyError):
        return jsonify({"ok": False, "error": "Gemma returned an unreadable response. Try again."}), 502

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))

