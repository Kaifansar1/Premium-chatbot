import os
import streamlit as st
from datetime import datetime
import pyttsx3
import re

# Optional Gemini import; app will show a warning if missing
try:
    from google import genai
except Exception:
    genai = None

# -------------------- Configuration --------------------
st.set_page_config(page_title="✨ Premium Text+Voice ChatBot", page_icon="🤖", layout="wide")
st.markdown("<style>body{background:#F4F7FB;} .stTextInput>div{border-radius:10px;}</style>", unsafe_allow_html=True)

# -------------------- Gemini Setup --------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
if genai is None:
    st.warning("Gemini SDK (google.genai) not installed or importable. Install with: pip install google-genai. The app will still run but Gemini features will be disabled.")
else:
    if not GEMINI_API_KEY:
        st.warning("GEMINI_API_KEY not set. Set the GEMINI_API_KEY env var or put it in .streamlit/secrets.toml as GEMINI_API_KEY = '...'.")
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        client = genai.Client()

# -------------------- Voice engine --------------------
engine = pyttsx3.init()
def speak(text, rate=150, volume=1.0, voice_id=None):
    try:
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error("Voice engine error: " + str(e))

# -------------------- Session state --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (role, text, meta)
if "username" not in st.session_state:
    st.session_state.username = ""
if "mood" not in st.session_state:
    st.session_state.mood = "Friendly"
if "voice_on" not in st.session_state:
    st.session_state.voice_on = False
if "voice_rate" not in st.session_state:
    st.session_state.voice_rate = 150
if "voice_volume" not in st.session_state:
    st.session_state.voice_volume = 1.0
if "voice_voice" not in st.session_state:
    st.session_state.voice_voice = None
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "trim_long_reads" not in st.session_state:
    st.session_state.trim_long_reads = True

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.username = st.text_input("Your name", st.session_state.username)
    st.session_state.mood = st.selectbox("Bot Mood / Personality", ["Friendly", "Formal", "Playful", "Sarcastic"])
    st.session_state.voice_on = st.checkbox("🔊 Voice Output", value=st.session_state.voice_on)
    st.session_state.trim_long_reads = st.checkbox("📝 Smart Read (short first)", value=True)
    st.subheader("Voice Controls")
    st.session_state.voice_rate = st.slider("Speaking rate", 80, 260, st.session_state.voice_rate)
    st.session_state.voice_volume = st.slider("Volume", 0.1, 1.0, st.session_state.voice_volume)
    all_voices = engine.getProperty('voices')
    voice_options = {v.name: v.id for v in all_voices}
    selected_voice = st.selectbox("Voice (system)", ["Default"] + list(voice_options.keys()))
    if selected_voice != "Default":
        st.session_state.voice_voice = voice_options[selected_voice]
    else:
        st.session_state.voice_voice = None
    st.markdown("---")
    st.subheader("Pro Toggles")
    use_realtime_apis = st.checkbox("Use specialized external APIs for live facts (weather/news)", value=False)
    st.caption("If off, Gemini will answer from model knowledge; if on, the app can call dedicated APIs for real-time data.")

    st.markdown("---")
    st.write("Commands: `/help`, `/clear`, `/time`, `/date`, `/about`")
    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.success("Chat cleared.")

# -------------------- Utilities --------------------
def system_prompt_for_mood(mood):
    base = "You are a helpful assistant."
    if mood == "Formal":
        return base + " Answer politely, concisely, and formally."
    if mood == "Playful":
        return base + " Be playful, use light humor and friendly tone."
    if mood == "Sarcastic":
        return base + " Use mild sarcasm and witty lines while staying helpful."
    return base + " Be friendly, clear, and encouraging."

def smart_trim_text(text, max_sentences=3):
    sentences = re.split(r'(?<=[.!?])\\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text, None
    short = " ".join(sentences[:max_sentences])
    remainder = " ".join(sentences[max_sentences:])
    return short + " ...", remainder

def generate_gemini_answer(prompt, system_instruction=None, max_output_tokens=1024):
    if genai is None:
        return "⚠️ Gemini SDK not available. Install google-genai and set GEMINI_API_KEY."
    try:
        contents = []
        if system_instruction:
            contents.append({"role":"system","content": system_instruction})
        contents.append({"role":"user","content": prompt})
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            max_output_tokens=max_output_tokens
        )
        # Extract text - different SDK versions may vary
        text = None
        if hasattr(resp, "text") and resp.text:
            text = resp.text
        elif hasattr(resp, "output") and resp.output:
            try:
                text = resp.output[0].content[0].text
            except Exception:
                text = str(resp)
        else:
            text = str(resp)
        return text
    except Exception as e:
        return f"⚠️ Gemini API error: {e}"

def handle_command(cmd):
    cmd = cmd.strip().lower()
    if cmd == "/help":
        return (
            "**Pro Commands**\n"
            "- `/help` — show this help\n"
            "- `/clear` — clear the conversation\n"
            "- `/time` — show current time\n"
            "- `/date` — show current date\n"
            "- `/about` — about this bot\n\n"
            "Use the sidebar to toggle voice & mood."
        )
    if cmd == "/clear":
        st.session_state.chat_history = []
        return "🧹 Cleared the chat."
    if cmd == "/time":
        return "🕒 Current time: " + datetime.now().strftime("%H:%M:%S")
    if cmd == "/date":
        return "📅 " + datetime.now().strftime("%A, %B %d, %Y")
    if cmd == "/about":
        return "✨ Premium Text+Voice ChatBot — powered by Gemini (optional). Developed by Kaif Ansari."
    return None

# -------------------- UI layout --------------------
left_col, right_col = st.columns([3,1])

with right_col:
    st.markdown("### 🔎 Quick Actions")
    if st.button("☰ /help"):
        st.session_state.chat_history.append(("user_cmd", "/help", {}))
    if st.button("🗑 /clear"):
        st.session_state.chat_history.append(("user_cmd", "/clear", {}))
    if st.button("🕒 /time"):
        st.session_state.chat_history.append(("user_cmd", "/time", {}))
    if st.button("📅 /date"):
        st.session_state.chat_history.append(("user_cmd", "/date", {}))

with left_col:
    st.markdown(f"## 🤖 Premium ChatBot — {st.session_state.mood} Mode")
    if st.session_state.username:
        st.markdown(f"**Hello {st.session_state.username}!** Ask me anything. (Tip: use `/help` for commands)")

    chat_container = st.container()
    with chat_container:
        for role, txt, meta in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"<div style='text-align:right;background:#DCF8C6;padding:8px;border-radius:10px;max-width:85%;margin-left:15%;'>{txt}</div>", unsafe_allow_html=True)
            elif role == "assistant":
                st.markdown(f"<div style='text-align:left;background:#ffffff;padding:10px;border-radius:10px;max-width:85%;margin-right:15%;border:1px solid #e6e6e6;'>{txt}</div>", unsafe_allow_html=True)
            elif role == "user_cmd":
                st.markdown(f"<div style='text-align:right;background:#F0F0F0;padding:6px;border-radius:8px;max-width:70%;margin-left:30%;font-size:13px;color:#333'>{txt}</div>", unsafe_allow_html=True)

    user_input = st.text_input("💬 Type your message (or a command)", key="main_input")
    if st.button("Send") or (user_input and st.session_state.get("main_input") == user_input):
        msg = user_input.strip()
        if not msg:
            st.warning("Type a message first.")
        else:
            st.session_state.chat_history.append(("user", msg, {}))
            cmd_result = None
            if msg.startswith("/"):
                cmd_result = handle_command(msg)
                if cmd_result is not None:
                    st.session_state.chat_history.append(("assistant", cmd_result, {}))
                    st.session_state.last_response = cmd_result
                    if st.session_state.voice_on:
                        speak(cmd_result, rate=st.session_state.voice_rate, volume=st.session_state.voice_volume, voice_id=st.session_state.voice_voice)
                    st.experimental_rerun()
                else:
                    st.session_state.chat_history.append(("assistant", "Unknown command. Try /help.", {}))
                    st.experimental_rerun()

            system_inst = system_prompt_for_mood(st.session_state.mood)
            if st.session_state.username:
                system_inst += f" Address the user as {st.session_state.username} when appropriate."

            if msg.lower() in ["continue", "tell me more", "more"]:
                prompt = (st.session_state.last_response or "") + "\n\nPlease continue from where you left off."
            else:
                prompt = msg

            with st.spinner("Thinking..."):
                raw_answer = generate_gemini_answer(prompt, system_instruction=system_inst, max_output_tokens=1024)

            remainder = None
            displayed = raw_answer
            if st.session_state.trim_long_reads:
                displayed, remainder = smart_trim_text(raw_answer, max_sentences=3)

            st.session_state.chat_history.append(("assistant", displayed, {"full": raw_answer, "remainder": remainder}))
            st.session_state.last_response = raw_answer

            if st.session_state.voice_on:
                speak(displayed, rate=st.session_state.voice_rate, volume=st.session_state.voice_volume, voice_id=st.session_state.voice_voice)

            suggestions = []
            if "weather" in msg.lower():
                suggestions = ["Tomorrow's forecast", "Weekly summary", "Humidity details"]
            elif "joke" in msg.lower() or "fun" in msg.lower():
                suggestions = ["Another joke", "Clean joke", "Short pun"]
            else:
                suggestions = ["Explain simply", "Give an example", "Summarize in 2 lines"]

            cols = st.columns(len(suggestions))
            for i, s in enumerate(suggestions):
                if cols[i].button(s):
                    st.session_state.chat_history.append(("user", s, {}))
                    with st.spinner("Thinking..."):
                        ans = generate_gemini_answer(s, system_instruction=system_inst, max_output_tokens=512)
                    st.session_state.chat_history.append(("assistant", ans, {}))
                    if st.session_state.voice_on:
                        speak(ans, rate=st.session_state.voice_rate, volume=st.session_state.voice_volume, voice_id=st.session_state.voice_voice)

    if st.session_state.chat_history:
        last_role, last_text, last_meta = st.session_state.chat_history[-1]
        if last_role == "assistant" and last_meta and last_meta.get("remainder"):
            if st.button("Continue reading"):
                remainder_text = last_meta["remainder"]
                st.session_state.chat_history.append(("assistant", remainder_text, {"full": last_meta["full"], "remainder": None}))
                st.session_state.last_response = last_meta["full"]
                if st.session_state.voice_on:
                    speak(remainder_text, rate=st.session_state.voice_rate, volume=st.session_state.voice_volume, voice_id=st.session_state.voice_voice)

st.markdown("---")
st.markdown("Made with ❤️ by Kaif Ansari — Gemini-powered text + voice chatbot (Gemini optional)")
