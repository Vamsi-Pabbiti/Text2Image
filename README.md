# Text2Image — AI Image Generator

A production-grade AI image generation web app built with Python & Flask.

## Features
- User authentication (Register / Login / Logout)
- Async image generation using threading
- Multiple AI models (FLUX, DreamShaper, Turbo)
- Personal gallery with favorites & delete
- Persistent storage with SQLite
- Clean logging system

## Tech Stack
- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **AI:** Pollinations AI API
- **Database:** SQLite
- **Frontend:** HTML, CSS, Vanilla JS

## Setup
pip install -r requirements.txt
python app.py

## Project Structure
vividai/
├── app.py          # Main Flask app
├── models.py       # Database models
├── services.py     # Image generation logic
├── config.py       # Configuration
├── static/         # CSS & JS
└── templates/      # HTML templates