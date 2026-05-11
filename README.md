# VividAI — AI Image Generator

A production-grade AI image generation web app built with Flask and Hugging Face.

## Features
- User authentication (Register / Login / Logout)
- Async image generation using Python threading
- Multiple AI models (SDXL, FLUX, DreamShaper)
- Personal gallery with favorites & delete
- Rate limiting (10 images/hour per user)
- Structured logging to file + console
- Clean app factory pattern with Blueprints

## Tech Stack
- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **AI:** Hugging Face Inference API
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** HTML, CSS, Vanilla JS

## Setup

### 1. Clone & install
git clone https://github.com/yourname/vividai.git
cd vividai
pip install -r requirements.txt

### 2. Configure environment
cp .env.example .env
# Add your HF_TOKEN and SECRET_KEY in .env

### 3. Run
python run.py

### 4. Production
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"

## Project Structure
app/
  models.py        → Database models
  routes/          → Blueprints (auth, main, gallery)
  services/        → Business logic (image generation)
  utils/           → Helper functions
config.py          → Environment-based configuration
run.py             → Entry point