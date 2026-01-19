from flask import Flask, render_template, request, url_for
import os
from datetime import datetime
from huggingface_hub import InferenceClient
import time

app = Flask(__name__)

# 🔑 Token updated as requested
HF_TOKEN = os.getenv("HF_TOKEN")

# Increased timeout to 120 seconds to give the model time to wake up
client = InferenceClient(api_key=HF_TOKEN, timeout=120)

IMAGE_FOLDER = os.path.join("static", "images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    image_filename = None
    error = None

    if request.method == "POST":
        user_prompt = request.form.get("prompt")
        if not user_prompt:
            error = "Please enter a prompt!"
        else:
            try:
                detailed_prompt = (
                    f"A professional, high-quality, {user_prompt}, photorealistic, "
                    f"cinematic lighting, 8k resolution, highly detailed, sharp focus"
                )
                image = client.text_to_image(
                    detailed_prompt, 
                    model="stabilityai/stable-diffusion-xl-base-1.0"
                )
s
                filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                save_path = os.path.join(IMAGE_FOLDER, filename)
                image.save(save_path)
                image_filename = filename

            except Exception as e:
                error_msg = str(e)
                # Specific check for the 'Loading' state (503 error)
                if "503" in error_msg:
                    error = "AI is still waking up. Please wait 15 seconds and click 'Generate' again."
                elif "401" in error_msg:
                    error = "Authentication failed. Please verify your token is active."
                else:
                    error = f"Generation failed: {error_msg if error_msg else 'Server timed out. Try again.'}"

    return render_template("index.html", image_filename=image_filename, error=error)

if __name__ == "__main__":
    app.run()