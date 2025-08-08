# Premium Text+Voice ChatBot (Gemini-enabled)

This is a **single-file** Streamlit project implementing a premium text+voice chatbot. It uses Google Gemini (via the google-genai SDK) as the primary LLM when available, and `pyttsx3` for local voice output.

## Features
- Gemini-powered natural-language answers (optional; requires GEMINI_API_KEY)
- Voice output (pyttsx3) with controls: rate, volume, and system voice selection
- Mood/Personality modes: Friendly, Formal, Playful, Sarcastic
- Smart read (first few sentences + "Continue reading")
- Commands: `/help`, `/clear`, `/time`, `/date`, `/about`
- Session memory (chat kept in Streamlit session state)

## Files in this package
- `premium_chatbot.py` — main Streamlit app (single file)
- `requirements.txt` — Python dependencies
- `.streamlit/secrets.toml.template` — template for storing GEMINI_API_KEY
- `README.md` — this file

## Quick setup (local)
1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\\Scripts\\activate    # Windows (PowerShell)
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Gemini API key (optional — Gemini provides better answers):
   - Linux / macOS:
     ```bash
     export GEMINI_API_KEY="YOUR_KEY_HERE"
     ```
   - Windows (PowerShell):
     ```powershell
     setx GEMINI_API_KEY "YOUR_KEY_HERE"
     ```
   Or copy the contents of `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml` and add your key.

4. Run the app:
   ```bash
   streamlit run premium_chatbot.py
   ```

## Notes
- If `google-genai` (Gemini SDK) is not installed or `GEMINI_API_KEY` is missing, the app still runs in a degraded mode where Gemini responses are replaced with a helpful warning. Install the SDK and set `GEMINI_API_KEY` to enable full features.
- For **high-quality** neural TTS, consider replacing `pyttsx3` with a cloud TTS (Google Cloud TTS) — this requires additional credentials.

If you want I can also prepare a ready-to-deploy folder for **Streamlit Cloud / Heroku / Railway**, with a `Procfile` and deployment notes.