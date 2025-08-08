# premium_chatbot.py
import os
import json
import streamlit as st
from datetime import datetime
import re
import textwrap
from gtts import gTTS
import tempfile

# ---------------------------
# Safe rerun helper for Streamlit versions compatibility
# ---------------------------
def safe_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        # For newer Streamlit versions where experimental_rerun is removed
        from streamlit.runtime.scriptrunner import request_rerun
        request_rerun()

# ---------------------------
# GEMINI / TTS CONFIGURATION
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None) or st.secrets.get("GEMINI_API_KEY", None) or "YOUR_GEMINI_API_KEY"

try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    gemini_available = True
except Exception as e:
    genai = None
    gemini_available = False

# ---------------------------
# PERSISTENT MEMORY
# ---------------------------
MEMORY_FILE = "memory.json"
MAX_MEMORY_MESSAGES = 500

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem[-MAX_MEMORY_MESSAGES:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error("Could not save memory: " + str(e))

# ---------------------------
# UTILITIES
# ---------------------------
def smart_trim_text(text, max_sentences=3):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text, None
    short = " ".join(sentences[:max_sentences])
    remainder = " ".join(sentences[max_sentences:])
    return short + " ...", remainder

def offline_fallback(prompt):
    p = prompt.strip().lower()
    if p in ("hi", "hello", "hey"):
        return "Hi — I'm offline right now, but I can still answer a few simple questions. Try asking 'time' or 'date'."
    if "time" in p:
        return "I can't fetch external data offline, but your system time is available locally."
    if "date" in p:
        return datetime.now().strftime("%A, %B %d, %Y")
    if "joke" in p:
        return "Why did the programmer quit his job? Because he didn't get arrays (a raise)."
    return "Sorry — I can't reach Gemini now. Try again later or enable offline-friendly prompts."

def format_role(role):
    return "You" if role == "user" else "Assistant"

# ---------------------------
# GEMINI INTERACTION
# ---------------------------
def generate_gemini_answer(prompt, system_instruction=None, max_output_tokens=512):
    if not gemini_available or genai is None:
        return offline_fallback(prompt)
    try:
        contents = []
        if system_instruction:
            contents.append({"role": "system", "content": system_instruction})
        contents.append({"role": "user", "content": prompt})
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        resp = model.generate_content(
            prompt if isinstance(prompt, str) else prompt,
            max_output_tokens=max_output_tokens
        )
        if hasattr(resp, "text") and resp.text:
            return resp.text
        if hasattr(resp, "output") and resp.output:
            try:
                return resp.output[0].content[0].text
            except Exception:
                return str(resp)
        return str(resp)
    except Exception as e:
        return f"⚠️ Gemini error: {e}. (Falling back offline.)\n\n" + offline_fallback(prompt)

# ---------------------------
# VOICE (TTS) FUNCTIONS - REPLACED pyttsx3 with gTTS for cloud compatibility
# ---------------------------
def speak(text, rate=160, volume=0.9, voice_id=None):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            tts.save(fp.name)
            fp.seek(0)
            audio_bytes = fp.read()
            st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.warning("TTS failed: " + str(e))

# ---------------------------
# STREAMLIT APP UI + LOGIC
# ---------------------------

st.set_page_config(page_title="✨ Premium Text+Voice ChatBot", page_icon="🤖", layout="wide")

st.markdown("""
<style>
:root { --bg: #0f1723; --card: #0b1220; --muted: #9aa4b2; --accent: #00a6fb; --user:#0b9a6c; }
body { background: radial-gradient(circle at 10% 20%, #0b1220, #07101a 40%, #02060a); color: #e6eef6; }
.chat-area { max-width: 900px; margin: auto; padding: 18px; border-radius: 14px; background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); box-shadow: 0 6px 30px rgba(0,0,0,0.6); }
.header { text-align:center; padding-bottom:10px; }
.subtle { color: var(--muted); font-size: 13px; }
.bubble { padding:12px 14px; border-radius: 12px; display: inline-block; margin: 8px 0; max-width:80%; line-height:1.4; }
.bubble.user { background: linear-gradient(90deg,#075E54,#087f66); color:#fff; margin-left:auto; border-bottom-right-radius:4px; }
.bubble.bot { background: linear-gradient(90deg,#0b1220,#0f1723); color:#e6eef6; border:1px solid rgba(255,255,255,0.03); border-bottom-left-radius:4px; }
.meta { font-size:12px; color:var(--muted); margin-top:4px; }
.input-row { display:flex; gap:8px; margin-top:12px; }
.textbox { flex:1; }
.send-btn { background: linear-gradient(90deg,#00a6fb,#0066ff); border:none; color:white; padding:10px 14px; border-radius:10px; cursor:pointer; }
.suggest { background: rgba(255,255,255,0.04); padding:8px 10px; border-radius:8px; border:1px solid rgba(255,255,255,0.03); margin-right:8px; cursor:pointer; display:inline-block; color:#e6eef6; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#07101a,#031020); color:#e6eef6; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='chat-area'>", unsafe_allow_html=True)
st.markdown("<div class='header'><h1 style='margin:0'>🤖 Premium Text + Voice ChatBot</h1><div class='subtle'>Gemini-backed answers • Voice • Personalities • Memory</div></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    username = st.text_input("Your name (optional)", st.session_state.get("username",""))
    if username:
        st.session_state["username"] = username
    mood = st.selectbox("Bot Personality", ["Friendly","Formal","Playful","Sarcastic","Teacher"], index=0)
    st.session_state["mood"] = mood
    st.markdown("---")
    st.subheader("Voice Controls")
    voice_on = st.checkbox("Enable Voice Output", value=st.session_state.get("voice_on", False))
    st.session_state["voice_on"] = voice_on
    rate = st.slider("Speaking rate", 80, 260, st.session_state.get("voice_rate", 150))
    st.session_state["voice_rate"] = rate
    volume = st.slider("Volume", 0.1, 1.0, st.session_state.get("voice_volume", 1.0))
    st.session_state["voice_volume"] = volume
    st.selectbox("System voice (optional)", ["Default"])
    st.markdown("---")
    st.subheader("Advanced")
    st.session_state["trim_long_reads"] = st.checkbox("Smart Read (short first)", value=st.session_state.get("trim_long_reads", True))
    use_realtime = st.checkbox("Use realtime APIs for weather/news (optional)", value=False)
    st.session_state["use_realtime"] = use_realtime
    st.markdown("---")
    st.write("Commands: `/help`, `/clear`, `/time`, `/date`, `/about`")
    if st.button("Clear persistent memory (all)"):
        save_memory([])
        st.success("Memory cleared.")
    st.markdown("Gemini available: **{}**".format("Yes" if gemini_available else "No"))
    if not gemini_available:
        st.warning("Gemini SDK missing or API key not configured. Install `google-generativeai` and set GEMINI_API_KEY.")

if "chat" not in st.session_state:
    st.session_state.chat = load_memory()

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

qa1, qa2, qa3, qa4 = st.columns([1,1,1,1])
if qa1.button("☁ Weather (Delhi)"):
    st.session_state.chat.append(("user","weather Delhi", timestamp(), {}))
if qa2.button("😂 Joke"):
    st.session_state.chat.append(("user","tell me a joke", timestamp(), {}))
if qa3.button("💡 Quote"):
    st.session_state.chat.append(("user","inspirational quote", timestamp(), {}))
if qa4.button("📰 News (top)"):
    st.session_state.chat.append(("user","latest news headlines", timestamp(), {}))

def render_chat():
    for i, (role, text, time_str, meta) in enumerate(st.session_state.chat[-200:]):
        safe_text = text.replace("\n","<br>")
        if role == "user":
            st.markdown(f"<div class='bubble user'><b>🧑 {st.session_state.get('username','You')}:</b><br>{safe_text}</div><div class='meta' style='text-align:right'>{time_str}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bubble bot'><b>🤖 Bot:</b><br>{safe_text}</div><div class='meta'>{time_str}</div>", unsafe_allow_html=True)

if not st.session_state.chat:
    welcome = "Hello! I'm your premium assistant. Ask me anything — choose a personality from the sidebar. Try `/help` to see commands."
    st.session_state.chat = [("bot", welcome, timestamp(), {})]

render_chat()

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
col_input, col_send = st.columns([8,1])
with col_input:
    user_input = st.text_input("💬 Type your message (or use a command)", key="main_input", value="")
with col_send:
    send = st.button("Send", key="send_btn")

def handle_command(cmd):
    cmd = cmd.strip().lower()
    if cmd == "/help":
        return ("bot", textwrap.dedent("""
            **Pro Commands**
            - /help — show this help
            - /clear — clear conversation (session)
            - /time — current time
            - /date — current date
            - /about — about this bot
            """), timestamp(), {})
    if cmd == "/clear":
        st.session_state.chat = []
        return ("bot", "Conversation cleared (session).", timestamp(), {})
    if cmd == "/time":
        return ("bot", "🕒 Current time: " + datetime.now().strftime("%H:%M:%S"), timestamp(), {})
    if cmd == "/date":
        return ("bot", "📅 " + datetime.now().strftime("%A, %B %d, %Y"), timestamp(), {})
    if cmd == "/about":
        about = "✨ Premium Text+Voice ChatBot — Gemini-powered (optional). Features: personalities, smart read, persistent memory."
        return ("bot", about, timestamp(), {})
    return None

def system_prompt_for_mood(mood):
    base = "You are a helpful assistant."
    if mood == "Formal":
        return base + " Answer politely, concisely, and formally."
    if mood == "Playful":
        return base + " Be playful, use light humor and friendly tone."
    if mood == "Sarcastic":
        return base + " Use mild sarcasm and witty lines while staying helpful."
    if mood == "Teacher":
        return base + " Explain clearly with examples and simple language."
    return base + " Be friendly, clear, and encouraging."

def build_context_prompt(user_msg, memory_window=8):
    recent = st.session_state.chat[-(memory_window*1 + 1):]
    convo = []
    for role, text, t, meta in recent:
        role_label = "User" if role == "user" else "Assistant"
        convo.append(f"{role_label}: {text}")
    convo_text = "\n".join(convo)
    system_inst = system_prompt_for_mood(st.session_state.get("mood","Friendly"))
    if st.session_state.get("username"):
        system_inst += f" Address the user as {st.session_state['username']} when appropriate."
    prompt = f"{system_inst}\nConversation:\n{convo_text}\nUser: {user_msg}\nAssistant:"
    return prompt

if send and user_input is not None:
    msg = user_input.strip()
    if not msg:
        st.warning("Type a message first.")
    else:
        st.session_state.chat.append(("user", msg, timestamp(), {}))

        if msg.startswith("/"):
            cmd_result = handle_command(msg)
            if cmd_result:
                st.session_state.chat.append(cmd_result)
                save_memory(st.session_state.chat)
                safe_rerun()
            else:
                st.session_state.chat.append(("bot", "Unknown command. Try /help.", timestamp(), {}))
                save_memory(st.session_state.chat)
                safe_rerun()

        prompt = build_context_prompt(msg, memory_window=6)

        with st.spinner("Thinking..."):
            raw_answer = generate_gemini_answer(prompt, system_instruction=None, max_output_tokens=1024)

        displayed, remainder = raw_answer, None
        if st.session_state.get("trim_long_reads", True):
            displayed, remainder = smart_trim_text(raw_answer, max_sentences=3)

        meta = {"full": raw_answer, "remainder": remainder}
        st.session_state.chat.append(("bot", displayed, timestamp(), meta))
        st.session_state.last_response = raw_answer

        if st.session_state.get("voice_on", False):
            speak(displayed, rate=st.session_state.get("voice_rate",150), volume=st.session_state.get("voice_volume",1.0), voice_id=st.session_state.get("voice_voice", None))

        suggestions = []
        low = msg.lower()
        if "weather" in low:
            suggestions = ["Tomorrow's forecast", "Weekly summary", "Humidity details"]
        elif "joke" in low or "fun" in low:
            suggestions = ["Another joke", "Short pun", "Clean joke"]
        else:
            suggestions = ["Explain simply", "Give an example", "Summarize in 2 lines"]

        cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            if cols[i].button(s):
                st.session_state.chat.append(("user", s, timestamp(), {}))
                with st.spinner("Thinking..."):
                    ans = generate_gemini_answer(build_context_prompt(s), max_output_tokens=512)
                st.session_state.chat.append(("bot", ans, timestamp(), {}))
                if st.session_state.get("voice_on", False):
                    speak(ans, rate=st.session_state.get("voice_rate",150), volume=st.session_state.get("voice_volume",1.0), voice_id=st.session_state.get("voice_voice", None))
                save_memory(st.session_state.chat)
                safe_rerun()

        save_memory(st.session_state.chat)
        safe_rerun()

if st.session_state.chat:
    last_role, last_text, last_time, last_meta = st.session_state.chat[-1]
    if last_role == "bot" and last_meta and last_meta.get("remainder"):
        if st.button("Continue reading"):
            remainder_text = last_meta["remainder"]
            st.session_state.chat.append(("bot", remainder_text, timestamp(), {"full": last_meta["full"], "remainder": None}))
            if st.session_state.get("voice_on", False):
                speak(remainder_text, rate=st.session_state.get("voice_rate",150), volume=st.session_state.get("voice_volume",1.0), voice_id=st.session_state.get("voice_voice", None))
            save_memory(st.session_state.chat)
            safe_rerun()

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:#9aa4b2;font-size:12px;margin-top:10px'>Made with ❤️ by Kaif Ansari — Gemini-powered (optional)</div>", unsafe_allow_html=True)

