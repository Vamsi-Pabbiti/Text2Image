import os
import io
import logging
import requests
from datetime import datetime
from urllib.parse import quote
from PIL import Image

logger = logging.getLogger(__name__)

MODELS = [
    {"id": "flux",         "name": "FLUX",          "desc": "Best quality & realistic"},
    {"id": "flux-realism", "name": "FLUX Realism",   "desc": "Ultra photorealistic"},
    {"id": "turbo",        "name": "Turbo",          "desc": "Fastest generation"},
    {"id": "dreamshaper",  "name": "DreamShaper",    "desc": "Artistic & creative"},
]

SIZES = {
    "square":    (1024, 1024),
    "landscape": (1344, 768),
    "portrait":  (768, 1344),
}


def get_model_ids():
    return [m["id"] for m in MODELS]


def generate_image(api_key, prompt, negative_prompt, model_id, aspect, steps, guidance, seed=None):
    w, h     = SIZES.get(aspect, (1024, 1024))
    enhanced = f"{prompt}, masterpiece, best quality, highly detailed, sharp focus, 8k"
    seed_val = seed if seed is not None else 42

    url = (
        f"https://image.pollinations.ai/prompt/{quote(enhanced)}"
        f"?model={model_id}"
        f"&width={w}&height={h}"
        f"&seed={seed_val}"
        f"&nologo=true"
    )
    if negative_prompt:
        url += f"&negative={quote(negative_prompt)}"

    logger.info(f"Pollinations → model={model_id}, prompt={prompt[:60]}")

    try:
        response = requests.get(url, timeout=120)
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No internet connection.")

    if response.status_code != 200:
        raise RuntimeError(f"Generation failed (HTTP {response.status_code}). Try again.")

    if "image" not in response.headers.get("Content-Type", ""):
        raise RuntimeError("Unexpected response. Try a different model.")

    image = Image.open(io.BytesIO(response.content))
    logger.info("Image generated successfully.")
    return image


def save_image(image, user_id, folder):
    os.makedirs(folder, exist_ok=True)
    filename = f"img_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    image.save(os.path.join(folder, filename))
    return filename