"""
Sauti — Your Local Language Broadcast Bridge
Powered by Sunbird AI
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend.sunbird_client import LANGUAGE_NAMES
from backend.pipeline import run_pipeline

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sauti — Language Bridge",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg:         #0d1117;
  --surface:    #161b22;
  --surface-2:  #1c2330;
  --border:     #2a3344;
  --amber:      #f0a500;
  --amber-glow: rgba(240,165,0,.12);
  --cream:      #f5ede0;
  --cream-dim:  #c9b89e;
  --text:       #e8ddd0;
  --muted:      #7e8d9e;
  --success:    #3fb950;
  --error:      #f85149;
  --r:          12px;
  --rlg:        18px;
}

/* ── Global background & font ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background: var(--bg) !important;
  font-family: 'DM Sans', sans-serif !important;
  color: var(--text) !important;
}

/* ── Kill default Streamlit chrome ── */
[data-testid="stHeader"]          { display: none !important; }
[data-testid="stSidebar"]         { display: none !important; }
[data-testid="stToolbar"]         { display: none !important; }
[data-testid="stDecoration"]      { display: none !important; }
[data-testid="stStatusWidget"]    { display: none !important; }
footer, #MainMenu                 { display: none !important; }

/* ── Remove all default padding from the main container ── */
.main .block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"] > div:first-child {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Ambient background glow ── */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 55% 35% at 85% 8%,  rgba(240,165,0,.07) 0%, transparent 65%),
    radial-gradient(ellipse 45% 45% at 15% 85%, rgba(240,165,0,.04) 0%, transparent 65%);
}

/* ═══════════════════════════════════════════
   HERO HEADER
═══════════════════════════════════════════ */
.sauti-hero {
  padding: 1.75rem 2.5rem 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: var(--bg);
}
.logo-mark {
  width: 48px; height: 48px; flex-shrink: 0;
  background: var(--amber);
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 24px rgba(240,165,0,.38);
}
.logo-mark svg { width: 26px; height: 26px; }
.hero-text h1 {
  font-family: 'DM Serif Display', serif;
  font-size: 1.85rem; margin: 0; line-height: 1;
  color: var(--cream); letter-spacing: -.4px;
}
.hero-text p {
  margin: .3rem 0 0;
  font-size: .82rem; font-weight: 300;
  color: var(--muted); letter-spacing: .01em;
}

/* ═══════════════════════════════════════════
   PIPELINE STRIP
═══════════════════════════════════════════ */
.pip-strip {
  display: flex; align-items: center;
  padding: .7rem 2.5rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  overflow-x: auto; gap: 2px;
  scrollbar-width: none;
}
.pip-strip::-webkit-scrollbar { display: none; }
.ps {
  display: flex; align-items: center; gap: .45rem;
  font-size: .72rem; font-weight: 500; letter-spacing: .02em;
  color: var(--muted); white-space: nowrap;
  padding: .28rem .7rem; border-radius: 999px;
  transition: color .2s, background .2s;
}
.ps.active { color: var(--amber); background: var(--amber-glow); }
.ps.done   { color: var(--success); }
.ps-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.ps-arr { color: var(--border); font-size: .8rem; padding: 0 2px; user-select: none; }

/* ═══════════════════════════════════════════
   COLUMN PANEL STYLING
   Target Streamlit's actual column containers
═══════════════════════════════════════════ */

/* Left column — input panel */
[data-testid="stHorizontalBlock"] > div:first-child {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  padding: 1.75rem 1.5rem 2rem !important;
  min-height: calc(100vh - 115px) !important;
}

/* Right column — results panel */
[data-testid="stHorizontalBlock"] > div:last-child {
  background: var(--bg) !important;
  padding: 1.75rem 2rem 2rem !important;
  min-height: calc(100vh - 115px) !important;
}

/* Remove gap/padding between columns */
[data-testid="stHorizontalBlock"] {
  gap: 0 !important;
  align-items: stretch !important;
}

/* ═══════════════════════════════════════════
   SECTION LABELS
═══════════════════════════════════════════ */
.sec-label {
  font-size: .68rem; font-weight: 600;
  letter-spacing: .09em; text-transform: uppercase;
  color: var(--amber); margin-bottom: .75rem;
  display: flex; align-items: center; gap: .4rem;
}
.sec-label svg { width: 12px; height: 12px; }

/* ═══════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════ */
.sdiv {
  height: 1px; background: var(--border);
  margin: 1.25rem 0;
}

/* ═══════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
═══════════════════════════════════════════ */

/* Radio buttons */
[data-testid="stRadio"] > div {
  gap: .5rem !important;
}
[data-testid="stRadio"] label {
  background: var(--surface-2) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 9px !important;
  padding: .5rem 1rem !important;
  color: var(--muted) !important;
  font-size: .85rem !important;
  transition: all .15s !important;
  cursor: pointer !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  border-color: var(--amber) !important;
  background: var(--amber-glow) !important;
  color: var(--amber) !important;
}

/* Textarea */
[data-testid="stTextArea"] textarea {
  background: var(--surface-2) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--r) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: .875rem !important;
  line-height: 1.6 !important;
  resize: vertical !important;
  transition: border-color .15s, box-shadow .15s !important;
}
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--amber) !important;
  box-shadow: 0 0 0 3px var(--amber-glow) !important;
  outline: none !important;
}
[data-testid="stTextArea"] textarea::placeholder { color: var(--muted) !important; }

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--surface-2) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: var(--r) !important;
  padding: 1rem !important;
  transition: border-color .15s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--amber) !important; }
[data-testid="stFileUploader"] section { background: transparent !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--muted) !important; font-size: .82rem !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzone"] button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
  font-size: .8rem !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
  background: var(--surface-2) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--r) !important;
  color: var(--text) !important;
}
[data-testid="stSelectbox"] > div > div:focus-within {
  border-color: var(--amber) !important;
  box-shadow: 0 0 0 3px var(--amber-glow) !important;
}
[data-testid="stSelectbox"] svg { color: var(--muted) !important; }
[data-baseweb="popover"] { background: var(--surface-2) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
[role="listbox"] { background: var(--surface-2) !important; }
[role="option"]  { color: var(--text) !important; font-size: .875rem !important; }
[role="option"]:hover { background: var(--amber-glow) !important; color: var(--amber) !important; }

/* Button */
[data-testid="stButton"] button {
  width: 100% !important;
  background: var(--amber) !important;
  color: #0d1117 !important;
  border: none !important;
  border-radius: var(--r) !important;
  font-family: 'DM Serif Display', serif !important;
  font-size: .95rem !important;
  padding: .75rem 1.5rem !important;
  box-shadow: 0 4px 18px rgba(240,165,0,.3) !important;
  transition: background .15s, box-shadow .15s, transform .1s !important;
  letter-spacing: .2px !important;
}
[data-testid="stButton"] button:hover {
  background: #f7b200 !important;
  box-shadow: 0 6px 26px rgba(240,165,0,.45) !important;
  transform: translateY(-1px) !important;
}
[data-testid="stButton"] button:active { transform: translateY(0) !important; }
[data-testid="stButton"] button:disabled {
  background: var(--surface-2) !important;
  color: var(--muted) !important;
  box-shadow: none !important;
  transform: none !important;
  border: 1px solid var(--border) !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: var(--amber) !important; }
[data-testid="stSpinner"] svg { stroke: var(--amber) !important; }

/* General text colour fixes */
p, span, li, label, div { color: inherit !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; margin: 0 !important; }

/* Audio player */
audio {
  width: 100% !important;
  border-radius: 8px !important;
  margin-top: .5rem !important;
}

/* ═══════════════════════════════════════════
   RESULT CARDS
═══════════════════════════════════════════ */
.rcard {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  animation: fadeUp .35s ease both;
}
.rcard:nth-child(1) { animation-delay: .00s; }
.rcard:nth-child(2) { animation-delay: .06s; }
.rcard:nth-child(3) { animation-delay: .12s; }
.rcard:nth-child(4) { animation-delay: .18s; }
.rcard:nth-child(5) { animation-delay: .24s; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.rcard-head {
  display: flex; align-items: center; gap: .65rem;
  margin-bottom: .9rem;
}
.rcard-icon {
  width: 32px; height: 32px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.rcard-icon svg { width: 15px; height: 15px; }
.ic-blue   { background: rgba(88,166,255,.12); color: #58a6ff; }
.ic-amber  { background: var(--amber-glow);    color: var(--amber); }
.ic-green  { background: rgba(63,185,80,.1);   color: var(--success); }
.ic-purple { background: rgba(188,140,255,.1); color: #bc8cff; }

.rcard-title { font-size: .9rem; font-weight: 600; color: var(--cream); line-height: 1.2; }
.rcard-sub   { font-size: .72rem; color: var(--muted); margin-top: 2px; }
.rcard-body  {
  font-size: .875rem; line-height: 1.7; color: var(--text);
  border-top: 1px solid var(--border);
  padding-top: .85rem; margin-top: 0;
}
.rcard-body.serif { font-family: 'DM Serif Display', serif; font-size: .95rem; line-height: 1.65; }

/* ═══════════════════════════════════════════
   EMPTY STATE
═══════════════════════════════════════════ */
.empty-st {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; text-align: center;
  padding: 4rem 2rem; gap: .85rem;
  color: var(--muted);
  min-height: 400px;
}
.empty-icon {
  width: 60px; height: 60px; border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: .25rem;
}
.empty-st h3 {
  font-family: 'DM Serif Display', serif;
  font-size: 1.2rem; color: var(--cream); margin: 0;
}
.empty-st p { font-size: .83rem; max-width: 280px; line-height: 1.65; margin: 0; color: var(--muted); }

/* ═══════════════════════════════════════════
   ERROR BANNER
═══════════════════════════════════════════ */
.err-banner {
  background: rgba(248,81,73,.07);
  border: 1px solid rgba(248,81,73,.28);
  border-radius: var(--r);
  padding: 1rem 1.25rem;
  display: flex; gap: .75rem; align-items: flex-start;
  margin-bottom: 1rem;
}
.err-banner svg { width: 16px; height: 16px; color: var(--error); flex-shrink: 0; margin-top: 2px; }
.err-title { font-size: .875rem; font-weight: 600; color: var(--error); }
.err-msg   { font-size: .82rem; color: rgba(248,81,73,.8); margin-top: 3px; line-height: 1.5; }

/* ═══════════════════════════════════════════
   HINT TEXT
═══════════════════════════════════════════ */
.hint { font-size: .75rem; color: var(--muted); margin-top: .3rem; line-height: 1.5; }

</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("results", None), ("error", None), ("processing", False),
              ("input_mode", "Text"), ("target_lang", "lug")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── SVG icon helpers (clean, no emoji) ────────────────────────────────────────
def _svg(path_d, viewbox="0 0 24 24", fill="none", stroke="currentColor", extra=""):
    return (f'<svg viewBox="{viewbox}" fill="{fill}" stroke="{stroke}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" {extra}>{path_d}</svg>')

SVG_MIC    = _svg('<path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>'
                  '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/>')
SVG_DOC    = _svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                  '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
                  '<line x1="16" y1="17" x2="8" y2="17"/>')
SVG_STAR   = _svg('<path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>',
                  fill="currentColor", stroke="none")
SVG_GLOBE  = _svg('<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
                  '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>')
SVG_PLAY   = _svg('<polygon points="5 3 19 12 5 21 5 3"/>', fill="currentColor", stroke="none")
SVG_ALERT  = _svg('<circle cx="12" cy="12" r="10"/>'
                  '<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>')
SVG_RADIO  = _svg('<path d="M3 18v-6a9 9 0 0 1 18 0v6"/>'
                  '<path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/>'
                  '<path d="M3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>')
SVG_UPLOAD = _svg('<polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>'
                  '<path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>')


# ═══════════════════════════════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="sauti-hero">
  <div class="logo-mark">
    <svg viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="13" cy="11" rx="7" ry="8" fill="#0d1117" opacity=".8"/>
      <circle cx="9"  cy="10.5" r="1.5" fill="#0d1117"/>
      <circle cx="13" cy="8.5"  r="1.5" fill="#0d1117"/>
      <circle cx="17" cy="10.5" r="1.5" fill="#0d1117"/>
      <rect x="10" y="18" width="6" height="5" rx="1" fill="#0d1117" opacity=".7"/>
    </svg>
  </div>
  <div class="hero-text">
    <h1>Sauti</h1>
    <p>Your Language Bridge &mdash; Transcribe, Summarise &amp; Broadcast in Ugandan Languages</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE STRIP
# ═══════════════════════════════════════════════════════════════════════════════
res = st.session_state.results
proc = st.session_state.processing

if proc:
    states = ["done", "active", "active", "active", "active", ""]
elif res:
    states = ["done"] * 6
else:
    states = ["active", "", "", "", "", ""]

STEPS = ["Input", "Transcribe", "Summarise", "Translate", "Synthesise", "Output"]
html = '<div class="pip-strip">'
for i, (label, state) in enumerate(zip(STEPS, states)):
    dot = ('<svg viewBox="0 0 10 10" fill="currentColor" width="8" height="8">'
           '<circle cx="5" cy="5" r="4"/></svg>' if state == "done"
           else '<div class="ps-dot"></div>')
    html += f'<div class="ps {state}">{dot} {label}</div>'
    if i < len(STEPS) - 1:
        html += '<span class="ps-arr">›</span>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TWO-COLUMN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1, 1.85], gap="small")


# ╔══════════════════════════════╗
# ║  LEFT — Input & Settings    ║
# ╚══════════════════════════════╝
with left:

    # Input mode
    st.markdown('<div class="sec-label">Input Mode</div>', unsafe_allow_html=True)
    mode = st.radio(
        "mode_radio",
        options=["Text", "Audio File"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.input_mode = mode

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

    text_val = None
    audio_file = None

    if mode == "Text":
        st.markdown('<div class="sec-label">Paste or type your content</div>', unsafe_allow_html=True)
        text_val = st.text_area(
            "txt",
            placeholder="Paste a news article, announcement, report or any English text here…",
            height=210,
            label_visibility="collapsed",
        )
    else:
        st.markdown(
            f'<div class="sec-label">{SVG_UPLOAD} Upload Audio File</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<p class="hint">Supported: MP3, WAV, OGG, M4A &nbsp;·&nbsp; Max 5 minutes</p>',
                    unsafe_allow_html=True)
        audio_file = st.file_uploader(
            "audio",
            type=["mp3", "wav", "ogg", "m4a", "aac"],
            label_visibility="collapsed",
        )

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

    # Language picker
    st.markdown('<div class="sec-label">Target Language</div>', unsafe_allow_html=True)
    LANGS = {"lug": "Luganda", "nyn": "Runyankole", "teo": "Ateso", "lgg": "Lugbara", "ach": "Acholi"}
    lang_names = list(LANGS.values())
    lang_codes = list(LANGS.keys())

    sel_name = st.selectbox(
        "lang",
        options=lang_names,
        index=lang_codes.index(st.session_state.target_lang),
        label_visibility="collapsed",
    )
    st.session_state.target_lang = lang_codes[lang_names.index(sel_name)]

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

    # Run button
    can_run = bool((text_val and text_val.strip()) or audio_file)
    clicked = st.button(
        f"Broadcast in {sel_name}",
        disabled=not can_run,
        use_container_width=True,
    )

    if clicked:
        st.session_state.processing = True
        st.session_state.results = None
        st.session_state.error = None

        with st.spinner(f"Running pipeline — this may take 30–60 s on the free tier…"):
            try:
                audio_bytes, audio_filename = None, None
                if audio_file:
                    audio_bytes = audio_file.read()
                    audio_filename = audio_file.name

                result = run_pipeline(
                    text_input=text_val if mode == "Text" else None,
                    audio_bytes=audio_bytes,
                    audio_filename=audio_filename,
                    target_language=st.session_state.target_lang,
                )
                st.session_state.results = result
                st.session_state.error = None
            except Exception as exc:
                st.session_state.error = str(exc)
                st.session_state.results = None

        st.session_state.processing = False
        st.rerun()


# ╔══════════════════════════════╗
# ║  RIGHT — Results            ║
# ╚══════════════════════════════╝
with right:

    # ── Error ──
    if st.session_state.error:
        st.markdown(f"""
        <div class="err-banner">
          {SVG_ALERT}
          <div>
            <div class="err-title">Something went wrong</div>
            <div class="err-msg">{st.session_state.error}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Empty state ──
    elif not st.session_state.results:
        st.markdown(f"""
        <div class="empty-st">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#f0a500" stroke-width="1.5"
              stroke-linecap="round" stroke-linejoin="round" width="28" height="28">
              <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
              <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/>
              <path d="M3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
            </svg>
          </div>
          <h3>Ready to broadcast</h3>
          <p>Enter text or upload an audio file on the left, choose a target language,
             then click <em>Broadcast</em> to run the full pipeline.</p>
        </div>""", unsafe_allow_html=True)

    # ── Results ──
    else:
        r = st.session_state.results
        lang = LANGUAGE_NAMES.get(st.session_state.target_lang, "Local Language")

        def rcard(icon_html, icon_cls, title, sub, body, serif=False):
            body_cls = "rcard-body serif" if serif else "rcard-body"
            st.markdown(f"""
            <div class="rcard">
              <div class="rcard-head">
                <div class="rcard-icon {icon_cls}">{icon_html}</div>
                <div>
                  <div class="rcard-title">{title}</div>
                  <div class="rcard-sub">{sub}</div>
                </div>
              </div>
              <div class="{body_cls}">{body}</div>
            </div>""", unsafe_allow_html=True)

        # Transcript (audio mode)
        if r.get("transcript"):
            rcard(SVG_MIC, "ic-blue", "Transcript",
                  "Audio converted to text via Sunbird STT",
                  r["transcript"])

        # Source text (text mode)
        if not r.get("transcript") and r.get("source_text"):
            body = r["source_text"][:900] + ("…" if len(r["source_text"]) > 900 else "")
            rcard(SVG_DOC, "ic-blue", "Source Text",
                  "Your original input", body)

        # Summary
        if r.get("summary"):
            rcard(SVG_STAR, "ic-amber", "Summary",
                  "Condensed by Sunbird Summarisation · PII anonymised",
                  r["summary"], serif=True)

        # Translation
        if r.get("translation"):
            rcard(SVG_GLOBE, "ic-purple", f"Translated to {lang}",
                  "Powered by Sunflower LLM",
                  r["translation"], serif=True)

        # Audio player card
        if r.get("audio_url"):
            st.markdown(f"""
            <div class="rcard">
              <div class="rcard-head">
                <div class="rcard-icon ic-green">{SVG_PLAY}</div>
                <div>
                  <div class="rcard-title">Audio Broadcast in {lang}</div>
                  <div class="rcard-sub">Generated by Sunbird TTS — play or download</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            st.audio(r["audio_url"])