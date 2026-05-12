import os
import base64
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
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

/* ── Reset & Base ─── */
*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg:          #0d1117;
  --surface:     #161b22;
  --surface-2:   #1c2330;
  --border:      #2a3344;
  --amber:       #f0a500;
  --amber-dim:   #c17f00;
  --amber-glow:  rgba(240,165,0,.12);
  --cream:       #f5ede0;
  --cream-dim:   #c9b89e;
  --text:        #e8ddd0;
  --text-muted:  #7e8d9e;
  --success:     #3fb950;
  --error:       #f85149;
  --radius:      12px;
  --radius-lg:   20px;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'DM Sans', sans-serif !important;
  color: var(--text) !important;
}

[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; }

/* ── Hide Streamlit branding ── */
footer, #MainMenu { visibility: hidden; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }

/* ── Main wrapper ── */
.sauti-wrap {
  min-height: 100vh;
  background:
    radial-gradient(ellipse 60% 40% at 80% 10%, rgba(240,165,0,.06) 0%, transparent 60%),
    radial-gradient(ellipse 50% 50% at 20% 80%, rgba(240,165,0,.04) 0%, transparent 60%),
    var(--bg);
}

/* ── Hero ── */
.sauti-hero {
  padding: 3rem 4rem 2rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 2rem;
}
.sauti-logo-mark {
  width: 52px; height: 52px;
  background: var(--amber);
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 28px rgba(240,165,0,.35);
}
.sauti-logo-mark svg { width: 28px; height: 28px; }
.sauti-title-block h1 {
  font-size: 2rem; margin: 0;
  color: var(--cream);
  letter-spacing: -0.5px;
}
.sauti-title-block p {
  margin: .25rem 0 0; color: var(--text-muted);
  font-size: .9rem; font-weight: 300;
}

/* ── Pipeline badge strip ── */
.pipeline-strip {
  display: flex; align-items: center; gap: 0;
  padding: 1rem 4rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
}
.p-step {
  display: flex; align-items: center; gap: .6rem;
  font-size: .78rem; font-weight: 500;
  color: var(--text-muted);
  white-space: nowrap;
  padding: .35rem .8rem;
  border-radius: 999px;
  transition: color .2s, background .2s;
}
.p-step.active { color: var(--amber); background: var(--amber-glow); }
.p-step.done   { color: var(--success); }
.p-arrow { color: var(--border); margin: 0 .1rem; font-size: .85rem; }
.p-step-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* ── Main layout ── */
.sauti-main {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 0;
  min-height: calc(100vh - 130px);
}

/* ── Left panel ── */
.sauti-left {
  padding: 2rem;
  border-right: 1px solid var(--border);
  background: var(--surface);
}

/* ── Card ── */
.card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.25rem;
}
.card-label {
  font-size: .7rem; font-weight: 600;
  letter-spacing: .08em; text-transform: uppercase;
  color: var(--amber); margin-bottom: .9rem;
  display: flex; align-items: center; gap: .5rem;
}

/* ── Tab switcher ── */
.tab-row {
  display: flex; gap: .5rem; margin-bottom: 1.25rem;
}
.tab-btn {
  flex: 1; padding: .6rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  font-family: 'DM Sans', sans-serif;
  font-size: .85rem; font-weight: 500;
  cursor: pointer;
  transition: all .15s;
  display: flex; align-items: center; justify-content: center; gap: .5rem;
}
.tab-btn.sel {
  border-color: var(--amber);
  background: var(--amber-glow);
  color: var(--amber);
}
.tab-btn:hover:not(.sel) { border-color: var(--text-muted); color: var(--text); }

/* ── Language grid ── */
.lang-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem;
}
.lang-btn {
  padding: .6rem .4rem; border-radius: 8px;
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  font-family: 'DM Sans', sans-serif;
  font-size: .8rem; font-weight: 500;
  cursor: pointer; text-align: center;
  transition: all .15s;
}
.lang-btn.sel {
  border-color: var(--amber);
  background: var(--amber-glow);
  color: var(--amber);
}
.lang-btn:hover:not(.sel) { border-color: var(--cream-dim); color: var(--cream); }

/* ── Run button ── */
.run-btn {
  width: 100%; padding: .85rem;
  background: var(--amber);
  color: #0d1117;
  border: none; border-radius: var(--radius);
  font-family: 'DM Serif Display', serif;
  font-size: 1rem; font-weight: 400; letter-spacing: .3px;
  cursor: pointer;
  transition: background .15s, transform .1s, box-shadow .15s;
  box-shadow: 0 4px 20px rgba(240,165,0,.3);
  display: flex; align-items: center; justify-content: center; gap: .6rem;
  margin-top: .5rem;
}
.run-btn:hover { background: #f7b200; box-shadow: 0 6px 28px rgba(240,165,0,.45); transform: translateY(-1px); }
.run-btn:active { transform: translateY(0); }
.run-btn:disabled { background: var(--border); color: var(--text-muted); cursor: not-allowed;
  box-shadow: none; transform: none; }

/* ── Right panel ── */
.sauti-right {
  padding: 2rem 2.5rem;
  overflow-y: auto;
}

/* ── Result cards ── */
.result-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem 1.75rem;
  margin-bottom: 1.25rem;
  animation: fadeUp .4s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.result-card:nth-child(1) { animation-delay: 0s; }
.result-card:nth-child(2) { animation-delay: .07s; }
.result-card:nth-child(3) { animation-delay: .14s; }
.result-card:nth-child(4) { animation-delay: .21s; }

.rc-head {
  display: flex; align-items: center; gap: .65rem;
  margin-bottom: 1rem;
}
.rc-icon {
  width: 34px; height: 34px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rc-icon.blue   { background: rgba(88,166,255,.12); color: #58a6ff; }
.rc-icon.amber  { background: var(--amber-glow); color: var(--amber); }
.rc-icon.green  { background: rgba(63,185,80,.1); color: var(--success); }
.rc-icon.purple { background: rgba(188,140,255,.1); color: #bc8cff; }

.rc-title  { font-size: .95rem; font-weight: 600; color: var(--cream); }
.rc-sub    { font-size: .75rem; color: var(--text-muted); margin-top: 1px; }
.rc-body   { font-size: .9rem; line-height: 1.65; color: var(--text); }
.rc-body.serif { font-family: 'DM Serif Display', serif; font-size: 1rem; }

/* ── Spinner ── */
.spinner-wrap {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 4rem 2rem; gap: 1.5rem;
  color: var(--text-muted);
}
.spinner {
  width: 44px; height: 44px;
  border: 3px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin .75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.spinner-steps { display: flex; flex-direction: column; gap: .5rem; }
.spinner-step  {
  display: flex; align-items: center; gap: .6rem;
  font-size: .82rem; padding: .4rem .75rem; border-radius: 8px;
  color: var(--text-muted);
}
.spinner-step.active {
  color: var(--amber); background: var(--amber-glow);
}
.spinner-step.done { color: var(--success); }
.spinner-step svg { width: 14px; height: 14px; flex-shrink: 0; }

/* ── Empty state ── */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 5rem 2rem; text-align: center; gap: 1rem;
  color: var(--text-muted);
}
.empty-state-icon {
  width: 64px; height: 64px; border-radius: 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: .5rem;
}

/* ── Error banner ── */
.error-banner {
  background: rgba(248,81,73,.08);
  border: 1px solid rgba(248,81,73,.3);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  color: #f85149;
  font-size: .875rem;
  display: flex; gap: .75rem; align-items: flex-start;
  margin-bottom: 1rem;
}

/* ── Audio player override ── */
audio {
  width: 100%; margin-top: .5rem;
  border-radius: 8px;
  filter: invert(1) hue-rotate(180deg) brightness(.85);
}

/* ── Streamlit overrides for inputs ── */
[data-testid="stTextArea"] textarea {
  background: var(--surface-2) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: .9rem !important;
  resize: vertical !important;
}
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--amber) !important;
  box-shadow: 0 0 0 3px var(--amber-glow) !important;
  outline: none !important;
}
[data-testid="stFileUploader"] {
  background: var(--surface-2) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: var(--radius) !important;
  transition: border-color .15s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--amber) !important;
}
[data-testid="stFileUploader"] label { color: var(--text-muted) !important; }
[data-testid="stSelectbox"] select,
div[data-baseweb="select"] { color: var(--text) !important; }
div[data-baseweb="select"] > div {
  background: var(--surface-2) !important;
  border-color: var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stRadio"] label { color: var(--text) !important; }
p, li, span { color: var(--text) !important; }
label { color: var(--text-muted) !important; }
.stButton button {
  font-family: 'DM Serif Display', serif !important;
  font-size: 1rem !important;
  background: var(--amber) !important;
  color: #0d1117 !important;
  border: none !important;
  border-radius: var(--radius) !important;
  padding: .7rem 2rem !important;
  width: 100% !important;
  box-shadow: 0 4px 20px rgba(240,165,0,.3) !important;
  transition: all .15s !important;
}
.stButton button:hover {
  background: #f7b200 !important;
  box-shadow: 0 6px 28px rgba(240,165,0,.45) !important;
  transform: translateY(-1px) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ──────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "error" not in st.session_state:
    st.session_state.error = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "text"
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "lug"

# ── Helper: SVG icons ──────────────────────────────────────────────────────────
def icon_mic():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>"""

def icon_text():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <polyline points="4 7 4 4 20 4 20 7"/>
      <line x1="9" y1="20" x2="15" y2="20"/>
      <line x1="12" y1="4" x2="12" y2="20"/>
    </svg>"""

def icon_play():
    return """<svg viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>"""

def icon_globe():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>"""

def icon_check():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
      stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>"""

def icon_alert():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>"""

def icon_wave():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round">
      <path d="M2 12 Q5 6 8 12 Q11 18 14 12 Q17 6 20 12 Q22 15 24 12"/>
    </svg>"""

def icon_doc():
    return """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>"""

def icon_sparkle():
    return """<svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L13.09 8.26L19 6L14.74 10.74L21 12L14.74 13.26L19 18L13.09 15.74L12 22L10.91 15.74L5 18L9.26 13.26L3 12L9.26 10.74L5 6L10.91 8.26L12 2Z"/>
    </svg>"""

# ── HERO ───────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="sauti-wrap">
  <div class="sauti-hero">
    <div class="sauti-logo-mark">
      <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 4C9 4 5 8 5 13c0 3 1.5 5.5 3.8 7.1L8 24h8l-.8-3.9C17.5 18.5 19 16 19 13c0-5-4-9-5-9z"
              fill="#0d1117" opacity=".85"/>
        <circle cx="9.5" cy="12" r="1.5" fill="#0d1117"/>
        <circle cx="14" cy="10" r="1.5" fill="#0d1117"/>
        <circle cx="18.5" cy="12" r="1.5" fill="#0d1117"/>
      </svg>
    </div>
    <div class="sauti-title-block">
      <h1>Sauti</h1>
      <p>Your Language Bridge — Transcribe, Summarise & Broadcast in Ugandan Languages</p>
    </div>
  </div>
""",
    unsafe_allow_html=True,
)

# ── PIPELINE STRIP ─────────────────────────────────────────────────────────────
steps = ["Input", "Transcribe", "Summarise", "Translate", "Synthesise", "Output"]
results = st.session_state.results
processing = st.session_state.processing

step_states = []
if not processing and results is None:
    step_states = ["active"] + [""] * 5
elif processing:
    step_states = ["done", "active", "active", "active", "active", ""]
else:  # done
    step_states = ["done"] * 6

strip_html = '<div class="pipeline-strip">'
for i, (s, state) in enumerate(zip(steps, step_states)):
    cls = f"p-step {state}".strip()
    if state == "done":
        dot = f'<svg viewBox="0 0 12 12" fill="currentColor"><circle cx="6" cy="6" r="4"/></svg>'
    else:
        dot = '<div class="p-step-dot"></div>'
    strip_html += f'<div class="{cls}">{dot} {s}</div>'
    if i < len(steps) - 1:
        strip_html += '<span class="p-arrow">›</span>'
strip_html += "</div>"
st.markdown(strip_html, unsafe_allow_html=True)

# ── MAIN BODY ──────────────────────────────────────────────────────────────────
st.markdown('<div class="sauti-main">', unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════╗
# ║  LEFT PANEL — Input + Settings                          ║
# ╚══════════════════════════════════════════════════════════╝
left, right = st.columns([420, 1000], gap="medium")

with left:
    # ── Input mode toggle ──
    st.markdown('<div class="card-label">Input Mode</div>', unsafe_allow_html=True)
    mode = st.radio(
        "input_mode_radio",
        options=["Text", "Audio File"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.input_mode = mode.lower().replace(" ", "_")

    st.markdown("---")

    text_val = None
    audio_file = None

    if st.session_state.input_mode == "text":
        st.markdown('<div class="card-label">Paste or type your text</div>', unsafe_allow_html=True)
        text_val = st.text_area(
            "text_input_area",
            placeholder="Paste a news article, announcement, report or any English text here...",
            height=200,
            label_visibility="collapsed",
        )
    else:
        st.markdown('<div class="card-label">Upload Audio File</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:.8rem;color:var(--text-muted);margin-bottom:.5rem">'
            "MP3, WAV, OGG, M4A · Max 5 minutes</p>",
            unsafe_allow_html=True,
        )
        audio_file = st.file_uploader(
            "audio_upload",
            type=["mp3", "wav", "ogg", "m4a", "aac"],
            label_visibility="collapsed",
        )

    st.markdown("---")

    # ── Language picker ──
    st.markdown('<div class="card-label">Target Language</div>', unsafe_allow_html=True)
    lang_options = {
        "lug": "Luganda",
        "nyn": "Runyankole",
        "teo": "Ateso",
        "lgg": "Lugbara",
        "ach": "Acholi",
    }
    lang_display = list(lang_options.values())
    lang_codes = list(lang_options.keys())

    selected_lang_name = st.selectbox(
        "target_language_select",
        options=lang_display,
        index=lang_codes.index(st.session_state.target_lang),
        label_visibility="collapsed",
    )
    st.session_state.target_lang = lang_codes[lang_display.index(selected_lang_name)]

    st.markdown("---")

    # ── Run button ──
    can_run = (text_val and text_val.strip()) or (audio_file is not None)
    if st.button(
        "Broadcast in " + selected_lang_name,
        disabled=not can_run,
        use_container_width=True,
    ):
        st.session_state.processing = True
        st.session_state.results = None
        st.session_state.error = None

        with st.spinner("Running pipeline — this may take 30–60 seconds…"):
            try:
                audio_bytes = None
                audio_filename = None
                if audio_file:
                    audio_bytes = audio_file.read()
                    audio_filename = audio_file.name

                result = run_pipeline(
                    text_input=text_val if st.session_state.input_mode == "text" else None,
                    audio_bytes=audio_bytes,
                    audio_filename=audio_filename,
                    target_language=st.session_state.target_lang,
                )
                st.session_state.results = result
                st.session_state.error = None
            except Exception as e:
                st.session_state.error = str(e)
                st.session_state.results = None

        st.session_state.processing = False
        st.rerun()

# ╔══════════════════════════════════════════════════════════╗
# ║  RIGHT PANEL — Results                                  ║
# ╚══════════════════════════════════════════════════════════╝
with right:

    # ── Error state ──
    if st.session_state.error:
        st.markdown(
            f"""<div class="error-banner">
              {icon_alert()}
              <div><strong>Something went wrong</strong><br>
              <span style="font-size:.85rem;opacity:.85">{st.session_state.error}</span></div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Empty state ──
    elif st.session_state.results is None and not st.session_state.processing:
        st.markdown(
            f"""<div class="empty-state">
              <div class="empty-state-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="#f0a500" stroke-width="1.5"
                  stroke-linecap="round" stroke-linejoin="round" width="28" height="28">
                  <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
                  <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/>
                  <path d="M3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
                </svg>
              </div>
              <div style="font-family:'DM Serif Display',serif;font-size:1.25rem;color:var(--cream)">
                Ready to broadcast
              </div>
              <div style="font-size:.875rem;max-width:320px;line-height:1.6">
                Enter text or upload audio on the left, choose a language, then click
                <em>Broadcast</em> to run the full pipeline.
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Results ──
    elif st.session_state.results:
        res = st.session_state.results
        lang_name = LANGUAGE_NAMES.get(st.session_state.target_lang, "Local Language")

        # Card 1 — Transcript (audio mode only)
        if res.get("transcript"):
            st.markdown(
                f"""<div class="result-card">
                  <div class="rc-head">
                    <div class="rc-icon blue">{icon_mic()}</div>
                    <div>
                      <div class="rc-title">Transcript</div>
                      <div class="rc-sub">Audio converted to text via Sunbird STT</div>
                    </div>
                  </div>
                  <div class="rc-body">{res['transcript']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Card 2 — Original / Source text (text mode only, skip if audio shown)
        if not res.get("transcript") and res.get("source_text"):
            st.markdown(
                f"""<div class="result-card">
                  <div class="rc-head">
                    <div class="rc-icon blue">{icon_doc()}</div>
                    <div>
                      <div class="rc-title">Source Text</div>
                      <div class="rc-sub">Your original input</div>
                    </div>
                  </div>
                  <div class="rc-body">{res['source_text'][:800]}{'…' if len(res['source_text']) > 800 else ''}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Card 3 — Summary
        if res.get("summary"):
            st.markdown(
                f"""<div class="result-card">
                  <div class="rc-head">
                    <div class="rc-icon amber">{icon_sparkle()}</div>
                    <div>
                      <div class="rc-title">Summary</div>
                      <div class="rc-sub">Condensed by Sunbird Summarisation · PII anonymised</div>
                    </div>
                  </div>
                  <div class="rc-body serif">{res['summary']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Card 4 — Translation
        if res.get("translation"):
            st.markdown(
                f"""<div class="result-card">
                  <div class="rc-head">
                    <div class="rc-icon purple">{icon_globe()}</div>
                    <div>
                      <div class="rc-title">Translated to {lang_name}</div>
                      <div class="rc-sub">Powered by Sunflower LLM</div>
                    </div>
                  </div>
                  <div class="rc-body serif">{res['translation']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Card 5 — Audio
        if res.get("audio_url"):
            st.markdown(
                f"""<div class="result-card">
                  <div class="rc-head">
                    <div class="rc-icon green">{icon_play()}</div>
                    <div>
                      <div class="rc-title">Audio Broadcast in {lang_name}</div>
                      <div class="rc-sub">Generated by Sunbird TTS — play or download below</div>
                    </div>
                  </div>""",
                unsafe_allow_html=True,
            )
            st.audio(res["audio_url"])
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close sauti-wrap