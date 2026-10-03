"""
Text to Voice (Text-to-Speech) App with an animated AI girl "Aira"
Converts text into speech with Google Text-to-Speech (gTTS). No API key needed.
Aira reacts to the voice: her mouth follows the loudness of the audio, she blinks,
nods, shows a mood, and the words light up as they are spoken.
"""
import base64
import json
import re
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS

st.set_page_config(page_title="Text to Voice", page_icon="🎙️", layout="centered")

LANGUAGES = {
    "English": "en", "Hindi": "hi", "Telugu": "te", "Tamil": "ta",
    "Bengali": "bn", "Marathi": "mr", "Kannada": "kn", "Malayalam": "ml",
    "Gujarati": "gu", "Urdu": "ur", "French": "fr", "Spanish": "es",
    "German": "de", "Japanese": "ja",
}
ACCENTS = {"Indian": "co.in", "American": "com", "British": "co.uk", "Australian": "com.au"}  # English only
SAMPLES = {
    "English": "Hello! Welcome to my text to speech project. Have a great day.",
    "Hindi": "नमस्ते! मेरे टेक्स्ट टू स्पीच प्रोजेक्ट में आपका स्वागत है।",
    "Telugu": "నమస్కారం! నా టెక్స్ట్ టు స్పీచ్ ప్రాజెక్ట్‌కు స్వాగతం.",
}
# smile = mouth curve, brow_dy / brow_ang = eyebrow lift and tilt, blush = cheek color, bob = head movement
MOODS = {
    "😊 Happy": {"smile": 14, "brow_dy": -2, "brow_ang": 0, "blush": 0.5, "bob": 1.0},
    "🤩 Excited": {"smile": 22, "brow_dy": -8, "brow_ang": 8, "blush": 0.85, "bob": 1.8},
    "😌 Calm": {"smile": 8, "brow_dy": 0, "brow_ang": -3, "blush": 0.3, "bob": 0.6},
}
MAX_CHARS = 500  # change this number to allow more or fewer characters
OUTFITS = {"Sky blue": "#a9c6e4", "Rose": "#f4a6c0", "Lavender": "#b9a7f0", "Mint": "#9fe0c9"}


def synthesize(text: str, lang: str, tld: str, slow: bool) -> bytes:
    buf = BytesIO()
    gTTS(text=text, lang=lang, tld=tld, slow=slow).write_to_fp(buf)
    return buf.getvalue()


PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
html, body, [class*="css"], .stApp { font-family:'Quicksand', sans-serif; }
.stApp { background:linear-gradient(160deg, #fde4f2 0%, #e6e4ff 55%, #d9f0ff 100%); background-attachment:fixed; }
[data-testid="stHeader"] { background:transparent; }
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp .stCaption { color:#3b2a5a; }
[data-testid="stToolbar"], [data-testid="stToolbar"] * { color:#3b2a5a !important; }

h1.title { margin:0; text-align:center; font-weight:700; font-size:2.6rem; color:#3b2a5a;
  background:linear-gradient(90deg,#8b5cf6,#ff6fae); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
p.sub { text-align:center; margin:4px 0 6px; }

/* Sidebar: deep purple panel, white text, dark boxes */
[data-testid="stSidebar"] { background:#2b1a52 !important; }
[data-testid="stSidebar"] :is(h1,h2,h3,label,p,span,small,div) { color:#ffffff !important; }
[data-testid="stSidebar"] [data-baseweb="select"] div { background-color:#1d1038 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { border:2px solid #a78bfa !important; border-radius:12px !important; }
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill:#ffffff !important; }
[data-baseweb="popover"] :is(ul, li, div) { background:#ffffff !important; color:#3b2a5a !important; }
[data-baseweb="popover"] li:hover { background:#efe7ff !important; }

/* Main inputs */
.stTextArea textarea { background:#ffffff !important; color:#3b2a5a !important; -webkit-text-fill-color:#3b2a5a;
  border:2px solid #c4b5fd !important; border-radius:14px !important; }
.stTextArea textarea:focus { border-color:#ff6fae !important; box-shadow:0 0 0 2px rgba(255,111,174,.3) !important; }
[data-testid="stFileUploaderDropzone"] { background:#ffffff !important; border:2px dashed #c4b5fd !important; border-radius:14px !important; }
[data-testid="stFileUploaderDropzone"] :is(span, small, p, div) { color:#3b2a5a !important; }
[data-testid="stFileUploaderDropzone"] button { background:#8b5cf6 !important; border:0 !important; }
[data-testid="stFileUploaderDropzone"] button * { color:#ffffff !important; }

/* Buttons */
.stButton > button, .stDownloadButton > button { border:0; border-radius:99px; padding:.65rem 1.6rem; font-weight:700;
  background:linear-gradient(135deg,#8b5cf6,#ff6fae); box-shadow:0 4px 0 #5b3fc0; }
.stButton > button, .stButton > button *, .stDownloadButton > button, .stDownloadButton > button * { color:#ffffff !important; }
</style>
"""

AVATAR = """
<style>
  html, body { margin:0; background:transparent; font-family:'Quicksand', 'Segoe UI', sans-serif; color:#3b2a5a; }
  .wrap { max-width:520px; margin:0 auto; text-align:center; }
  #bubble { display:inline-block; background:#fff; border-radius:18px; padding:8px 16px; font-size:15px; font-weight:700;
    box-shadow:0 6px 16px rgba(91,63,192,.18); margin-bottom:6px; }
  svg { width:100%; max-width:340px; height:auto; overflow:visible; }
  .sp { transform-box:fill-box; transform-origin:center; animation:twinkle 3s ease-in-out infinite; }
  .d2 { animation-delay:1s; } .d3 { animation-delay:2s; }
  @keyframes twinkle { 0%,100% { transform:scale(.6); opacity:.5; } 50% { transform:scale(1.15); opacity:1; } }
  .blink { transform-origin:150px 140px; animation:blink 4.2s infinite; }
  @keyframes blink { 0%,93%,100% { transform:scaleY(1); } 96% { transform:scaleY(.08); } }
  .note { position:absolute; font-size:26px; opacity:0; }
  body.speaking .note { animation:float 2.4s ease-in infinite; }
  .n1 { left:14%; top:30%; color:#ff6fae; } .n2 { right:14%; top:36%; color:#8b5cf6; animation-delay:.8s !important; }
  .n3 { right:24%; top:14%; color:#14b8a6; animation-delay:1.5s !important; }
  @keyframes float { 0% { opacity:0; transform:translateY(20px) rotate(-10deg); } 20% { opacity:1; }
    100% { opacity:0; transform:translateY(-70px) rotate(14deg); } }
  .stage { position:relative; }
  #sub { background:rgba(255,255,255,.85); border-radius:16px; padding:12px 16px; margin:6px 0 10px; max-height:96px; overflow:auto;
    line-height:1.7; font-size:16px; text-align:left; position:relative; }
  #sub span { padding:1px 3px; border-radius:6px; transition:background .12s; }
  #sub span.on { background:#ff6fae; color:#fff; }
  audio { width:100%; }
  @media (prefers-reduced-motion: reduce) { .blink, .sp, body.speaking .note { animation:none; } }
</style>
<div class="wrap">
  <div id="bubble">__BUBBLE__</div>
  <div class="stage">
    <span class="note n1">♪</span><span class="note n2">♫</span><span class="note n3">♪</span>
    <svg viewBox="0 0 300 340" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="hair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7e5ab"/><stop offset=".5" stop-color="#ebc97a"/><stop offset="1" stop-color="#d6a652"/></linearGradient>
        <radialGradient id="skin" cx=".5" cy=".4" r=".7"><stop offset="0" stop-color="#ffecdd"/><stop offset=".7" stop-color="#f9d4bc"/><stop offset="1" stop-color="#efba9f"/></radialGradient>
        <radialGradient id="iris2" cx=".5" cy=".4" r=".7"><stop offset="0" stop-color="#9a8d7c"/><stop offset="1" stop-color="#4b4238"/></radialGradient>
        <linearGradient id="dress" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".28"/><stop offset="1" stop-color="#000000" stop-opacity=".12"/></linearGradient>
        <filter id="soft"><feGaussianBlur stdDeviation="4"/></filter>
        <g id="eyeG">
          <ellipse cx="122" cy="140" rx="15" ry="12.5" fill="#fffaf5"/>
          <circle cx="122" cy="140" r="9.5" fill="url(#iris2)"/><circle cx="122" cy="140" r="4.6" fill="#1c1713"/>
          <circle cx="118" cy="136" r="3.2" fill="#fff"/><circle cx="126" cy="144" r="1.6" fill="#fff" opacity=".8"/>
          <path d="M108 133 Q122 121 136 133" stroke="#d1a38c" stroke-width="1.3" fill="none" opacity=".7"/>
          <path d="M106 139 Q122 123 138 139" stroke="#3a2a1c" stroke-width="3.4" fill="none" stroke-linecap="round"/>
          <path d="M137 138 Q142 135 145 130" stroke="#3a2a1c" stroke-width="2.6" fill="none" stroke-linecap="round"/>
          <path d="M110 147 Q122 153 134 147" stroke="#c99a86" stroke-width="1.5" fill="none" opacity=".6"/>
        </g>
      </defs>
      <g style="transform-origin:150px 170px" id="rings">
        <circle cx="150" cy="170" r="132" fill="none" stroke="#ff6fae" stroke-width="3" opacity=".3"/>
        <circle cx="150" cy="170" r="150" fill="none" stroke="#8b5cf6" stroke-width="2" opacity=".22"/>
      </g>
      <ellipse cx="80" cy="304" rx="32" ry="27" fill="__OUTFIT__"/><ellipse cx="80" cy="304" rx="32" ry="27" fill="url(#dress)"/>
      <ellipse cx="220" cy="304" rx="32" ry="27" fill="__OUTFIT__"/><ellipse cx="220" cy="304" rx="32" ry="27" fill="url(#dress)"/>
      <path d="M80 340 Q84 276 126 262 L174 262 Q216 276 220 340Z" fill="__OUTFIT__"/>
      <path d="M80 340 Q84 276 126 262 L174 262 Q216 276 220 340Z" fill="url(#dress)"/>
      <path d="M134 232 L134 266 Q150 278 166 266 L166 232Z" fill="url(#skin)"/>
      <path d="M134 246 Q150 258 166 246 L166 232 L134 232Z" fill="#e7ae92" opacity=".45"/>
      <path d="M150 270 L123 262 L133 288Z M150 270 L177 262 L167 288Z" fill="#ffffff" opacity=".6"/>
      <circle cx="150" cy="298" r="2.6" fill="#eef3fa"/><circle cx="150" cy="316" r="2.6" fill="#eef3fa"/>
      <g id="head">
        <path d="M84 118 Q72 42 150 30 Q228 42 216 118 Q238 150 246 200 Q256 240 244 270 Q236 292 252 316 Q232 322 214 308 Q200 296 206 270 L94 270 Q100 296 86 308 Q68 322 48 316 Q64 292 56 270 Q44 240 54 200 Q62 150 84 118Z" fill="url(#hair)"/>
        <path d="M66 160 Q56 214 68 264 M234 160 Q244 214 232 264 M76 290 Q70 304 62 310 M224 290 Q230 304 238 310" stroke="#fff3c4" stroke-width="3" fill="none" stroke-linecap="round" opacity=".55"/>
        <path d="M70 200 Q56 262 66 304 Q82 300 94 282 Q86 240 98 200Z" fill="url(#hair)"/>
        <path d="M230 200 Q244 262 234 304 Q218 300 206 282 Q214 240 202 200Z" fill="url(#hair)"/>
        <path d="M92 128 Q92 62 150 60 Q208 62 208 128 Q208 190 178 222 Q150 246 122 222 Q92 190 92 128Z" fill="url(#skin)"/>
        <ellipse id="blushL" cx="107" cy="178" rx="18" ry="10" fill="#ff9fb0" filter="url(#soft)"/>
        <ellipse id="blushR" cx="193" cy="178" rx="18" ry="10" fill="#ff9fb0" filter="url(#soft)"/>
        <g class="blink"><use href="#eyeG"/><use href="#eyeG" transform="translate(300 0) scale(-1 1)"/></g>
        <path id="browL" d="M102 120 Q120 111 140 117" stroke="#b2884a" stroke-width="4.5" fill="none" stroke-linecap="round"/>
        <path id="browR" d="M160 117 Q180 111 198 120" stroke="#b2884a" stroke-width="4.5" fill="none" stroke-linecap="round"/>
        <path d="M148 158 Q144 174 137 180 Q150 187 163 180 Q156 174 152 158" stroke="#e2ae98" stroke-width="1.6" fill="none" opacity=".85"/>
        <ellipse cx="150" cy="164" rx="3" ry="8" fill="#fff" opacity=".22"/>
        <path id="mouth" d="" fill="#e27a86" stroke="#b84a5a" stroke-width="2" stroke-linejoin="round"/>
        <path d="M150 52 Q108 52 92 108 Q86 146 94 190 L104 190 Q104 140 124 108 Q142 86 150 52Z" fill="url(#hair)"/>
        <path d="M150 52 Q192 52 208 108 Q214 146 206 190 L196 190 Q196 140 176 108 Q158 86 150 52Z" fill="url(#hair)"/>
        <path d="M144 60 Q112 68 100 112 M156 60 Q188 68 200 112" stroke="#fff3c4" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".6"/>
      </g>
    </svg>
  </div>
  <div id="sub"></div>
  <audio id="a" controls src="__AUDIO__"></audio>
</div>
<script>
const CFG = __MOOD__, WORDS = __WORDS__, HAS_AUDIO = __HAS_AUDIO__;
const a = document.getElementById('a'), sub = document.getElementById('sub'), bubble = document.getElementById('bubble');
const mouth = document.getElementById('mouth'), head = document.getElementById('head'), rings = document.getElementById('rings');
if (!HAS_AUDIO) a.style.display = 'none';
sub.innerHTML = WORDS.map(w => '<span>' + w.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</span>').join(' ');
const spans = sub.querySelectorAll('span');
document.getElementById('blushL').setAttribute('opacity', CFG.blush * 0.8);
document.getElementById('blushR').setAttribute('opacity', CFG.blush * 0.8);
document.getElementById('browL').setAttribute('transform', `translate(0 ${CFG.brow_dy}) rotate(${-CFG.brow_ang} 121 116)`);
document.getElementById('browR').setAttribute('transform', `translate(0 ${CFG.brow_dy}) rotate(${CFG.brow_ang} 179 116)`);

let speaking = false, analyser = null, buf = null, srcNode = null, ctx = null, vol = 0, last = -1;
a.addEventListener('play', () => {
  speaking = true; document.body.classList.add('speaking'); bubble.textContent = '🎙️ Listen to me...';
  try {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    if (!srcNode) {
      srcNode = ctx.createMediaElementSource(a); analyser = ctx.createAnalyser(); analyser.fftSize = 256;
      buf = new Uint8Array(analyser.fftSize); srcNode.connect(analyser); analyser.connect(ctx.destination);
    }
    ctx.resume();
  } catch (e) { analyser = null; }
});
function stop(msg) { speaking = false; document.body.classList.remove('speaking'); bubble.textContent = msg; }
a.addEventListener('pause', () => stop('Paused ✋'));
a.addEventListener('ended', () => { stop('All done! Want another one? ✨'); spans.forEach(s => s.classList.remove('on')); last = -1; });
a.addEventListener('timeupdate', () => {
  if (!a.duration || !spans.length) return;
  const i = Math.min(spans.length - 1, Math.floor(a.currentTime / a.duration * spans.length));
  if (i !== last) {
    if (last >= 0) spans[last].classList.remove('on');
    spans[i].classList.add('on'); last = i; sub.scrollTop = Math.max(0, spans[i].offsetTop - 40);
  }
});

function frame(ts) {
  const t = ts / 1000; let target = 0;
  if (speaking) {
    if (analyser) {
      analyser.getByteTimeDomainData(buf); let s = 0;
      for (const v of buf) { const d = (v - 128) / 128; s += d * d; }
      target = Math.min(1, Math.sqrt(s / buf.length) * 5);
    } else target = 0.3 + 0.5 * Math.abs(Math.sin(t * 11));
  }
  vol += (target - vol) * 0.4;
    const y = 204, up = y + CFG.smile * 0.22, lo = y + CFG.smile * 0.6 + vol * 36;
    mouth.setAttribute('d', `M134 ${y} Q150 ${up} 166 ${y} Q150 ${lo} 134 ${y}Z`);
    head.setAttribute('transform', `translate(0 ${Math.sin(t * 5) * 2.5 * vol * CFG.bob}) rotate(${Math.sin(t * 1.7) * (speaking ? 2.2 : 1) * CFG.bob} 150 262)`);
    rings.style.transform = `scale(${1 + vol * 0.12})`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
"""


def render_avatar(audio, text, mood, outfit):
    words = re.findall(r"\S+", text) if text else []
    bubble = "Press play ▶ and watch me speak!" if audio else "Hi, I'm Aira! ✨ Type something and I'll say it."
    html = (
        AVATAR.replace("__MOOD__", json.dumps(MOODS[mood]))
        .replace("__WORDS__", json.dumps(words))
        .replace("__HAS_AUDIO__", "true" if audio else "false")
        .replace("__AUDIO__", "data:audio/mp3;base64," + base64.b64encode(audio).decode() if audio else "")
        .replace("__OUTFIT__", OUTFITS[outfit])
        .replace("__BUBBLE__", bubble)
    )
    components.html(html, height=640 if audio else 560)


st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ---------------- Sidebar ----------------
st.sidebar.header("🎀 Settings")
lang_name = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
accent = "Indian"
if lang_name == "English":
    accent = st.sidebar.selectbox("Accent", list(ACCENTS.keys()))
slow = st.sidebar.checkbox("Slow speech")
mood = st.sidebar.selectbox("Aira's mood", list(MOODS.keys()))
outfit = st.sidebar.selectbox("Aira's outfit", list(OUTFITS.keys()))
st.sidebar.caption("Tip: type the text in the same language you select.")

# ---------------- Main ----------------
st.markdown('<h1 class="title">🎙️ Text to Voice</h1><p class="sub">Meet Aira. She reads your text out loud and acts it out.</p>',
            unsafe_allow_html=True)

source = st.radio("Input type", ["Type text", "Upload .txt"], horizontal=True)
if source == "Type text":
    text = st.text_area("Your text", value=SAMPLES.get(lang_name, ""), height=160, max_chars=MAX_CHARS)
else:
    file = st.file_uploader("Upload a .txt file", type=["txt"])
    text = file.read().decode("utf-8", errors="ignore") if file else ""
    if len(text) > MAX_CHARS:
        st.warning(f"The file has {len(text)} characters. Only the first {MAX_CHARS} will be used.")
        text = text[:MAX_CHARS]
    if text:
        st.text_area("File content", text, height=160, disabled=True)
st.caption(f"{len(text)} / {MAX_CHARS} characters")

if st.button("🔊 Convert to speech", type="primary"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Aira is getting ready..."):
            try:
                audio = synthesize(text, LANGUAGES[lang_name], ACCENTS[accent], slow)
                st.session_state["tts"] = {"audio": audio, "text": text}
            except Exception as e:
                st.error(f"Failed: {e}. Check your internet connection.")

tts = st.session_state.get("tts")
render_avatar(tts["audio"] if tts else None, tts["text"] if tts else "", mood, outfit)
if tts:
    st.download_button("⬇️ Download MP3", tts["audio"], "speech.mp3", "audio/mpeg")