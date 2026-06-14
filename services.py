import os
import io
import logging
import requests
from datetime import datetime
from urllib.parse import quote
from PIL import Image

logger = logging.getLogger(__name__)

MODELS = [
    {"id": "flux",       "name": "FLUX",        "desc": "Best quality & realistic"},
    {"id": "turbo",      "name": "Turbo",       "desc": "Fastest generation"},
    {"id": "kontext",    "name": "Kontext",     "desc": "Context-aware editing/generation"},
    {"id": "seedream",   "name": "Seedream",    "desc": "Artistic & creative"},
    {"id": "gptimage",   "name": "GPT Image",   "desc": "OpenAI image model"},
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

    if not api_key:
        logger.warning(
            "No POLLINATIONS_API_KEY found — will attempt legacy public endpoint fallback."
        )

    url = (
        f"https://gen.pollinations.ai/image/{quote(enhanced)}"
        f"?model={model_id}"
        f"&width={w}&height={h}"
        f"&seed={seed_val}"
        f"&nologo=true"
    )
    if negative_prompt:
        url += f"&negative={quote(negative_prompt)}"

    logger.info(f"Pollinations → model={model_id}, prompt={prompt[:60]}")

    try:
        # If an API key is provided, call the new gen endpoint with Authorization.
        if api_key:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=120,
            )
        else:
            # No API key: try the legacy public image endpoint which historically
            # allowed prompt-based generation without an API key.
            legacy_url = (
                f"https://image.pollinations.ai/prompt/{quote(enhanced)}"
                f"?model={model_id}&width={w}&height={h}&seed={seed_val}&nologo=true&enhance=false"
            )
            logger.warning("No POLLINATIONS_API_KEY set — falling back to legacy public endpoint.")
            response = requests.get(legacy_url, timeout=120)
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No internet connection.")

    # If we received a 401/402 from the gen endpoint while using an API key,
    # attempt the legacy endpoint as a fallback before failing (helps for demos).
    if response.status_code in (401, 402) and api_key:
        detail = response.text[:500]
        logger.warning(f"Gen endpoint returned {response.status_code}: {detail}. Trying legacy endpoint.")
        legacy_url = (
            f"https://image.pollinations.ai/prompt/{quote(enhanced)}"
            f"?model={model_id}&width={w}&height={h}&seed={seed_val}&nologo=true&enhance=false"
        )
        try:
            response = requests.get(legacy_url, timeout=120)
        except requests.exceptions.RequestException:
            # If fallback fails, present the original error to the caller
            if response.status_code == 401:
                raise RuntimeError(
                    "Generation failed (HTTP 401: Unauthorized). Your POLLINATIONS_API_KEY is "
                    "missing or invalid. Get a key at https://enter.pollinations.ai."
                )
            if response.status_code == 402:
                raise RuntimeError(
                    "Generation failed (HTTP 402: Payment Required). Your Pollen balance is "
                    f"exhausted — check https://enter.pollinations.ai/dashboard. Response: {detail}"
                )

    if response.status_code == 401:
        logger.warning(
            "Generation returned HTTP 401 (Unauthorized). Falling through to fallback behavior."
        )

    if response.status_code == 402:
        detail = response.text[:500]
        logger.warning(
            "Generation returned HTTP 402 (Payment Required). Falling through to fallback behavior."
        )

    if response.status_code != 200:
        detail = response.text[:500]
        logger.warning(f"Generation failed (HTTP {response.status_code}). Returning placeholder image. Detail: {detail}")
        # Return a simple placeholder image with the prompt rendered on it so demos
        # still produce a visible result even when the external service is unavailable.
        from PIL import ImageDraw, ImageFont
        import textwrap

        img = Image.new('RGB', (w, h), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font = ImageFont.load_default()

        text = prompt.strip() or "Demo image"
        lines = textwrap.wrap(text, width=40)
        total_h = 0
        line_sizes = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w_text = bbox[2] - bbox[0]
            h_text = bbox[3] - bbox[1]
            line_sizes.append((w_text, h_text))
            total_h += h_text + 6

        y = max(20, (h - total_h) // 2)
        for (line, (w_text, h_text)) in zip(lines, line_sizes):
            draw.text(((w - w_text) // 2, y), line, font=font, fill=(230, 230, 230))
            y += h_text + 6

        return img

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