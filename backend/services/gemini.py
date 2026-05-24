import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_GEN_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")
_model = genai.GenerativeModel(_GEN_MODEL)


def embed_text(text: str) -> list[float]:
    """Embed a single string → 768-dim Gemini vector."""
    result = genai.embed_content(model=_EMBED_MODEL, content=text[:8000])
    return result["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings. Sequential — Gemini has no true batch endpoint."""
    return [embed_text(t) for t in texts]


def generate(prompt: str) -> str:
    """Plain text generation."""
    try:
        response = _model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Gemini error: {e}]"


def generate_json(prompt: str) -> str:
    """Generation expected to return JSON — same call, caller parses."""
    return generate(prompt)


def describe_blueprint_page(image_path: str) -> str:
    """
    Vision call: extract technical information from a blueprint page image.
    Called for drawing-heavy pages where text extraction yields < 200 chars.
    """
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        img_part = {"mime_type": "image/png", "data": image_data}
        prompt = (
            "You are analysing a construction engineering drawing. "
            "Extract and list ALL of the following that are visible:\n"
            "1. All dimensions and measurements (include units — mm, m, inches)\n"
            "2. Material specifications or concrete grades (e.g. C25, M30, f'c=4000psi)\n"
            "3. Rebar sizes, spacing, and arrangement (e.g. 16mm dia @ 150mm c/c)\n"
            "4. Grid references, sheet numbers, revision marks\n"
            "5. Component labels: beams, columns, slabs, walls, MEP elements\n"
            "6. Any notes, callouts, or specification references\n"
            "7. Elevation levels or datum references\n"
            "Be precise and technical. Format as a numbered structured list. "
            "If a section has nothing visible, skip it."
        )
        response = _model.generate_content([img_part, prompt])
        return response.text
    except Exception as e:
        print(f"[gemini.describe_blueprint_page] Failed: {e}")
        return ""
